from typing import Any, Dict, List

from backend.db import connect, execute, normalize_error, query


def obter_registro_por_id(id_) -> Dict[str, Any] | None:
    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT id, data, categoria, valor
            FROM registros
            WHERE id = :id
            """,
            {
                "id": id_,
            },
        )
        if not rows:
            return None

        row = rows[0]
        return {
            "id": row[0],
            "data": row[1],
            "categoria": row[2],
            "valor": row[3],
        }
    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def listar_registros() -> List[Dict[str, Any]]:
    conn = connect()
    try:
        rows = query(conn, "SELECT * FROM registros ORDER BY data DESC")
        result = []
        for r in rows:
            if isinstance(r, dict) or hasattr(r, "keys"):  # sqlite3.Row
                result.append(
                    {
                        "id": r["id"],
                        "data": r["data"],
                        "categoria": r["categoria"],
                        "valor": r["valor"],
                    }
                )
            else:
                result.append(
                    {
                        "id": r[0],
                        "data": r[1],
                        "categoria": r[2],
                        "valor": r[3],
                    }
                )
        return result
    finally:
        conn.close()


def inserir_registro(registro, origem: str = "streamlit") -> None:
    conn = connect()
    try:
        execute(
            conn,
            "INSERT INTO registros (data, categoria, valor, origem) VALUES (:data, :categoria, :valor, :origem)",
            {
                "data": registro.data,
                "categoria": registro.categoria,
                "valor": registro.valor,
                "origem": origem,
            },
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def upsert_registro(registro, origem: str = "streamlit") -> None:
    """
    UP SERT VIA VIEW (vw_registros_upsert) — COMO FUNCIONA E IMPACTO NA CONSISTÊNCIA

    1) Chave lógica e unicidade:
       - A unicidade de (data, categoria) é garantida por um ÍNDICE UNIQUE criado na migration V003.
         Isso significa que, independente da rota (view ou insert direto na tabela), o banco
         NÃO permitirá duas linhas distintas com o mesmo par (data, categoria).

    2) Por que usar a VIEW para escrever?
       - A view tem um gatilho INSTEAD OF INSERT que traduz o insert em:
           INSERT INTO registros (...)
           ON CONFLICT(data, categoria) DO UPDATE ...
         Ou seja, se já existir um registro com (data, categoria), em vez de falhar, o
         comando vira um UPDATE atômico da linha existente (padrão “last-write-wins”).
       - Benefício: sua aplicação fica idempotente quanto à chave lógica; você pode “inserir”
         sempre que quiser, e o banco decide se insere ou atualiza sem erro de integridade.

    3) E se eu fizer INSERT direto na tabela (sem a view)?
       - A integridade também é verificada porque o UNIQUE está na TABELA.
       - Diferença: o INSERT direto vai levantar sqlite3.IntegrityError se o par (data, categoria)
         já existir, pois não há a cláusula ON CONFLICT para converter em UPDATE. Você teria
         que tratar a exceção e decidir o que fazer (ex.: tentar um UPDATE depois).
       - Resumo:
           • INSERT via VIEW  -> nunca cria duplicado; resolve conflito com UPDATE automático.
           • INSERT direto    -> integridade é verificada igual; porém, em caso de duplicidade,
                                 sua aplicação recebe ERRO em vez de “update automático”.

    4) Timestamps com seu desenho atual (V002 + V003):
       - No caminho INSERT (sem conflito):
           • 'criado_em' é preenchido por trigger AFTER INSERT se vier NULL.
           • 'atualizado_em' NÃO é setado automaticamente no INSERT (fica NULL até o primeiro UPDATE).
       - No caminho UPDATE (conflito pelo UPSERT ou UPDATE por id):
           • 'atualizado_em' é atualizado para CURRENT_TIMESTAMP (via DO UPDATE da view ou via trigger AFTER UPDATE).
       - Se você preferir que 'atualizado_em' já nasça igual ao 'criado_em' nos INSERTs sem conflito,
         há duas opções:
           (a) criar um trigger AFTER INSERT que set 'atualizado_em = CURRENT_TIMESTAMP' quando for NULL; ou
           (b) alterar o trigger da VIEW para já inserir 'atualizado_em = CURRENT_TIMESTAMP' no caminho INSERT.

    5) Concorrência:
       - Você habilitou WAL na V003, o que melhora leituras concorrentes e reduz bloqueios.
       - O UPSERT (INSERT ... ON CONFLICT DO UPDATE) é atômico por linha; duas gravações simultâneas
         para a mesma (data, categoria) não criam duplicado — no pior caso, a última vence.
         Se você precisar mesclar valores (ex.: somar 'valor' em vez de sobrescrever), basta
         ajustar a cláusula DO UPDATE para refletir essa regra.

    6) Quando usar cada rota?
       - Use SEMPRE a VIEW quando a “identidade” do registro for (data, categoria) e você
         quiser evitar lidar com erros de duplicidade no app.
       - Use UPDATE por id (id_) quando a edição for explícita de uma linha específica.
    """
    conn = connect()
    try:
        # Insere na VIEW; o gatilho INSTEAD OF converte em INSERT ... ON CONFLICT ... faz UPDATE
        execute(
            conn,
            "INSERT INTO vw_registros_upsert (data, categoria, valor, origem) VALUES (:data, :categoria, :valor, :origem)",
            {
                "data": registro.data,
                "categoria": registro.categoria,
                "valor": registro.valor,
                "origem": origem,
            },
        )
        conn.commit()

    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def atualizar_registro_com_auditoria(id_, registro):
    """
    Atualiza um registro por ID e retorna (antes, depois).
    Retorna None se o registro não existir.
    """

    conn = connect()
    try:
        antes = obter_registro_por_id(id_)
        if not antes:
            return None

        execute(
            conn,
            """
            UPDATE registros
               SET data = :data, categoria = :categoria, valor = :valor
             WHERE id = :id
            """,
            {
                "data": registro.data,
                "categoria": registro.categoria,
                "valor": registro.valor,
                "id": id_,
            },
        )

        conn.commit()
        depois = obter_registro_por_id(id_)
        return antes, depois

    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def atualizar_registro(id_, registro) -> bool:
    """
    Atualiza um registro por ID.
    - Não altera 'atualizado_em' manualmente; trigger cuida disso.
    - Pode lançar sqlite3.IntegrityError se (data, categoria) colidir com outro registro.
    Retorna:
        True  -> se 1 linha foi atualizada
        False -> se nenhum registro com esse id_ foi encontrado
    """

    conn = connect()
    try:
        cur = execute(
            conn,
            """
            UPDATE registros
               SET data = :data, categoria = :categoria, valor = :valor
             WHERE id = :id
            """,
            {
                "data": registro.data,
                "categoria": registro.categoria,
                "valor": registro.valor,
                "id": id_,
            },
        )
        conn.commit()
        return cur.rowcount == 1

    except Exception as exc:
        # ocorre se (data, categoria) já existir em outro registro (índice UNIQUE)
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def deletar_registro_com_auditoria(id_) -> None:
    conn = connect()
    try:
        antes = obter_registro_por_id(id_)
        if not antes:
            return None

        execute(
            conn,
            "DELETE FROM registros WHERE id = :id",
            {"id": id_},
        )
        conn.commit()
        return antes
    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()


def deletar_registro(id_) -> None:
    conn = connect()
    try:
        execute(
            conn,
            "DELETE FROM registros WHERE id = :id",
            {"id": id_},
        )
        conn.commit()

    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()
