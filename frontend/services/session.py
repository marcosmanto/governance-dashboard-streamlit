import logging
import sys
import time

import streamlit as st

from backend.core.config import settings
from frontend.core.pages import Page

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


def require_auth():
    api = st.session_state.get("api")
    user = st.session_state.get("user")

    if not api or not user:
        st.switch_page(Page.LOGIN.path)
        st.stop()

    # Otimização: Valida no backend apenas a cada 60 segundos
    last_check = st.session_state.get("last_auth_check", 0)
    now = time.time()
    cache_duration = 60  # segundos

    if (now - last_check) > cache_duration:
        with st.spinner("Verificando sessão..."):  # Opcional: remover spinner para ser transparente
            logger.info("Check de permissão e sessão iniciada.")
            # chamada leve para validar sessão
            valid = api.ensure_user_refresh()

        if not valid:
            st.session_state.clear()
            st.switch_page(Page.LOGIN.path)
            st.stop()

        st.session_state["last_auth_check"] = now
    elif settings.ENV == "dev":
        logger.info("Verificação de sessão pulada (cache ativo).")

    return api, user
