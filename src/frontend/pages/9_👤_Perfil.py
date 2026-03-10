import base64
import time

import requests
import streamlit as st

from frontend.config import settings
from frontend.core.pages import Page
from frontend.layouts.base_layout import base_layout
from frontend.services.navigation import set_current_page

# Define a página atual para controle de navegação
set_current_page(Page.PROFILE)

# Usa o layout base
api, user = base_layout("Meu Perfil", "👤")

# 🔄 Otimização: Só busca do backend se faltar dados essenciais (evita delay)
if not user.get("email"):
    try:
        resp = api._request("GET", "/me")
        if resp.status_code == 200:
            user = resp.json()
            st.session_state.user = user  # Atualiza sessão
    except Exception:
        pass

st.title("👤 Meu Perfil")
st.caption("Gerencie suas informações pessoais e foto de perfil.")

# --- Layout em Colunas ---
col_info, col_avatar = st.columns([2, 1])

# --- Coluna 1: Dados Cadastrais ---
with col_info:
    st.subheader("📝 Dados Pessoais")
    with st.form("profile_form"):
        email = st.text_input("Email", value=user.get("email") or "")
        name = st.text_input("Nome de Exibição", value=user.get("name") or "")
        fullname = st.text_input("Nome Completo", value=user.get("fullname") or "")

        submitted = st.form_submit_button("Salvar Alterações", type="primary")

        if submitted:
            try:
                resp = api._request(
                    "PUT", "/me/profile", json={"email": email, "name": name, "fullname": fullname}
                )

                if resp.status_code == 200:
                    # 🔄 Recarrega dados do backend para garantir consistência total
                    # (evita perder o avatar_path se o objeto local estiver desincronizado)
                    user_resp = api._request("GET", "/me")
                    if user_resp.status_code == 200:
                        st.session_state.user = user_resp.json()

                    st.success("Perfil atualizado com sucesso!")
                    st.rerun()
                else:
                    error_detail = resp.json().get("detail", "Erro ao atualizar")
                    if error_detail == "EMAIL_ALREADY_EXISTS":
                        st.error("Este e-mail já está em uso por outro usuário.")
                    else:
                        st.error(f"Erro: {error_detail}")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

