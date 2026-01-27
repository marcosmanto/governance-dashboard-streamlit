# frontend/app_config.py
import streamlit as st


def init_page(
    page_title: str = "Painel de Dados",
    page_icon: str = ":bar_chart:",
    wide: bool = True,
    sidebar_state: str = "auto",
    menu_items: dict | None = None,
) -> None:
    """
    Inicializa a página Streamlit com configurações padrão da UI.
    - Chame no topo de CADA página (incluindo a página inicial).
    - Em Streamlit recentes, chamadas repetidas sobrescrevem apenas o que você passar.
    """
    layout = "wide" if wide else "centered"
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state=sidebar_state,
        menu_items=menu_items,
    )


# frontend/app_config.py
