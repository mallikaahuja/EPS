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

# Ensure these modules are available in your environment
try:
    from drawing_engine import render_svg, svg_to_png, export_dxf
    from symbols import SymbolRenderer
    from layout_engine import compute_positions_and_routing
    from dsl_generator import DSLGenerator
    from dexpi_converter import DEXPIConverter
    from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
    from control_systems import ControlSystemAnalyzer, PnIDValidator
    from hitl_validation import HITLValidator
except ImportError as e:
    st.error(f"Failed to import a critical module: {e}. Please ensure all required Python files (drawing_engine.py, symbols.py, etc.) are in your project directory and their dependencies are installed.")
    st.stop() # Stop execution if core modules are missing

# ─────────────────────────────────────
# DIAGNOSTIC FUNCTIONS
# ─────────────────────────────────────

def analyze_svg_content(svg_content):
    """Analyze SVG content to understand why it might be blank"""
    if not svg_content:
        return "❌ SVG is None or empty string"

    if len(svg_content) < 50:
        return f"❌ SVG too short ({len(svg_content)} chars): {svg_content}"

    # Check for basic SVG structure
    issues = []
    if "<svg" not in svg_content:
        issues.append("Missing <svg> tag")
    if "viewBox" not in svg_content:
        issues.append("Missing viewBox attribute")
    if "<g" not in svg_content and "<rect" not in svg_content and "<circle" not in svg_content and "<path" not in svg_content and "<line" not in svg_content and "<text" not in svg_content:
        issues.append("No common drawing elements found (g, rect, circle, path, line, text)")

    # Count drawing elements
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
    if element_counts:
        result += f"\nElement breakdown: {element_counts}"
    if issues:
        result += f"\n❌ Issues: {', '.join(issues)}"

    return result

def create_test_svg():
    """Create a simple test SVG to verify display functionality"""
    return '''<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
<rect x="10" y="10" width="100" height="60" fill="lightblue" stroke="black" stroke-width="2"/>
<circle cx="200" cy="50" r="30" fill="lightgreen" stroke="black" stroke-width="2"/>
<text x="50" y="120" text-anchor="middle" font-family="Arial" font-size="14">Test Equipment</text>
<text x="200" y="120" text-anchor="middle" font-family="Arial" font-size="14">Test Vessel</text>
<line x1="110" y1="40" x2="170" y2="50" stroke="black" stroke-width="2"/>
</svg>'''

def test_schemdraw_basic():
    """Test basic schemdraw functionality"""
    try:
        import schemdraw
        import schemdraw.elements as elm

        d = schemdraw.Drawing()
        d.add(elm.Resistor().label('Test'))
        d.add(elm.Capacitor())
        
        svg_content = d.get_imagedata('svg')
        return True, f"✅ Schemdraw test successful, SVG length: {len(svg_content)}"
    except ImportError:
        return False, "❌ Schemdraw not installed. Please install with `pip install schemdraw`"
    except Exception as e:
        return False, f"❌ Schemdraw test failed: {str(e)}"

def display_svg_safely(svg_content, caption="Generated Diagram"):
    """
    Attempts to display an SVG using multiple Streamlit methods, providing fallbacks.
    Returns True if any display method was successful, False otherwise.
    """
    if not svg_content:
        st.error(f"Cannot display empty SVG for: {caption}")
        return False

    display_successful = False

    # Method 1: Direct HTML embedding
    st.write(f"**Method 1: Direct HTML for {caption}**")
    try:
        st.markdown(f'<div style="border:1px solid #ccc; padding:10px; background:white; overflow:auto;">{svg_content}</div>', unsafe_allow_html=True)
        st.success("✅ Direct HTML display attempted.")
        display_successful = True
    except Exception as e:
        st.error(f"❌ Direct HTML display failed: {e}")

    # Method 2: Streamlit Image (via PNG conversion)
    st.write(f"**Method 2: Streamlit Image (via PNG conversion) for {caption}**")
    try:
        # Check if svg_to_png is available and successful
        if 'svg_to_png' in globals() and callable(svg_to_png):
            png = svg_to_png(svg_content)
            if png:
                st.image(png, caption=f"{caption} (PNG)", use_container_width=True)
                st.success("✅ PNG conversion and display successful.")
                display_successful = True
            else:
                st.warning("⚠️ svg_to_png returned empty/None PNG data. Falling back to direct SVG via st.image.")
                # Fallback to direct SVG display via st.image
                svg_bytes = svg_content.encode('utf-8')
                st.image(svg_bytes, caption=f"{caption} (Direct SVG Fallback)")
                st.success("✅ Direct SVG display via st.image attempted as fallback.")
                display_successful = True # Consider this a success for display
        else:
            st.warning("⚠️ `svg_to_png` function not available. Falling back to direct SVG via st.image.")
            svg_bytes = svg_content.encode('utf-8')
            st.image(svg_bytes, caption=f"{caption} (Direct SVG Fallback)")
            st.success("✅ Direct SVG display via st.image attempted as fallback.")
            display_successful = True

    except Exception as e:
        st.error(f"❌ Streamlit image display (PNG/Direct SVG fallback) failed: {e}")
        st.code(traceback.format_exc())

    return display_successful

