import hashlib
import json


def compute_event_hash(
    *,
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
):
    canonical = {
        "timestamp": timestamp,
        "username": username,
        "role": role,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "payload_before": payload_before,
        "payload_after": payload_after,
        "endpoint": endpoint,
        "method": method,
        "prev_hash": prev_hash,
    }

    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
