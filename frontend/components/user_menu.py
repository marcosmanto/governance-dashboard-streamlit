import time

import streamlit as st

from backend.core.config import settings
from frontend.core.pages import Page
from frontend.util.greeting import saudacao_usuario


def render_user_menu(api, user):
    if not user:
        return

    nome = user.get("name") or user.get("username")
    saudacao = saudacao_usuario(nome)

    # Lógica para montar a URL completa da imagem
    avatar_path = user.get("avatar_path")
    if avatar_path:
        # Se for caminho relativo (/static...), concatena com a URL da API
        if avatar_path.startswith("/"):
            avatar_url = f"{settings.API_BASE_URL}{avatar_path}?v={int(time.time())}"
        else:
            avatar_url = avatar_path
    else:
        # Avatar padrão (placeholder)
        avatar_url = f"https://ui-avatars.com/api/?name={nome}&background=random"

    with st.sidebar:
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;gap:10px;padding: 10px 0;">
            <img src="{avatar_url}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;border: 2px solid #e0e0e0;">
            <div style="line-height: 1.1;">
                <div style="font-size: 11px; color: gray;">{saudacao}</div>
                <div style="font-weight:600; font-size: 13px;">{user.get("role", "").upper()}</div>
            </div>
        </div>
        <hr style="margin: 5px 0 10px 0;">
        """,
            unsafe_allow_html=True,
        )

        # Menu de navegação rápida
        st.markdown(
            '<div style="font-size: 12px; font-weight: 600; color: #666; margin-bottom: 5px;">⚙️ CONTA</div>',
            unsafe_allow_html=True,
        )

        if st.button("👤 Meu Perfil", use_container_width=True):
            st.switch_page(Page.PROFILE.path)

        if st.button("🔐 Trocar Senha", use_container_width=True):
            st.switch_page(Page.CHANGE_PASSWORD.path)

        if st.button("🚪 Sair", type="primary", use_container_width=True):
            api.logout()
            st.session_state.clear()
            st.switch_page(Page.LOGIN.path)
