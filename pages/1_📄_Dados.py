import streamlit as st
from data.loader import carregar_dados

st.title("📄 Dados detalhados")

df = carregar_dados()

# reaproveita filtro da sessão
categoria = st.session_state.get("categoria")

print(f"Page dados: categoria {categoria}")

if categoria:
    df = df[df["categoria"] == categoria]
    st.caption(f"Categoria selecionada: {categoria}")
else:
    st.caption("Nenhum filtro aplicado")

st.dataframe(df)
