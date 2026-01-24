from backend.database import get_connection


def listar_registros():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registros")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "data": row[1], "categoria": row[2], "valor": row[3]}
        for row in rows
    ]


def inserir_registro(data, categoria, valor):
    conn = get_connection()
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
    conn = get_connection()
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM registros WHERE id = ?",
        (id_,),
    )
    conn.commit()
    conn.close()
