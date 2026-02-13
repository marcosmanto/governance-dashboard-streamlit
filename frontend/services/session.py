import streamlit as st

from frontend.core.pages import Page


def require_auth():
    api = st.session_state.get("api")
    user = st.session_state.get("user")

    if not api or not user:
        st.switch_page(Page.LOGIN.path)
        st.stop()

    with st.spinner("Verificando sessão..."):
        # chamada leve para validar sessão
        resp = api.ensure_user_refresh()

        if not resp:
            st.session_state.clear()
            st.switch_page(Page.LOGIN.path)
            st.stop()

    return api, user
