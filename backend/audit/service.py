import json
from datetime import datetime, timezone

from backend.db import connect, execute, normalize_error


def registrar_evento(
    *,
    username: str,
    role: str,
    action: str,
    resource: str,
    resource_id: int | None,
    payload_before: dict | None,
    payload_after: dict | None,
    endpoint: str,
    method: str,
):
    conn = connect()
    try:
        execute(
            conn,
            """
            INSERT INTO auditoria (
                timestamp,
                username,
                role,
                action,
                resource,
                resource_id,
                payload_before,
                payload_after,
                endpoint,
                method
            )
            VALUES (:timestamp,:username,:role,:action,:resource,:resource_id,:payload_before,:payload_after,:endpoint,:method)
            """,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "username": username,
                "role": role,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "payload_before": json.dumps(payload_before) if payload_before else None,
                "payload_after": json.dumps(payload_after) if payload_after else None,
                "endpoint": endpoint,
                "method": method,
            },
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()
