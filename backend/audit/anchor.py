import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import HTTPException

from backend.audit.service import obter_ultimo_hash
from backend.core.config import settings
from backend.db import connect
from backend.models import UserContext

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


def _save_to_local_file(timestamp: str, last_hash: str, username: str) -> str:
    """Estratégia 1: Arquivo Local Append-Only"""
    path = Path("data/anchors.log")
    entry = f"{timestamp} | HASH:{last_hash} | USER:{username}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
    return str(path.absolute())


def _save_to_git(timestamp: str, last_hash: str, username: str) -> str | None:
    """Estratégia 2: Commit no Git (se disponível)"""
    if not Path(".git").is_dir():
        return None

    try:
        msg = f"🛡️ ANCHOR: {last_hash} | {timestamp} | {username}"
        # --allow-empty permite criar commit sem mudar arquivos, apenas para registro no log
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", msg],
            check=True,
            capture_output=True,
        )
        # Pega o hash do commit gerado
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        )
        return res.stdout.strip()
    except Exception:
        return None  # Falha silenciosa se git não estiver configurado ou der erro


def perform_anchoring(user: UserContext) -> dict:
    """
    Executa ancoragem em múltiplas camadas: Local, Git e Pastebin.
    """
    conn = connect()
    try:
        last_hash = obter_ultimo_hash(conn)
    finally:
        conn.close()

    if not last_hash:
        raise HTTPException(status_code=400, detail="Cadeia de auditoria vazia")

    now = datetime.now(timezone.utc).isoformat()
    results = {"hash": last_hash, "timestamp": now}

    # 1️⃣ Camada Local
    try:
        local_path = _save_to_local_file(now, last_hash, user.username)
        results["local_file"] = local_path
    except Exception as e:
        results["local_file_error"] = str(e)

    # 2️⃣ Camada Git
    git_hash = _save_to_git(now, last_hash, user.username)
    if git_hash:
        results["git_commit"] = git_hash

    # 3️⃣ Camada Externa (Pastebin) - Opcional se configurado
    if settings.PASTEBIN_DEV_KEY:
        try:
            paste_url = _post_to_pastebin(now, last_hash, user.username)
            results["pastebin_url"] = paste_url
        except Exception as e:
            results["pastebin_error"] = str(e)

    return results


def _post_to_pastebin(timestamp: str, last_hash: str, username: str) -> str:
    """Lógica isolada do Pastebin"""

    # Conteúdo da âncora
    paste_content = f"""
    === GOVERNANCE DASHBOARD ANCHOR ===
    Timestamp: {timestamp}
    Anchor Hash: {last_hash}
    Signed By: {username}
    ===================================
    """

    data = {
        "api_dev_key": settings.PASTEBIN_DEV_KEY,
        "api_option": "paste",
        "api_paste_code": paste_content,
        "api_paste_name": f"Anchor {timestamp}",
        "api_paste_private": "1",  # 0=Public, 1=Unlisted, 2=Private
    }

    user_key = _get_pastebin_user_key()
    if user_key:
        data["api_user_key"] = user_key

    resp = requests.post("https://pastebin.com/api/api_post.php", data=data, timeout=10)

    if "Bad API Request" in resp.text:
        raise HTTPException(status_code=502, detail=f"Erro no Pastebin: {resp.text}")

    return resp.text  # Retorna a URL (ex: https://pastebin.com/xxxx)