# ─────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────

st.set_page_config(page_title="EPS P&ID Generator - DIAGNOSTIC", layout="wide")

st.title("🔍 EPS P&ID Generator - DIAGNOSTIC MODE")
st.warning("This is a diagnostic version to identify why your diagram is blank.")

# ─────────────────────────────────────
# DIAGNOSTIC TESTS FIRST
# ─────────────────────────────────────

st.header("🧪 Diagnostic Tests")

# Test 1: Basic Streamlit image display
st.subheader("Test 1: Basic Image Display")
test_svg = create_test_svg()
st.write("**Test SVG Analysis:**")
st.write(analyze_svg_content(test_svg))

col1, col2 = st.columns(2)
with col1:
    st.write("**Raw SVG (should show shapes):**")
    st.markdown(f'<div style="border:1px solid #ccc; padding:10px;">{test_svg}</div>', unsafe_allow_html=True)

with col2:
    st.write("**As Streamlit Image (should show shapes):**")
    # Using the new safe display function for the initial test
    display_svg_safely(test_svg, "Basic Streamlit Test SVG")

# Test 2: Schemdraw availability
st.subheader("Test 2: Schemdraw Basic Test")
schemdraw_works, schemdraw_msg = test_schemdraw_basic()
st.write(schemdraw_msg)

# ─────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────

st.header("📊 Data Loading")

data_loaded_successfully = True # Flag to track overall data loading
equipment_df = pd.DataFrame()
pipeline_df = pd.DataFrame()
inline_df = pd.DataFrame()

try:
    equipment_df = pd.read_csv("equipment_list.csv")
    st.success(f"Equipment: {len(equipment_df)} rows")
    st.write("**First few equipment rows:**")
    st.dataframe(equipment_df.head())
except FileNotFoundError:
    st.error("❌ `equipment_list.csv` not found. Please ensure it's in the same directory.")
    data_loaded_successfully = False
except Exception as e:
    st.error(f"Equipment loading failed: {e}")
    data_loaded_successfully = False

try:
    pipeline_df = pd.read_csv("pipeline_list.csv")
    st.success(f"Pipelines: {len(pipeline_df)} rows")
    st.write("**First few pipeline rows:**")
    st.dataframe(pipeline_df.head())
except FileNotFoundError:
    st.error("❌ `pipeline_list.csv` not found. Please ensure it's in the same directory.")
    data_loaded_successfully = False
except Exception as e:
    st.error(f"Pipeline loading failed: {e}")
    data_loaded_successfully = False

try:
    inline_df = pd.read_csv("inline_component_list.csv")
    st.success(f"Inline: {len(inline_df)} rows")
    st.write("**First few inline rows:**")
    st.dataframe(inline_df.head())
except FileNotFoundError:
    st.error("❌ `inline_component_list.csv` not found. Please ensure it's in the same directory.")
    data_loaded_successfully = False
except Exception as e:
    st.error(f"Inline loading failed: {e}")
    data_loaded_successfully = False

if not data_loaded_successfully:
    st.error("❌ Critical data missing. Cannot proceed with diagram generation.")
    st.stop()


# ─────────────────────────────────────
# STEP-BY-STEP DIAGRAM GENERATION (Modified in app.py)
# ─────────────────────────────────────

