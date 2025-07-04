import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai
from streamlit_elements import elements, mui
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- COMPLETE COMPONENT LIBRARY ---
# Ensure this dictionary matches your standardized filenames in the "symbols" folder.
AVAILABLE_COMPONENTS = {
    "Vertical Vessel": "vertical_vessel.png",
    "Butterfly Valve": "butterfly_valve.png",
    "Gate Valve": "gate_valve.png",
    "Dry Pump Model": "dry_pump_model.png",
    "Discharge Condenser": "discharge_condenser.png",
    # (Your full list of components should be here)
}

# --- HELPER & GENERATION FUNCTIONS ---

def create_placeholder_image(text, path):
    try:
        img = Image.new('RGB', (100, 75), color=(240, 240, 240))
        d = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        d.rectangle([0,0,99,74], outline="black")
        d.text((10,30), f"MISSING:\n{text}", fill=(0,0,0), font=font)
        img.save(path)
        return str(path)
    except Exception:
        return None

def generate_pnid_graph(component_list):
    if not component_list: return None
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', ranksep='1.0', nodesep='0.5')
    dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
    
    dot.node("INLET", "INLET", shape='point', width='0.1')
    last_node = "INLET"
    
    for comp in component_list:
        tag = comp['tag']
        comp_type = comp['type']
        img_filename = AVAILABLE_COMPONENTS.get(comp_type)

        if img_filename:
            img_path = SYMBOLS_DIR / img_filename
            if os.path.exists(img_path):
                dot.node(tag, label=tag, image=str(img_path))
            else:
                placeholder_path = TEMP_DIR / img_filename
                create_placeholder_image(comp_type, placeholder_path)
                dot.node(tag, label=tag, image=str(placeholder_path))
        else:
            dot.node(tag, label=f"{tag}\n({comp_type})", shape='box', style='dashed')
        
        dot.edge(last_node, tag)
        last_node = tag
        
    dot.node("OUTLET", "OUTLET", shape='point', width='0.1')
    dot.edge(last_node, "OUTLET")
    return dot

# --- INITIALIZE SESSION STATE ---
if 'components' not in st.session_state:
    st.session_state.components = []
if "show_modal" not in st.session_state:
    st.session_state.show_modal = False

# --- UI DEFINITION ---
st.title("EPS P&ID Generator")
st.markdown("Use the sidebar to add components. The preview will update automatically.")

with st.sidebar:
    st.subheader("P&ID Builder")
    if st.button("➕ Add New Component", use_container_width=True):
        st.session_state.show_modal = True

# This `elements` frame WRAPS the modal, which fixes the ElementsFrameError
with elements("ui_elements"):
    with mui.Modal(
        "Add a New Component to the Sequence",
        open=st.session_state.show_modal,
        onClose=lambda: setattr(st.session_state, 'show_modal', False),
    ):
        with mui.Box(sx={"p": 4, "bgcolor": "background.paper"}):
            ctype = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()), key="modal_ctype")
            tag = st.text_input("Tag / Label (must be unique)", value=f"Comp-{len(st.session_state.components)+1}", key="modal_tag")
            
            if st.button("Save Component", key="modal_save"):
                if tag and not any(c['tag'] == tag for c in st.session_state.components):
                    st.session_state.components.append({"type": ctype, "tag": tag})
                    st.session_state.show_modal = False
                    st.rerun()
                else:
                    st.warning("Tag is empty or already exists.")

# --- MAIN PAGE DISPLAY ---
col1, col2 = st.columns([1, 2])

with col1:
    with st.container(border=True):
        st.subheader("Component Sequence")
        if st.session_state.components:
            df = pd.DataFrame(st.session_state.components)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.button("Clear All", use_container_width=True, type="secondary"):
                st.session_state.components = []
                st.rerun()
        else:
            st.info("No components added yet.")

with col2:
    with st.container(border=True):
        st.subheader("Live P&ID Preview")
        if st.session_state.components:
            p_and_id_graph = generate_pnid_graph(st.session_state.components)
            if p_and_id_graph:
                st.graphviz_chart(p_and_id_graph)
                
                try:
                    png_data = p_and_id_graph.pipe(format='png')
                    st.download_button(
                        label="⬇️ Download P&ID as PNG",
                        data=png_data,
                        file_name="generated_pnid.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Could not render PNG for download. Error: {e}")
        else:
            st.info("Your diagram will appear here once you add components.")
