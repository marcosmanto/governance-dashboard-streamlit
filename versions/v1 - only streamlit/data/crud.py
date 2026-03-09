from data.database import criar_conexao


def inserir_registro(data, categoria, valor):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO registros (data, categoria, valor)
        VALUES (?, ?, ?)
        """,
        (data, categoria, valor),
    )
    conn.commit()
    conn.close()


def atualizar_registro(id_, data, categoria, valor):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE registros
        SET data = ?, categoria = ?, valor = ?
        WHERE id = ?
        """,
        (data, categoria, valor, id_),
    )
    conn.commit()
    conn.close()


def deletar_registro(id_):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM registros WHERE id = ?",
        (id_,),
    )
    conn.commit()
    conn.close()
