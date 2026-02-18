import time

import requests
import streamlit as st

from backend.core.config import settings
from frontend.app_config import init_page
from frontend.core.pages import Page
from frontend.services.navigation import set_current_page

token_from_link = st.session_state.get("reset_token_from_link", "")

set_current_page(Page.RESET_PASSWORD)

init_page(page_title="Redefinir senha", page_icon="🔑")
st.title("🔑 Redefinir senha")

st.session_state.login_error_message = None
token = st.text_input("Token de redefinição", value=token_from_link)
new_password = st.text_input("Nova senha", type="password")
confirm_password = st.text_input("Confirmar nova senha", type="password")

if st.button("Redefinir", type="primary"):
    if not token.strip():
        st.error("Informe o token.")
    elif not new_password:
        st.error("Informe a nova senha.")
    elif new_password != confirm_password:
        st.error("As senhas não coincidem.")
    else:
        try:
            resp = requests.post(
                f"{settings.API_BASE_URL}/reset-password",
                json={"token": token.strip(), "new_password": new_password},
                timeout=10,
            )

            if resp.status_code >= 500:
                st.error("Erro interno ao redefinir a senha.")
            else:
                st.session_state.reset_token_from_link = None
                # 🔒 Sempre resposta genérica
                st.success("Se o token for válido, a senha será redefinida.")
                time.sleep(5)
                st.switch_page(Page.LOGIN.path)
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar à API.")
        except Exception as exc:
            st.error(f"Erro inesperado: {exc}")
