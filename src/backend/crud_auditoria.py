from backend.db import connect, normalize_error, query


def listar_auditoria(
    *,
    username=None,
    action=None,
    resource=None,
    data_inicio=None,
    data_fim=None,
    limit=500,
):
    conn = connect()
    try:
        sql = """
        SELECT id, timestamp, username, role, action,
               resource, resource_id,
               payload_before, payload_after,
               endpoint, method
          FROM auditoria
         WHERE 1=1
        """

        params = {}

        if username:
            sql += " AND username = :username"
            params["username"] = username

        if action:
            sql += " AND action = :action"
            params["action"] = action

        if resource:
            sql += " AND resource = :resource"
            params["resource"] = resource

        # =========================
        # 🗓️ FILTRO POR DATA
        # =========================
        if data_inicio:
            sql += " AND timestamp >= :data_inicio"
            params["data_inicio"] = f"{data_inicio}T00:00:00"

        if data_fim:
            sql += " AND timestamp <= :data_fim"
            params["data_fim"] = f"{data_fim}T23:59:59.999999"

        sql += " ORDER BY timestamp DESC LIMIT :limit"
        params["limit"] = limit

        rows = query(conn, sql, params)

        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "username": row["username"],
                "role": row["role"],
                "action": row["action"],
                "resource": row["resource"],
                "resource_id": row["resource_id"],
                "payload_before": row["payload_before"],
                "payload_after": row["payload_after"],
                "endpoint": row["endpoint"],
                "method": row["method"],
            }
            for row in rows
        ]

    except Exception as exc:
        raise normalize_error(exc)
    finally:
        conn.close()