st.header("🔧 Step-by-Step Diagram Generation")

# Initialize components
ai_assistant = PnIDAIAssistant()
smart_suggestions = SmartPnIDSuggestions(ai_assistant)
symbol_renderer = SymbolRenderer()

dsl = None # Initialize dsl to None
dsl_json = None # Initialize dsl_json to None

# Step 1: DSL Generation (MODIFIED FOR DATACLASS DSLGENERATOR)
st.subheader("Step 1: DSL Generation")
try:
    dsl = DSLGenerator()
    dsl.set_metadata(project="EPS", drawing_number="001", revision="00", date=datetime.now().strftime("%Y-%m-%d"))

    # Use the generate_from_csvs method from the advanced DSLGenerator
    st.write("**Calling `dsl.generate_from_csvs()`...**")
    dsl.generate_from_csvs(
        equipment_df=equipment_df,
        inline_df=inline_df,
        pipeline_df=pipeline_df,
        connection_df=connection_df,
        layout_df=layout_df # Pass layout data if available
    )

    # After generation, detect control loops
    st.write("**Detecting control loops...**")
    dsl.detect_control_loops()

    st.success(f"DSL created with {len(dsl.components)} components, {len(dsl.connections)} connections, {len(dsl.control_loops)} control loops.")

    # Show DSL components (CRITICAL FIX HERE: Iterate over .values() or .items())
    if dsl.components:
        st.write("**DSL Components (first 3):**")
        # --- THIS IS THE CRUCIAL LINE TO CHANGE ---
        for comp_obj in list(dsl.components.values())[:3]: # Iterate over the actual DSLComponent objects
            # --- AND THIS LINE TO ACCESS ID AND TYPE VALUE ---
            st.write(f"  • {comp_obj.id} ({comp_obj.type.value})") # Access attributes from the object, .type.value for Enum
            st.json(comp_obj.to_dict()) # Show the full dict representation for debugging
    else:
        st.error("❌ No components in DSL after generation!")

    # Show DSL connections (Fix here too, for consistency)
    if dsl.connections:
        st.write("**DSL Connections (first 3):**")
        # --- FIX HERE TOO ---
        for conn_obj in list(dsl.connections.values())[:3]: # Iterate over the actual DSLConnection objects
            st.write(f"  • {conn_obj.id} ({conn_obj.from_component} -> {conn_obj.to_component})")
            st.json(conn_obj.to_dict())
    else:
        st.warning("⚠️ No connections in DSL after generation.")

    # Show DSL control loops (this part was likely already correct if using list)
    if dsl.control_loops:
        st.write("**DSL Control Loops:**")
        for loop_obj in dsl.control_loops:
            st.write(f"  • {loop_obj.id} ({loop_obj.type})")
            st.json(loop_obj.to_dict())
    else:
        st.info("ℹ️ No control loops detected.")


except Exception as e:
    st.error(f"DSL Generation failed: {e}")
    st.write("**Traceback:**")
    st.code(traceback.format_exc())
    st.stop()

# Step 2: DSL to JSON
st.subheader("Step 2: DSL to JSON Conversion")
if dsl: # Ensure DSL object exists from previous step
    try:
        dsl_json_str = dsl.to_dsl("json")
        dsl_json = json.loads(dsl_json_str)

        st.success(f"JSON conversion successful")
        st.write(f"Components in JSON: {len(dsl_json.get('components', []))}")

        # Show first component
        if dsl_json.get('components'):
            st.write("**First component in JSON:**")
            st.json(dsl_json['components'][0])
        else:
            st.error("❌ No components in JSON!")

    except Exception as e:
        st.error(f"JSON conversion failed: {e}")
        st.code(traceback.format_exc())
        st.stop()
else:
    st.error("DSL object not created in previous step. Cannot proceed with JSON conversion.")
    st.stop()

# Step 3: DEXPI Conversion
st.subheader("Step 3: DEXPI Conversion")
dexpi_xml = None # Initialize dexpi_xml
if dsl_json: # Ensure dsl_json exists
    try:
        dexpi_converter = DEXPIConverter()
        dexpi_xml = dexpi_converter.convert(dsl_json)

        if dexpi_xml:
            st.success(f"DEXPI conversion successful, XML length: {len(dexpi_xml)}")
            st.write("**DEXPI XML (first 500 chars):**")
            st.code(dexpi_xml[:500], language="xml")
        else:
            st.error("❌ DEXPI conversion returned empty result!")

    except Exception as e:
        st.error(f"DEXPI conversion failed: {e}")
        st.code(traceback.format_exc())