# --- Coluna 2: Avatar ---
with col_avatar:
    st.subheader("📸 Foto de Perfil")

    # Upload de nova foto
    uploaded_file = st.file_uploader("Alterar foto", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        st.image(uploaded_file, width=150, caption="Pré-visualização")

        if st.button("Salvar Nova Foto", type="primary"):
            # Validação de tamanho no frontend para uma melhor UX
            if uploaded_file.size > 2 * 1024 * 1024:  # 2MB
                st.error("O arquivo é muito grande. O limite máximo é de 2MB.")
                # Não continua para o spinner/upload
                st.stop()

            with st.spinner("Enviando..."):
                try:
                    # Prepara o arquivo para envio multipart/form-data
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

                    # Usa requests direto aqui pois o wrapper api._request pode tentar serializar JSON
                    resp = requests.post(
                        f"{settings.API_BASE_URL}/me/avatar",
                        headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                        files=files,
                        timeout=15,
                        verify=settings.SSL_VERIFY,
                    )

                    if resp.status_code == 200:
                        # 🔄 Recarrega dados do backend para garantir consistência e URL atualizada
                        user_resp = api._request("GET", "/me")
                        if user_resp.status_code == 200:
                            st.session_state.user = user_resp.json()

                        st.success("Avatar atualizado!")
                        st.rerun()
                    else:
                        st.error(f"Erro no upload: {resp.text}")
                except Exception as e:
                    st.error(f"Erro ao enviar arquivo: {e}")
    else:
        # Exibe avatar atual
        avatar_path = user.get("avatar_path")
        if avatar_path:
            if avatar_path.startswith("/"):
                # ?v=timestamp força o navegador a recarregar a imagem (cache busting)
                img_url = f"{settings.API_BASE_URL}{avatar_path}?v={int(time.time())}"
            else:
                img_url = avatar_path
        else:
            nome = user.get("name") or user.get("username") or "User"
            img_url = f"https://ui-avatars.com/api/?name={nome}&background=random&size=150"

        st.image(img_url, width=150, caption="Avatar Atual")

# --- Seção de Permissões ---
st.divider()
st.subheader("🛡️ Permissões e Acesso")
st.info(f"Seu nível de acesso atual é: **{user.get('role', '').upper()}**")

with st.expander("Solicitar mudança de nível de acesso"):
    with st.form("role_request_form"):
        new_role = st.selectbox("Nível desejado", ["editor", "admin", "reader"])
        justification = st.text_area(
            "Justificativa", placeholder="Explique por que precisa deste acesso..."
        )

        if st.form_submit_button("Enviar Solicitação"):
            if new_role == user.get("role"):
                st.warning("Você já possui este perfil.")
            elif not justification.strip():
                st.error("A justificativa é obrigatória.")
            else:
                try:
                    resp = api._request(
                        "POST",
                        "/me/role-request",
                        json={"requested_role": new_role, "justification": justification},
                    )
                    if resp.status_code == 200:
                        st.success("Solicitação enviada! Um administrador analisará seu pedido.")
                    else:
                        st.error(resp.json().get("detail", "Erro ao enviar."))
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- Seção de Segurança (MFA) ---
st.divider()
st.subheader("🔐 Autenticação de Dois Fatores (2FA)")


@st.dialog("⚠️ Desativar 2FA")
def disable_mfa_dialog():
    st.write(
        "Para sua segurança, confirme sua senha atual para desativar a autenticação de dois fatores."
    )
    password = st.text_input("Senha atual", type="password")

    if st.button("Confirmar Desativação", type="primary"):
        if not password:
            st.error("Informe a senha.")
            return

        try:
            resp = api._request("POST", "/me/mfa/disable", json={"password": password})
            if resp.status_code == 200:
                st.success("2FA desativado com sucesso!")
                # 🔄 Recarrega dados do backend
                user_resp = api._request("GET", "/me")
                if user_resp.status_code == 200:
                    st.session_state.user = user_resp.json()
                time.sleep(1)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao desativar"))
        except Exception as e:
            st.error(f"Erro: {e}")


if user.get("mfa_enabled"):
    st.success("✅ 2FA Ativado", icon="🛡️")
    if st.button("Desativar 2FA"):
        disable_mfa_dialog()
else:
    st.info("Proteja sua conta ativando a autenticação de dois fatores.")

    if st.button("Configurar / Ativar 2FA"):
        with st.spinner("Gerando QR Code..."):
            try:
                resp = api._request("POST", "/me/mfa/setup")
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.mfa_setup_data = data
                else:
                    st.error("Erro ao iniciar configuração 2FA")
            except Exception as e:
                st.error(f"Erro: {e}")

if "mfa_setup_data" in st.session_state:
    data = st.session_state.mfa_setup_data
    st.info(
        "Escaneie o QR Code abaixo com seu aplicativo autenticador (Google Authenticator, Authy, etc)."
    )

    # Exibir QR Code
    st.image(base64.b64decode(data["qr_code"]), width=200)
    st.text_input("Segredo (caso não consiga ler o QR)", value=data["secret"], disabled=True)

    code = st.text_input("Digite o código de 6 dígitos gerado pelo app", max_chars=6)

    if st.button("Validar e Ativar"):
        resp = api._request("POST", "/me/mfa/enable", json={"code": code})
        if resp.status_code == 200:
            st.success("✅ 2FA Ativado com sucesso! Você precisará dele no próximo login.")
            del st.session_state.mfa_setup_data
            time.sleep(3)
            st.rerun()
        else:
            st.error(resp.json().get("detail", "Código inválido"))
