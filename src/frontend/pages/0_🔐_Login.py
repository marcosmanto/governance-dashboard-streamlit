import time

import requests
import streamlit as st

from frontend.app_config import init_page
from frontend.config import settings
from frontend.core.pages import Page
from frontend.services.api import APIClient

user = st.session_state.get("user")

login_error_message = st.session_state.get("login_error_message")

if login_error_message:
    st.toast(st.session_state.get("login_error_message"))

if user:
    st.info(
        f"Você *já está logado* como :orange[-> **{user['username']}**] e com o nível de permissão :orange[-> **{user['role']}**]",
        icon=":material/info:",
    )
    time.sleep(3)
    st.switch_page("Home.py")
    st.stop()


api = APIClient(
    base_url=settings.API_BASE_URL,
    access_token=st.session_state.get("access_token"),
    refresh_token=st.session_state.get("refresh_token"),
)

st.session_state.api = api

init_page(page_title="Login", page_icon="🔐")
st.title("🔐 Login")

st.session_state.setdefault("login_in_progress", False)

st.markdown(
    """
    <style>
    /* Caixa de login baseada no bloco que contém o marcador */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stMarkdown"] [data-login-box-marker]) {
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.02);
        padding: 20px 22px;
        border-radius: 12px;
        margin-top: 8px;
    }
    /* Espaçamento interno entre widgets */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stMarkdown"] [data-login-box-marker]) > div {
        gap: 0.5rem;
    }
    /* Esconde o marcador visual */
    [data-login-box-marker] { display: none; }
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.dialog("🔁 Recuperar senha")
def forgot_password_dialog(prefill_username: str | None = None):
    st.caption("Informe seu usuário para receber instruções de redefinição.")
    with st.form("forgot_password_form", enter_to_submit=True):
        username = st.text_input(
            "Usuário",
            value=prefill_username or "",
            placeholder="Digite seu usuário",
        )
        submitted = st.form_submit_button("Enviar", type="primary")

    if submitted:
        if not username.strip():
            st.toast("Informe o usuário.")
            return

        with st.spinner("Enviando solicitação..."):
            try:
                requests.post(
                    f"{settings.API_BASE_URL}/forgot-password",
                    json={"username": username.strip()},
                    timeout=10,
                )
                # 🔒 Sempre resposta genérica
                st.success("Se o usuário existir, você receberá instruções para redefinir a senha.")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar à API.")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

    st.divider()
    if st.button("Já tenho um token"):
        st.switch_page(Page.RESET_PASSWORD.path)


with st.container(
    border=True,
):
    st.markdown('<span data-login-box-marker="true"></span>', unsafe_allow_html=True)
    username = st.text_input("Usuário", key="login_username")
    with st.form("login", enter_to_submit=True):
        password = st.text_input("Senha", type="password", key="login_password")
        otp_code = st.text_input(
            "Código 2FA (se ativado)",
            max_chars=6,
            key="login_otp",
            help="Deixe em branco se não usar 2FA",
        )
        can_submit = bool(st.session_state.get("login_username", "").strip())

        submitted = st.form_submit_button(
            "Entrar",
            type="primary",
            disabled=st.session_state.login_in_progress or not can_submit,
            on_click=lambda: st.session_state.update(
                {"login_in_progress": True, "login_error_message": None}
            ),
        )

        if login_error_message:
            st.error(login_error_message)

        if submitted:
            st.toast("Login em andamento. Aguarde..", icon=":material/login:")

            errors = []
            if not st.session_state.get("login_username", "").strip():
                errors.append("Informe o usuário.")
            if not password:
                errors.append("Informe a senha.")

            if errors:
                st.session_state.login_in_progress = False
                for msg in errors:
                    st.error(msg)
            else:
                try:
                    with st.spinner("Entrando..."):
                        resp = api.login(
                            st.session_state.get("login_username", ""), password, otp_code
                        )

                    if resp.status_code == 403:
                        try:
                            detail = resp.json().get("detail")
                        except Exception:
                            detail = None

                        if detail in ("PASSWORD_CHANGE_REQUIRED", "PASSWORD_EXPIRED"):
                            st.session_state.login_error_message = detail
                            raise ValueError(detail)

                    if resp.status_code == 401 and resp.json().get("detail") == "MFA_REQUIRED":
                        st.session_state.login_error_message = (
                            "⚠️ Autenticação de dois fatores obrigatória. Digite o código."
                        )
                        raise ValueError("MFA_REQUIRED")

                    if resp.status_code != 200:
                        st.session_state.login_error_message = "Usuário ou senha inválidos"
                        # Não interrompe o app para manter o botão "Esqueci minha senha"
                        raise ValueError("LOGIN_INVALID")

                    data = resp.json()

                    # 🔐 salva tokens sempre
                    st.session_state.access_token = data["access_token"]
                    st.session_state.refresh_token = data["refresh_token"]

                    # inicializa API client
                    st.session_state.api = APIClient(
                        base_url=settings.API_BASE_URL,
                        access_token=data["access_token"],
                        refresh_token=data["refresh_token"],
                    )
                    st.session_state.login_error_message = None

                    # 🚨 CASO ESPECIAL: senha pendente
                    if data.get("must_change_password"):
                        st.session_state.force_password_change = True
                        st.session_state.login_in_progress = False
                        print(Page.CHANGE_PASSWORD.path)
                        st.switch_page(Page.CHANGE_PASSWORD.path)
                        st.stop()

                    st.session_state.force_password_change = False
                    st.session_state.user = data["user"]
                    st.success("Login realizado com sucesso")
                    st.switch_page("Home.py")

                except Exception as e:
                    if str(e) in ["LOGIN_INVALID", "MFA_REQUIRED"] or str(e) == detail:
                        # erro já exibido acima
                        pass
                    else:
                        st.login_error_message = f"Erro ao conectar à API: {e}"
                        # st.error(f"Erro ao conectar à API: {e}")

                st.session_state.login_in_progress = False
                st.rerun()


st.divider()
if st.button("Esqueci minha senha"):
    forgot_password_dialog(prefill_username=st.session_state.get("login_username", ""))
