import time
import streamlit as st

from frontend.core.pages import Page


def require_auth():
    api = st.session_state.get("api")
    user = st.session_state.get("user")

    if not api or not user:
        st.switch_page(Page.LOGIN.path)
        st.stop()

    with st.spinner("Verificando sessão..."):
    # Otimização: Valida no backend apenas a cada 60 segundos
    last_check = st.session_state.get("last_auth_check", 0)
    now = time.time()
    cache_duration = 60  # segundos

    if (now - last_check) > cache_duration:
        # with st.spinner("Verificando sessão..."): # Opcional: remover spinner para ser transparente
        # chamada leve para validar sessão
        resp = api.ensure_user_refresh()
        valid = api.ensure_user_refresh()

        if not resp:
        if not valid:
            st.session_state.clear()
            st.switch_page(Page.LOGIN.path)
            st.stop()

        st.session_state["last_auth_check"] = now

    return api, user
