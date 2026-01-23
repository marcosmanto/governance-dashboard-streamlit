import streamlit as st
from charts.charts import grafico_evolucao
from data.loader import carregar_dados

st.set_page_config(page_title="Painel Evolutivo de Dados", layout="wide")
st.title("📊 Painel Evolutivo de Dados")

df = carregar_dados()

# --- ler query params ---
query_params = st.query_params
categoria_qp = query_params.get("categoria", [None])[0]

# --- inicializar estado ---
if "categoria" not in st.session_state:
    st.session_state.categoria = categoria_qp or df["categoria"].iloc[0]

categorias = df["categoria"].unique()

# --- sidebar ---
with st.sidebar:
    try:
        cat_idx = categorias.tolist().index(st.session_state.categoria)
    except ValueError:
        cat_idx = 0

    categoria = st.selectbox(
        "Categoria",
        options=df["categoria"].unique(),
        index=cat_idx,
    )

    st.divider()

    if st.button("Recarregar dados"):
        st.cache_data.clear()
        st.success("Dados recarregados")
        st.rerun()


# --- salvar no estado e na URL ---
st.session_state.categoria = categoria
st.query_params.categoria = categoria


df_filtrado = df[df["categoria"] == categoria]

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        padding-left: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- layout ---
col1, col2 = st.columns([2, 1])

with col1:
    fig = grafico_evolucao(df_filtrado, categoria)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric(label="Total de registros", value=len(df_filtrado))
    st.metric(label="Soma do valor", value=df_filtrado["valor"].sum())
