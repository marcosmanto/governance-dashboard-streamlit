import pandas as pd
import streamlit as st
from data.database import criar_conexao


@st.cache_resource
def get_connection():
    return criar_conexao()


@st.cache_data
def carregar_dados():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM registros", conn, parse_dates=["data"])
