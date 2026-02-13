import pandas as pd
import streamlit as st

from frontend.app_config import init_page
from frontend.core.pages import Page
from frontend.services.errors import handle_api_error
from frontend.services.navigation import set_current_page
from frontend.services.session import require_auth

set_current_page(Page.AUDITORIA)

api, user = require_auth()

init_page(page_title="Auditoria", page_icon="📜")

st.session_state.login_error_message = None

# =====================
# 🔐 Segurança
# =====================

if user["role"] != "admin":
    st.warning("Acesso restrito a administradores.")
    st.stop()

st.title("📜 Auditoria do Sistema")

# =====================
# 🔎 Filtros
# =====================
with st.expander("🔎 Filtros", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        username = st.text_input("Usuário")

    with col2:
        action = st.selectbox(
            "Ação",
            options=["", "INSERT", "UPDATE", "DELETE", "PUT", "POST"],
        )

    with col3:
        resource = st.text_input("Recurso (ex: registros)")

    col4, col5 = st.columns(2)
    with col4:
        data_inicio = st.date_input("Data inicial", value=None, format="DD/MM/YYYY")

    with col5:
        data_fim = st.date_input("Data final", value=None, format="DD/MM/YYYY")

# =====================
# 📡 Buscar auditoria
# =====================
params = {}

if username:
    params["username"] = username

if action:
    params["action"] = action

if resource:
    params["resource"] = resource

if data_inicio:
    params["data_inicio"] = data_inicio.isoformat()

if data_fim:
    params["data_fim"] = data_fim.isoformat()

try:
    resp = api.listar_auditoria(params)
    handle_api_error(resp)

    dados = resp.json()
    df = pd.DataFrame(dados)

except Exception as e:
    st.error(f"Erro ao carregar auditoria: {e}")
    st.stop()

# =====================
# 📊 Exibição
# =====================
if df.empty:
    st.info("Nenhum evento encontrado com os filtros informados.")
    st.stop()

st.dataframe(
    df,
    width="stretch",
    hide_index=True,
)

# =====================
# 🧾 Exportação CSV
# =====================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="🧾 Baixar CSV",
    data=csv,
    file_name="auditoria.csv",
    mime="text/csv",
)
