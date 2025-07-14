# app.py

import streamlit as st
import pandas as pd
import json
import os

from process_mapper import map_process_to_eps_products
from booster_logic import evaluate_booster_requirements
from advanced_rendering import ProfessionalRenderer
from control_systems import add_control_logic_block

# --- File Paths ---
EQUIPMENT_CSV = "enhanced_equipment_layout.csv"
PIPELINE_CSV = "pipe_connections_layout.csv"
COMPONENTS_CSV = "components.csv"
PIPES_CSV = "pipes.csv"
COMPONENT_MAP_JSON = "component_mapping.json"
SYMBOLS_FOLDER = "symbols"

# --- Load All Layout and Metadata Files ---
@st.cache_data
def load_data():
    eq_layout = pd.read_csv(EQUIPMENT_CSV)
    pipe_layout = pd.read_csv(PIPELINE_CSV)
    components_df = pd.read_csv(COMPONENTS_CSV)
    pipes_df = pd.read_csv(PIPES_CSV)
    with open(COMPONENT_MAP_JSON, "r") as f:
        port_mapping = json.load(f)
    return eq_layout, pipe_layout, components_df, pipes_df, port_mapping

eq_layout, pipe_layout, components_df, pipes_df, port_mapping = load_data()

# --- Page Title ---
st.set_page_config(layout="wide")
st.title("EPS Interactive PFD → P&ID Generator")

# --- PHASE 1: Process Input and Recommendation ---
with st.expander("📋 Step 1: Enter Process Details"):
    industry = st.selectbox("Industry", ["Pharmaceutical", "Chemical", "Food & Beverage", "Wastewater"])
    flow_rate = st.number_input("Flow Rate (m³/h)", min_value=1)
    pressure = st.number_input("Vacuum Level (mbar)", min_value=0.01)
    application = st.text_input("Application", placeholder="e.g. drying, filtration, solvent recovery")
    compliance = st.multiselect("Compliance", ["cGMP", "FDA", "HACCP", "ISO 9001"])
    automation = st.selectbox("Automation Level", ["None", "Basic Panel", "PLC", "SCADA"])
    vapor_type = st.selectbox("Vapor Type", ["Clean", "Condensable", "Corrosive"])
    contamination_sensitive = st.checkbox("Contamination-Sensitive?", value=True)

    if st.button("🎯 Recommend EPS System"):
        product_list = map_process_to_eps_products(industry, flow_rate, pressure, application, compliance)
        primary_pump = next((p for p in product_list if "Pump" in p and "Booster" not in p), None)

        booster_cfg, booster_warnings = evaluate_booster_requirements(
            flow_rate=flow_rate,
            pressure=pressure,
            process_vapor_type=vapor_type.lower(),
            contamination_sensitive=contamination_sensitive,
            primary_pump_type=primary_pump,
            automation_level=automation
        )

        st.session_state["components"] = product_list.copy()
        if booster_cfg["enabled"]:
            st.session_state["components"].append("Mechanical Vacuum Booster")
            st.session_state["booster_cfg"] = booster_cfg
            st.success("✅ Booster added based on process needs.")

        st.success("🧠 EPS Product Mapping Complete")
        for comp in st.session_state["components"]:
            st.markdown(f"- **{comp}**")
        for warn in booster_warnings:
            st.warning(warn)

# --- PHASE 2: P&ID GENERATION UI ---
st.markdown("---")
st.header("🛠️ Step 2: Customize and Render Final P&ID")

if "components" not in st.session_state:
    st.info("Please run Step 1 to proceed.")
else:
    # Editable Component Tag Table
    st.subheader("🔖 Component Tagging")
    tag_df = pd.DataFrame({
        "Component": st.session_state["components"],
        "Tag": [f"C-{i+1:03d}" for i in range(len(st.session_state["components"]))]
    })
    edited_df = st.data_editor(tag_df, num_rows="dynamic", use_container_width=True)
    selected_tags = edited_df.to_dict("records")

    # Symbol Previews
    st.subheader("🖼️ Symbol Preview")
    cols = st.columns(5)
    for idx, row in enumerate(selected_tags):
        sym_file = os.path.join(SYMBOLS_FOLDER, f"{row['Component'].lower().replace(' ', '_')}.svg")
        with cols[idx % 5]:
            st.markdown(f"**{row['Tag']}**")
            if os.path.exists(sym_file):
                st.image(sym_file, use_column_width=True)
            else:
                st.error("❌ Symbol not found")

    # Layout Controls
    st.subheader("📐 Layout & Grid Settings")
    col1, col2, col3, col4 = st.columns(4)
    grid_rows = col1.slider("Grid Rows", 1, 12, 6)
    grid_cols = col2.slider("Grid Columns", 1, 12, 6)
    spacing = col3.slider("Spacing", 80, 300, 150)
    scale = col4.slider("Symbol Scale", 0.2, 2.0, 1.0)

    # Final Button to Render
    if st.button("🚀 Generate Final P&ID"):
        st.success("Rendering P&ID...")

        # Build component list
        component_ids = [row["Component"].lower().replace(" ", "_") for row in selected_tags]

        # --- Use ProfessionalRenderer ---
        renderer = ProfessionalRenderer()
        pid_svg = renderer.render_professional_pnid(
            components=component_ids,
            pipes=pipe_layout.to_dict("records"),
            width=grid_cols * spacing,
            height=grid_rows * spacing
        )

        # Add control logic and ISA panel
        booster_flags = st.session_state.get("booster_cfg", {})
        pid_svg = add_control_logic_block(pid_svg, booster_flags)

        # Output
        st.subheader("🧾 Final P&ID Output")
        st.image(pid_svg, use_column_width=True)
        st.download_button("📥 Download PNG", pid_svg.encode(), file_name="pid_output.png")
        st.download_button("📐 Download DXF", pid_svg.encode(), file_name="pid_output.dxf")
