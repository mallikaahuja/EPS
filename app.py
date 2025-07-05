import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf import const as ezdxf_const
from PIL import Image, ImageDraw, ImageFont
import openai
import base64

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

# --- FONT SETUP ---
try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except:
    FONT = ImageFont.load_default()

# --- DATA ---
@st.cache_data
def load_csv(file): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- TAGGING ---
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

# --- DALL·E GENERATION ---
def generate_symbol(type_name, image_name):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("Missing OPENAI_API_KEY.")
        return
    prompt = f"A clean, ISA 5.1 compliant black-and-white 2D engineering P&ID symbol for '{type_name}'. Transparent background. No text or labels."
    try:
        client = openai.OpenAI(api_key=api_key)
        res = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json"
        )
        img_data = base64.b64decode(res.data[0].b64_json)
        with open(os.path.join(SYMBOLS_CACHE_DIR, image_name), "wb") as f:
            f.write(img_data)
    except Exception as e:
        st.error(f"Image generation error: {e}")

# --- IMAGE FETCH ---
def get_image(image_name, type_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_symbol(type_name, image_name)
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA").resize((100, 100))
        except:
            return None
    return None

# --- MAIN DIAGRAM RENDER ---
def render_pid():
    canvas = Image.new("RGBA", (2000, 1400), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    grid_spacing = 220
    tag_pos = {}

    # Equipment placement
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x, y = 120 + (i % 5) * grid_spacing, 150 + (i // 5) * 300
        tag_pos[eq["tag"]] = (x, y)
        img = get_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Pipeline with arrows on both ends
    for pipe in st.session_state.components["pipelines"]:
        start = tag_pos.get(pipe["from"])
        end = tag_pos.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # Inline component midpoints
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if not pipe: continue
        start = tag_pos.get(pipe["from"])
        end = tag_pos.get(pipe["to"])
        if start and end:
            mid_x = int((start[0] + end[0]) / 2) + 50
            mid_y = start[1] + 30
            img = get_image(comp["symbol"], comp["type"])
            if img:
                canvas.paste(img, (mid_x - 50, mid_y), img)
            draw.text((mid_x, mid_y + 110), comp["tag"], fill="black", font=FONT, anchor="ms")

    # Legend box
    draw.rectangle([(1700, 50), (1980, 1300)], outline="black", width=2)
    draw.text((1750, 60), "LEGEND", font=FONT, fill="black")
    y_pos = 100
    all_types = list({e["type"] for e in st.session_state.components["equipment"]} | {i["type"] for i in st.session_state.components["inline"]})
    for t in all_types:
        draw.text((1750, y_pos), f"• {t}", font=FONT, fill="black")
        y_pos += 30

    return canvas

# --- DXF ---
def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(eq["tag"], dxfattribs={"height": 1.5}).set_placement((x+15, -5))
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode("utf-8")

# --- AI SUGGESTIONS ---
def get_ai_notes():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key: return "❌ Missing OpenAI Key"
        client = openai.OpenAI(api_key=api_key)
        summary = ", ".join([f"{e['tag']} ({e['type']})" for e in st.session_state.components["equipment"]])
        prompt = f"Suggest 5 engineering or safety improvements for this P&ID: {summary}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("➕ Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Generated Tag", value=tag, disabled=True)
        if st.button("Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    st.header("🔗 Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag])
        tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("Add Pipeline"):
            st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
            st.rerun()

    st.header("🔧 Add Inline Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("Inline Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        if st.button("Add Inline"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Component Summary")
c1, c2, c3 = st.columns(3)
with c1: st.dataframe(st.session_state.components["equipment"])
with c2: st.dataframe(st.session_state.components["pipelines"])
with c3: st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("📊 P&ID Diagram")
image = render_pid()
if image:
    st.image(image)
    col1, col2 = st.columns(2)
    with col1:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_diagram.png", "image/png")
    with col2:
        st.download_button("Download DXF", generate_dxf(), "pid_diagram.dxf", "application/dxf")

st.markdown("---")
st.subheader("🤖 AI Engineering Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_notes())
