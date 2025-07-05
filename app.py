import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from PIL import Image, ImageDraw, ImageFont, ImageFile
import openai
import base64

ImageFile.LOAD_TRUNCATED_IMAGES = True  # Prevent crash from incomplete images

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = "symbols"
os.makedirs(SYMBOLS_DIR, exist_ok=True)

# --- LOAD DATA ---
@st.cache_data
def load_data(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_data("equipment_list.csv")
pipeline_df = load_data("pipeline_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- STATE ---
for key in ["equipment", "pipelines", "inline"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- AUTO TAG ---
def auto_tag(prefix, existing):
    i = 1
    while f"{prefix}-{i:03}" in existing:
        i += 1
    return f"{prefix}-{i:03}"

# --- GENERATE SYMBOL WITH DALL·E ---
def generate_symbol_dalle(component_type, image_filename):
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        prompt = f"Clean 2D ISA-standard black and white P&ID symbol for '{component_type}', line art, no text, no labels, transparent PNG."
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="b64_json"
        )
        image_data = base64.b64decode(response.data[0].b64_json)
        image_path = os.path.join(SYMBOLS_DIR, image_filename)
        with open(image_path, "wb") as f:
            f.write(image_data)
        return image_path
    except Exception as e:
        st.error(f"AI Image error: {e}")
        return None

# --- LOAD SYMBOL (OR GENERATE) ---
def get_symbol(component_type, image_name):
    filepath = os.path.join(SYMBOLS_DIR, image_name)
    if not os.path.exists(filepath):
        generate_symbol_dalle(component_type, image_name)
    try:
        return Image.open(filepath).convert("RGBA").resize((100, 100))
    except Exception as e:
        st.warning(f"Could not load image '{image_name}': {e}")
        return None

# --- RENDER P&ID ---
def render_pid_layout():
    canvas = Image.new("RGBA", (1600, 1000), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    positions = {}
    x = 100
    for comp in st.session_state.equipment:
        positions[comp["tag"]] = (x, 300)
        img = get_symbol(comp["type"], comp["image"])
        if img:
            canvas.paste(img, (x - 50, 250), img)
            draw.text((x, 360), comp["tag"], fill="black", anchor="ms")
        x += 250

    for pipe in st.session_state.pipelines:
        p1 = positions.get(pipe["from"])
        p2 = positions.get(pipe["to"])
        if p1 and p2:
            draw.line([p1, p2], fill="black", width=3)
            draw.polygon([(p2[0]-10, p2[1]-6), (p2[0], p2[1]), (p2[0]-10, p2[1]+6)], fill="black")

    return canvas

# --- EXPORT DXF ---
def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, comp in enumerate(st.session_state.equipment):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+20, 0), (x+20, 20), (x, 20), (x, 0)])
        msp.add_text(comp["tag"], dxfattribs={"height": 2.5}).set_pos((x+10, -5))
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

# --- AI ENGINEER ---
def get_ai_suggestions():
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        summary = ", ".join([f"{e['tag']} ({e['type']})" for e in st.session_state.equipment])
        prompt = f"Suggest 5 improvements for a P&ID with: {summary}."
        response = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.equipment])
        st.text_input("New Tag", value=tag, disabled=True)
        if st.button("Add Equipment"):
            st.session_state.equipment.append({"type": eq_type, "tag": tag, "image": row["Symbol_Image"]})
            st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.equipment) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.equipment])
        to_opts = [e["tag"] for e in st.session_state.equipment if e["tag"] != from_tag]
        to_tag = st.selectbox("To", to_opts)
        pipe_tag = auto_tag("PL", [p["tag"] for p in st.session_state.pipelines])
        st.text_input("Pipeline Tag", value=pipe_tag, disabled=True)
        if st.button("Add Pipeline"):
            st.session_state.pipelines.append({"tag": pipe_tag, "from": from_tag, "to": to_tag})
            st.rerun()

    if st.button("🗑 Reset All", use_container_width=True):
        for k in ["equipment", "pipelines", "inline"]: st.session_state[k] = []
        st.rerun()

# --- MAIN UI ---
st.title("🧠 EPS Interactive P&ID Generator")

st.subheader("📊 Components Overview")
col1, col2 = st.columns(2)
with col1: st.dataframe(st.session_state.equipment, hide_index=True, use_container_width=True)
with col2: st.dataframe(st.session_state.pipelines, hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("🖼️ P&ID Diagram Preview")
layout = render_pid_layout()
if layout:
    st.image(layout)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf = io.BytesIO(); layout.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_layout.png", "image/png")
    with col_dl2:
        dxf = generate_dxf()
        st.download_button("Download DXF", dxf, "pid_layout.dxf", "application/dxf")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Thinking like a senior process engineer..."):
        st.markdown(get_ai_suggestions())
