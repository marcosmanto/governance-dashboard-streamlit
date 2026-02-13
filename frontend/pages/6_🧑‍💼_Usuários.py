import pandas as pd
import streamlit as st

from frontend.core.pages import Page
from frontend.services.navigation import set_current_page
from frontend.services.session import require_auth

set_current_page(Page.USERS)

api, user = require_auth()

st.set_page_config(page_title="Administração de Usuários", layout="wide")

st.session_state.login_error_message = None

# =====================
# 🔐 Segurança
# =====================

# 🔒 Página com acesso restrito ao perfil admin
if user["role"] != "admin":
    st.error("Acesso restrito a administradores.")
    st.stop()

st.title("🧑‍💼 Administração de Usuários")

response = api._request("GET", "/admin/users")

usuarios = response.json()

df = pd.DataFrame(usuarios)

st.dataframe(df, width="stretch")

st.divider()

st.subheader("🔁 Reset de senha")

username = st.selectbox("Usuário", df["username"].tolist())

if st.button("Resetar senha", type="primary"):
    resp = api._request("POST", f"/admin/users/{username}/reset-password")
    if resp.status_code == 200:
        senha = resp.json()
        st.success("Senha resetada com sucesso")
        st.divider()
        st.error("⚠️ Senha temporária gerada")
        st.code(senha["temporary_password"])
        st.caption("Copie agora. Ela não será exibida novamente.")
    else:
        st.error(f"Erro ao resetar senha: ({resp.status_code})")
