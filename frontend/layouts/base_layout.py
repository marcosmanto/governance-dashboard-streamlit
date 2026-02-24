import streamlit as st

from frontend.components.user_menu import render_user_menu
from frontend.services.session import require_auth


def base_layout(page_title: str, page_icon: str, wide: bool = False):
    # 1. Configuração da página deve ser SEMPRE a primeira instrução Streamlit
    layout_mode = "wide" if wide else "centered"

    try:
        st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout_mode)
    except Exception:
        # Evita erro se set_page_config for chamado duas vezes (bug comum no Streamlit)
        pass

    # 2. Verifica autenticação
    api, user = require_auth()

    # 3. Renderiza menu lateral
    render_user_menu(api, user)

    return api, user
