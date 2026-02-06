import streamlit as st

from frontend.services.api import APIClient

# 🚨 Se não existir dados de sessão direciona ao login
api = st.session_state.get("api")
user = st.session_state.get("user")
must_change_password = st.session_state.get("must_change_password")

if must_change_password is not None:
    if not api or not user:
        st.switch_page("pages/0_🔐_Login.py")
        st.stop()

st.title(
    f"🔑 Troca {'obrigatória ' if st.session_state.get('force_password_change') else ''}de senha"
)


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

with st.form("change_password", clear_on_submit=True):
    old = st.text_input("Senha atual", type="password")
    new = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")

    submitted = st.form_submit_button("Alterar senha")

    if submitted:
        if new != confirm:
            st.error("As senhas não coincidem")
            st.stop()
        else:
            resp = api._request(
                "POST",
                "/admin/change-password",
                json={
                    "old_password": old,
                    "new_password": new,
                },
            )

            data = resp.json()

            if resp.status_code != 200:
                try:
                    detail = data["detail"]
                except Exception:
                    detail = "Erro ao alterar a senha"

                st.error(detail)
                st.stop()

            # ✅ sucesso: senha modificada

            # recria o contexto de login
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]

            st.session_state.api = APIClient(
                base_url=api.base_url,
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
            )

            st.session_state.user = data["user"]
            st.session_state.force_password_change = False

            st.success("Senha alterada com sucesso")
            st.switch_page("Home.py")
