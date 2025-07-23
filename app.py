# EPS Interactive P&ID Generator - Full Streamlit App with Dropdowns & Control Loop Fix

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import platform
from datetime import datetime

# ─────────────────────────────────────
# MODULE IMPORTS
# ─────────────────────────────────────
from drawing_engine import render_svg, svg_to_png, export_dxf
from symbols import SymbolRenderer
from layout_engine import compute_positions_and_routing
from dsl_generator import DSLGenerator
from dexpi_converter import DEXPIConverter
from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
from control_systems import ControlSystemAnalyzer, PnIDValidator
from hitl_validation import HITLValidator

# Optional Visio (Windows only)
if platform.system() == "Windows":
    try:
        from visio_generator import VisioP_IDGenerator
        VISIO_AVAILABLE = True
    except ImportError:
        VISIO_AVAILABLE = False
else:
    VISIO_AVAILABLE = False

# ─────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────
st.set_page_config(page_title="EPS P&ID Generator", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .svg-container { border: 2px solid #ccc; border-radius: 8px; background: white; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .ai-suggestion { background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# INIT
# ─────────────────────────────────────
@st.cache_resource
def init_ai():
    return PnIDAIAssistant()

ai_assistant = init_ai()
smart_suggestions = SmartPnIDSuggestions(ai_assistant)
symbol_renderer = SymbolRenderer()

# ─────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────
try:
    equipment_df = pd.read_csv("equipment_list.csv")
    pipeline_df = pd.read_csv("pipeline_list.csv")
    inline_df = pd.read_csv("inline_component_list.csv")
    st.success(f"✅ Loaded {len(equipment_df)} equipment, {len(pipeline_df)} pipelines, {len(inline_df)} inline components")
except Exception as e:
    st.error(f"❌ Failed to load CSV files: {e}")
    st.stop()

# ─────────────────────────────────────
# SIDEBAR CONFIG
# ─────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Diagram Configuration")
    show_grid = st.checkbox("Show Grid", True)
    show_legend = st.checkbox("Show Legend", True)
    show_control_loops = st.checkbox("Show Control Loops", True)
    show_validation = st.checkbox("Show HITL Validation", True)
    zoom = st.slider("Zoom", 0.5, 3.0, 1.0, 0.1)
    export_format = st.selectbox("Export Format", ["PNG", "SVG", "DXF", "DEXPI", "PDF"])
    process_type = st.selectbox("Process Type", ["vacuum_system", "distillation", "reaction", "utilities"])
    enable_ai = st.checkbox("Enable AI Suggestions", True)

    st.markdown("### Optional Components")
    include_condenser = st.checkbox("Vapour Condenser + Catch Pot", True)
    include_acg = st.checkbox("ACG Filter", True)
    include_silencer = st.checkbox("Discharge Silencer + Catch Pot", True)

# ─────────────────────────────────────
# TABS
# ─────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📐 Diagram", "📦 Equipment", "📋 Validation", "🧠 AI Suggestions", "🔁 HITL", "📤 Export"])

# ─────────────────────────────────────
# TAB 1: DIAGRAM
# ─────────────────────────────────────
with tab1:
    st.subheader("📐 Generated P&ID Diagram")

    with st.spinner("Generating DSL → Layout → SVG..."):
        dsl = DSLGenerator()
        dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))

        try:
            layout_df = pd.read_csv("enhanced_equipment_layout.csv")
        except FileNotFoundError:
            layout_df = None

        optional_ids = []
        if not include_condenser:
            optional_ids += ["vapour_condenser", "catch_pot_1"]
        if not include_acg:
            optional_ids.append("acg_filter")
        if not include_silencer:
            optional_ids += ["discharge_silencer", "catch_pot_2"]

        for _, row in equipment_df.iterrows():
            if row["ID"] not in optional_ids:
                dsl.add_component_from_row(row, layout_df)

        for _, row in inline_df.iterrows():
            if row["ID"] not in optional_ids:
                dsl.add_component_from_row(row, layout_df)

        for _, row in pipeline_df.iterrows():
            dsl.add_connection_from_row(row)

        dsl.detect_control_loops()

        positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)
        import json
        dsl_json = json.loads(dsl.to_dsl("json"))
        svg, tag_map = render_svg(dsl_json, symbol_renderer, positions, show_grid, show_legend, zoom)
        try:
        png = svg_to_png(svg)
        st.image(png, caption="Generated P&ID Diagram", use_column_width=True)
        except Exception as e:
        st.error(f"Could not render diagram as PNG: {e}")
