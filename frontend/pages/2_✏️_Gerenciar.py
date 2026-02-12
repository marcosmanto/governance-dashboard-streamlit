import time

import requests
import streamlit as st

from frontend.app_config import init_page
from frontend.loaders.registros import carregar_registros
from frontend.services.errors import handle_api_error

init_page(page_title="Gerenciar registros", page_icon=":pencil:")

st.session_state.login_error_message = None
user = st.session_state.get("user")
api = st.session_state.get("api")

if user is None:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

with st.spinner("Verificando usuário..."):
    resp = api._request("GET", f"/admin/users/{user['username']}/check")

if api is None:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()


role = user["role"]

if role not in ("editor", "admin"):
    st.warning("Você não tem permissão para editar registros.")
    st.stop()

st.title("✏️ Gerenciar registros")

df = carregar_registros(api)

# ======================
# ➕ INSERIR
# ======================
st.subheader("➕ Novo registro")

with st.form("form_inserir", clear_on_submit=False):
    data = st.date_input("Data", format="DD/MM/YYYY")
    categoria = st.selectbox("Categoria", options=df["categoria"].unique())
    valor = st.number_input("Valor", step=1)

    submitted = st.form_submit_button("Inserir", type="primary")

if submitted:
    erros = []

    if not categoria.strip():
        erros.append("A categoria é obrigatória.")

    if valor is None:
        erros.append("O valor é obrigatório.")

    if erros:
        for erro in erros:
            st.error(erro, icon=":material/error:")
    else:
        try:
            resp = api.criar_registro(
                {
                    "data": str(data),
                    "categoria": categoria.strip(),
                    "valor": int(valor),
                }
            )

            handle_api_error(resp)

            st.cache_data.clear()
            st.toast("Registro adicionado com sucesso.", icon=":material/check:")
            time.sleep(5)
            st.rerun()
        except requests.exceptions.HTTPError as e:
            st.error(f"Erro da API ({e.response.status_code})")
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar à API.")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")


# ======================
# ✏️ EDITAR / 🗑️ EXCLUIR
# ======================
st.subheader("✏️ Editar / 🗑️ Excluir")

# 🔍 BUSCA REGISTROS =========

# st.subheader("🔍 Buscar registro")


# inicialização
if "busca" not in st.session_state:
    st.session_state.busca = ""

if "busca_input" not in st.session_state:
    st.session_state.busca_input = st.session_state.busca

st.markdown(
    """
    <style>
    /* container da busca */
    div[data-testid="stVerticalBlock"]:has(> div > div > input[aria-label="🔍 Buscar registro"]) {
        background-color: rgba(0, 123, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def on_busca_change():
    st.session_state.busca = st.session_state.busca_input


def limpar_busca():
    st.session_state.busca = ""
    st.session_state.busca_input = ""


with st.chat_message(
    "user",
    avatar='<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <rect width="24" height="24" fill="transparent"></rect><circle cx="12" cy="12" r="9" fill="#fff" /><path fill-rule="evenodd" clip-rule="evenodd" d="M2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12ZM9 11.5C9 10.1193 10.1193 9 11.5 9C12.8807 9 14 10.1193 14 11.5C14 12.8807 12.8807 14 11.5 14C10.1193 14 9 12.8807 9 11.5ZM11.5 7C9.01472 7 7 9.01472 7 11.5C7 13.9853 9.01472 16 11.5 16C12.3805 16 13.202 15.7471 13.8957 15.31L15.2929 16.7071C15.6834 17.0976 16.3166 17.0976 16.7071 16.7071C17.0976 16.3166 17.0976 15.6834 16.7071 15.2929L15.31 13.8957C15.7471 13.202 16 12.3805 16 11.5C16 9.01472 13.9853 7 11.5 7Z" fill="#f74a36"></path></g></svg>',
):
    _, col_busca, col_limpar, _ = st.columns([0.5, 18, 2, 0.1], vertical_alignment="bottom")

    with col_busca:
        st.text_input(
            "Buscar registro",
            key="busca_input",
            placeholder="Categoria, valor ou data (ex: A, 50, 01/2025)",
            on_change=on_busca_change,
        )

    with col_limpar:
        st.button("❌", help="Limpar busca", on_click=limpar_busca)


busca = st.session_state.busca.strip().lower()

df_filtrado = df.copy()

if busca:
    df_filtrado = df[
        df["id"].astype(str).str.contains(busca)
        | df["categoria"].str.lower().str.contains(busca)
        | df["valor"].astype(str).str.contains(busca)
        | df["data"].dt.strftime("%d/%m/%Y").str.contains(busca)
    ]

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado.")
    st.stop()


def formatar_registro(row):
    return (
        f"[ ID {row['id']}] ▶ Data: {row['data'].strftime('%d/%m/%Y')} , "
        f"Categoria: {row['categoria']} , "
        f"Valor: {row['valor']}"
    )


opcoes = {row["id"]: formatar_registro(row) for _, row in df_filtrado.iterrows()}


registro_id = st.selectbox(
    "Selecione o registro",
    options=list(opcoes.keys()),
    format_func=lambda x: opcoes[x],
)

registro = df_filtrado[df_filtrado["id"] == registro_id].iloc[0]

with st.form("form_editar", clear_on_submit=True):
    data_edit = st.date_input("Data", registro["data"], format="DD/MM/YYYY")
    categoria_edit = st.text_input("Categoria", registro["categoria"])
    valor_edit = st.number_input("Valor", value=int(registro["valor"]), step=1)

    col1, col2 = st.columns(2)
    salvar = col1.form_submit_button("Salvar alterações", type="primary")
    if role == "admin":
        excluir = col2.form_submit_button("Excluir registro")

if salvar:
    try:
        resp = api.atualizar_registro(
            registro_id,
            {
                "data": str(data_edit),
                "categoria": categoria_edit.strip(),
                "valor": int(valor_edit),
            },
        )
        handle_api_error(resp)
        st.cache_data.clear()
        st.toast("Registro atualizado com sucesso.", icon=":material/check:")
        time.sleep(5)
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")


@st.dialog("⚠️ Confirmar exclusão")
def confirmar_exclusao(id_):
    st.error("Essa ação não pode ser desfeita.")
    st.write("Você está prestes a excluir o registro:")
    st.write(f"{opcoes[registro_id]}")
    st.write("")

    col1, col2 = st.columns(2)

    if col1.button("Cancelar"):
        st.rerun()

    if col2.button("Excluir definitivamente"):
        try:
            resp = api.deletar_registro(id_)
            handle_api_error(resp)
            st.cache_data.clear()
            st.error("Registro excluído.")
            time.sleep(3)
            limpar_busca()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir: {e}")


if role == "admin":
    if excluir:
        confirmar_exclusao(registro_id)
