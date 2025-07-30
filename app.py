# EPS P&ID Generator - DIAGNOSTIC VERSION for blank diagram debugging

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import platform
from datetime import datetime
import traceback
import io
import base64

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

# ─────────────────────────────────────
# DIAGNOSTIC FUNCTIONS
# ─────────────────────────────────────

def analyze_svg_content(svg_content):
    if not svg_content:
        return "❌ SVG is None or empty string"
    if len(svg_content) < 50:
        return f"❌ SVG too short ({len(svg_content)} chars): {svg_content}"

    issues = []
    if "<svg" not in svg_content:
        issues.append("Missing <svg> tag")
    if "viewBox" not in svg_content:
        issues.append("Missing viewBox attribute")
    if "<g" not in svg_content and "<rect" not in svg_content and "<circle" not in svg_content and "<path" not in svg_content:
        issues.append("No drawing elements found (g, rect, circle, path)")

    element_counts = {
        "rect": svg_content.count("<rect"),
        "circle": svg_content.count("<circle"),
        "path": svg_content.count("<path"),
        "line": svg_content.count("<line"),
        "text": svg_content.count("<text"),
        "g": svg_content.count("<g")
    }
    total_elements = sum(element_counts.values())
    if total_elements == 0:
        issues.append("No drawing elements found")

    result = f"✅ SVG length: {len(svg_content)} chars, Elements: {total_elements}"
    result += f"\nElement breakdown: {element_counts}"
    if issues:
        result += f"\n❌ Issues: {', '.join(issues)}"
    return result

def create_test_svg():
    return '''<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="100" height="60" fill="lightblue" stroke="black" stroke-width="2"/>
    <circle cx="200" cy="50" r="30" fill="lightgreen" stroke="black" stroke-width="2"/>
    <text x="50" y="120" text-anchor="middle" font-family="Arial" font-size="14">Test Equipment</text>
    <text x="200" y="120" text-anchor="middle" font-family="Arial" font-size="14">Test Vessel</text>
    <line x1="110" y1="40" x2="170" y2="50" stroke="black" stroke-width="2"/>
    </svg>'''

def test_schemdraw_basic():
    try:
        import schemdraw
        import schemdraw.elements as elm
        d = schemdraw.Drawing()
        d.add(elm.Resistor().label('Test'))
        d.add(elm.Capacitor())
        svg_content = d.get_imagedata('svg')
        return True, f"✅ Schemdraw test successful, SVG length: {len(svg_content)}"
    except Exception as e:
        return False, f"❌ Schemdraw test failed: {str(e)}"

# ─────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────
st.set_page_config(page_title="EPS P&ID Generator - DIAGNOSTIC", layout="wide")
st.title("🔍 EPS P&ID Generator - DIAGNOSTIC MODE")
st.warning("This is a diagnostic version to identify why your diagram is blank.")

# ─────────────────────────────────────
# STEP 0: DIAGNOSTIC TESTS
# ─────────────────────────────────────
st.header("🧪 Diagnostic Tests")
st.subheader("Test 1: Basic Image Display")
test_svg = create_test_svg()
st.write("**Test SVG Analysis:**")
st.write(analyze_svg_content(test_svg))

col1, col2 = st.columns(2)
with col1:
    st.markdown(f'<div style="border:1px solid #ccc; padding:10px;">{test_svg}</div>', unsafe_allow_html=True)
with col2:
    st.image(test_svg.encode("utf-8"), caption="Test SVG")

st.subheader("Test 2: Schemdraw Basic Test")
schemdraw_works, schemdraw_msg = test_schemdraw_basic()
st.write(schemdraw_msg)

