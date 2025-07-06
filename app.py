import streamlit as st
import pandas as pd
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf import enums  # The correct import for alignment constants
import openai
import requests

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 20)
    SMALL_FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    FONT = ImageFont.load_default()
    SMALL_FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    return pd.read_csv(file_name) if os.path.exists(file_name) else pd.DataFrame()

equipment_options = load_data("equipment_list.csv")
inline_options = load_data("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS ---
def auto_tag(prefix, existing_items):
    existing_tags = [item['tag'] for item in existing_items]
    count = 1
    while f"{prefix}-{count:03}" in existing_tags: count += 1
    return f"{prefix}-{count:03}"

def generate_image_stability(type_name, image_name):
    api_key = os.environ.get("STABILITY_API_KEY")
    if not api_key:
        st.error("Missing STABILITY_API_KEY in environment.")
        return
    st.info(f"Generating ISA-compliant symbol for '{type_name}'...")
    try:
        # --- DEFINITIVE STABILITY AI FIX ---
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "image/png"},
            files={"prompt": (None, f"ISA S5.1 standard P&ID symbol for '{type_name}', professional 2D engineering schematic icon. Clean, black line art. No text, no shadows, pure white background.")},
            data={"output_format": "png", "aspect_ratio": "1:1"}
        )
        if response.status_code == 200:
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f: f.write(response.content)
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
        return None
    try:
        return Image.open(path).convert("RGBA").resize((120, 120))
    except Exception:
        img = Image.new("RGBA", (120, 120), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (119,119)], outline="red", width=2)
        draw.text((10, 50), f"LOAD\nFAILED", fill="red", font=SMALL_FONT)
        return img

def render_professional_pid():
    if not st.session_state.components['equipment']: return None
    canvas = Image.new("RGBA", (2400, 1600), "white")
    draw = ImageDraw.Draw(canvas)
    
    # ADVANCED LAYOUT ENGINE: Map types to grid coordinates (col, row)
    layout_map = {eq['tag']: (i * 2, 2) for i, eq in enumerate(st.session_state.components['equipment'])}
    
    node_positions = {}
    x_offset, y_offset = 200, 200
    col_width, row_height = 350, 250

    for eq in st.session_state.components['equipment']:
        tag, eq_type = eq['tag'], eq['type']
        col, row = layout_map.get(tag, (len(node_positions) * 2, 4))
        px, py = x_offset + col * col_width, y_offset + row * row_height
        node_positions[tag] = {'x': px, 'y': py, 'in':(px-60, py), 'out':(px+60, py), 'top':(px, py-60), 'bottom':(px, py+60)}
        img = get_symbol_image(eq_type, eq["symbol"])
        if img:
            canvas.paste(img, (px - 60, py - 60), img)
            draw.text((px, py + 70), tag, fill="black", font=FONT, anchor="ms")
            
    for pipe in st.session_state.components['pipelines']:
        start, end = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
        if not (start and end): continue

        p1, p2 = start['out'], end['in']
        draw.line([p1, p2], fill="black", width=3)
        draw.polygon([(p2[0]-12, p2[1]-8), (p2[0], p2[1]), (p2[0]-12, p2[1]+8)], fill="black")
        
        inline_comps = [c for c in st.session_state.components['inline'] if c['pipe_tag'] == pipe['tag']]
        num_segments = len(inline_comps) + 1
        for i, comp in enumerate(inline_comps):
            frac = (i + 1) / num_segments
            mid_x, mid_y = int(p1[0] + frac * (p2[0] - p1[0])), p1[1]
            img = get_symbol_image(comp["type"], comp["symbol"])
            if img:
                canvas.paste(img, (mid_x - 60, mid_y - 60), img)
                draw.text((mid_x, mid_y + 70), comp['tag'], fill="black", font=FONT, anchor="ms")
    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30)], close=True)
        # --- DEFINITIVE EZDXF FIX ---
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        text.set_placement((x + 15, -5), align=enums.TextEntityAlignment.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def get_ai_suggestions():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key: return "⚠️ AI service unavailable."
        client = openai.OpenAI(api_key=api_key)
        summary = ", ".join([f"{e['tag']} ({e['type']})" for e in st.session_state.components['equipment']])
        prompt = f"As a senior process engineer, provide 5 specific design and safety improvements for a P&ID containing: {summary}."
        response = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"⚠️ AI Error: {e}"

def canvas_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_options.empty:
        eq_type = st.sidebar.selectbox("Equipment Type", equipment_options["type"].unique())
        row = equipment_options[equipment_options["type"] == eq_type].iloc[0]
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
    if st.session_state.components["pipelines"] and not inline_options.empty:
        inline_type = st.sidebar.selectbox("In-line Type", inline_options["type"].unique())
        row = inline_options[inline_options["type"] == inline_type].iloc[0]
        pipe_tag = st.sidebar.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["inline"])
        st.sidebar.text_input("New In-line Tag", value=tag, disabled=True)
        if st.sidebar.button("➕ Add In-Line"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()
    if st.sidebar.button("🔄 Reset All", use_container_width=True):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Component Summary")
c1, c2, c3 = st.columns(3)
with c1: c1.dataframe(st.session_state.components["equipment"])
with c2: c2.dataframe(st.session_state.components["pipelines"])
with c3: c3.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_professional_pid()
if diagram:
    st.image(diagram)
    st.subheader("📤 Export P&ID")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button("Download PNG", canvas_to_bytes(diagram), "pid.png", "image/png", use_container_width=True)
    with d_col2:
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add components from the sidebar to begin.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing P&ID..."):
        st.markdown(get_ai_suggestions())
