import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf import const as ezdxf_const
import openai
import requests
import base64
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 15)
except IOError:
    FONT = ImageFont.load_default()

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
def auto_tag(prefix, existing_tags):
    count = 1
    while f"{prefix}-{count:03}" in existing_tags: count += 1
    return f"{prefix}-{count:03}"

def generate_symbol_with_dalle(type_name, image_name):
    st.info(f"Symbol '{image_name}' not found. Generating with DALL·E 3...")
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("AI Error: OPENAI_API_KEY not set in environment variables.")
            return
        client = openai.OpenAI(api_key=api_key)
        prompt = f"A professional 2D P&ID symbol for a '{type_name}'. Style: clean, black line art, schematic, ISA 5.1 standard. Background: perfectly white, fully transparent. NO text, shadows, gradients, or 3D effects. Single, centered, vector-style engineering icon."
        with st.spinner(f"DALL·E is creating symbol for {type_name}..."):
            response = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024", response_format="b64_json")
            image_data = base64.b64decode(response.data[0].b64_json)
        with open(os.path.join(SYMBOLS_CACHE_DIR, image_name), "wb") as f: f.write(image_data)
        st.success(f"New symbol created! Reloading...")
        st.rerun()
    except Exception as e:
        st.error(f"AI symbol generation failed: {e}")

def get_symbol_image(image_name, type_name):
    cache_path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if os.path.exists(cache_path):
        return Image.open(cache_path).convert("RGBA").resize((100, 100))
    generate_symbol_with_dalle(type_name, image_name)
    return None

def render_professional_pid():
    if not st.session_state.components['equipment']: return None
    canvas = Image.new("RGBA", (2000, 1200), (240, 242, 246, 255))
    draw = ImageDraw.Draw(canvas)
    layout_map = {comp['tag']: (i * 2 + 1, 2) for i, comp in enumerate(st.session_state.components['equipment'])}
    node_positions = {}
    for eq in st.session_state.components['equipment']:
        tag = eq['tag']
        col, row = layout_map.get(tag, (len(node_positions) * 2 + 1, 4))
        px, py = 150 + col * 150, 150 + row * 150
        node_positions[tag] = {'x': px, 'y': py, 'in': (px-50, py), 'out': (px+50, py), 'top':(px, py-50), 'bottom':(px, py+50)}
        img = get_symbol_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (px - 50, py - 50), img)
            draw.text((px, py + 60), tag, fill="black", font=FONT, anchor="ms")
    for pipe in st.session_state.components['pipelines']:
        start_node, end_node = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
        if start_node and end_node:
            p1 = start_node['out']
            p2 = end_node['in']
            draw.line([p1, (p1[0] + 20, p1[1]), (p2[0] - 20, p2[1]), p2], fill="black", width=3)
            draw.polygon([(p2[0]-10, p2[1]-6), (p2[0], p2[1]), (p2[0]-10, p2[1]+6)], fill="black")
    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components['equipment']):
        x = i * 50
        msp.add_lwpolyline([(x, 0), (x+20, 0), (x+20, 20), (x, 20), (x, 0)])
        text = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        text.set_placement((x + 10, -5), align=ezdxf_const.TOP_CENTER)
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
        eq_type = st.selectbox("Equipment Type", equipment_options["type"].unique())
        eq_row = equipment_options[equipment_options["type"] == eq_type].iloc[0]
        eq_tag = auto_tag(eq_row["Tag Prefix"], [e["tag"] for e in st.session_state.components['equipment']])
        st.text_input("New Tag", value=eq_tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components['equipment'].append({"type": eq_type, "tag": eq_tag, "symbol": eq_row["Symbol_Image"]})
            st.rerun()
    st.header("Add Pipeline")
    if len(st.session_state.components['equipment']) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components['equipment']])
        to_opts = [e["tag"] for e in st.session_state.components['equipment'] if e["tag"] != from_tag]
        if to_opts:
            to_tag = st.selectbox("To", to_opts)
            tag = auto_tag("P", [p["tag"] for p in st.session_state.components['pipelines']])
            st.text_input("New Pipeline Tag", value=tag, disabled=True)
            if st.button("➕ Add Pipeline"):
                st.session_state.components['pipelines'].append({"tag": tag, "from": from_tag, "to": to_tag})
                st.rerun()
    st.header("Add In-Line Component")
    if st.session_state.components['pipelines'] and not inline_options.empty:
        inline_type = st.selectbox("In-Line Type", inline_options["type"].unique())
        inline_row = inline_options[inline_options["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components['pipelines']])
        tag = auto_tag(inline_row["Tag Prefix"], [i["tag"] for i in st.session_state.components['inline']])
        st.text_input("In-Line Tag", value=tag, disabled=True)
        if st.button("➕ Add In-Line"):
            st.session_state.components['inline'].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": inline_row["Symbol_Image"]})
            st.rerun()
    if st.sidebar.button("🗑 Reset All", use_container_width=True):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("🔍 Components Overview")
c1, c2, c3 = st.columns(3)
with c1: c1.dataframe(st.session_state.components['equipment'])
with c2: c2.dataframe(st.session_state.components['pipelines'])
with c3: c3.dataframe(st.session_state.components['inline'])

st.markdown("---")
st.subheader("📊 P&ID Diagram Preview")
canvas = render_professional_pid()
if canvas:
    st.image(canvas)
    st.subheader("📤 Export")
    c1, c2 = st.columns(2)
    c1.download_button("Download PNG", canvas_to_bytes(canvas), "p_and_id.png", "image/png", use_container_width=True)
    c2.download_button("Download DXF", generate_dxf(), "p_and_id.dxf", "application/dxf", use_container_width=True)

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing P&ID..."):
        st.markdown(get_ai_suggestions())
