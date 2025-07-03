# app.py - DIAGNOSTIC TOOL VERSION

import streamlit as st
import pandas as pd
from graphviz import Digraph
import os
import base64

st.set_page_config(layout="wide")
st.title("P&ID Generator (Diagnostic Mode)")

AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png", "ACG Filter (Suction)": "ACG filter at suction .PNG", "Air Cooler": "Air_Cooled.png",
    "Averaging Pitot Tube": "Averaging_Pitot_Tube.png", "Axial Flow Fan": "Axial_flow_fan.png",
    "Bag Filter/Separator": "Bag.png", "Bin/Silo": "Bin.png", "Briquetting Machine": "Briquetting_Machine.png",
    "Butterfly Valve": "Butterfly valve.PNG", "Catch Pot (Auto, for Condenser)": "Catch pot with Auto drain for condenser.PNG",
    "Catch Pot (Auto Drain)": "Catch pot with auto drain.PNG", "Check Valve": "Check valve.PNG",
    "Vertical Vessel": "Vertical vessel.jpg", "General Connection": "General.png",
    # This is a truncated list for the test
}

if 'component_list' not in st.session_state:
    st.session_state.component_list = []

st.header("Step 1: Add ONE Component for Testing")
with st.form("component_form", clear_on_submit=True):
    comp_type = st.selectbox("Component Type", options=sorted(list(AVAILABLE_COMPONENTS.keys())))
    comp_label = st.text_input("Component Label / Tag", "V-101")
    submitted = st.form_submit_button("Add Component")
    if submitted and comp_label:
        st.session_state.component_list.append({
            "Tag": comp_label, "Symbol_Image": AVAILABLE_COMPONENTS[comp_type], "Description": comp_type
        })
        st.rerun()

st.header("Step 2: Generate P&ID and Run Diagnostics")
if st.button("Run Diagnostics", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add one component to test.")
    else:
        st.subheader("--- DIAGNOSTIC REPORT ---")
        
        # --- File System Check ---
        st.markdown("### 1. File System Check")
        try:
            current_directory = os.getcwd()
            st.info(f"Current Working Directory: `{current_directory}`")
            
            all_files_in_repo = []
            for root, dirs, files in os.walk(current_directory):
                for name in files:
                    all_files_in_repo.append(os.path.join(root, name))
            
            st.write("Files found in the repository root:")
            st.code('\n'.join(all_files_in_repo[-10:])) # Show last 10 files
        except Exception as e:
            st.error(f"Could not list files: {e}")

        # --- Component Processing Check ---
        st.markdown("### 2. Component Processing Check")
        for component in st.session_state.component_list:
            tag = component['Tag']
            filename = component['Symbol_Image']
            
            st.markdown(f"**Processing `{tag}` (Filename: `{filename}`):**")
            
            # Test relative path
            relative_path = os.path.join("PN&D-Symbols-library", filename)
            st.write(f"Attempting Relative Path: `{relative_path}`")
            if os.path.exists(relative_path):
                st.success("✅ Relative path EXISTS.")
            else:
                st.error("❌ Relative path DOES NOT EXIST.")

        # --- Drawing Attempt ---
        st.markdown("### 3. Drawing Attempt")
        with st.spinner("Drawing..."):
            dot = Digraph()
            dot.attr(rankdir='LR')
            dot.node("INLET", "INLET", shape='plaintext')
            dot.node("OUTLET", "OUTLET", shape='plaintext')
            all_tags = ["INLET"] + [c['Tag'] for c in st.session_state.component_list] + ["OUTLET"]

            for component in st.session_state.component_list:
                # Use the relative path again for the actual drawing
                image_path = os.path.join("PN&D-Symbols-library", component['Symbol_Image'])
                dot.node(name=component['Tag'], label=component['Tag'], image=image_path, shape='none')

            for i in range(len(all_tags) - 1):
                dot.edge(all_tags[i], all_tags[i+1])
            
            st.graphviz_chart(dot)
            st.success("Drawing command sent to Graphviz.")

if st.button("Start Over"):
    st.session_state.component_list = []
    st.rerun()
