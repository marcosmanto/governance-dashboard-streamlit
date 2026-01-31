import time

import streamlit as st

from frontend.app_config import init_page
from frontend.services.api import APIClient

user = st.session_state.get("user")

if user:
    st.info(
        f"Você *já está logado* como :orange[-> **{user['username']}**] e com o nível de permissão :orange[-> **{user['role']}**]",
        icon=":material/info:",
    )
    time.sleep(3)
    st.switch_page("Home.py")
    st.stop()

API_BASE = "http://localhost:8000"

api = APIClient(
    base_url=API_BASE,
    access_token=st.session_state.get("access_token"),
    refresh_token=st.session_state.get("refresh_token"),
)

st.session_state.api = api

init_page(page_title="Login", page_icon="🔐")
st.title("🔐 Login")

with st.form("login", enter_to_submit=True):
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.form_submit_button("Entrar", type="primary"):
        try:
            resp = api.login(username, password)

            if resp.status_code != 200:
                st.error("Usuário ou senha inválidos")
                st.stop()

            data = resp.json()

            # 🔐 salva tokens sempre
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]

            # inicializa API client
            st.session_state.api = APIClient(
                base_url=API_BASE,
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
            )
            print(data)
            # 🚨 CASO ESPECIAL: senha pendente
            if data.get("must_change_password"):
                st.session_state.force_password_change = True
                st.switch_page("pages/7_🔑_Change_Password.py")
                st.stop()

            st.session_state.user = data["user"]
            st.success("Login realizado com sucesso")
            st.switch_page("Home.py")

        except Exception as e:
            st.error(f"Erro ao conectar à API: {e}")
