import streamlit as st
import pandas as pd
import os
import io
import base64
import requests
import time
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf import const as ezdxf_const

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

try:
    FONT = ImageFont.truetype("arial.ttf", 18)
    SMALL_FONT = ImageFont.truetype("arial.ttf", 14)
except IOError:
    FONT = ImageFont.load_default()
    SMALL_FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS ---
def auto_tag(prefix, existing):
    count = 1
    existing_tags = [item['tag'] for item in existing]
    while f"{prefix}-{count:03}" in existing_tags:
        count += 1
    return f"{prefix}-{count:03}"

def generate_image_stability(type_name, image_name):
    if not STABILITY_API_KEY:
        st.error("Missing STABILITY_API_KEY in environment variables.")
        return None

    prompt = f"ISA S5.1 standard P&ID symbol for a '{type_name}', professional 2D engineering schematic icon. Clean, black line art. No text, no shadows. Pure white, transparent background."
    
    st.info(f"Generating symbol for '{type_name}' with Stability AI...")
    try:
        # Use multipart/form-data by passing prompt to 'files'
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "image/png"},
            files={"prompt": (None, prompt)},
            data={"output_format": "png", "aspect_ratio": "1:1"}
        )
        if response.status_code == 200:
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f:
                f.write(response.content)
            st.success(f"New symbol '{image_name}' created! Reloading...")
            st.rerun()
        else:
            st.error(f"Stability API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Image generation request failed: {e}")

def get_symbol_image(type_name, image_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_image_stability(type_name, image_name)
        return None # Rerun will be triggered
    try:
        return Image.open(path).convert("RGBA").resize((100, 100))
    except:
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (99,99)], outline="red", width=2)
        draw.text((10, 40), f"LOAD\nFAILED", fill="red", font=SMALL_FONT)
        return img

def render_pid_diagram():
    # Advanced Layout Engine
    canvas = Image.new("RGBA", (2400, 1600), "white")
    draw = ImageDraw.Draw(canvas)
    
    # 1. Define the grid and component positions
    layout_grid = {eq['tag']: (i, 1) for i, eq in enumerate(st.session_state.components["equipment"])}
    node_positions = {}
    x_start, y_start, x_step, y_step = 200, 400, 350, 250

    for eq in st.session_state.components["equipment"]:
        col, row = layout_grid.get(eq['tag'], (0,0))
        x, y = x_start + col * x_step, y_start + row * y_step
        node_positions[eq['tag']] = {'x': x, 'y': y}

    # 2. Draw pipelines first (as background layer)
    for pipe in st.session_state.components["pipelines"]:
        start, end = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
        if start and end:
            draw.line([(start['x']+50, start['y']), (end['x']-50, end['y'])], fill="black", width=3)
            # Draw arrow
            draw.polygon([(end['x']-50, end['y']-6), (end['x']-40, end['y']), (end['x']-50, end['y']+6)], fill="black")

    # 3. Draw equipment and in-line components on top
    for eq in st.session_state.components["equipment"]:
        x, y = node_positions[eq['tag']]['x'], node_positions[eq['tag']]['y']
        img = get_symbol_image(eq["type"], eq["symbol"])
        if img:
            canvas.paste(img, (x-50, y-50), img)
            draw.text((x, y+60), eq["tag"], fill="black", font=FONT, anchor="ms")
    
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if pipe:
            start, end = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
            if start and end:
                mid_x = int((start['x'] + end['x']) / 2)
                mid_y = start['y']
                img = get_symbol_image(comp["type"], comp["symbol"])
                if img:
                    # Erase a small section of the line
                    draw.line([(mid_x-60, mid_y), (mid_x+60, mid_y)], fill="white", width=5)
                    # Paste component
                    canvas.paste(img, (mid_x-50, mid_y-50), img)
                    draw.text((mid_x, mid_y+60), comp["tag"], fill="black", font=FONT, anchor="ms")

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 150
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        # Corrected DXF text alignment
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        text.set_placement((x + 15, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def canvas_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.sidebar.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["equipment"])
        st.sidebar.text_input("Generated Tag", value=tag, disabled=True)
        if st.sidebar.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()
    st.header("Add Pipeline")
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
    st.header("Add In-Line Component")
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

# --- MAIN UI ---
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
    with d_col1:
        st.download_button("Download PNG", canvas_to_bytes(diagram), "pid.png", "image/png", use_container_width=True)
    with d_col2:
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf", use_container_width=True)
