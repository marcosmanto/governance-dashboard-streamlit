import requests
import streamlit as st

from backend.core.config import settings
from frontend.core.pages import Page
from frontend.layouts.base_layout import base_layout
from frontend.services.navigation import set_current_page

# Define a página atual para controle de navegação
set_current_page(Page.PROFILE)

# Usa o layout base
api, user = base_layout("Meu Perfil", "👤")

# 🔄 Força atualização dos dados do usuário (incluindo avatar e campos)
try:
    resp = api._request("GET", "/me")
    if resp.status_code == 200:
        user = resp.json()
        st.session_state.user = user  # Atualiza sessão para refletir no menu lateral
except Exception:
    # Se falhar (ex: erro de conexão), usa os dados em cache da sessão
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
                    st.success(
                        "Perfil atualizado com sucesso! Recarregue a página para ver as mudanças."
                    )
                    # Opcional: Forçar recarregamento dos dados do usuário na sessão
                    # st.rerun()
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

    # Exibe avatar atual
    avatar_path = user.get("avatar_path")
    if avatar_path:
        if avatar_path.startswith("/"):
            img_url = f"{settings.API_BASE_URL}{avatar_path}"
        else:
            img_url = avatar_path
    else:
        nome = user.get("name") or user.get("username") or "User"
        img_url = f"https://ui-avatars.com/api/?name={nome}&background=random&size=150"

    st.image(img_url, width=150, caption="Avatar Atual")

    # Upload de nova foto
    uploaded_file = st.file_uploader("Alterar foto", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        if st.button("Enviar Foto"):
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
                    )

                    if resp.status_code == 200:
                        st.success("Avatar atualizado!")
                        st.rerun()
                    else:
                        st.error(f"Erro no upload: {resp.text}")
                except Exception as e:
                    st.error(f"Erro ao enviar arquivo: {e}")
