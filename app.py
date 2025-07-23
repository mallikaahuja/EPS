# EPS Interactive P&ID Generator - Full Streamlit App

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import platform
from datetime import datetime
from drawing_engine import render_svg, svg_to_png, export_dxf
from symbols import SymbolRenderer
from layout_engine import compute_positions_and_routing
from dsl_generator import DSLGenerator
from dexpi_converter import DEXPIConverter
from hitl_validation import create_hitl_ui
from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
from control_systems import ControlSystemAnalyzer, PnIDValidator

# Optional Visio import
if platform.system() == "Windows":
    try:
        from visio_generator import VisioP_IDGenerator
        VISIO_AVAILABLE = True
    except ImportError:
        VISIO_AVAILABLE = False
else:
    VISIO_AVAILABLE = False

# ─────────────────────────────────────
# PAGE CONFIG & STYLING
# ─────────────────────────────────────
st.set_page_config(
    page_title="EPS P&ID Generator with AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    .main > div { padding-top: 0rem; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .svg-container {
        border: 2px solid #ccc; border-radius: 8px; background: white;
        padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .validation-success { background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }
    .validation-warning { background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
    .validation-error { background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
    .ai-suggestion { background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# INIT AI + RENDERER
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
# SIDEBAR CONFIGURATION
# ─────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Diagram Configuration")
    show_grid = st.checkbox("Show Grid", True)
    show_legend = st.checkbox("Show Legend", True)
    show_control_loops = st.checkbox("Show Control Loops", True)
    show_validation = st.checkbox("Show HITL Validation", True)
    zoom = st.slider("Zoom Level", 0.5, 3.0, 1.0, 0.1)
    export_format = st.selectbox("Export Format", ["PNG", "SVG", "DXF", "DEXPI", "PDF"])
    process_type = st.selectbox("Process Type", ["vacuum_system", "distillation", "reaction", "utilities"])
    enable_ai = st.checkbox("Enable AI Suggestions", True)

# ─────────────────────────────────────
# TABS
# ─────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📐 Diagram",
    "📦 Equipment",
    "📋 Validation",
    "🧠 AI Suggestions",
    "🔁 HITL",
    "📤 Export"
])

# ─────────────────────────────────────
# DSL + DEXPI + SCHEMDRAW DIAGRAM
# ─────────────────────────────────────
with tab1:
    st.subheader("📐 Generated P&ID Diagram")

    with st.spinner("Generating DSL → Layout → SVG..."):
        dsl = DSLGenerator()
        dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))
        for _, row in equipment_df.iterrows(): dsl.add_component(row.to_dict())
        for _, row in inline_df.iterrows(): dsl.add_component(row.to_dict())
        for _, row in pipeline_df.iterrows(): dsl.add_connection(row.to_dict())
        dsl.detect_control_loops()

        positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)
        svg, tag_map = render_svg(dsl.to_dsl("json"), symbol_renderer, positions, show_grid, show_legend, zoom)

        st.components.v1.html(f"""
        <div class='svg-container'>
            <div style="transform: scale({zoom}); transform-origin: top left;">
                {svg}
            </div>
        </div>
        """, height=700, scrolling=True)

# ─────────────────────────────────────
# EQUIPMENT TABLE
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
# VALIDATION
# ─────────────────────────────────────
with tab3:
    st.subheader("📋 P&ID Validation")
    validator = PnIDValidator()
    issues = validator.validate(dsl.to_dsl("json"))
    if not issues:
        st.success("✅ No major validation errors.")
    else:
        for issue in issues:
            st.warning(f"⚠️ {issue}")

# ─────────────────────────────────────
# AI SUGGESTIONS
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
# HITL VALIDATION
# ─────────────────────────────────────
with tab5:
    st.subheader("🔁 Human-in-the-Loop (HITL) Validation")
    create_hitl_ui()

# ─────────────────────────────────────
# EXPORT
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
