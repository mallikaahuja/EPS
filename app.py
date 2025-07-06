import streamlit as st
import pandas as pd
import os
import io
import base64
import requests
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf.addons.drawing import matplotlib as draw_mpl
from io import BytesIO

# CONFIG
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

# Get API key from secrets or environment
STABILITY_API_KEY = st.secrets.get("STABILITY_API_KEY") or os.getenv("STABILITY_API_KEY")
if not STABILITY_API_KEY:
    st.error("❌ Missing Stability API Key. Set STABILITY_API_KEY in secrets.toml or environment variables.")
    st.stop()

# Font setup
try:
    FONT = ImageFont.truetype("arial.ttf", 14)
except:
    try:
        FONT = ImageFont.truetype("DejaVuSans.ttf", 14)
    except:
        FONT = ImageFont.load_default()

# LOAD DATA
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

# STATE INIT
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# TAGGING
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

# Create fallback symbols for missing images
def create_fallback_symbol(text):
    img = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5, 5, 95, 95], outline="black", width=2)
    draw.text((50, 50), text, fill="black", font=FONT, anchor="mm")
    return img

# STABILITY IMAGE GEN
def generate_symbol_stability(type_name, image_name):
    if not STABILITY_API_KEY:
        return False
        
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}"}
    payload = {
        "prompt": f"Technical schematic symbol for {type_name}, isometric, clean lines, no background",
        "output_format": "png",
        "height": 512,
        "width": 512
    }
    
    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers=headers,
            files={"none": ''},
            data=payload,
            timeout=30
        )
        response.raise_for_status()
        
        path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
        with open(path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        st.warning(f"Symbol generation failed: {str(e)}")
        return False

# GET IMAGE
def get_image(image_name, type_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    
    if not os.path.exists(path):
        if not generate_symbol_stability(type_name, image_name):
            return create_fallback_symbol(type_name[:3].upper())
    
    try:
        img = Image.open(path)
        return img.convert("RGBA").resize((100, 100))
    except Exception:
        return create_fallback_symbol(type_name[:3].upper())

# DRAW DIAGRAM
def render_pid_diagram():
    canvas = Image.new("RGBA", (2000, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    tag_positions = {}
    grid_spacing = 250

    # EQUIPMENT
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 100 + (i % 5) * grid_spacing
        y = 150 + (i // 5) * 300
        tag_positions[eq["tag"]] = (x, y)
        img = get_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # PIPELINES
    for pipe in st.session_state.components["pipelines"]:
        start = tag_positions.get(pipe["from"])
        end = tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # INLINE
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if pipe and pipe["from"] in tag_positions and pipe["to"] in tag_positions:
            mid_x = int((tag_positions[pipe["from"]][0] + tag_positions[pipe["to"]][0]) / 2) + 50
            mid_y = tag_positions[pipe["from"]][1] + 30
            img = get_image(comp["symbol"], comp["type"])
            if img:
                canvas.paste(img, (mid_x - 50, mid_y), img)
            draw.text((mid_x, mid_y + 110), comp["tag"], fill="black", font=FONT, anchor="ms")

    # LEGEND
    draw.rectangle([(1700, 50), (1980, 1450)], outline="black", width=2)
    draw.text((1750, 60), "LEGEND", font=FONT, fill="black")
    y_cursor = 100
    all_types = list({e["type"] for e in st.session_state.components["equipment"]} |
                     {i["type"] for i in st.session_state.components["inline"]})
    for t in all_types:
        draw.text((1750, y_cursor), f"• {t}", font=FONT, fill="black")
        y_cursor += 30

    return canvas

# DXF EXPORT
def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    y_pos = 0
    
    # Add equipment
    for eq in st.session_state.components["equipment"]:
        points = [(0, y_pos), (50, y_pos), (50, y_pos+10), (0, y_pos+10), (0, y_pos)]
        msp.add_lwpolyline(points)
        msp.add_text(eq["tag"], dxfattribs={"height": 2.5}).set_pos((0, y_pos-3))
        y_pos += 15
        
    # Add pipelines
    y_pos += 10
    for pipe in st.session_state.components["pipelines"]:
        msp.add_text(f"{pipe['tag']}: {pipe['from']} → {pipe['to']}", 
                    dxfattribs={"height": 2.0}).set_pos((0, y_pos))
        y_pos += 7
        
    # Add inline components
    y_pos += 5
    for comp in st.session_state.components["inline"]:
        msp.add_text(f"{comp['tag']} ({comp['type']}) on {comp['pipe_tag']}", 
                    dxfattribs={"height": 1.8}).set_pos((0, y_pos))
        y_pos += 5
        
    buffer = BytesIO()
    doc.saveas(buffer)
    return buffer.getvalue()

# API status check
try:
    response = requests.get(
        "https://api.stability.ai/v2beta/balance",
        headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
        timeout=5
    )
    if response.status_code == 200:
        st.sidebar.success("✅ Stability API Connected")
    else:
        st.sidebar.warning(f"⚠️ API Issues: {response.status_code}")
except Exception as e:
    st.sidebar.error(f"❌ API Connection Failed: {str(e)}")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Generated Tag", value=tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        to_tag = st.selectbox("To", to_opts)
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
st.subheader("📋 Component Summary")
col1, col2, col3 = st.columns(3)
with col1: 
    st.write("**Equipment**")
    st.dataframe(st.session_state.components["equipment"] or pd.DataFrame(), hide_index=True)
with col2: 
    st.write("**Pipelines**")
    st.dataframe(st.session_state.components["pipelines"] or pd.DataFrame(), hide_index=True)
with col3: 
    st.write("**Inline Components**")
    st.dataframe(st.session_state.components["inline"] or pd.DataFrame(), hide_index=True)

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    c1, c2 = st.columns(2)
    with c1:
        buf = BytesIO()
        diagram.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid.png", "image/png")
    with c2:
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf")