else:
    st.warning("Skipping DEXPI conversion as DSL JSON was not generated.")

# Step 4: Position Computation
st.subheader("Step 4: Position Computation")
positions, routes, inlines = {}, {}, {} # Initialize to empty
try:
    # Ensure dataframes are not empty before passing
    if not equipment_df.empty and not pipeline_df.empty and not inline_df.empty:
        positions, routes, inlines = compute_positions_and_routing(equipment_df, pipeline_df, inline_df)
        st.success(f"Position computation successful")
        st.write(f"Positions computed: {len(positions) if positions else 0}")

        if positions:
            st.write("**Sample positions:**")
            sample_positions = dict(list(positions.items())[:3])  # First 3
            st.json(sample_positions)
        else:
            st.warning("⚠️ No positions computed - will use default positions if implemented in render_svg.")
    else:
        st.warning("Cannot compute positions: one or more input DataFrames (equipment_df, pipeline_df, inline_df) are empty.")

except Exception as e:
    st.error(f"Position computation failed: {e}")
    st.code(traceback.format_exc())
    positions, routes, inlines = {}, {}, {} # Reset in case of failure


# ═══════════════════════════════════════════════════════════════════
# FIX #3: Updated App.py Section (replace the diagram generation part)
# ═══════════════════════════════════════════════════════════════════

# Replace the “Step 5: SVG Rendering” section in your diagnostic app with:

st.subheader("Step 5: SVG Rendering (FIXED)")
svg = None # Initialize svg here for scope later
tag_map = None # Initialize tag_map here for scope later

if dsl_json: # Ensure dsl_json is available
    try:
        st.write("**Calling render_svg with:**")
        st.write(f"  • DSL JSON components: {len(dsl_json.get('components', []))}")
        st.write(f"  • Symbol renderer: {type(symbol_renderer)}")
        st.write(f"  • Positions: {len(positions) if positions else 0}")

        svg, tag_map = render_svg(
            dsl_json, 
            symbol_renderer, 
            positions, 
            True,  # show_grid
            True,  # show_legend
            1.0    # zoom
        )

        st.write("**SVG Analysis:**")
        svg_analysis = analyze_svg_content(svg)
        st.write(svg_analysis)

        if svg and len(svg) > 100:
            st.success("✅ SVG generation successful!")
            
            # Show raw SVG
            st.write("**Raw SVG (first 1000 chars):**")
            st.code(svg[:1000], language="xml")
            
            # Use the new safe display function
            st.write("**SVG Display (Fixed Method):**")
            display_success = display_svg_safely(svg, "Generated P&ID Diagram")
            
            if not display_success:
                st.error("All display methods failed - check your SVG content")
                
        else:
            st.error("❌ SVG generation failed or returned empty content!")
            
            # Test with a minimal working example
            st.write("**Testing with minimal SVG:**")
            minimal_svg = '''<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">
            <rect x="50" y="50" width="80" height="60" fill="lightblue" stroke="black" stroke-width="2"/>
            <circle cx="200" cy="80" r="30" fill="lightgreen" stroke="black" stroke-width="2"/>
            <text x="90" y="85" text-anchor="middle" font-size="12">EB-001</text>
            <text x="200" y="85" text-anchor="middle" font-size="12">YS-001</text>
            <line x1="130" y1="80" x2="170" y2="80" stroke="black" stroke-width="2"/>
            </svg>'''
            
            display_svg_safely(minimal_svg, "Minimal Test Diagram")

    except Exception as e:
        st.error(f"❌ SVG rendering failed: {e}")
        st.code(traceback.format_exc())
else:
    st.error("Cannot perform SVG rendering as DSL JSON was not generated.")


# ─────────────────────────────────────
# SUMMARY & RECOMMENDATIONS
# ─────────────────────────────────────

st.header("📋 Summary & Next Steps")

