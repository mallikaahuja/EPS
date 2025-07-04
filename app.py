import streamlit as st
import pandas as pd
from pathlib import Path
import base64
import ezdxf
import tempfile
import io

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols")

# --- STANDARD COMPONENT ORDER (From Your Code) ---
# This defines the automatic sorting logic for the P&ID flow.
STANDARD_ORDER = [
    "Flexible Connection (Suction)", "Pressure Transmitter (Suction)", "Temperature Gauge (Suction)",
    "Temperature Transmitter (Suction)", "ACG Filter (Suction)", "Suction Filter", "EPO Valve",
    "Dry Pump Model", "Discharge Silencer", "Flexible Connection (Discharge)", 
    "Pressure Transmitter (Discharge)", "Temperature Gauge (Discharge)", "Temperature Transmitter (Discharge)",
    "Discharge Condenser", "Catch Pot (Auto Drain)", "Scrubber", "Flame Arrestor (Discharge)"
]

# --- HELPER FUNCTIONS (From Your Code, with fixes) ---

def list_symbol_names():
    """Dynamically lists available components by reading the symbol filenames."""
    if not SYMBOLS_DIR.exists():
        st.error(f"Symbol directory '{SYMBOLS_DIR}' not found!")
        return []
    # Cleans up filenames to be user-friendly (e.g., "vertical_vessel.png" -> "vertical vessel")
    return sorted([f.stem.replace("_", " ") for f in SYMBOLS_DIR.glob("*.png")])

def load_symbol_image_base64(symbol_name):
    """Loads a symbol image and encodes it in Base64 for direct HTML embedding."""
    # Converts user-friendly name back to a standardized filename
    safe_filename = symbol_name.replace(" ", "_") + ".png"
    path = SYMBOLS_DIR / safe_filename
    if path.exists():
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return None

def create_dxf_data(component_list):
    """Creates DXF data in memory for download."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0
    # Create a simple line-based representation for each component in the DXF
    for comp in component_list:
        tag = comp['tag']
        typ = comp['type']
        msp.add_line((0, y), (2, y), dxfattribs={"layer": "Flow_Line"})
        # Add text labels for the tag and type
        msp.add_text(f"{tag}: {typ}", dxfattribs={'height': 0.3}).set_pos((2.5, y))
        y -= 2.0 # Space out components vertically
    
    # Write the DXF to an in-memory stream instead of a temporary file
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")

def reorder_components_by_standard_order(components):
    """Sorts the component list based on the predefined STANDARD_ORDER."""
    type_to_order_index = {t: i for i, t in enumerate(STANDARD_ORDER)}
    # Any component not in the standard order gets a high index to place it at the end.
    return sorted(components, key=lambda x: type_to_order_index.get(x['type'], len(STANDARD_ORDER)))

# --- SESSION STATE INITIALIZATION ---
if "component_list" not in st.session_state:
    st.session_state.component_list = []

# --- UI LAYOUT ---
st.title("EPS Interactive P&ID Generator")

with st.sidebar:
    st.header("Add Component")
    all_symbols = list_symbol_names()
    if not all_symbols:
        st.error("No symbols found. Please ensure the 'symbols' folder is populated.")
    else:
        comp_type = st.selectbox("Component Type", all_symbols)
        comp_tag = st.text_input("Tag / Label (must be unique)", key="comp_tag_input")
        if st.button("Save Component", use_container_width=True):
            if comp_tag and comp_type:
                if any(c['tag'] == comp_tag for c in st.session_state.component_list):
                    st.error(f"Tag '{comp_tag}' already exists.")
                else:
                    st.session_state.component_list.append({"type": comp_type, "tag": comp_tag})
                    st.rerun() # Rerun to update the UI immediately
            else:
                st.warning("Both tag and component type are required.")
    
    if st.session_state.component_list:
        if st.button("Clear All Components", use_container_width=True, type="secondary"):
            st.session_state.component_list = []
            st.rerun()

# --- Main Display Area ---
col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("Component Sequence")
    if st.session_state.component_list:
        # Auto-order the components for display
        ordered_components = reorder_components_by_standard_order(st.session_state.component_list)
        df = pd.DataFrame(ordered_components)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No components added yet.")

with col2:
    st.subheader("Live Preview")
    if st.session_state.component_list:
        ordered_components = reorder_components_by_standard_order(st.session_state.component_list)
        
        # Build the HTML for the preview
        preview_items = []
        for comp in ordered_components:
            img_data = load_symbol_image_base64(comp['type'])
            if img_data:
                preview_items.append(f"""
                    <div style="display:inline-block; text-align:center; margin: 0 15px;">
                        <img src="{img_data}" style="height:80px;"><br>
                        <b style="font-size:14px;">{comp['tag']}</b><br>
                        <small style="color:grey;">{comp['type']}</small>
                    </div>
                """)
        
        # Use a container with horizontal scrolling
        st.markdown(f"""
            <div style="display:flex; align-items:center; width:100%; overflow-x:auto; border:1px solid #e0e0e0; padding:10px; border-radius:5px;">
                <b style="margin-right:15px;">INLET →</b>
                {'<b style="font-size:24px; margin: 0 5px;">→</b>'.join(preview_items)}
                <b style="margin-left:15px;">→ OUTLET</b>
            </div>
        """, unsafe_allow_html=True)

        # --- Download Button Logic ---
        st.markdown("---")
        st.subheader("Export")
        try:
            dxf_data = create_dxf_data(ordered_components)
            st.download_button(
                label="Download as DXF",
                data=dxf_data,
                file_name="generated_pid.dxf",
                mime="application/dxf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"DXF Export Failed: {e}")

    else:
        st.info("Your P&ID preview will appear here once components are added.")
