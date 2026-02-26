import json

import pandas as pd
import streamlit as st

from frontend.core.pages import Page
from frontend.layouts.base_layout import base_layout
from frontend.services.navigation import set_current_page

set_current_page(Page.INTEGRIDADE)

api, user = base_layout("Integridade da Auditoria", "🔐", wide=True)

# =====================
# 🔐 Segurança
# =====================

if user["role"] != "admin":
    st.warning("Acesso restrito a administradores.")
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
# 🔎 VERIFICAÇÃO E EVIDÊNCIA
# ============================

with st.spinner("Verificando integridade e buscando evidências..."):
    # 1. Re-executa a verificação para atualizar o status
    verify_resp = api._request("GET", "/admin/audit/verify")
    # 2. Busca o relatório forense completo
    evidence_resp = api._request("GET", "/admin/audit/evidence")

if verify_resp.status_code != 200 or evidence_resp.status_code != 200:
    st.error("Erro ao executar verificação e obter evidência.")
    st.code(f"Verify Response: {verify_resp.status_code} - {verify_resp.text}")
    st.code(f"Evidence Response: {evidence_resp.status_code} - {evidence_resp.text}")
    st.stop()

evidence_report = evidence_resp.json()
is_valid = evidence_report.get("status") == "OK"

# ============================
# 🟢 / 🔴 STATUS VISUAL
# ============================

if is_valid:
    st.success("✔ Auditoria íntegra e confiável")
    verify_result = verify_resp.json()
    st.metric("Eventos verificados na última checagem", verify_result.get("checked_events", "N/A"))
else:
    st.error("❌ Violação de Integridade Detectada")

    forensic_record = evidence_report.get("forensic_record")
    if forensic_record:
        st.write("#### Detalhes da Violação")

        try:
            violation_details = json.loads(forensic_record.get("payload_after", "{}"))
        except (json.JSONDecodeError, TypeError):
            violation_details = {}

        col1, col2 = st.columns(2)
        col1.metric("ID do Evento Comprometido", violation_details.get("broken_at_id", "N/A"))
        col2.metric(
            "Data da Detecção (UTC)",
            pd.to_datetime(evidence_report.get("violated_at")).strftime("%d/%m/%Y %H:%M:%S"),
        )

        st.warning(f"**Motivo:** `{violation_details.get('reason', 'Desconhecido')}`")

        with st.expander("🔍 Detalhes Técnicos da Evidência"):
            st.write("##### Hash Esperado vs. Encontrado")
            if "expected_prev_hash" in violation_details:
                st.code(
                    f"- Hash Anterior Esperado: {violation_details['expected_prev_hash']}\n+ Hash Anterior Encontrado: {violation_details['found_prev_hash']}",
                    language="diff",
                )
            elif "expected" in violation_details:
                st.code(
                    f"- Hash Calculado: {violation_details['expected']}\n+ Hash Armazenado: {violation_details['found']}",
                    language="diff",
                )

            st.write("##### Registro Forense Completo")
            st.json(evidence_report, expanded=False)
    else:
        st.warning(f"Motivo: **{evidence_report.get('reason', 'Desconhecido')}**")
        st.warning(f"Evento afetado (ID): **{evidence_report.get('violated_event_id', 'N/A')}**")

# ============================
# 🧾 EXPORTAÇÃO
# ============================

st.divider()
st.subheader("🧾 Exportar Relatório Forense")

# JSON Export
json_bytes = json.dumps(evidence_report, indent=2, default=str).encode("utf-8")

# CSV Export
flat_data = {}
flat_data.update(evidence_report)
forensic_record = flat_data.pop("forensic_record", {})
if forensic_record:
    forensic_flat = {f"forensic_{k}": v for k, v in forensic_record.items()}
    flat_data.update(forensic_flat)

if "forensic_payload_after" in flat_data and flat_data["forensic_payload_after"]:
    try:
        payload_details = json.loads(flat_data.pop("forensic_payload_after"))
        payload_flat = {f"violation_{k}": v for k, v in payload_details.items()}
        flat_data.update(payload_flat)
    except Exception:
        pass

df_export = pd.DataFrame([flat_data])
csv_bytes = df_export.to_csv(index=False).encode("utf-8")

col1, col2, _ = st.columns([1, 1, 3])
col1.download_button(
    label="📥 Baixar JSON",
    data=json_bytes,
    file_name="relatorio_integridade.json",
    mime="application/json",
    use_container_width=True,
)
col2.download_button(
    label="📄 Baixar CSV",
    data=csv_bytes,
    file_name="relatorio_integridade.csv",
    mime="text/csv",
    use_container_width=True,
)

# ============================
# 🔗 ANCORAGEM EXTERNA
# ============================
st.divider()
st.subheader("🔗 Ancoragem Criptográfica Externa")
st.caption(
    "Cria uma prova externa e imutável do estado atual da cadeia de auditoria, publicando o último hash em um serviço terceiro (Pastebin)."
)

if st.button("⚓ Criar Âncora no Pastebin", type="primary", use_container_width=True):
    with st.spinner("Gerando âncora externa..."):
        try:
            resp = api._request("POST", "/admin/audit/anchor")
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Âncora criada com sucesso! URL: {data['url']}")
                st.link_button("Abrir Âncora no Pastebin", url=data["url"])
            else:
                st.error(f"Erro ao criar âncora: {resp.text}")
        except Exception as e:
            st.error(f"Erro de conexão ao criar âncora: {e}")

# ============================
# ⛔ BLOQUEIO DE ESCRITA
# ============================

st.divider()
st.subheader("⛔ Proteção do sistema")

if not is_valid:
    st.error(
        """
        ⚠️ **A auditoria foi comprometida.**

        O sistema está agora em modo **SOMENTE LEITURA** para preservar as evidências.
        Nenhuma nova inserção, atualização ou exclusão será permitida até que a integridade seja restaurada.
        """
    )
else:
    st.info("Sistema liberado para operações de escrita.")
