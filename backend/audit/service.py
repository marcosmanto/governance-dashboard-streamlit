import json
from datetime import datetime, timezone

from backend.audit.hash import compute_event_hash
from backend.db import connect, execute, normalize_error, query


def obter_ultimo_hash(conn):
    rows = query(
        conn,
        """
        SELECT event_hash
            FROM auditoria
        WHERE event_hash IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        {},
    )
    return rows[0]["event_hash"] if rows else None


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
        # 1️⃣ Normalizar payloads ANTES (string única e determinística) e gerar timestamp
        payload_before_json = (
            json.dumps(payload_before, sort_keys=True, ensure_ascii=False)
            if payload_before
            else None
        )
        payload_after_json = (
            json.dumps(payload_after, sort_keys=True, ensure_ascii=False) if payload_after else None
        )

        timestamp = datetime.now(timezone.utc).isoformat()

        # 2️⃣ Buscar hash anterior
        prev_hash = obter_ultimo_hash(conn)

        # 3️⃣ Calcular hash do evento (usando exatamente o que será salvo)
        event_hash = compute_event_hash(
            timestamp=timestamp,
            username=username,
            role=role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            payload_before=payload_before_json,
            payload_after=payload_after_json,
            endpoint=endpoint,
            method=method,
            prev_hash=prev_hash,
        )

        # 4️⃣ Persistir evento COM hash
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
                method,
                prev_hash,
                event_hash
            )
            VALUES (
                :timestamp,
                :username,
                :role,
                :action,
                :resource,
                :resource_id,
                :payload_before,
                :payload_after,
                :endpoint,
                :method,
                :prev_hash,
                :event_hash
            )
            """,
            {
                "timestamp": timestamp,
                "username": username,
                "role": role,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "payload_before": payload_before_json,
                "payload_after": payload_after_json,
                "endpoint": endpoint,
                "method": method,
                "prev_hash": prev_hash,
                "event_hash": event_hash,
            },
        )

        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise normalize_error(exc)
    finally:
        conn.close()
