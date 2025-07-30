# EPS Interactive P&ID Generator - Streamlit App with Enhanced Debugging

import streamlit as st
import pandas as pd
import json
import platform
from datetime import datetime

from drawing_engine import render_svg, svg_to_png, export_dxf
from symbols import SymbolRenderer
from layout_engine import compute_positions_and_routing
from dsl_generator import DSLGenerator
from dexpi_converter import DEXPIConverter
from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
from control_systems import PnIDValidator
from hitl_validation import HITLValidator

# Optional Visio support
VISIO_AVAILABLE = False
if platform.system() == "Windows":
    try:
        from visio_generator import VisioP_IDGenerator
        VISIO_AVAILABLE = True
    except ImportError:
        pass

# Config
st.set_page_config(page_title="EPS P&ID Generator", layout="wide")
st.markdown("""
<style>
    .svg-container { border: 2px solid #ccc; border-radius: 8px; background: white; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .ai-suggestion { background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; border-radius: 5px; }
    .debug-info { font-family: monospace; background: #f9f9f9; padding: 10px; border: 1px dashed #ccc; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Init
@st.cache_resource
def init_ai():
    return PnIDAIAssistant()
ai_assistant = init_ai()
smart_suggestions = SmartPnIDSuggestions(ai_assistant)
symbol_renderer = SymbolRenderer()
dsl = DSLGenerator()
svg = ""

# Load CSVs
def load_data():
    try:
        equipment_df = pd.read_csv("equipment_list.csv")
        pipeline_df = pd.read_csv("pipeline_list.csv")
        inline_df = pd.read_csv("inline_component_list.csv")
        return equipment_df, pipeline_df, inline_df
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.stop()

equipment_df, pipeline_df, inline_df = load_data()

# Layout fallback
def fallback_layout(df):
    layout = []
    x, y = 50, 50
    for _, row in df.iterrows():
        layout.append({'ID': row['ID'], 'X': x, 'Y': y, 'Width': 100, 'Height': 60})
        x += 150
        if x > 800: x, y = 50, y + 100
    return pd.DataFrame(layout)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    show_grid = st.checkbox("Show Grid", True)
    show_legend = st.checkbox("Show Legend", True)
    zoom = st.slider("Zoom", 0.5, 3.0, 1.0, 0.1)
    export_format = st.selectbox("Export Format", ["PNG", "SVG", "DXF", "DEXPI"])
    enable_ai = st.checkbox("Enable AI Suggestions", True)
    process_type = st.selectbox("Process Type", ["vacuum_system", "reaction", "distillation"])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📐 Diagram", "📦 Equipment", "📋 Validation", "🧠 AI", "🔁 HITL", "📤 Export", "🧰 Debug"
])

# ───────────────────────────────
# 📐 TAB 1: Diagram
# ───────────────────────────────
with tab1:
    st.subheader("📐 Generated P&ID Diagram")

    dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))
    try:
        layout_df = pd.read_csv("enhanced_equipment_layout.csv")
    except:
        layout_df = fallback_layout(equipment_df)

    for _, row in equipment_df.iterrows():
        try:
            dsl.add_component_from_row(row, layout_df)
        except Exception as e:
            st.warning(f"⚠️ Failed to add {row['ID']}: {e}")

    for _, row in inline_df.iterrows():
        try:
            dsl.add_component_from_row(row, layout_df)
        except:
            pass

    for _, row in pipeline_df.iterrows():
        try:
            dsl.add_connection_from_row(row)
        except:
            pass

    if len(dsl.components) == 0:
        st.error("❌ No components found. Check layout or CSV input.")
        st.stop()

    dsl.detect_control_loops()
    dsl_json = json.loads(dsl.to_dsl("json"))
    positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)

    if not dsl_json.get("components"):
        st.error("❌ DSL JSON is empty")
        st.stop()

    try:
        svg, tag_map = render_svg(dsl_json, symbol_renderer, positions, show_grid, show_legend, zoom)
        if not svg:
            st.error("❌ SVG is blank. Render failed.")
        else:
            png = svg_to_png(svg)
            st.image(png, use_column_width=True)
    except Exception as e:
        st.error(f"❌ Diagram render failed: {e}")

# 📦 TAB 2: Equipment Data
with tab2:
    st.dataframe(equipment_df)
    st.dataframe(pipeline_df)
    st.dataframe(inline_df)

# 📋 TAB 3: Validation
with tab3:
    validator = PnIDValidator(dsl.components, dsl.connections)
    issues = validator.run_validation(dsl.to_dsl("json"))
    if not issues:
        st.success("✅ No issues found.")
    else:
        for i in issues:
            st.warning(i)

# 🧠 TAB 4: AI Suggestions
with tab4:
    if enable_ai:
        recs = smart_suggestions.generate_suggestions(dsl.to_dsl("json"), process_type)
        for r in recs:
            st.markdown(f"<div class='ai-suggestion'>{r}</div>", unsafe_allow_html=True)
    else:
        st.info("AI suggestions disabled.")

# 🔁 TAB 5: HITL
with tab5:
    validator = HITLValidator()
    session = validator.create_session("EPS", dsl_json)
    st.write(f"Session ID: {session.session_id}")
    st.progress(session.completion_percentage / 100)
    if session.validation_items:
        st.dataframe(pd.DataFrame([vars(i) for i in session.validation_items]))
    st.download_button("⬇️ Download Report", data=json.dumps(validator.export_validation_report(), indent=2), file_name="validation.json")

# 📤 TAB 6: Export
with tab6:
    if svg:
        if export_format == "PNG":
            st.download_button("Download PNG", svg_to_png(svg), file_name="diagram.png")
        elif export_format == "SVG":
            st.download_button("Download SVG", svg, file_name="diagram.svg")
        elif export_format == "DXF":
            dxf = export_dxf(dsl.to_dsl("json"))
            st.download_button("Download DXF", dxf, file_name="diagram.dxf")
        elif export_format == "DEXPI":
            dexpi = DEXPIConverter().convert(dsl_json)
            st.download_button("Download DEXPI", dexpi, file_name="diagram.dexpi")

# 🧰 TAB 7: Debug Info
with tab7:
    st.subheader("🧰 Debug")
    st.write("DSL JSON")
    st.json(dsl_json)
    st.write("Positions")
    st.json(positions)
    st.write("SVG (First 500 chars)")
    st.code(svg[:500])
