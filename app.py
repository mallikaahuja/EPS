# app.py

import streamlit as st
import pandas as pd
import json
import os

from process_mapper import map_process_to_eps_products
from booster_logic import evaluate_booster_requirements
from advanced_rendering import ProfessionalRenderer
from control_systems import add_control_logic_block

# Load supporting files
@st.cache_data
def load_data():
    with open("component_mapping.json") as f:
        component_mapping = json.load(f)
    eq_layout = pd.read_csv("enhanced_equipment_layout.csv")
    pipe_layout = pd.read_csv("pipe_connections_layout.csv")
    equipment_list = pd.read_csv("equipment_list.csv")
    pipeline_list = pd.read_csv("pipeline_list.csv")
    inline_list = pd.read_csv("inline_component_list.csv")
    return component_mapping, eq_layout, pipe_layout, equipment_list, pipeline_list, inline_list

component_mapping, eq_layout, pipe_layout, equipment_list, pipeline_list, inline_list = load_data()

# Phase 1 — Process Recommendation
st.set_page_config(layout="wide")
st.title("EPS Interactive PFD → P&ID Generator")

with st.expander("🧠 Step 1: EPS System Recommendation"):
    industry = st.selectbox("Industry", ["Pharmaceutical", "Chemical", "Food & Beverage", "Wastewater"])
    flow_rate = st.number_input("Flow Rate (m³/h)", min_value=1)
    pressure = st.number_input("Vacuum Level (mbar)", min_value=0.01)
    application = st.text_input("Application", placeholder="e.g. drying, filtration, solvent recovery")
    compliance = st.multiselect("Compliance", ["cGMP", "FDA", "HACCP", "ISO 9001"])
    automation = st.selectbox("Automation Level", ["None", "Basic Panel", "PLC", "SCADA"])
    vapor_type = st.selectbox("Vapor Type", ["Clean", "Condensable", "Corrosive"])
    contamination_sensitive = st.checkbox("Contamination-Sensitive?", value=True)

    if st.button("🎯 Recommend EPS Configuration"):
        recommended = map_process_to_eps_products(industry, flow_rate, pressure, application, compliance)
        primary = next((r for r in recommended if "Pump" in r and "Booster" not in r), None)
        booster_cfg, booster_warnings = evaluate_booster_requirements(
            flow_rate, pressure, vapor_type.lower(), contamination_sensitive, primary, automation
        )
        st.session_state["autocomponents"] = recommended.copy()
        if booster_cfg["enabled"]:
            st.session_state["autocomponents"].append("Mechanical Vacuum Booster")
            st.session_state["booster_cfg"] = booster_cfg

        st.success("✅ EPS Mapping Complete")
        for c in st.session_state["autocomponents"]:
            st.markdown(f"- {c}")
        for w in booster_warnings:
            st.warning(w)

# Phase 2 — Manual + Auto Component Selection
st.markdown("---")
st.header("🔧 Step 2: Build and Customize Your P&ID")

with st.expander("➕ Add Components"):
    col1, col2, col3 = st.columns(3)
    equipment = col1.selectbox("Equipment", equipment_list["Component"].tolist())
    pipeline = col2.selectbox("Pipeline", pipeline_list["Component"].tolist())
    inline = col3.selectbox("Inline Component", inline_list["Component"].tolist())

    if "components" not in st.session_state:
        st.session_state["components"] = []

    if st.button("➕ Add Selected Components"):
        st.session_state["components"] += [equipment, pipeline, inline]

    if "autocomponents" in st.session_state:
        if st.button("✨ Use Auto-Generated EPS Setup"):
            st.session_state["components"] = st.session_state["autocomponents"]

# Component Table
st.subheader("📋 Tag Table")
comp_data = [{"Component": c, "Tag": f"C-{i+1:03d}"} for i, c in enumerate(st.session_state["components"])]
tag_df = pd.DataFrame(comp_data)
edited_df = st.data_editor(tag_df, num_rows="dynamic", use_container_width=True)
selected_tags = edited_df.to_dict("records")

# Layout Controls
st.subheader("🧱 Layout Controls")
col1, col2, col3, col4 = st.columns(4)
grid_rows = col1.slider("Grid Rows", 1, 12, 6)
grid_cols = col2.slider("Grid Columns", 1, 12, 6)
spacing = col3.slider("Spacing", 80, 300, 150)
scale = col4.slider("Symbol Scale", 0.5, 2.0, 1.0)

# Preview Panel
st.subheader("🖼️ Symbol Preview")
cols = st.columns(6)
for idx, row in enumerate(selected_tags):
    sym_file = f"symbols/{row['Component'].lower().replace(' ', '_')}.svg"
    with cols[idx % 6]:
        st.markdown(f"**{row['Tag']}**")
        if os.path.exists(sym_file):
            st.image(sym_file, use_column_width=True)
        else:
            st.error("Missing")

# Generate P&ID
if st.button("🚀 Generate Final P&ID"):
    component_ids = [r["Component"].lower().replace(" ", "_") for r in selected_tags]

    renderer = ProfessionalRenderer(booster_config=st.session_state.get("booster_cfg", {}))
    pid_svg = renderer.render_professional_pnid(
        components=component_ids,
        pipes=pipe_layout.to_dict("records"),
        width=grid_cols * spacing,
        height=grid_rows * spacing
    )

    pid_svg = add_control_logic_block(pid_svg, st.session_state.get("booster_cfg", {}))

    st.subheader("📌 Final Output")
    st.image(pid_svg, use_column_width=True)
    st.download_button("📥 PNG", pid_svg.encode(), file_name="pid_output.png")
    st.download_button("📐 DXF", pid_svg.encode(), file_name="pid_output.dxf")
