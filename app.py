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

# --- STANDARD COMPONENT ORDER ---
STANDARD_ORDER = [
    "Vacuum Pump", "Discharge Silencer", "Catch Pot", "Vacuum Breaker Valve", "Cooling Water Inlet",
    "Heat Exchanger", "Condenser", "Receiver", "Pressure Transmitter", "Vertical Vessel"
]

# --- HELPERS ---
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

def reorder_components_by_standard_order(components):
    type_to_order = {t: i for i, t in enumerate(STANDARD_ORDER)}
    return sorted(components, key=lambda x: type_to_order.get(x['type'], len(STANDARD_ORDER)))

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

# --- Display Component Sequence ---
st.subheader("Component Sequence (Auto-Ordered)")

if st.session_state.component_list:
    ordered_components = reorder_components_by_standard_order(st.session_state.component_list)
    df = pd.DataFrame(ordered_components)
    st.table(df)
else:
    st.info("No components added yet.")

# --- Scrollable Preview ---
st.markdown("---")
st.subheader("Live Preview (Scroll →)")
st.markdown("""
    <style>
    .scrollable-preview {
        overflow-x: scroll;
        white-space: nowrap;
    }
    .preview-block {
        display: inline-block;
        margin-right: 40px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

if st.session_state.component_list:
    ordered_components = reorder_components_by_standard_order(st.session_state.component_list)
    preview_html = '<div class="scrollable-preview">'
    for comp in ordered_components:
        img_data = load_symbol_image(comp['type'])
        if img_data:
            preview_html += f"""
            <div class="preview-block">
                <img src="{img_data}" width="100"><br>
                <b>{comp['tag']}</b><br>
                <small>{comp['type']}</small>
            </div>
            """
        else:
            preview_html += f"""
            <div class="preview-block">
                <div style="width:100px;height:100px;background:#ccc;">❓</div><br>
                <b>{comp['tag']}</b><br>
                <small>{comp['type']}</small>
            </div>
            """
    preview_html += '</div>'
    st.markdown(preview_html, unsafe_allow_html=True)

# --- Download DXF ---
st.markdown("---")
st.subheader("Export to DXF")
if st.button("Download DXF"):
    if not st.session_state.component_list:
        st.error("No components to export.")
    else:
        try:
            ordered = reorder_components_by_standard_order(st.session_state.component_list)
            dxf_path = create_dxf(ordered)
            with open(dxf_path, "rb") as f:
                st.download_button(
                    label="Download DXF File",
                    data=f,
                    file_name="EPS_PnID.dxf",
                    mime="application/dxf"
                )
        except Exception as e:
            st.error(f"DXF Export Failed: {e}")
