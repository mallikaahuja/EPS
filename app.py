import streamlit as st
import pandas as pd
import os
import io
import base64
import requests
import ezdxf
from ezdxf import const as ezdxf_const
from PIL import Image, ImageDraw, ImageFont
import openai

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 24)
    SMALL_FONT = ImageFont.truetype("arial.ttf", 18)
except IOError:
    FONT = ImageFont.load_default()
    SMALL_FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    return pd.read_csv(file_name) if os.path.exists(file_name) else pd.DataFrame()

equipment_df = load_data("equipment_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS ---
def auto_tag(prefix, existing_tags):
    count = 1
    while f"{prefix}-{count:03}" in existing_tags: count += 1
    return f"{prefix}-{count:03}"

def generate_image_stability(type_name, image_name):
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        st.error("STABILITY_API_KEY not found in environment variables.")
        return None
    
    st.info(f"Generating ISA-compliant symbol for '{type_name}' with Stability AI...")
    prompt = f"ISA S5.1 standard P&ID symbol for '{type_name}'. Black and white 2D schematic icon. Clean, thin lines. No text, no shadows, no background. Vector style."
    
    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "image/png"},
            files={"prompt": (None, prompt)},
            data={"output_format": "png", "aspect_ratio": "1:1", "model": "sd3-medium"}
        )
        if response.status_code == 200:
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f: f.write(response.content)
            st.success(f"New symbol '{image_name}' created. Reloading...")
            st.rerun()
        else:
            st.error(f"Stability API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Image generation request failed: {e}")

def get_symbol_image(type_name, image_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_image_stability(type_name, image_name)
        return None # App will rerun
    try:
        return Image.open(path).convert("RGBA").resize((100, 100))
    except:
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (99,99)], outline="red", width=2)
        draw.text((10, 40), f"LOAD\nFAILED", fill="red", font=SMALL_FONT)
        return img

def render_pid_diagram():
    # This is the advanced layout engine
    canvas = Image.new("RGBA", (2400, 1600), "white")
    draw = ImageDraw.Draw(canvas)
    node_positions = {}
    
    # Define a grid system
    x_start, y_start = 200, 200
    col_width, row_height = 400, 300

    # Manually define a layout that mimics your reference P&ID
    # This is the key to a professional look. We map TYPE to a grid position.
    layout_map = {
        "Suction Filter": (0, 1),
        "Dry Vacuum Pump": (1, 1),
        "Ex. Condenser": (2, 1),
        "Catch Pot": (2, 2), # Directly below the condenser
        "Scrubber": (3, 1),
    }

    # Draw equipment and store their pixel coordinates
    for eq in st.session_state.components['equipment']:
        col, row = layout_map.get(eq['type'], (len(node_positions), 0))
        x, y = x_start + col * col_width, y_start + row * row_height
        node_positions[eq['tag']] = {'x': x, 'y': y, 'ports': {'in':(x-50, y), 'out':(x+50, y), 'top':(x, y-50), 'bottom':(x, y+50)}}
        img = get_symbol_image(eq['type'], eq['symbol'])
        if img:
            canvas.paste(img, (x-50, y-50), img)
            draw.text((x, y+60), eq['tag'], fill="black", font=FONT, anchor="ms")
    
    # Draw pipelines and in-line components
    for pipe in st.session_state.components['pipelines']:
        start, end = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
        if not (start and end): continue

        p1 = start['ports']['out'] if start['y'] == end['y'] else start['ports']['bottom']
        p2 = end['ports']['in'] if start['y'] == end['y'] else end['ports']['top']

        inline_comps = [c for c in st.session_state.components['inline'] if c['pipe_tag'] == pipe['tag']]
        num_segments = len(inline_comps) + 1
        
        last_point = p1
        for i, comp in enumerate(inline_comps):
            frac = (i + 1) / num_segments
            mid_x = int(p1[0] + frac * (p2[0] - p1[0]))
            mid_y = int(p1[1] + frac * (p2[1] - p1[1]))
            
            img = get_symbol_image(comp['type'], comp['symbol'])
            if img:
                canvas.paste(img, (mid_x-50, mid_y-50), img)
                draw.text((mid_x, mid_y+60), comp['tag'], fill="black", font=FONT, anchor="ms")

            draw.line([last_point, (mid_x - 50, mid_y)], fill="black", width=3)
            last_point = (mid_x + 50, mid_y)
        
        draw.line([last_point, p2], fill="black", width=3)
        # Draw arrow
        draw.polygon([(p2[0]-10, p2[1]-6), (p2[0], p2[1]), (p2[0]-10, p2[1]+6)], fill="black")

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30)], close=True)
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        # CORRECTED: Use set_align() and a direct string
        text.set_align('TOP_CENTER').set_pos((x + 15, -5))
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def get_ai_suggestions():
    # ... your AI suggestion logic here ...
    return "AI Suggestions feature is ready."

def canvas_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.sidebar.selectbox("Equipment Type", equipment_df["type"].unique())
        eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(eq_row["Tag Prefix"], st.session_state.components["equipment"])
        st.sidebar.text_input("Generated Tag", value=tag, disabled=True)
        if st.sidebar.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": eq_row["Symbol_Image"]})
            st.rerun()

    st.sidebar.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.sidebar.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        if to_opts:
            to_tag = st.sidebar.selectbox("To", to_opts)
            tag = auto_tag("PL", st.session_state.components["pipelines"])
            st.sidebar.text_input("New Pipeline Tag", value=tag, disabled=True)
            if st.sidebar.button("➕ Add Pipeline"):
                st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
                st.rerun()

    st.sidebar.header("Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.sidebar.selectbox("In-line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.sidebar.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["inline"])
        st.sidebar.text_input("New In-line Tag", value=tag, disabled=True)
        if st.sidebar.button("➕ Add In-Line"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    if st.sidebar.button("🔄 Reset All", use_container_width=True):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN PAGE ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Component Summary")
c1, c2, c3 = st.columns(3)
with c1: c1.dataframe(st.session_state.components["equipment"])
with c2: c2.dataframe(st.session_state.components["pipelines"])
with c3: c3.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    st.subheader("📤 Export P&ID")
    d_col1, d_col2 = st.columns(2)
    d_col1.download_button("Download PNG", canvas_to_bytes(diagram), "pid.png", "image/png", use_container_width=True)
    d_col2.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf", use_container_width=True)

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing P&ID..."):
        st.markdown(get_ai_suggestions())