# Use a more robust check for svg_analysis
if 'svg_analysis' in locals() and svg_analysis:
    st.write("**Diagram Generation Pipeline Status:**")
    st.write(f"✅ Data Loading: {'SUCCESS' if data_loaded_successfully else 'FAILED'}")
    st.write(f"✅ DSL Generation: {'SUCCESS' if dsl and dsl.components else 'FAILED'}")
    st.write(f"✅ JSON Conversion: {'SUCCESS' if dsl_json else 'FAILED'}")
    st.write(f"✅ DEXPI Conversion: {'SUCCESS' if dexpi_xml else 'FAILED or SKIPPED'}")
    st.write(f"✅ Position Computation: {'SUCCESS' if positions else '⚠️ EMPTY/FAILED'}")
    st.write(f"✅ SVG Rendering: {'SUCCESS' if svg and len(svg) > 100 else '❌ FAILED'}")

st.subheader("🎯 Specific Issues to Check:")

st.markdown("""
1.  **If basic Streamlit image display fails (Test 1)**: There might be an issue with your Streamlit installation or environment, or how `st.image` handles SVG bytes.
2.  **If `schemdraw` test fails (Test 2)**: Ensure `schemdraw` is installed (`pip install schemdraw`). While not directly used for the main P&ID generation in this code, it's a good general SVG rendering library test.
3.  **If data loading fails**: Ensure `equipment_list.csv`, `pipeline_list.csv`, and `inline_component_list.csv` exist in the same directory as `app.py`. Check their content for correct formatting.
4.  **If DSL generation fails**: Review `dsl_generator.py`, especially `DSLGenerator.add_component_from_row()`. Check the input `equipment_df` structure.
5.  **If JSON conversion fails**: Review `dsl_generator.py`'s `to_dsl()` method for JSON output.
6.  **If DEXPI conversion fails**: Review `dexpi_converter.py` and `DEXPIConverter.convert()`. This step might not directly impact SVG generation if the `render_svg` function doesn't depend on DEXPI XML.
7.  **If position computation fails or returns empty**: Review `layout_engine.py`'s `compute_positions_and_routing()` function. Incorrect or insufficient data in your CSVs can lead to this. The `render_svg` function might need to handle empty positions gracefully (e.g., by placing components at default coordinates).
8.  **If SVG rendering fails (CRITICAL Step 5)**: This is likely the core issue for a blank diagram.
    * **Check `drawing_engine.py`'s `render_svg()`**: Is it receiving the correct `dsl_json`? Does it correctly iterate through components and call `symbol_renderer.render_symbol`? Are there any hardcoded dimensions preventing elements from showing?
    * **Check `symbols.py`'s `SymbolRenderer`**: Is `render_symbol()` correctly generating SVG for each component type? Are the symbol definitions correct (e.g., paths, rectangles, circles)? Check for correct SVG namespaces and well-formedness. The "Direct symbol renderer test" in the diagnostic output is crucial here.
    * **Check `svg_to_png()`**: If `st.image` is failing, the conversion from SVG to PNG might be the problem. Ensure `cairosvg` or similar (if used) is installed and working.
9.  **If the generated SVG is very short or has "No drawing elements found"**: This strongly indicates that `render_svg` or `SymbolRenderer` is not producing any graphic elements, or elements are being rendered outside the `viewBox`.
""")

st.subheader("🔧 Manual Override Test")
if st.button("Generate Simple Test Diagram"):
    st.write("Creating a minimal test diagram…")
    try:
        # Create minimal test data
        test_svg = '''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
<rect x="50" y="50" width="100" height="60" fill="lightblue" stroke="black" stroke-width="2"/>
<rect x="250" y="50" width="100" height="60" fill="lightgreen" stroke="black" stroke-width="2"/>
<line x1="150" y1="80" x2="250" y2="80" stroke="black" stroke-width="3"/>
<text x="100" y="85" text-anchor="middle" font-size="12">PUMP-01</text>
<text x="300" y="85" text-anchor="middle" font-size="12">TANK-01</text>
</svg>'''
        # Use the safe display function here too
        display_svg_safely(test_svg, "Manual Override Test Diagram")
        st.success("If you see a simple pump-tank diagram above, then Streamlit SVG display works!")
        
    except Exception as e:
        st.error(f"Even simple test failed: {e}")

