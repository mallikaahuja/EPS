# EPS Interactive P&ID Generator - v2.2 Final Version with Debug Tab, Fallback Layout, JSON Fixes

import streamlit as st
import pandas as pd
import json
import platform
from datetime import datetime
import traceback

from drawing_engine import render_svg, svg_to_png, export_dxf
from symbols import SymbolRenderer
from layout_engine import compute_positions_and_routing
from dsl_generator import DSLGenerator
from dexpi_converter import DEXPIConverter
from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
from control_systems import ControlSystemAnalyzer, PnIDValidator
from hitl_validation import HITLValidator

if platform.system() == "Windows":
    try:
        from visio_generator import VisioP_IDGenerator
        VISIO_AVAILABLE = True
    except ImportError:
        VISIO_AVAILABLE = False
else:
    VISIO_AVAILABLE = False

st.set_page_config(page_title="EPS P&ID Generator", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .svg-container { border: 2px solid #ccc; border-radius: 8px; background: white; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .ai-suggestion { background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; border-radius: 5px; }
    .debug-info { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_ai():
    return PnIDAIAssistant()

ai_assistant = init_ai()
smart_suggestions = SmartPnIDSuggestions(ai_assistant)
symbol_renderer = SymbolRenderer()
svg = ""

def debug_log(message, data=None):
    st.write(f"🔍 **DEBUG**: {message}")
    if data is not None:
        if isinstance(data, (dict, list)):
            st.json(data)
        else:
            st.code(str(data))

def validate_csv_data(df, name):
    issues = []
    if df.empty:
        issues.append(f"{name} is empty")
    required_columns = {
        'equipment': ['ID', 'Type', 'Description'],
        'pipeline': ['ID', 'From', 'To'],
        'inline': ['ID', 'Type']
    }
    if name.lower() in required_columns:
        missing_cols = [col for col in required_columns[name.lower()] if col not in df.columns]
        if missing_cols:
            issues.append(f"{name} missing columns: {missing_cols}")
    return issues

def create_fallback_layout(equipment_df, inline_df):
    layout_data = []
    x_pos, y_pos = 50, 50
    for _, row in equipment_df.iterrows():
        layout_data.append({'ID': row['ID'], 'X': x_pos, 'Y': y_pos, 'Width': 100, 'Height': 60})
        x_pos += 150
        if x_pos > 600:
            x_pos = 50
            y_pos += 100
    for _, row in inline_df.iterrows():
        layout_data.append({'ID': row['ID'], 'X': x_pos, 'Y': y_pos, 'Width': 40, 'Height': 40})
        x_pos += 80
        if x_pos > 600:
            x_pos = 50
            y_pos += 100
    return pd.DataFrame(layout_data)

with st.sidebar:
    st.header("⚙️ Settings")
    show_grid = st.checkbox("Show Grid", True)
    show_legend = st.checkbox("Show Legend", True)
    zoom = st.slider("Zoom", 0.5, 3.0, 1.0, 0.1)
    export_format = st.selectbox("Export Format", ["PNG", "SVG", "DXF", "DEXPI", "PDF"])
    process_type = st.selectbox("Process Type", ["vacuum_system", "distillation", "reaction", "utilities"])
    enable_ai = st.checkbox("Enable AI Suggestions", True)

st.header("EPS P&ID Generator")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📐 Diagram", "📦 Equipment", "📋 Validation", "🧠 AI Suggestions", "🔁 HITL", "📤 Export", "🧰 Debug"])

# Load data
try:
    equipment_df = pd.read_csv("equipment_list.csv")
    pipeline_df = pd.read_csv("pipeline_list.csv")
    inline_df = pd.read_csv("inline_component_list.csv")
except Exception as e:
    st.error(f"Failed to load input files: {e}")
    st.stop()

layout_df = None
try:
    layout_df = pd.read_csv("enhanced_equipment_layout.csv")
except FileNotFoundError:
    layout_df = create_fallback_layout(equipment_df, inline_df)
    st.warning("⚠️ Layout file missing. Using fallback.")

with tab1:
    st.subheader("📐 Generated P&ID Diagram")

    dsl = DSLGenerator()
    dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))

    for _, row in equipment_df.iterrows():
        try:
            dsl.add_component_from_row(row, layout_df)
        except:
            continue

    for _, row in inline_df.iterrows():
        try:
            dsl.add_component_from_row(row, layout_df)
        except:
            continue

    for _, row in pipeline_df.iterrows():
        try:
            dsl.add_connection_from_row(row)
        except:
            continue

    if len(dsl.components) == 0:
        st.error("No components detected in DSL.")
        st.stop()

    try:
        dsl.detect_control_loops()
    except Exception as e:
        st.warning(f"Control loop detection failed: {e}")

    try:
        positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)
    except:
        positions, routes, inlines = {}, {}, {}

    try:
        dsl_json_str = dsl.to_dsl("json")
        dsl_json = json.loads(dsl_json_str)
    except Exception as e:
        st.error(f"DSL to JSON failed: {e}")
        st.stop()

    try:
        svg, tag_map = render_svg(dsl_json, symbol_renderer, positions, show_grid, show_legend, zoom)
        if not svg or len(svg) < 100:
            st.error("Empty or invalid SVG returned.")
        else:
            png = svg_to_png(svg)
            st.success("✅ Diagram generated!")
            st.image(png, caption="Generated P&ID", use_column_width=True)
    except Exception as e:
        st.error(f"SVG Rendering failed: {e}")

