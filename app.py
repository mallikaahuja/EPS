import streamlit as st
import pandas as pd
# from graphviz import Digraph  <- Commented out for now
# from pathlib import Path       <- Commented out for now
# import os                      <- Commented out for now
# import openai                  <- Commented out for now
# from PIL import Image, ImageDraw, ImageFont <- Commented out for now

st.set_page_config(layout="wide", page_title="Intelligent P&ID Generator", page_icon="🧠")

if 'equipment' not in st.session_state:
    st.session_state.equipment = []
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []
if 'inline_components' not in st.session_state:
    st.session_state.inline_components = []

st.title("🧠 Intelligent P&ID Generator - Step 1: UI Test")

with st.sidebar:
    st.subheader("P&ID Builder")
    with st.expander("1. Add Major Equipment", expanded=True):
        with st.form("add_equipment", clear_on_submit=True):
            eq_type = st.text_input("Equipment Type") # Simplified for now
            eq_tag = st.text_input("Equipment Tag (e.g., P-101)")
            if st.form_submit_button("Add Equipment", use_container_width=True):
                if eq_tag and not any(e['tag'] == eq_tag for e in st.session_state.equipment):
                    st.session_state.equipment.append({'tag': eq_tag, 'type': eq_type})
                else:
                    st.warning("Tag is empty or already exists.")

st.subheader("Current P&ID Data")
st.dataframe(pd.DataFrame(st.session_state.equipment))

st.success("If you can see this, the UI and Pandas are working correctly!")
