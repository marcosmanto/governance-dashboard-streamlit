import streamlit as st

from frontend.core.pages import Page


def set_current_page(page: Page):
    st.session_state["_page"] = page.key


def get_current_page() -> str | None:
    return st.session_state.get("_page")
