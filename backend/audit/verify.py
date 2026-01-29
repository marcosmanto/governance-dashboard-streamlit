from backend.audit.hash import compute_event_hash
from backend.db import query


def verificar_integridade_auditoria(conn):
    """
    Verifica a integridade da cadeia de auditoria.
    Retorna dict com status e ponto de falha (se houver).
    """

    rows = query(
        conn,
        """
        SELECT
            id,
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
        FROM auditoria
        WHERE event_hash IS NOT NULL
        ORDER BY id
        """,
        {},
    )

    prev_hash = None

    for row in rows:
        recalculated_hash = compute_event_hash(
            timestamp=row["timestamp"],
            username=row["username"],
            role=row["role"],
            action=row["action"],
            resource=row["resource"],
            resource_id=row["resource_id"],
            payload_before=row["payload_before"],
            payload_after=row["payload_after"],
            endpoint=row["endpoint"],
            method=row["method"],
            prev_hash=prev_hash,
        )

        # 1️⃣ Hash do próprio evento foi adulterado
        if recalculated_hash != row["event_hash"]:
            return {
                "valid": False,
                "reason": "event_hash mismatch",
                "broken_at_id": row["id"],
                "expected": recalculated_hash,
                "found": row["event_hash"],
            }

        # 2️⃣ Cadeia quebrada (prev_hash não bate)
        if row["prev_hash"] != prev_hash:
            return {
                "valid": False,
                "reason": "prev_hash mismatch",
                "broken_at_id": row["id"],
                "expected_prev_hash": prev_hash,
                "found_prev_hash": row["prev_hash"],
            }

        prev_hash = row["event_hash"]

    return {
        "valid": True,
        "checked_events": len(rows),
    }
