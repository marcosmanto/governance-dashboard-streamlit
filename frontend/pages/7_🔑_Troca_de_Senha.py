from time import sleep

import requests
import streamlit as st

from backend.core.config import settings
from frontend.core.pages import Page
from frontend.services.navigation import set_current_page

set_current_page(Page.CHANGE_PASSWORD)

must_change_password = st.session_state.get("must_change_password")

st.session_state.login_error_message = None
error_message = st.session_state.get("error_message")
if error_message:
    st.toast(st.session_state.get("error_message"))

# if must_change_password is not None:
#     if not api or not user:
#         st.switch_page(Page.LOGIN.path)
#         st.stop()

carregando = st.session_state.get("loading_password_change")

if carregando is None:
    st.session_state.loading_password_change = False
    carregando = False

st.title(f"🔑 Troca {'obrigatória ' if must_change_password else ''}de senha")


# 🔐 Política de senha — UX clara
with st.expander("📋 Política de senha", expanded=True):
    st.markdown("""
    Sua nova senha deve conter:
    - ✅ **Mínimo de 6 caracteres**
    - 🔠 **Pelo menos uma Letra maiúscula**
    - 🔡 **Pelo menos uma Letra minúscula**
    - 🔢 **Pelo menos um Número**
    - 🔣 **Pelo menos um Caractere especial** (`!@#$%^&*` etc)
    """)

if carregando:
    st.markdown(
        """
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(4px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            flex-direction: column;
            color: white;
            font-family: sans-serif;
        }

        .spinner {
            border: 6px solid rgba(255, 255, 255, 0.2);
            border-top: 6px solid #4CAF50;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }

        .overlay-text {
            font-size: 22px;
            font-weight: 500;
        }

        .overlay-subtext {
            font-size: 14px;
            opacity: 0.8;
            margin-top: 6px;
        }
        </style>

        <div class="overlay">
            <div class="spinner"></div>
            <div class="overlay-text">Atualizando sua senha...</div>
            <div class="overlay-subtext">Por favor aguarde.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # st.markdown(
    #     """
    #     <div style="
    #         position: fixed;
    #         top: 0;
    #         left: 0;
    #         width: 100%;
    #         height: 100%;
    #         background-color: rgba(0,0,0,0.6);
    #         z-index: 9999;
    #         display: flex;
    #         justify-content: center;
    #         align-items: center;
    #         font-size: 24px;
    #         color: white;
    #     ">
    #         🔄 Processando alteração de senha...
    #     </div>
    #     """,
    #     unsafe_allow_html=True,
    # )


with st.form("change_password"):
    old = st.text_input("Senha atual", type="password")
    new = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")

    submitted = st.form_submit_button(
        "Alterar senha",
        on_click=lambda: st.session_state.update({"error_message": None}),
    )

    if error_message:
        st.error(error_message)

    if submitted:
        if new != confirm:
            st.error("As senhas não coincidem")
            st.stop()
        else:
            # 🔒 ativa overlay
            st.session_state.loading_password_change = True
            st.rerun()
            # resp = api._request(
            #     "POST",
            #     "/admin/change-password",
            #     json={
            #         "old_password": old,
            #         "new_password": new,
            #     },
            # )

            # data = resp.json()

            # if resp.status_code != 200:
            #     try:
            #         detail = data["detail"]
            #     except Exception:
            #         detail = "Erro ao alterar a senha"

            #     st.error(detail)
            #     st.stop()

            # # ✅ sucesso: senha modificada

            # # recria o contexto de login
            # st.session_state.access_token = data["access_token"]
            # st.session_state.refresh_token = data["refresh_token"]

            # st.session_state.api = APIClient(
            #     base_url=api.base_url,
            #     access_token=data["access_token"],
            #     refresh_token=data["refresh_token"],
            # )

            # st.session_state.user = data["user"]
            # st.session_state.force_password_change = False

            # st.session_state.clear()
            # st.success("Senha alterada com sucesso")
            # time.sleep(3)
            # st.switch_page(Page.LOGIN.path)
            # st.switch_page("Home.py")

if carregando:
    with st.spinner("Validando senha e atualizando sessão..."):
        resp = requests.post(
            f"{settings.API_BASE_URL}/admin/change-password",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            json={
                "old_password": old,
                "new_password": new,
            },
            timeout=10,
        )

    data = resp.json()

    if resp.status_code != 200:
        st.session_state.loading_password_change = False
        try:
            detail = data["detail"]
        except Exception:
            detail = "Erro ao alterar a senha"

        # st.error(detail)
        st.session_state.error_message = detail
        st.rerun()

    # ✅ sucesso
    st.session_state.clear()
    st.success("Senha alterada com sucesso")
    sleep(2)
    st.switch_page(Page.LOGIN.path)
