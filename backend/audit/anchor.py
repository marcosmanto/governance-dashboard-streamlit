from datetime import datetime, timezone

import requests
from fastapi import HTTPException

from backend.audit.service import obter_ultimo_hash
from backend.core.config import settings
from backend.db import connect

# Cache simples para evitar login repetitivo no Pastebin
_cached_user_key: str | None = None


def _get_pastebin_user_key() -> str | None:
    global _cached_user_key
    if _cached_user_key:
        return _cached_user_key

    if not settings.PASTEBIN_USERNAME or not settings.PASTEBIN_PASSWORD:
        return None  # Sem credenciais, segue como Guest

    login_data = {
        "api_dev_key": settings.PASTEBIN_DEV_KEY,
        "api_user_name": settings.PASTEBIN_USERNAME,
        "api_user_password": settings.PASTEBIN_PASSWORD,
    }

    resp = requests.post("https://pastebin.com/api/api_login.php", data=login_data, timeout=10)
    if "Bad API Request" in resp.text:
        raise HTTPException(status_code=502, detail=f"Erro login Pastebin: {resp.text}")

    _cached_user_key = resp.text
    return _cached_user_key


def anchor_chain_to_pastebin(username: str) -> str:
    """
    Envia o último hash da cadeia para o Pastebin (Ancoragem Externa).
    Retorna a URL do paste gerado.
    """
    if not settings.PASTEBIN_DEV_KEY:
        raise HTTPException(status_code=500, detail="PASTEBIN_DEV_KEY não configurada")

    conn = connect()
    try:
        last_hash = obter_ultimo_hash(conn)
    finally:
        conn.close()

    if not last_hash:
        raise HTTPException(status_code=400, detail="Cadeia de auditoria vazia")

    now = datetime.now(timezone.utc).isoformat()

    # Conteúdo da âncora
    paste_content = f"""
    === GOVERNANCE DASHBOARD ANCHOR ===
    Timestamp: {now}
    Anchor Hash: {last_hash}
    Signed By: {username}
    ===================================
    """

    data = {
        "api_dev_key": settings.PASTEBIN_DEV_KEY,
        "api_option": "paste",
        "api_paste_code": paste_content,
        "api_paste_name": f"Anchor {now}",
        "api_paste_private": "1",  # 0=Public, 1=Unlisted, 2=Private
    }

    user_key = _get_pastebin_user_key()
    if user_key:
        data["api_user_key"] = user_key

    resp = requests.post("https://pastebin.com/api/api_post.php", data=data, timeout=10)

    if "Bad API Request" in resp.text:
        raise HTTPException(status_code=502, detail=f"Erro no Pastebin: {resp.text}")

    return resp.text  # Retorna a URL (ex: https://pastebin.com/xxxx)
