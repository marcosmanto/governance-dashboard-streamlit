import streamlit as st
from charts.charts import grafico_evolucao

from frontend.app_config import init_page
from frontend.loaders.registros import carregar_registros
from frontend.services.api import APIClient

if "access_token" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

api = APIClient(
    base_url="http://localhost:8000",
    access_token=st.session_state.access_token,
    refresh_token=st.session_state.refresh_token,
)

st.session_state.api = api


init_page(page_title="Home • Painel", page_icon=":house:", wide=True)
st.title("📊 Painel Evolutivo de Dados")

df = carregar_registros(api)

# --- ler query params ---
query_params = st.query_params
categoria_qp = query_params.get("categoria", [None])[0]

# --- inicializar estado ---
if "categoria" not in st.session_state:
    st.session_state.categoria = categoria_qp or df["categoria"].iloc[0]

categorias = df["categoria"].unique()

# --- sidebar ---
with st.sidebar:
    user = st.session_state.get("user")

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

    st.success(st.session_state.get("access_token"))

    if user:
        st.markdown(f"👤 **{user['username']}** ({user['role']})")
        if st.button("🚪 Logout"):
            api.logout()
            st.session_state.clear()
            st.switch_page("pages/0_🔐_Login.py")

    if st.button("Recarregar dados"):
        st.cache_data.clear()
        st.success("Dados recarregados")
        st.rerun()

    if st.button("Listar registros teste"):
        resp = api.listar_registros()
        st.success("Registros listados")
        st.write(resp.json())


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
    st.plotly_chart(fig, width="stretch")

with col2:
    st.metric(label="Total de registros", value=len(df_filtrado))
    st.metric(label="Soma do valor", value=df_filtrado["valor"].sum())
