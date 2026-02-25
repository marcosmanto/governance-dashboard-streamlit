import streamlit as st

from frontend.core.pages import Page
from frontend.layouts.base_layout import base_layout
from frontend.loaders.registros import carregar_registros
from frontend.services.navigation import set_current_page

set_current_page(Page.DATA)

api, user = base_layout("Dados detalhados", ":paper:")

st.title("📄 Dados detalhados")

df = carregar_registros()

# reaproveita filtro da sessão
categoria = st.session_state.get("categoria")

if categoria:
    df = df[df["categoria"] == categoria]
    st.caption(f"Categoria selecionada: {categoria}")
else:
    st.caption("Nenhum filtro aplicado")

st.dataframe(df)
