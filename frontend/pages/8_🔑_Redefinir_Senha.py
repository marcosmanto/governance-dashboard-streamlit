import requests
import streamlit as st

from frontend.app_config import init_page

API_BASE = "http://localhost:8000"

init_page(page_title="Redefinir senha", page_icon="🔑")
st.title("🔑 Redefinir senha")

token = st.text_input("Token de redefinição")
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
                f"{API_BASE}/reset-password",
                json={"token": token.strip(), "new_password": new_password},
                timeout=10,
            )

            if resp.status_code >= 500:
                st.error("Erro interno ao redefinir a senha.")
            else:
                # 🔒 Sempre resposta genérica
                st.success("Se o token for válido, a senha será redefinida.")
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar à API.")
        except Exception as exc:
            st.error(f"Erro inesperado: {exc}")
