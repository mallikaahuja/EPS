import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os

# --- CONFIGURATION (USING YOUR EXACT FOLDER NAME) ---
SYMBOLS_DIR = Path("PN&D-Symbols-library")
# A default image in case one is missing. Make sure "General.png" exists in your library.
DEFAULT_IMAGE = "General.png" 

# --- YOUR DIAGNOSTIC CHECK (Excellent idea!) ---
# This will run once at the start of the script.
if not SYMBOLS_DIR.exists():
    st.error(f"CRITICAL ERROR: The symbol directory was not found.")
    st.error(f"The code is looking for a folder named '{SYMBOLS_DIR}' in the root of the repository.")
    st.error("Please verify that the folder exists and the name matches exactly.")
    # We use st.stop() to halt the app if the symbols folder is missing.
    st.stop()

# --- YOUR COMPLETE COMPONENT LIBRARY ---
# This uses your exact filenames.
# Reminder: It is highly recommended to convert all .jpg and other formats to .png
AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png",
    "ACG Filter (Suction)": "ACG filter at suction .PNG",
    "Air Cooler": "Air_Cooled.png",
    "Averaging Pitot Tube": "Averaging_Pitot_Tube.png",
    # ... (the rest of your full dictionary)
    "Vertical Vessel": "Vertical vessel.jpg",
    "Y-Strainer": "Y-strainer.png"
}

# --- STREAMLIT APP ---
st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator")

# Initialize session state
if 'component_list' not in st.session_state:
    st.session_state.component_list = []

# --- UI (YOURS) ---
st.header("Step 1: Add Components")
col1, col2 = st.columns([1, 2])

with col1:
    with st.form("component_form", clear_on_submit=True):
        comp_type = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()))
        comp_tag = st.text_input("Component Tag (UNIQUE)", value=f"Comp-{len(st.session_state.component_list) + 1}")
        
        submitted = st.form_submit_button("Add Component")
        if submitted:
            if any(c['Tag'] == comp_tag for c in st.session_state.component_list):
                st.error(f"Tag '{comp_tag}' already exists!")
            else:
                st.session_state.component_list.append({
                    "Tag": comp_tag,
                    "Type": comp_type,
                    "Image": AVAILABLE_COMPONENTS[comp_type]
                })

with col2:
    st.write("### Current Components")
    if st.session_state.component_list:
        st.dataframe(pd.DataFrame(st.session_state.component_list)[['Tag', 'Type']], use_container_width=True, hide_index=True)
    else:
        st.info("No components added yet")

# --- DIAGRAM GENERATION (YOUR FUNCTION, CORRECTED) ---
st.header("Step 2: Generate P&ID")

def generate_pnid():
    """Generates the diagram using relative paths for reliability."""
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', ranksep='0.75', nodesep='0.5')
    dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
    
    dot.node("INLET", "INLET", shape='point', width='0.1')
    dot.node("OUTLET", "OUTLET", shape='point', width='0.1')
    
    last_node = "INLET"
    
    for component in st.session_state.component_list:
        tag = component['Tag']
        img_path_str = str(SYMBOLS_DIR / component['Image'])

        if os.path.exists(img_path_str):
            dot.node(tag, label=tag, image=img_path_str)
        else:
            # This check is good for debugging if an image is missing from the folder
            st.warning(f"Could not find image: '{img_path_str}'. Using default.")
            default_path_str = str(SYMBOLS_DIR / DEFAULT_IMAGE)
            dot.node(tag, label=f"{tag}\n(Image Missing)", image=default_path_str if os.path.exists(default_path_str) else "")
        
        dot.edge(last_node, tag)
        last_node = tag
    
    dot.edge(last_node, "OUTLET")
    return dot

if st.button("Generate P&ID", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add components first!")
    else:
        with st.spinner("Generating diagram..."):
            dot = generate_pnid()
            if dot:
                st.graphviz_chart(dot)
                try:
                    png_data = dot.pipe(format='png')
                    st.download_button("Download P&ID", data=png_data, file_name="generated_pnid.png", mime="image/png")
                except Exception as e:
                    st.error(f"Could not generate PNG for download. This can happen if an image format (like .jpg) is not supported by the Graphviz engine. Error: {e}")

if st.session_state.component_list:
    if st.button("Start Over", type="secondary"):
        st.session_state.component_list = []
        st.rerun()
