import json

import streamlit as st

from frontend.app_config import init_page

init_page(page_title="Integridade da Auditoria", page_icon="🔐")

api = st.session_state.get("api")
user = st.session_state.get("user")

if not api or not user:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

with st.spinner("Verificando usuário..."):
    resp = api._request("GET", f"/admin/users/{user['username']}/check")

if user["role"] != "admin":
    st.error("Acesso restrito a administradores.")
    st.stop()

st.title("🔐 Integridade da Auditoria")

col1, col2 = st.columns([3, 1])

with col2:
    if st.button(
        "🔄 Reexecutar verificação",
        use_container_width=True,
    ):
        st.rerun()
    st.space()

# ============================
# 🔎 VERIFICAÇÃO DA CADEIA
# ============================

with st.spinner("Verificando integridade da auditoria..."):
    resp = api._request("GET", "/admin/audit/verify")

if resp.status_code != 200:
    st.error("Erro ao verificar auditoria.")
    st.stop()

result = resp.json()

# ============================
# 🟢 / 🔴 STATUS VISUAL
# ============================

if result["valid"]:
    st.success("✔ Auditoria íntegra e confiável")
    st.metric("Eventos verificados", result.get("checked_events", 0))
else:
    st.error("❌ Violação detectada na auditoria")
    st.warning(f"Motivo: **{result['reason']}**")
    st.warning(f"Evento afetado (ID): **{result['broken_at_id']}**")

# ============================
# 🧾 EXPORTAÇÃO
# ============================

st.divider()
st.subheader("🧾 Exportar relatório")

export_data = {
    "status": "valid" if result["valid"] else "broken",
    "details": result,
}

json_bytes = json.dumps(export_data, indent=2).encode("utf-8")

st.download_button(
    label="📥 Baixar relatório (JSON)",
    data=json_bytes,
    file_name="integridade_auditoria.json",
    mime="application/json",
)

# ============================
# ⛔ BLOQUEIO DE ESCRITA
# ============================

st.divider()
st.subheader("⛔ Proteção do sistema")

if not result["valid"]:
    st.error(
        """
        ⚠️ **A auditoria foi comprometida.**

        Recomendações:
        - Bloquear novas operações de escrita
        - Investigar manualmente a base
        - Gerar evidências
        """
    )
else:
    st.info("Sistema liberado para operações de escrita.")