# ─────────────────────────────────────
# TAB 2: EQUIPMENT
# ─────────────────────────────────────
with tab2:
    st.subheader("📦 Equipment, Pipelines & Inline")
    st.write("### Equipment")
    st.dataframe(equipment_df)
    st.write("### Pipelines")
    st.dataframe(pipeline_df)
    st.write("### Inline Components")
    st.dataframe(inline_df)

# ─────────────────────────────────────
# TAB 3: VALIDATION
# ─────────────────────────────────────
with tab3:
    st.subheader("📋 P&ID Validation")
    validator = PnIDValidator(dsl.components, dsl.connections)
    issues = validator.validate(dsl.to_dsl("json"))
    if not issues:
        st.success("✅ No major validation errors.")
    else:
        for issue in issues:
            st.warning(f"⚠️ {issue}")

# ─────────────────────────────────────
# TAB 4: AI SUGGESTIONS
# ─────────────────────────────────────
with tab4:
    st.subheader("🧠 AI-Powered Suggestions")
    if enable_ai:
        recs = smart_suggestions.generate_suggestions(dsl.to_dsl("json"), process_type)
        for r in recs:
            st.markdown(f"<div class='ai-suggestion'>{r}</div>", unsafe_allow_html=True)
    else:
        st.info("AI suggestions are disabled")

# ─────────────────────────────────────
# TAB 5: HITL VALIDATION
# ─────────────────────────────────────
with tab5:
    st.subheader("🔁 Human-in-the-Loop (HITL) Validation")
    try:
        dsl_data = json.loads(dsl.to_dsl("json"))
        validator = HITLValidator()
        session = validator.create_session(project_id="EPS", dsl_data=dsl_data)
        st.write(f"Session ID: {session.session_id}")
        st.progress(session.completion_percentage / 100)
        if session.validation_items:
            st.dataframe(pd.DataFrame([vars(i) for i in session.validation_items]))
        else:
            st.success("No validation issues detected.")
        st.download_button("⬇️ Download Validation Report", data=json.dumps(validator.export_validation_report(), indent=2), file_name="validation_report.json")
    except Exception as e:
        st.error(f"❌ HITL validation failed: {e}")

# ─────────────────────────────────────
# TAB 6: EXPORT
# ─────────────────────────────────────
with tab6:
    st.subheader("📤 Export Diagram")
    if export_format == "SVG":
        st.download_button("⬇️ Download SVG", svg, file_name="pid.svg", mime="image/svg+xml")
    elif export_format == "PNG":
        png = svg_to_png(svg)
        st.download_button("⬇️ Download PNG", png, file_name="pid.png", mime="image/png")
    elif export_format == "DXF":
        dxf = export_dxf(dsl.to_dsl("json"))
        st.download_button("⬇️ Download DXF", dxf, file_name="pid.dxf", mime="application/dxf")
    elif export_format == "DEXPI":
        dexpi = DEXPIConverter().convert(json.loads(dsl.to_dsl("json")))
        st.download_button("⬇️ Download DEXPI", dexpi, file_name="pid.dexpi", mime="application/xml")
    elif export_format == "PDF":
        st.warning("PDF export coming soon.")

st.markdown("---")
st.caption("EPS P&ID Generator – powered by Schemdraw, DEXPI, Visio, and AI | v2.0")