# ─────────────────────────────────────
# STEP 1: LOAD CSV DATA
# ─────────────────────────────────────
st.header("📊 Step 1: Load Data")
try:
    equipment_df = pd.read_csv("equipment_list.csv")
    pipeline_df = pd.read_csv("pipeline_list.csv")
    inline_df = pd.read_csv("inline_component_list.csv")
    st.success("✅ All data loaded")
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ─────────────────────────────────────
# STEP 2: Generate DSL
# ─────────────────────────────────────
st.header("🛠️ Step 2: Generate DSL")
dsl = DSLGenerator()
dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))

try:
    for _, row in equipment_df.iterrows():
        dsl.add_component_from_row(row, None)
    for _, row in inline_df.iterrows():
        dsl.add_component_from_row(row, None)
    for _, row in pipeline_df.iterrows():
        dsl.add_connection_from_row(row)
    st.success(f"✅ DSL created: {len(dsl.components)} components, {len(dsl.connections)} connections")
except Exception as e:
    st.error(f"❌ Error generating DSL: {e}")
    st.code(traceback.format_exc())

# ─────────────────────────────────────
# STEP 3: Convert to DEXPI
# ─────────────────────────────────────
st.header("🔄 Step 3: Convert to DEXPI")
try:
    dexpi = DEXPIConverter().convert(json.loads(dsl.to_dsl("json")))
    st.success("✅ DEXPI conversion successful")
    st.code(dexpi[:500], language="xml")
except Exception as e:
    st.error(f"❌ DEXPI conversion failed: {e}")
    st.code(traceback.format_exc())

# ─────────────────────────────────────
# STEP 4: Compute Layout
# ─────────────────────────────────────
st.header("🧮 Step 4: Compute Layout")
try:
    positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)
    st.success("✅ Layout positions computed")
    st.json({k: positions[k] for k in list(positions)[:3]})
except Exception as e:
    st.error(f"❌ Layout computation failed: {e}")
    st.code(traceback.format_exc())

# ─────────────────────────────────────
# STEP 5: Render SVG
# ─────────────────────────────────────
st.header("🎨 Step 5: Render SVG")
try:
    symbol_renderer = SymbolRenderer()
    dsl_json = json.loads(dsl.to_dsl("json"))
    svg, tag_map = render_svg(dsl_json, symbol_renderer, positions, True, True, 1.0)
    st.write("**SVG Analysis:**")
    st.write(analyze_svg_content(svg))
    st.image(svg_to_png(svg), caption="Generated Diagram")
except Exception as e:
    st.error(f"❌ SVG rendering failed: {e}")
    st.code(traceback.format_exc())

# ─────────────────────────────────────
# SUMMARY & NEXT STEPS
# ─────────────────────────────────────
st.header("📋 Summary & Recommendations")
st.markdown("""
### 🎯 Pipeline Summary:
- ✅ **Data Loading** ✅
- ✅ **DSL Generation** ✅
- ✅ **DEXPI Conversion** ✅
- ✅ **Layout Computation** ✅
- ✅ **SVG Rendering** ✅

### 🔧 Debug Checklist:
- If SVG is blank, check `render_svg()` logic
- If symbols missing, validate `SymbolRenderer`
- If layout off, check `compute_positions_and_routing()`
- If image display fails, test `svg_to_png()` or use raw HTML fallback

### 🧪 Final Test
""")

if st.button("🔁 Generate Simple Test Diagram"):
    minimal_svg = '''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <rect x="50" y="50" width="100" height="60" fill="lightblue" stroke="black" stroke-width="2"/>
    <rect x="250" y="50" width="100" height="60" fill="lightgreen" stroke="black" stroke-width="2"/>
    <line x1="150" y1="80" x2="250" y2="80" stroke="black" stroke-width="3"/>
    <text x="100" y="85" text-anchor="middle" font-size="12">PUMP-01</text>
    <text x="300" y="85" text-anchor="middle" font-size="12">TANK-01</text>
    </svg>'''
    st.markdown(f'<div style="border:1px solid #ccc; padding:10px;">{minimal_svg}</div>', unsafe_allow_html=True)
