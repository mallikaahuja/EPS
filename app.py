import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf.enums import TextEntityAlignment
import openai
import base64
from PIL import Image, ImageDraw, ImageFont

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE = "symbols_cache"
os.makedirs(SYMBOLS_CACHE, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 15)
except IOError:
    FONT = ImageFont.load_default()

# --- DATA LOAD ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- SESSION ---
if "equipment" not in st.session_state: st.session_state.equipment = []
if "pipelines" not in st.session_state: st.session_state.pipelines = []
if "inline" not in st.session_state: st.session_state.inline = []

# --- UTILITY FUNCTIONS ---
def auto_tag(prefix, existing_tags):
    count = 1
    while f"{prefix}-{count:03}" in existing_tags:
        count += 1
    return f"{prefix}-{count:03}"

def generate_symbol_ai(component_type, filename):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found.")
        return None
    client = openai.OpenAI(api_key=api_key)
    prompt = f"A clean 2D P&ID black-and-white engineering symbol for '{component_type}', using ISA 5.1 standards. Pure white background, centered, no text, no shadows, vector-like schematic."

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json",
        )
        b64 = response.data[0].b64_json
        img_data = base64.b64decode(b64)
        with open(os.path.join(SYMBOLS_CACHE, filename), "wb") as f:
            f.write(img_data)
    except Exception as e:
        st.error(f"AI Image error: {e}")

def get_symbol(component_type, filename):
    filepath = os.path.join(SYMBOLS_CACHE, filename)
    generate_symbol_ai(component_type, filename)  # Always regenerate for consistency
    if os.path.exists(filepath):
        return Image.open(filepath).convert("RGBA").resize((100, 100))
    return Image.new("RGBA", (100, 100), (255, 0, 0, 100))

def render_pid_layout():
    if not st.session_state.equipment:
        return None
    width = 2000
    height = 1000
    canvas = Image.new("RGBA", (width, height), (245, 245, 245, 255))
    draw = ImageDraw.Draw(canvas)

    x_offset = 200
    y_mid = height // 2
    spacing = 200
    positions = {}

    for i, eq in enumerate(st.session_state.equipment):
        x = x_offset + i * spacing
        positions[eq["tag"]] = (x, y_mid)
        img = get_symbol(eq["type"], eq["image"])
        canvas.paste(img, (x - 50, y_mid - 50), img)
        draw.text((x, y_mid + 65), eq["tag"], fill="black", font=FONT, anchor="ms")

    for pipe in st.session_state.pipelines:
        start = positions.get(pipe["from"])
        end = positions.get(pipe["to"])
        if start and end:
            draw.line([start, end], fill="black", width=3)
            draw.polygon([(end[0]-10, end[1]-6), (end[0], end[1]), (end[0]-10, end[1]+6)], fill="black")

    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.equipment):
        x = i * 60
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        text.set_placement((x + 15, -5), align=TextEntityAlignment.TOP_CENTER)

    for pipe in st.session_state.pipelines:
        idx_from = next((i for i, e in enumerate(st.session_state.equipment) if e["tag"] == pipe["from"]), None)
        idx_to = next((i for i, e in enumerate(st.session_state.equipment) if e["tag"] == pipe["to"]), None)
        if idx_from is not None and idx_to is not None:
            x1, x2 = idx_from * 60 + 30, idx_to * 60
            msp.add_line((x1, 15), (x2, 15))

    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode("utf-8")

def export_image(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY not set"
    client = openai.OpenAI(api_key=api_key)
    comp_summary = ", ".join([f"{c['tag']} ({c['type']})" for c in st.session_state.equipment])
    prompt = f"You are a senior process engineer. Suggest 5 detailed improvements to a P&ID containing: {comp_summary}."
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("➕ Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Type", equipment_df["type"].unique())
        eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(eq_row["Tag Prefix"], [e["tag"] for e in st.session_state.equipment])
        st.text_input("New Tag", value=tag, disabled=True)
        if st.button("Add Equipment"):
            st.session_state.equipment.append({
                "type": eq_type,
                "tag": tag,
                "image": eq_row["Symbol_Image"]
            })
            st.rerun()

    st.header("🔗 Add Pipeline")
    if len(st.session_state.equipment) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.equipment])
        to_options = [e["tag"] for e in st.session_state.equipment if e["tag"] != from_tag]
        if to_options:
            to_tag = st.selectbox("To", to_options)
            pipe_tag = auto_tag("PL", [p["tag"] for p in st.session_state.pipelines])
            st.text_input("Pipeline Tag", value=pipe_tag, disabled=True)
            if st.button("Add Pipeline"):
                st.session_state.pipelines.append({"tag": pipe_tag, "from": from_tag, "to": to_tag})
                st.rerun()

    if st.button("🗑 Reset All"):
        st.session_state.equipment = []
        st.session_state.pipelines = []
        st.session_state.inline = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📦 Components")
col1, col2 = st.columns(2)
col1.dataframe(st.session_state.equipment)
col2.dataframe(st.session_state.pipelines)

st.markdown("---")
st.subheader("📊 P&ID Diagram Preview")
layout = render_pid_layout()
if layout:
    st.image(layout)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 Download PNG", export_image(layout), "pid_diagram.png", "image/png", use_container_width=True)
    with col_dl2:
        st.download_button("📥 Download DXF", generate_dxf(), "pid_diagram.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add equipment to begin layout.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())
