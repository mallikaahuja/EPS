import streamlit as st
import pandas as pd
import os
import ezdxf
from pathlib import Path
import tempfile
import base64

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols")

# --- HELPER FUNCTIONS ---

def list_symbol_names():
    return sorted([f.stem.replace("_", " ") for f in SYMBOLS_DIR.glob("*.png")])

def load_symbol_image(symbol_name):
    safe_name = symbol_name.replace(" ", "_") + ".png"
    path = SYMBOLS_DIR / safe_name
    if path.exists():
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return None

def create_dxf(component_list):
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0

    for idx, c in enumerate(component_list):
        tag = c['tag']
        typ = c['type']
        msp.add_line((0, y), (2, y))
        msp.add_text(f"{tag}: {typ}", dxfattribs={'height': 0.3}).set_pos((2.5, y))
        y -= 1.5

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmpfile:
        doc.saveas(tmpfile.name)
        tmpfile.seek(0)
        return tmpfile.name

# --- SESSION STATE ---
if "component_list" not in st.session_state:
    st.session_state.component_list = []

# --- UI ---

st.title("EPS Interactive P&ID Generator")

with st.sidebar:
    st.header("Add Component")
    all_symbols = list_symbol_names()
    comp_type = st.selectbox("Component Type", all_symbols)
    comp_tag = st.text_input("Tag / Label (must be unique)", key="comp_tag_input")
    if st.button("Save Component"):
        if comp_tag and comp_type:
            st.session_state.component_list.append({"type": comp_type, "tag": comp_tag})
        else:
            st.warning("Both tag and component type are required.")

st.subheader("Component Sequence (Drag to Reorder)")
if st.session_state.component_list:
    for i, comp in enumerate(st.session_state.component_list):
        st.text(f"{i+1}. {comp['tag']} - {comp['type']}")
else:
    st.info("No components added yet.")

st.markdown("---")

st.subheader("Live Preview & Export")
preview_cols = st.columns(len(st.session_state.component_list) or 1)
for i, comp in enumerate(st.session_state.component_list):
    with preview_cols[i]:
        st.markdown(f"<center><b>{comp['tag']}</b></center>", unsafe_allow_html=True)
        img_data = load_symbol_image(comp['type'])
        if img_data:
            st.image(img_data, use_column_width=True)
        else:
            st.error("Missing image")

if st.button("Download DXF"):
    if not st.session_state.component_list:
        st.error("No components to export.")
    else:
        try:
            dxf_path = create_dxf(st.session_state.component_list)
            with open(dxf_path, "rb") as f:
                st.download_button(
                    label="Download DXF File",
                    data=f,
                    file_name="EPS_PnID.dxf",
                    mime="application/dxf"
                )
        except Exception as e:
            st.error(f"DXF Export Failed: {e}")
