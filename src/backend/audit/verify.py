import json
from datetime import datetime, timezone

from backend.audit.hash import compute_event_hash
from backend.db import execute, query


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

    # Inicializa variáveis de estado (assumindo sucesso por padrão)
    status = "OK"
    violated_at = None
    violated_event_id = None
    reason = None
    broken_result = None

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
            broken_result = {
                "valid": False,
                "reason": "event_hash mismatch",
                "broken_at_id": row["id"],
                "expected": recalculated_hash,
                "found": row["event_hash"],
            }
            status = "VIOLATED"
            violated_at = datetime.now(timezone.utc).isoformat()
            violated_event_id = row["id"]
            reason = "event_hash mismatch"
            break

        # 2️⃣ Cadeia quebrada (prev_hash não bate)
        if row["prev_hash"] != prev_hash:
            broken_result = {
                "valid": False,
                "reason": "prev_hash mismatch",
                "broken_at_id": row["id"],
                "expected_prev_hash": prev_hash,
                "found_prev_hash": row["prev_hash"],
            }
            status = "VIOLATED"
            violated_at = datetime.now(timezone.utc).isoformat()
            violated_event_id = row["id"]
            reason = "prev_hash mismatch"
            break

        prev_hash = row["event_hash"]

    # 3️⃣ Atualizar status global de integridade
    execute(
        conn,
        """
        UPDATE audit_integrity
           SET status = :status,
               last_check_at = :now,
               violated_at = :violated_at,
               violated_event_id = :violated_event_id,
               reason = :reason
         WHERE id = 1
        """,
        {
            "status": status,
            "now": datetime.now(timezone.utc).isoformat(),
            "violated_at": violated_at,
            "violated_event_id": violated_event_id,
            "reason": reason,
        },
    )
    conn.commit()

    if broken_result:
        # 4️⃣ Registrar evento forense de violação (FORA DA CADEIA - event_hash NULL)
        # Isso serve como evidência imutável do momento da detecção.
        payload_evidence = json.dumps(broken_result, default=str)
        execute(
            conn,
            """
            INSERT INTO auditoria (
                timestamp, username, role, action, resource, resource_id,
                payload_before, payload_after, endpoint, method, prev_hash, event_hash
            ) VALUES (
                :timestamp, 'system', 'system', 'AUDIT_VIOLATION', 'auditoria', :res_id,
                NULL, :payload, '/admin/audit/verify', 'INTERNAL', NULL, NULL
            )
            """,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "res_id": violated_event_id,
                "payload": payload_evidence,
            },
        )
        conn.commit()

        return broken_result

    return {
        "valid": True,
        "checked_events": len(rows),
    }
