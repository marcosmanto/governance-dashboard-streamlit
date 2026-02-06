import streamlit as st

from frontend.app_config import init_page

init_page(page_title="Administração", page_icon=":material/handyman:", wide=True)


user = st.session_state.get("user")
api = st.session_state.get("api")

with st.spinner("Verificando usuário..."):
    resp = api._request("GET", f"/admin/users/{user['username']}/check")

if user is None or api is None:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

if user["role"] != "admin":
    st.warning("Acesso restrito a administradores.")
    st.stop()

st.title("🛠️ Administração")

# 1) Mostrar mensagem "flash" de sucesso (se existir) antes de desenhar o form
_flash = st.session_state.pop("flash_success", None)
if _flash:
    st.success(_flash)

# Se houver reset pendente, aplique AGORA (antes de instanciar os widgets)
if st.session_state.get("revoke_reset_pending"):
    st.session_state["revoke_username"] = ""
    st.session_state["revoke_confirm"] = False
    st.session_state.pop("revoke_reset_pending", None)

# Garanta defaults para as keys dos widgets (antes de criar o form)
st.session_state.setdefault("revoke_username", "")
st.session_state.setdefault("revoke_confirm", False)


st.header("💣 Revogar sessões de um usuário")

with st.form("revoke_user_sessions", clear_on_submit=False):
    # 2) Dê chaves (keys) aos widgets para controlar o estado
    username = st.text_input("Username do usuário", key="revoke_username")
    confirm = st.checkbox(
        "Confirmo que desejo revogar TODAS as sessões desse usuário", key="revoke_confirm"
    )
    submitted = st.form_submit_button("Revogar sessões", type="primary")

    if submitted:
        if not username.strip():
            st.error("Informe o username")
        elif not confirm:
            st.warning("Confirmação obrigatória")
        else:
            resp = api._request("POST", f"/admin/users/{username.strip()}/sessions/revoke")
            if resp.status_code == 200:
                # 4) Guarda a mensagem de sucesso para aparecer após o rerun
                st.session_state["flash_success"] = f"Sessões de {username} revogadas com sucesso"
                st.session_state["revoke_reset_pending"] = True

                st.rerun()
            else:
                st.error(f"Erro ao revogar sessões: ({resp.status_code})")


st.header("🎯 Revogar sessão específica")

with st.form("revoke_single_session", enter_to_submit=True):
    session_id = st.text_input("ID da sessão (session id)")
    confirm = st.checkbox("Confirmo que desejo revogar essa sessão")
    submitted = st.form_submit_button("Revogar sessão")

if submitted:
    if not session_id.strip():
        st.error("Informe o session_id.")
    elif not confirm:
        st.warning("Confirmação obrigatória.")
    else:
        resp = api._request(
            "POST",
            f"/admin/sessions/{session_id.strip()}/revoke",
        )

        if resp.status_code == 200:
            st.success("Sessão revogada com sucesso.")
        else:
            st.error(f"Erro ao revogar sessão ({resp.status_code})")

st.divider()

st.header("🧹 Limpar sessões vencidas ou revogadas")
st.space("xxsmall")

left, right = st.columns(2)

with left:
    if st.button("Remover sessões expiradas", width="stretch"):
        resp = api._request(
            "POST",
            "/admin/sessions/cleanup",
        )

        if resp.status_code == 200:
            data = resp.json()
            st.success(f"{data['deleted_sessions']} sessões removidas.")
        else:
            st.error(f"Erro ao limpar sessões ({resp.status_code})")


with right:
    if st.button("Remover sessões revogadas", width="stretch"):
        resp = api._request(
            "POST",
            "/admin/sessions/revoked/cleanup",
        )

        if resp.status_code == 200:
            data = resp.json()
            st.success(f"{data['deleted_sessions']} sessões removidas.")
        else:
            st.error(f"Erro ao limpar sessões ({resp.status_code})")
