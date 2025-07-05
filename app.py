import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io
import ezdxf
from ezdxf import const as ezdxf_const
import openai
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
SYMBOLS_PATH = "symbols"
os.makedirs(SYMBOLS_PATH, exist_ok=True)

# --- FONT (for better text rendering) ---
try:
    font = ImageFont.truetype("arial.ttf", 15)
    small_font = ImageFont.truetype("arial.ttf", 12)
except IOError:
    font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        st.error(f"Data file not found: {file_name}. Please ensure it is in the repository.")
        return pd.DataFrame()
    return pd.read_csv(file_name)

equipment_df = load_data("equipment_list.csv")
pipeline_df = load_data("pipeline_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state: st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS ---
def auto_tag(prefix, existing_tags):
    count = 1
    while f"{prefix}-{count:03}" in existing_tags: count += 1
    return f"{prefix}-{count:03}"

def get_component_image(image_name, component_type):
    # This function remains the same, using DALL-E as a fallback.
    # We will assume you have set up a database or will add symbols manually.
    local_path = os.path.join(SYMBOLS_PATH, image_name)
    if os.path.exists(local_path):
        return Image.open(local_path).convert("RGBA").resize((100, 100))
    # Placeholder for DALL-E or DB logic
    img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0), (99,99)], outline="red", width=2)
    draw.text((10, 40), f"MISSING\n{component_type}", fill="red", font=small_font)
    return img

# --- ADVANCED PIL/Pillow P&ID RENDERING ENGINE ---
def render_professional_pid():
    if not st.session_state.components['equipment']: return None

    # Define a layout grid
    grid_x_step = 250
    grid_y_step = 200
    canvas_width = 2000
    canvas_height = 1200
    
    canvas = Image.new("RGBA", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    
    # Manually define positions for a layout similar to your reference
    # This is the key to a professional look. We map tags to (x, y) grid coordinates.
    layout_grid = {
        "V-101": (1, 2),  # Suction Filter
        "P-101": (3, 2),  # Pump
        "C-101": (5, 2),  # Main Condenser
        "V-102": (5, 3),  # Catch Pot below condenser
        "S-101": (7, 2),  # Scrubber
        "N2-IN": (3, 1), # N2 Purge inlet
        "CW-IN": (4, 1), # Cooling Water inlet
    }
    
    # Store pixel positions of components
    node_positions = {}

    # 1. Draw Equipment
    for eq in st.session_state.components['equipment']:
        tag = eq['tag']
        if tag in layout_grid:
            gx, gy = layout_grid[tag]
            px, py = gx * grid_x_step, gy * grid_y_step
            node_positions[tag] = {"x": px, "y": py, "ports": {"in": (px-50, py), "out": (px+50, py), "top": (px, py-50), "bottom": (px, py+50)}}
            
            img = get_component_image(eq["image_name"], eq["type"])
            canvas.paste(img, (px - 50, py - 50), img)
            draw.text((px, py + 60), tag, fill="black", font=font, anchor="ms")

    # 2. Draw Pipelines
    for pipe in st.session_state.components['pipelines']:
        from_node = node_positions.get(pipe['from'])
        to_node = node_positions.get(pipe['to'])
        if not from_node or not to_node: continue

        # Simple horizontal connection for now
        start_point = from_node['ports']['out']
        end_point = to_node['ports']['in']
        draw.line([start_point, end_point], fill="black", width=3)
        
        # Draw arrow
        draw.polygon([ (end_point[0]-10, end_point[1]-5), (end_point[0]), end_point[1], (end_point[0]-10, end_point[1]+5)], fill="black")

    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    eq_positions = {eq['tag']: (i * 40, 0) for i, eq in enumerate(st.session_state.components['equipment'])}
    
    for eq in st.session_state.components['equipment']:
        x_pos, y_pos = eq_positions[eq['tag']]
        msp.add_lwpolyline([(x_pos-5, y_pos-5), (x_pos+5, y_pos-5), (x_pos+5, y_pos+5), (x_pos-5, y_pos+5), (x_pos-5,-5)])
        
        # CORRECTED: Use the correct constant from ezdxf.const
        text_entity = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        text_entity.set_placement((x_pos, y_pos - 8), align=ezdxf_const.TOP_CENTER)
        
    for pipe in st.session_state.components['pipelines']:
        start_pos = eq_positions.get(pipe['from'])
        end_pos = eq_positions.get(pipe['to'])
        if start_pos and end_pos:
            msp.add_line((start_pos[0] + 5, start_pos[1]), (end_pos[0] - 5, end_pos[1]))
            
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode('utf-8')

def get_ai_suggestions():
    # Your AI function
    pass

# --- UI ---
with st.sidebar:
    st.title("P&ID Builder")
    st.markdown("---")
    with st.expander("➕ Add Equipment", expanded=True):
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        eq_tag = auto_tag(eq_row["Tag Prefix"], [e['tag'] for e in st.session_state.components['equipment']])
        st.text_input("New Tag", value=eq_tag, disabled=True, key="eq_tag_display")
        if st.button("Add Equipment"):
            st.session_state.components['equipment'].append({"type": eq_type, "tag": eq_tag, "image_name": eq_row["Symbol_Image"]})
            st.rerun()
    with st.expander("🔗 Add Pipeline"):
        if len(st.session_state.components['equipment']) >= 2:
            from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.components['equipment']])
            to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.components['equipment']], index=1)
            pipe_tag = auto_tag("P", [p['tag'] for p in st.session_state.components['pipelines']])
            st.text_input("New Pipeline Tag", value=pipe_tag, disabled=True, key="pipe_tag_display")
            if st.button("Add Pipeline"):
                st.session_state.components['pipelines'].append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
                st.rerun()
    # ... Add UI for in-line components similarly

st.title("🧠 EPS Interactive P&ID Generator")
with st.container(border=True):
    st.subheader("Current Project Components")
    c1, c2, c3 = st.columns(3)
    with c1: st.dataframe(st.session_state.components['equipment'])
    with c2: st.dataframe(st.session_state.components['pipelines'])
    with c3: st.dataframe(st.session_state.components['inline'])

st.markdown("---")
st.subheader("🖼️ P&ID Diagram Preview")
pid_image = render_professional_pid()
if pid_image:
    st.image(pid_image)
    st.subheader("📤 Export P&ID")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf = io.BytesIO()
        pid_image.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_layout.png", "image/png", use_container_width=True)
    with col_dl2:
        dxf_data = generate_dxf()
        if dxf_data:
            st.download_button("Download DXF", dxf_data, "pid_layout.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add some equipment to see the P&ID preview.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Thinking..."):
        st.markdown(get_ai_suggestions()) # This should be defined now