with tab2:
    st.write("### Equipment")
    st.dataframe(equipment_df)
    st.write("### Pipelines")
    st.dataframe(pipeline_df)
    st.write("### Inline Components")
    st.dataframe(inline_df)

with tab3:
    st.subheader("📋 P&ID Validation")
    validator = PnIDValidator(dsl.components, dsl.connections)
    try:
        issues = validator.run_validation(dsl.to_dsl("json"))
        if not issues:
            st.success("✅ No major validation errors.")
        else:
            st.warning(f"{len(issues)} validation issues:")
            for issue in issues:
                st.write(f"• {issue}")
    except Exception as e:
        st.error(f"Validation failed: {e}")

with tab4:
    st.subheader("🧠 AI Suggestions")
    if enable_ai:
        try:
            recs = smart_suggestions.generate(dsl.to_dsl("json"), process_type)
            for r in recs:
                st.markdown(f"<div class='ai-suggestion'>{r}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"AI suggestion error: {e}")
    else:
        st.info("AI disabled")

with tab5:
    st.subheader("🔁 HITL Validation")
    try:
        dsl_data = json.loads(dsl.to_dsl("json"))
        validator = HITLValidator()
        session = validator.create_session(project_id="EPS", dsl_data=dsl_data)
        st.write(f"Session ID: {session.session_id}")
        st.progress(session.completion_percentage / 100)
        if session.validation_items:
            st.dataframe(pd.DataFrame([vars(i) for i in session.validation_items]))
        else:
            st.success("No validation issues.")
        st.download_button(
            "⬇️ Download Report",
            data=json.dumps(validator.export_validation_report(), indent=2, default=str),
            file_name="validation_report.json"
        )
    except Exception as e:
        st.error(f"HITL failed: {e}")

with tab6:
    st.subheader("📤 Export")
    if export_format == "SVG":
        st.download_button("⬇️ Download SVG", svg, file_name="pid.svg", mime="image/svg+xml")
    elif export_format == "PNG":
        try:
            png = svg_to_png(svg)
            st.download_button("⬇️ Download PNG", png, file_name="pid.png", mime="image/png")
        except Exception as e:
            st.error(f"PNG export failed: {e}")
    elif export_format == "DXF":
        try:
            dxf = export_dxf(dsl.to_dsl("json"))
            st.download_button("⬇️ Download DXF", dxf, file_name="pid.dxf", mime="application/dxf")
        except Exception as e:
            st.error(f"DXF export failed: {e}")
    elif export_format == "DEXPI":
        try:
            dexpi_converter = DEXPIConverter()
            dexpi_xml = dexpi_converter.convert(dsl_json)
            st.download_button("⬇️ Download DEXPI", dexpi_xml, file_name="pid.dexpi", mime="application/xml")
        except Exception as e:
            st.error(f"DEXPI export failed: {e}")
    elif export_format == "PDF":
        st.warning("PDF export coming soon.")

with tab7:
    st.subheader("🧰 Debug Info")
    st.json(dsl.to_dsl("json"))
    if layout_df is not None:
        st.dataframe(layout_df)
    if svg:
        st.code(svg[:1000], language="xml")

st.markdown("---")
st.caption("EPS Generator | DSL → DEXPI → Schemdraw | v2.2 (with fallback layout, debug tab, JSON fix)")
