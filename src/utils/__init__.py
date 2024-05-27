import streamlit as st

DEBUG_MODE = bool(st.secrets.get("DEBUG") or False)

def is_debug():
    return DEBUG_MODE