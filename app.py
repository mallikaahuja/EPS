import streamlit as st
import pandas as pd
import os
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import ezdxf
import openai

# ---------- SETUP ----------
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")

# File paths
EQUIPMENT_CSV = "equipment_list.csv"
PIPELINE_CSV = "pipeline_list.csv"
INLINE_CSV = "inline_component_list.csv"
SYMBOLS_FOLDER = "symbols"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------- HELPERS ----------
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to load {path}: {e}")
        return pd.DataFrame()

def generate_tag(prefix, existing_tags):
    i = 1
    while True:
        tag = f"{prefix}-{i:03}"
        if tag not in existing_tags:
            return tag
        i += 1

def get_symbol_image(symbol_name):
    path = os.path.join(SYMBOLS_FOLDER, symbol_name)
    if os.path.exists(path):
        return Image.open(path)
    return None

def draw_missing_symbol(label):
    img = Image.new("RGB", (120, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (119, 99)], outline="black")
    draw.text((10, 40), f"MISSING\n{label}", fill="black")
    return img

def get_ai_symbol_image(component_type):
    try:
        if not OPENAI_API_KEY:
            return draw_missing_symbol(component_type)
        response = openai.Image.create(
            prompt=f"Simple black & white technical PNG icon for a '{component_type}' in P&ID diagram, no background.",
            n=1,
            size="128x128"
        )
        image_url = response["data"][0]["url"]
        image_data = requests.get(image_url).content
        return Image.open(io.BytesIO(image_data))
    except Exception:
        return draw_missing_symbol(component_type)

def render_symbol_preview(component_type, image_name):
    img = get_symbol_image(image_name)
    if img:
        st.image(img, caption=component_type, width=100)
    else:
        fallback_img = get_ai_symbol_image(component_type)
        st.image(fallback_img, caption=f"{component_type} (AI/Fallback)", width=100)

def export_png(canvas_items):
    width, height = 900, 300
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    x, y = 50, 150
    spacing = 150

    for item in canvas_items:
        symbol_img = get_symbol_image(item["image"])
        if symbol_img:
            img.paste(symbol_img.resize((80, 80)), (x, y - 40))
        else:
            draw.rectangle([x, y - 40, x + 80, y + 40], outline="black")
            draw.text((x + 5, y - 10), f"MISSING\n{item['type']}", fill="black")
        draw.text((x + 10, y + 50), item["tag"], fill="black")
        x += spacing

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_dxf(equipment, pipelines, inline_components):
    doc = ezdxf.new()
    msp = doc.modelspace()

    x, y = 0, 0
    spacing = 30
    tag_positions = {}

    for eq in equipment:
        tag = eq["tag"]
        msp.add_lwpolyline([(x, y), (x + 10, y)], dxfattribs={"layer": "Equipment"})
        msp.add_text(tag, dxfattribs={"height": 2.5}).set_pos((x, y - 5))
        tag_positions[tag] = (x + 5, y)
        x += spacing

    for pipe in pipelines:
        from_tag = pipe["from"]
        to_tag = pipe["to"]
        if from_tag in tag_positions and to_tag in tag_positions:
            x1, y1 = tag_positions[from_tag]
            x2, y2 = tag_positions[to_tag]
            msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "Pipelines"})
            mid_x = (x1 + x2) / 2
            msp.add_text(pipe["tag"], dxfattribs={"height": 2.5}).set_pos((mid_x, y1 + 5))

    for item in inline_components:
        tag = item["tag"]
        msp.add_circle((x, y), radius=1.5, dxfattribs={"layer": "Inline"})
        msp.add_text(tag, dxfattribs={"height": 2.5}).set_pos((x, y - 5))
        x += spacing

    buffer = io.StringIO()
    doc.write(buffer)
    buffer.seek(0)
    return buffer

# ---------- SESSION INIT ----------
for key in ["equipment", "pipelines", "inline"]:
    if key not in st.session_state:
        st.session_state[key] = []

# ---------- UI ----------
st.title("🧠 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)

# Load CSVs
equipment_df = load_csv(EQUIPMENT_CSV)
pipeline_df = load_csv(PIPELINE_CSV)
inline_df = load_csv(INLINE_CSV)

# --- Equipment ---
with col1:
    st.subheader("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["Type"])
        symbol_img = equipment_df[equipment_df["Type"] == eq_type]["Symbol_Image"].values[0]
        prefix = equipment_df[equipment_df["Type"] == eq_type]["Tag Prefix"].values[0]
        eq_tag = generate_tag(prefix, [e["tag"] for e in st.session_state.equipment])
        if st.button("Add Equipment"):
            st.session_state.equipment.append({"type": eq_type, "tag": eq_tag, "image": symbol_img})

# --- Pipeline ---
with col2:
    st.subheader("Add Pipeline")
    pipe_tag = generate_tag("P", [p["tag"] for p in st.session_state.pipelines])
    from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment], key="from_pipe")
    to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], key="to_pipe")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})

# --- Inline ---
with col3:
    st.subheader("Add In-Line Component")
    if not inline_df.empty:
        in_type = st.selectbox("In-line Type", inline_df["Type"])
        in_img = inline_df[inline_df["Type"] == in_type]["Symbol_Image"].values[0]
        prefix = inline_df[inline_df["Type"] == in_type]["Tag Prefix"].values[0]
        in_tag = generate_tag(prefix, [i["tag"] for i in st.session_state.inline])
        pipe_choices = [p["tag"] for p in st.session_state.pipelines]
        selected_pipe = st.selectbox("On Pipeline", pipe_choices) if pipe_choices else ""
        if st.button("Add In-Line Component"):
            st.session_state.inline.append({
                "type": in_type, "tag": in_tag, "pipe_tag": selected_pipe, "image": in_img
            })

# ---------- DISPLAY TABLES ----------
st.subheader("📊 Equipment")
st.table(pd.DataFrame(st.session_state.equipment))

st.subheader("📊 Pipelines")
st.table(pd.DataFrame(st.session_state.pipelines))

st.subheader("📊 In-Line Components")
st.table(pd.DataFrame(st.session_state.inline))

# ---------- PREVIEW ----------
st.subheader("🖼️ P&ID Diagram Preview (Mockup Layout)")
st.markdown("📍 Showing component layout with actual PNGs or fallback images")
for comp in st.session_state.equipment:
    render_symbol_preview(comp["type"], comp["image"])

# ---------- EXPORT ----------
st.subheader("📤 Export P&ID")
if st.button("Download PNG"):
    buf = export_png(st.session_state.equipment)
    st.download_button("Download PNG", buf, file_name="pid_diagram.png")

if st.button("Download DXF"):
    dxf_buf = generate_dxf(st.session_state.equipment, st.session_state.pipelines, st.session_state.inline)
    st.download_button("Download DXF", dxf_buf, file_name="pid_diagram.dxf")

# ---------- AI SUGGESTIONS ----------
st.subheader("🤖 AI Engineer Suggestions")
def get_ai_suggestions():
    try:
        if not OPENAI_API_KEY:
            return "Missing API key. Please set OPENAI_API_KEY in environment."
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're an expert process engineer. Suggest improvements."},
                {"role": "user", "content": f"Here are the components: {st.session_state.equipment}"}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI failed: {e}"

if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())
