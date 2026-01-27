import streamlit as st

from data.loader import carregar_dados
from frontend.app_config import init_page

init_page(page_title="Dados detalhados", page_icon=":paper:")

st.title("📄 Dados detalhados")

df = carregar_dados()

# reaproveita filtro da sessão
categoria = st.session_state.get("categoria")

if categoria:
    df = df[df["categoria"] == categoria]
    st.caption(f"Categoria selecionada: {categoria}")
else:
    st.caption("Nenhum filtro aplicado")

st.dataframe(df)
