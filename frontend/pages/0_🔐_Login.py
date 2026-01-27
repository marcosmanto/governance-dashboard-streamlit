import streamlit as st

from frontend.services.api import APIClient

if st.session_state.get("api") is not None:
    st.switch_page("Home.py")
    st.stop()

BASE_URL = "http://localhost:8000"

st.title("🔐 Login")

if "api" not in st.session_state:
    st.session_state.api = None

username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    api = APIClient(BASE_URL, username, password)

    if api.test_auth():
        me = api.me().json()
        st.session_state.api = api
        st.session_state.user = me
        st.success("Login realizado com sucesso")
        st.switch_page("Home.py")
    else:
        st.error("Usuário ou senha inválidos")
