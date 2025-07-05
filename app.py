import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from PIL import Image, ImageDraw, ImageFont
import base64
import requests

# CONFIG
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "sk-jovim5KFgN8dOBmZ67Gt8vvGAYHm40y8CMoeV2DzQmxjp9hn")
STABILITY_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    FONT = ImageFont.load_default()

# LOAD CSV
@st.cache_data
def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

def generate_symbol_stability(type_name, image_name):
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    prompt = f"Monochrome ISA S5.1 compliant P&ID symbol for '{type_name}', black-and-white vector style, schematic, no labels, transparent background"
    data = {
        "prompt": prompt,
        "output_format": "png",
        "model": "stable-image-core",
    }
    try:
        response = requests.post(STABILITY_URL, headers=headers, json=data)
        if response.ok:
            with open(os.path.join(SYMBOLS_CACHE_DIR, image_name), "wb") as f:
                f.write(response.content)
        else:
            st.warning(f"Stability API Error: {response.status_code}")
    except Exception as e:
        st.warning(f"Stability API failed: {e}")

def get_symbol_image(image_name, type_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_symbol_stability(type_name, image_name)
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA").resize((100, 100))
        except Exception as e:
            st.warning(f"Image broken for {type_name}: {e}")
            return None
    return None

def render_pid_diagram():
    canvas = Image.new("RGBA", (2000, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    tag_positions = {}
    grid_spacing = 200

    # Draw equipment
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 100 + (i % 5) * grid_spacing
        y = 150 + (i // 5) * 300
        tag_positions[eq["tag"]] = (x, y)
        img = get_symbol_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Draw pipelines
    for pipe in st.session_state.components["pipelines"]:
        start = tag_positions.get(pipe["from"])
        end = tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # Draw inline components
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if pipe:
            mid_x = (tag_positions[pipe["from"]][0] + tag_positions[pipe["to"]][0]) // 2 + 50
            mid_y = tag_positions[pipe["from"]][1] + 30
            img = get_symbol_image(comp["symbol"], comp["type"])
            if img:
                canvas.paste(img, (mid_x - 50, mid_y), img)
            draw.text((mid_x, mid_y + 110), comp["tag"], fill="black", font=FONT, anchor="ms")

    # Dynamic legend
    draw.rectangle([(1700, 50), (1980, 1400)], outline="black", width=2)
    draw.text((1750, 60), "LEGEND", font=FONT, fill="black")
    y_cursor = 100
    types = list({e["type"] for e in st.session_state.components["equipment"]} |
                 {i["type"] for i in st.session_state.components["inline"]})
    for t in types:
        draw.text((1750, y_cursor), f"• {t}", font=FONT, fill="black")
        y_cursor += 30

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(eq["tag"], dxfattribs={"height": 1.5}).set_pos((x + 15, -5), align="TOP_CENTER")
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

# SIDEBAR
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Tag", value=tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag])
        tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("➕ Add Pipeline"):
            st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
            st.rerun()

    st.header("Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("In-line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        if st.button("➕ Add Inline"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# MAIN
st.title("🧠 EPS Interactive P&ID Generator")
col1, col2, col3 = st.columns(3)
with col1: st.dataframe(st.session_state.components["equipment"])
with col2: st.dataframe(st.session_state.components["pipelines"])
with col3: st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    b1, b2 = st.columns(2)
    with b1:
        buf = io.BytesIO()
        diagram.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_diagram.png", "image/png")
    with b2:
        st.download_button("Download DXF", generate_dxf_file(), "pid_diagram.dxf", "application/dxf")
