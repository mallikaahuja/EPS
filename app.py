import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io
import ezdxf
import openai

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_PATH = "symbols"

# --- Load CSVs ---
@st.cache_data
def load_csv(file_name):
    return pd.read_csv(file_name)

equipment_df = load_csv("equipment_list.csv")
pipeline_df = load_csv("pipeline_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- Session State ---
if "equipment" not in st.session_state: st.session_state.equipment = []
if "pipelines" not in st.session_state: st.session_state.pipelines = []
if "inline" not in st.session_state: st.session_state.inline = []

# --- Tagging ---
def auto_tag(component_type, prefix):
    count = sum(1 for c in st.session_state.equipment + st.session_state.pipelines + st.session_state.inline if c['type'] == component_type)
    return f"{prefix}-{count+1:03}"

# --- Image Handling ---
def get_component_image(image_name, fallback_text="MISSING"):
    image_path = os.path.join(SYMBOLS_PATH, image_name)
    if os.path.exists(image_path):
        return Image.open(image_path).resize((100, 100))
    else:
        img = Image.new("RGB", (100, 100), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), fallback_text, fill="black")
        return img

# --- Layout Rendering ---
def render_pid_preview():
    canvas = Image.new("RGB", (1200, 300), "white")
    draw = ImageDraw.Draw(canvas)
    x = 50
    spacing = 200

    for comp in st.session_state.equipment:
        img = get_component_image(comp["image"])
        canvas.paste(img, (x, 80))
        draw.text((x+20, 190), comp["tag"], fill="black")
        x += spacing

    st.image(canvas, caption="🖼️ P&ID Diagram Preview (Mockup Layout)", use_column_width=True)

# --- DXF Export ---
def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()

    x = 0
    spacing = 40
    for comp in st.session_state.equipment:
        msp.add_circle((x, 0), radius=5)
        msp.add_text(comp["tag"], dxfattribs={"height": 2.5}).set_pos((x-5, -8))
        x += spacing

    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode()

# --- AI Suggestions ---
def get_ai_suggestions():
    try:
        client = openai.Client(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a process design engineer."},
                {"role": "user", "content": "Suggest 10 ways to improve this P&ID design."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- Sidebar UI ---
st.title("🧠 EPS Interactive P&ID Generator")

# --- Add Equipment ---
st.subheader("➕ Add Equipment")
eq_type = st.selectbox("Equipment Type", equipment_df["type"])
eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
eq_tag = auto_tag(eq_type, eq_row["Tag Prefix"])
if st.button("Add Equipment"):
    st.session_state.equipment.append({
        "type": eq_type,
        "tag": eq_tag,
        "image": eq_row["Symbol_Image"]
    })
    st.rerun()

# --- Add Pipeline ---
st.subheader("➕ Add Pipeline")
if st.session_state.equipment:
    from_opts = [e["tag"] for e in st.session_state.equipment]
    to_opts = [e["tag"] for e in st.session_state.equipment]
    from_eq = st.selectbox("From", from_opts)
    to_eq = st.selectbox("To", to_opts)
    if st.button("Add Pipeline"):
        pipe_tag = auto_tag("Pipeline", "P")
        st.session_state.pipelines.append({
            "tag": pipe_tag,
            "from": from_eq,
            "to": to_eq
        })
        st.rerun()

# --- Add In-Line Component ---
st.subheader("➕ Add In-Line Component")
if st.session_state.pipelines:
    inline_type = st.selectbox("In-line Type", inline_df["type"])
    inline_row = inline_df[inline_df["type"] == inline_type].iloc[0]
    pipe_opts = [p["tag"] for p in st.session_state.pipelines]
    pipe_choice = st.selectbox("On Pipeline", pipe_opts)
    if st.button("Add In-Line Component"):
        inline_tag = auto_tag(inline_type, inline_row["Tag Prefix"])
        st.session_state.inline.append({
            "type": inline_type,
            "tag": inline_tag,
            "pipe_tag": pipe_choice,
            "image": inline_row["Symbol_Image"]
        })
        st.rerun()

# --- Reset Button ---
if st.button("Reset All"):
    st.session_state.equipment = []
    st.session_state.pipelines = []
    st.session_state.inline = []
    st.rerun()

# --- Show Tables ---
st.markdown("### Equipment")
st.dataframe(st.session_state.equipment, use_container_width=True)
st.markdown("### Pipelines")
st.dataframe(st.session_state.pipelines, use_container_width=True)
st.markdown("### In-Line Components")
st.dataframe(st.session_state.inline, use_container_width=True)

# --- Render Layout ---
render_pid_preview()

# --- AI Suggestions ---
st.markdown("### 🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())

# --- Export ---
st.markdown("### 📤 Export P&ID")
col1, col2 = st.columns(2)
with col1:
    png = render_pid_preview()
    st.download_button("Download PNG", data=png, file_name="pid_layout.png", mime="image/png")
with col2:
    dxf_data = generate_dxf()
    st.download_button("Download DXF", data=dxf_data, file_name="pid_layout.dxf", mime="application/dxf")
