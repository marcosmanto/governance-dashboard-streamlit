from datetime import time

import pandas as pd
import streamlit as st

from frontend.core.pages import Page
from frontend.layouts.base_layout import base_layout
from frontend.services.navigation import set_current_page

set_current_page(Page.USERS)

api, user = base_layout("Administração de Usuários", "🧑‍💼", wide=True)

# =====================
# 🔐 Segurança
# =====================

# 🔒 Página com acesso restrito ao perfil admin
if user["role"] != "admin":
    st.error("Acesso restrito a administradores.")
    st.stop()

st.title("🧑‍💼 Administração de Usuários")

tab_users, tab_requests = st.tabs(["👥 Lista de Usuários", "📩 Solicitações de Acesso"])

with tab_users:
    response = api._request("GET", "/admin/users")
    usuarios = response.json()
    df = pd.DataFrame(usuarios)

    # Formata coluna de MFA para visualização amigável
    if "mfa_enabled" in df.columns:
        df["2FA"] = df["mfa_enabled"].apply(lambda x: "✅ Ativo" if x else "❌ Inativo")

    # Exibe tabela com colunas selecionadas
    st.dataframe(
        df[["id", "username", "role", "2FA", "created_at"]], width="stretch", hide_index=True
    )

    st.divider()
    st.subheader("🔁 Reset de senha")
    username = st.selectbox("Usuário", df["username"].tolist())
    if st.button("Resetar senha", type="primary"):
        resp = api._request("POST", f"/admin/users/{username}/reset-password")
        if resp.status_code == 200:
            senha = resp.json()
            st.success("Senha resetada com sucesso")
            st.divider()
            st.error("⚠️ Senha temporária gerada")
            st.code(senha["temporary_password"])
            st.caption("Copie agora. Ela não será exibida novamente.")
        else:
            st.error(f"Erro ao resetar senha: ({resp.status_code})")

    st.divider()
    st.subheader("🛡️ Gestão de 2FA")

    users_with_mfa = []
    if "mfa_enabled" in df.columns:
        users_with_mfa = df[df["mfa_enabled"].astype(bool)]["username"].tolist()

    if not users_with_mfa:
        st.info("Nenhum usuário com 2FA ativo.")
    else:
        user_mfa = st.selectbox("Usuário para remover 2FA", users_with_mfa, key="mfa_reset_select")
        if st.button(
            "Remover 2FA do Usuário",
            type="primary",
            help="Use isso se o usuário perdeu o acesso ao autenticador",
        ):
            with st.spinner("Removendo 2FA..."):
                resp = api._request("POST", f"/admin/users/{user_mfa}/mfa/reset")
                if resp.status_code == 200:
                    st.success(
                        f"2FA de **{user_mfa}** removido com sucesso. O usuário poderá logar apenas com senha."
                    )
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Erro ao remover 2FA: {resp.text}")

with tab_requests:
    st.subheader("Solicitações Pendentes")
    resp = api._request("GET", "/admin/role-requests")
    if resp.status_code == 200:
        requests_data = resp.json()
        pending = [r for r in requests_data if r["status"] == "PENDING"]

        if not pending:
            st.info("Nenhuma solicitação pendente.")
        else:
            for req in pending:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.markdown(f"**{req['username']}** deseja ser **{req['requested_role']}**")
                    c1.caption(f"Justificativa: {req['justification']}")
                    c1.caption(f"Data: {req['created_at']}")

                    if c2.button(
                        "✅ Aprovar",
                        key=f"app_{req['id']}",
                        type="primary",
                        width="stretch",
                    ):
                        api._request("POST", f"/admin/role-requests/{req['id']}/approve")
                        st.rerun()

                    if c3.button("❌ Rejeitar", key=f"rej_{req['id']}", width="stretch"):
                        api._request("POST", f"/admin/role-requests/{req['id']}/reject")
                        st.rerun()
    # histórico de pedidos
    st.divider()
    st.subheader("Histórico de Pedidos")

    if resp.status_code == 200:
        history = [r for r in requests_data if r["status"] != "PENDING"]
        if not history:
            st.info("Nenhum histórico de solicitações.")
        else:
            df_history = pd.DataFrame(history)
            df_history["created_at"] = pd.to_datetime(df_history["created_at"]).dt.strftime(
                "%d/%m/%Y %H:%M"
            )
            df_history["processed_at"] = pd.to_datetime(df_history["processed_at"]).dt.strftime(
                "%d/%m/%Y %H:%M"
            )

            # Função para estilizar o status como um badge
            def style_status(val):
                if val == "APPROVED":
                    # Verde sucesso (fundo translúcido, texto forte)
                    return "background-color: rgba(25, 135, 84, 0.2); color: #198754; font-weight: bold; border-radius: 4px; padding: 2px 8px;"
                elif val == "REJECTED":
                    # Vermelho erro
                    return "background-color: rgba(220, 53, 69, 0.2); color: #dc3545; font-weight: bold; border-radius: 4px; padding: 2px 8px;"
                return ""

            st.dataframe(
                df_history[
                    [
                        "username",
                        "requested_role",
                        "justification",
                        "status",
                        "processed_by",
                        "created_at",
                        "processed_at",
                    ]
                ].style.map(style_status, subset=["status"]),
                column_config={
                    "username": "Usuário",
                    "requested_role": "Perfil Solicitado",
                    "justification": "Justificativa",
                    "status": "Situação",
                    "processed_by": "Processado por",
                    "created_at": "Solicitado em",
                    "processed_at": "Processado em",
                },
                width="stretch",
                hide_index=True,
            )
            st.divider()

    else:
        st.error(f"Erro ao buscar histórico: ({resp.status_code})")
