import streamlit as st

from frontend.core.pages import Page

__all__ = ["handle_api_error"]

# print(">>> carregando errors.py")
# print(">>> globals:", list(globals().keys()))


def handle_api_error(resp):
    if resp.status_code == 401:
        st.error("Sessão expirada ou credenciais inválidas.")
        st.session_state.api = None
        st.switch_page(Page.LOGIN.path)
        st.stop()

    if resp.status_code == 403:
        st.error("Você não tem permissão para executar esta ação.")
        st.stop()

    if resp.status_code >= 500:
        st.error("Erro interno no servidor.")
        st.stop()
