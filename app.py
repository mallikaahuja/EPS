import streamlit as st
import pandas as pd
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import ezdxf
import requests
import uuid

# === CONFIG ===
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

# === FONT ===
try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    FONT = ImageFont.load_default()

# === LOAD CSV ===
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
pipeline_df = load_csv("pipeline_list.csv")
inline_df = load_csv("inline_component_list.csv")

# === STATE ===
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# === HELPERS ===
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

def generate_image_stability(prompt, image_name):
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        st.error("Missing STABILITY_API_KEY in environment.")
        return None
    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "prompt": prompt,
                "output_format": "png",
                "mode": "text-to-image",
                "model": "core",
                "seed": 123,
                "aspect_ratio": "1:1"
            }
        )
        if response.status_code == 200:
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f:
                f.write(response.content)
            return outpath
        else:
            st.warning(f"Stability API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Generation error: {e}")
    return None

def get_symbol_image(type_name, image_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        prompt = f"ISA S5.1 style black-and-white schematic 2D icon for '{type_name}', engineering P&ID symbol, PNG, no text or shadow, transparent background"
        generate_image_stability(prompt, image_name)
    if os.path.exists(path):
        return Image.open(path).convert("RGBA").resize((100, 100))
    return None

def render_pid_diagram():
    canvas = Image.new("RGBA", (2000, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    grid_spacing = 200
    tag_positions = {}

    # Equipment layout
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 100 + (i % 5) * grid_spacing
        y = 100 + (i // 5) * 300
        tag_positions[eq["tag"]] = (x, y)
        img = get_symbol_image(eq["type"], eq["symbol"])
        if img:
            canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Pipelines with bidirectional arrows
    for pipe in st.session_state.components["pipelines"]:
        start = tag_positions.get(pipe["from"])
        end = tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # Inline components
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if not pipe:
            continue
        mid_x = int((tag_positions[pipe["from"]][0] + tag_positions[pipe["to"]][0]) / 2) + 50
        mid_y = tag_positions[pipe["from"]][1] + 30
        img = get_symbol_image(comp["type"], comp["symbol"])
        if img:
            canvas.paste(img, (mid_x - 50, mid_y), img)
        draw.text((mid_x, mid_y + 110), comp["tag"], fill="black", font=FONT, anchor="ms")

    # Legend box
    draw.rectangle([(1700, 50), (1980, 1400)], outline="black", width=2)
    draw.text((1750, 60), "LEGEND", font=FONT, fill="black")
    y_cursor = 100
    all_types = list({e["type"] for e in st.session_state.components["equipment"]} |
                     {i["type"] for i in st.session_state.components["inline"]})
    for t in all_types:
        draw.text((1750, y_cursor), f"• {t}", font=FONT, fill="black")
        y_cursor += 30

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30)], close=True)
        msp.add_text(eq["tag"], dxfattribs={"height": 2.5}).set_location((x + 15, -5))
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

# === SIDEBAR ===
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Generated Tag", value=tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({
                "type": eq_type,
                "tag": tag,
                "symbol": row["Symbol_Image"]
            })
            st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag])
        tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("➕ Add Pipeline"):
            st.session_state.components["pipelines"].append({
                "tag": tag, "from": from_tag, "to": to_tag
            })
            st.rerun()

    st.header("Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("In-line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        if st.button("➕ Add Inline"):
            st.session_state.components["inline"].append({
                "type": inline_type,
                "tag": tag,
                "pipe_tag": pipe_tag,
                "symbol": row["Symbol_Image"]
            })
            st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# === MAIN ===
st.title("🧠 EPS Interactive P&ID Generator")

st.subheader("📋 Component Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.dataframe(st.session_state.components["equipment"])
with col2:
    st.dataframe(st.session_state.components["pipelines"])
with col3:
    st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    buf = io.BytesIO()
    diagram.save(buf, format="PNG")
    st.download_button("Download PNG", buf.getvalue(), "pid.png", "image/png")
    st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf")
