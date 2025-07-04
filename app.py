import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Intelligent P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True) # Create a temp directory for placeholders

# --- COMPONENT LIBRARY ---
# This dictionary MUST match your standardized filenames.
AVAILABLE_COMPONENTS = {
    "Vertical Vessel": "vertical_vessel.png",
    "Butterfly Valve": "butterfly_valve.png",
    "Gate Valve": "gate_valve.png",
    "Dry Pump Model": "dry_pump_model.png",
    "Discharge Condenser": "discharge_condenser.png",
    # (Populate with your full list of components)
}
EQUIPMENT_TYPES = sorted(["Vertical Vessel", "Dry Pump Model", "Discharge Condenser"])
INLINE_TYPES = sorted(["Butterfly Valve", "Gate Valve"])


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

def generate_p_and_id():
    """Generates the diagram using the data in session state."""
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.5')
    dot.attr('node', shape='box', style='rounded')

    # Group equipment in a subgraph
    with dot.subgraph(name='cluster_main_process') as c:
        c.attr(label='Main Process Area', style='filled', color='lightgrey')
        for item in st.session_state.equipment:
            img_filename = AVAILABLE_COMPONENTS.get(item['type'], "general.png")
            img_path = SYMBOLS_DIR / img_filename
            if not img_path.exists():
                img_path = create_placeholder_image(item['type'], TEMP_DIR / img_filename)
            
            if img_path:
                 c.node(item['tag'], label=item['tag'], image=str(img_path), shape='none')
            else: # Fallback if placeholder fails
                c.node(item['tag'], f"{item['tag']}\n({item['type']})")

    # Connect pipelines and insert inline components
    for pipe in st.session_state.pipelines:
        components_on_this_pipe = [c for c in st.session_state.inline_components if c['pipe_tag'] == pipe['tag']]
        last_node_in_chain = pipe['from']
        
        for comp in components_on_this_pipe:
            comp_node_name = f"{comp['tag']}_{pipe['tag']}"
            img_filename = AVAILABLE_COMPONENTS.get(comp['type'], "general.png")
            img_path = SYMBOLS_DIR / img_filename
            if not img_path.exists():
                img_path = create_placeholder_image(comp['type'], TEMP_DIR / img_filename)

            if img_path:
                dot.node(comp_node_name, label=comp['tag'], image=str(img_path), shape='none')
            else:
                dot.node(comp_node_name, f"{comp['tag']}\n({comp['type']})")
            
            dot.edge(last_node_in_chain, comp_node_name)
            last_node_in_chain = comp_node_name
            
        dot.edge(last_node_in_chain, pipe['to'])

    return dot

# --- INITIALIZE SESSION STATE ---
if 'equipment' not in st.session_state: st.session_state.equipment = []
if 'pipelines' not in st.session_state: st.session_state.pipelines = []
if 'inline_components' not in st.session_state: st.session_state.inline_components = []

# --- UI ---
st.title("🧠 Intelligent P&ID Generator - Step 2: Drawing Test")

with st.sidebar:
    st.subheader("P&ID Builder")
    with st.expander("1. Add Major Equipment", expanded=True):
        with st.form("add_equipment", clear_on_submit=True):
            eq_type = st.selectbox("Equipment Type", EQUIPMENT_TYPES)
            eq_tag = st.text_input("Equipment Tag (e.g., P-101)")
            if st.form_submit_button("Add Equipment", use_container_width=True):
                if eq_tag and not any(e['tag'] == eq_tag for e in st.session_state.equipment):
                    st.session_state.equipment.append({'tag': eq_tag, 'type': eq_type})
                else: st.warning("Tag is empty or already exists.")

    equipment_tags = [e['tag'] for e in st.session_state.equipment]
    if len(equipment_tags) >= 2:
        with st.expander("2. Define Pipelines"):
            with st.form("add_pipeline", clear_on_submit=True):
                pipe_tag = st.text_input("Pipeline Tag (e.g., 100-B-1)")
                pipe_from = st.selectbox("From Equipment", equipment_tags)
                pipe_to = st.selectbox("To Equipment", equipment_tags)
                if st.form_submit_button("Add Pipeline", use_container_width=True):
                    if pipe_tag and pipe_from != pipe_to:
                        st.session_state.pipelines.append({'tag': pipe_tag, 'from': pipe_from, 'to': pipe_to})
                    else: st.warning("Tag is empty or 'From' and 'To' are the same.")

    pipeline_tags = [p['tag'] for p in st.session_state.pipelines]
    if pipeline_tags:
        with st.expander("3. Add In-Line Components"):
            with st.form("add_inline", clear_on_submit=True):
                inline_type = st.selectbox("Component Type", INLINE_TYPES)
                inline_pipe = st.selectbox("On Pipeline", pipeline_tags)
                inline_tag = st.text_input("Component Tag (e.g., HV-101)")
                if st.form_submit_button("Add In-Line Component", use_container_width=True):
                    if inline_tag: st.session_state.inline_components.append({'tag': inline_tag, 'type': inline_type, 'pipe_tag': inline_pipe})
                    else: st.warning("Please provide a tag for the component.")

# --- Main Display Area ---
st.subheader("Current P&ID Data")
col1, col2, col3 = st.columns(3)
with col1:
    st.dataframe(pd.DataFrame(st.session_state.equipment), hide_index=True)
with col2:
    st.dataframe(pd.DataFrame(st.session_state.pipelines), hide_index=True)
with col3:
    st.dataframe(pd.DataFrame(st.session_state.inline_components), hide_index=True)

st.markdown("---")
st.subheader("Generated P&ID Preview")
if st.session_state.equipment:
    final_dot = generate_p_and_id()
    st.graphviz_chart(final_dot)
else:
    st.info("Add equipment in the sidebar to begin.")
