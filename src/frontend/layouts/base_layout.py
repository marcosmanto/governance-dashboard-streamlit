import streamlit as st

from frontend.components.user_menu import render_user_menu
from frontend.services.session import require_auth

# ⚙️ Settings de Estilo da Sidebar
SIDEBAR_FONT_SIZE = "14px"
SIDEBAR_BUTTON_SIZE = "13px"


def base_layout(page_title: str, page_icon: str, wide: bool = False):
    # 1. Configuração da página deve ser SEMPRE a primeira instrução Streamlit
    layout_mode = "wide" if wide else "centered"

    try:
        st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout_mode)
    except Exception:
        # Evita erro se set_page_config for chamado duas vezes (bug comum no Streamlit)
        pass

    # 🎨 Injeção de CSS para ajuste fino da Sidebar
    st.markdown(
        f"""
        <style>
        /* Ajuste global de fontes na sidebar (afeta textos soltos) */
        section[data-testid="stSidebar"] * {{
            font-size: {SIDEBAR_FONT_SIZE} !important;
        }}

        /* Botões mais compactos e com fonte menor */
        section[data-testid="stSidebar"] .stButton button {{
            font-size: {SIDEBAR_BUTTON_SIZE} !important;
            padding-top: 4px !important;
            padding-bottom: 4px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            min-height: 0px !important;
            height: auto !important;
            line-height: 1.2 !important;
            margin-top: 2px !important;
            margin-bottom: 2px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 2. Verifica autenticação
    api, user = require_auth()

    # 🔄 Recuperação de dados completos (Avatar/Email)
    # Se o objeto user vier apenas do token (sem avatar_path), buscamos o perfil completo
    if user and "avatar_path" not in user:
        try:
            resp = api._request("GET", "/me")
            if resp.status_code == 200:
                full_data = resp.json()
                user.update(full_data)
                st.session_state.user = user
        except Exception:
            pass

    # 3. Renderiza menu lateral
    render_user_menu(api, user)

    return api, user
