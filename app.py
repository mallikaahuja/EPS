# app.py

import streamlit as st
import pandas as pd
import json
import os

from process_mapper import map_process_to_eps_products
from booster_logic import evaluate_booster_requirements
from advanced_rendering import render_final_pid
from control_systems import add_control_logic_block

# --- File Paths ---
EQUIPMENT_CSV = "enhanced_equipment_layout.csv"
PIPELINE_CSV = "pipe_connections_layout.csv"
COMPONENT_MAP_JSON = "component_mapping.json"
COMPONENTS_CSV = "components.csv"
PIPES_CSV = "pipes.csv"
SYMBOLS_FOLDER = "symbols"

# --- Load Data ---
@st.cache_data
def load_all_data():
    eq = pd.read_csv(EQUIPMENT_CSV)
    pipes = pd.read_csv(PIPELINE_CSV)
    comps = pd.read_csv(COMPONENTS_CSV)
    plines = pd.read_csv(PIPES_CSV)
    with open(COMPONENT_MAP_JSON, "r") as f:
        portmap = json.load(f)
    return eq, pipes, comps, plines, portmap

eq_layout, pipe_layout, components_df, pipes_df, port_mapping = load_all_data()

# --- Phase 1: Process Flow Inputs ---
st.title("EPS Interactive PFD → P&ID Generator")

with st.expander("🔍 Step 1: Enter Process Requirements"):
    industry = st.selectbox("Industry", ["Pharmaceutical", "Chemical", "Food & Beverage", "Wastewater"])
    flow_rate = st.number_input("Flow Rate (m³/h)", min_value=1)
    pressure = st.number_input("Vacuum Level (mbar)", min_value=0.01)
    application = st.text_input("Application", placeholder="e.g. solvent recovery, drying")
    compliance = st.multiselect("Compliance", ["cGMP", "FDA", "HACCP", "ISO 9001"])
    automation = st.selectbox("Automation Level", ["None", "Basic Panel", "PLC", "SCADA"])
    vapor_type = st.selectbox("Vapor Type", ["Clean", "Condensable", "Corrosive"])
    contamination_sensitive = st.checkbox("Contamination-Sensitive (Pharma/Food)?", value=True)

    if st.button("🎯 Recommend EPS Systems"):
        recommended = map_process_to_eps_products(industry, flow_rate, pressure, application, compliance)
        primary = next((r for r in recommended if "Pump" in r and "Booster" not in r), None)
        booster_cfg, booster_warnings = evaluate_booster_requirements(
            flow_rate, pressure, vapor_type.lower(), contamination_sensitive, primary, automation
        )

        st.session_state["components"] = recommended.copy()
        if booster_cfg["enabled"]:
            st.session_state["components"].append("Mechanical Vacuum Booster")
            st.session_state["booster_cfg"] = booster_cfg

        st.success("🧠 EPS Recommendation Complete")
        for comp in st.session_state["components"]:
            st.markdown(f"- ✅ **{comp}**")
        for warn in booster_warnings:
            st.warning(warn)

# --- Phase 2: Full P&ID UI ---
st.markdown("---")
st.header("🛠️ Step 2: Customize Components & Layout")

if "components" not in st.session_state:
    st.info("Please run Step 1 first.")
else:
    # Editable tag table
    st.subheader("📋 Component List")
    tag_df = pd.DataFrame({
        "Component": st.session_state["components"],
        "Tag": [f"C-{i+1:03d}" for i in range(len(st.session_state["components"]))]
    })

    edited_df = st.data_editor(tag_df, num_rows="dynamic", use_container_width=True)
    selected_tags = edited_df.to_dict("records")

    # Symbol preview
    st.subheader("🖼️ Symbol Preview")
    scroll_cols = st.columns(4)
    for idx, row in enumerate(selected_tags):
        symbol_file = os.path.join(SYMBOLS_FOLDER, f"{row['Component'].lower().replace(' ', '_')}.svg")
        with scroll_cols[idx % 4]:
            st.markdown(f"**{row['Tag']}**")
            if os.path.exists(symbol_file):
                st.image(symbol_file, use_column_width=True)
            else:
                st.error("❌ Symbol not found")

    # Layout controls
    st.subheader("🧩 Layout Controls")
    col1, col2, col3 = st.columns(3)
    grid_rows = col1.slider("Grid Rows", 1, 10, 5)
    grid_cols = col2.slider("Grid Columns", 1, 10, 5)
    spacing = col3.slider("Spacing", 20, 300, 120)
    scale = st.slider("Symbol Scale", 0.2, 2.0, 1.0)

    # Generate button
    if st.button("🧪 Generate Final P&ID"):
        comp_ids = [row["Component"].lower().replace(" ", "_") for row in selected_tags]

        pid_svg = render_final_pid(
            component_list=comp_ids,
            equipment_layout_df=eq_layout,
            pipe_layout_df=pipe_layout,
            port_mapping=port_mapping,
            booster_config=st.session_state.get("booster_cfg", {})
        )

        pid_svg = add_control_logic_block(pid_svg, st.session_state.get("booster_cfg", {}))

        st.subheader("📌 Final P&ID Diagram")
        st.image(pid_svg, use_column_width=True)

        # Exports
        st.download_button("📥 Download PNG", pid_svg.encode(), file_name="pid_output.png")
        st.download_button("📐 Download DXF", pid_svg.encode(), file_name="pid_output.dxf")
