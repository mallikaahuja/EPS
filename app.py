# EPS Interactive P&ID Generator - Full Updated app.py
import streamlit as st
import pandas as pd
import os
import io
import base64
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFile
import ezdxf

ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="📈")
SYMBOLS_DIR = "symbols_cache"
os.makedirs(SYMBOLS_DIR, exist_ok=True)
FONT = ImageFont.load_default()

# --- API KEYS ---
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")

# --- LOAD CSVs ---
@st.cache_data
def load_data(file): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()
equip_df = load_data("equipment_list.csv")
pipe_df = load_data("pipeline_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- SESSION ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- UTILS ---
def auto_tag(prefix, existing): i = 1; tag = f"{prefix}-{i:03}"
while tag in existing: i += 1; tag = f"{prefix}-{i:03}"
return tag

def generate_stability_symbol(label, image_file):
    prompt = f"Black and white ISA P&ID 2D schematic symbol for {label}, engineering drawing, no color or text"
    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
        json={"prompt": prompt, "mode": "text-to-image", "output_format": "png"}
    )
    if response.status_code == 200:
        with open(image_file, "wb") as f: f.write(response.content)
    else:
        st.warning(f"Image gen failed: Error code {response.status_code} - {response.text}")

def get_symbol_image(image_name, label):
    filepath = os.path.join(SYMBOLS_DIR, image_name)
    if not os.path.exists(filepath): generate_stability_symbol(label, filepath)
    if os.path.exists(filepath):
        try:
            return Image.open(filepath).convert("RGBA").resize((100, 100))
        except Exception as e:
            st.warning(f"Could not load image: {e}")
    return None

# --- DRAW P&ID ---
def render_pid():
    img = Image.new("RGBA", (2000, 1600), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    grid_x, grid_y = 200, 200
    tag_pos = {}

    for i, e in enumerate(st.session_state.components["equipment"]):
        x, y = 100 + (i % 4) * grid_x, 100 + (i // 4) * grid_y
        tag_pos[e["tag"]] = (x, y)
        symbol = get_symbol_image(e["symbol"], e["type"])
        if symbol: img.paste(symbol, (x, y), symbol)
        draw.text((x+50, y+110), e["tag"], fill="black", font=FONT, anchor="ms")

    for p in st.session_state.components["pipelines"]:
        if p["from"] in tag_pos and p["to"] in tag_pos:
            x1, y1 = tag_pos[p["from"]]; x2, y2 = tag_pos[p["to"]]
            x1 += 100; y1 += 50; x2 += 0; y2 += 50
            draw.line([(x1,y1),(x2,y2)], fill="black", width=3)
            draw.polygon([(x2-10,y2-6),(x2,y2),(x2-10,y2+6)], fill="black")
            draw.polygon([(x1+10,y1-6),(x1,y1),(x1+10,y1+6)], fill="black")

    for c in st.session_state.components["inline"]:
        p = next((p for p in st.session_state.components["pipelines"] if p["tag"] == c["pipe_tag"]), None)
        if p and p["from"] in tag_pos and p["to"] in tag_pos:
            x1, y1 = tag_pos[p["from"]]; x2, y2 = tag_pos[p["to"]]
            mx, my = (x1 + x2)//2 + 50, y1 + 40
            sym = get_symbol_image(c["symbol"], c["type"])
            if sym: img.paste(sym, (mx - 50, my), sym)
            draw.text((mx, my + 110), c["tag"], fill="black", font=FONT, anchor="ms")

    # --- LEGEND ---
    draw.rectangle([(1700, 50), (1980, 1400)], outline="black", width=2)
    draw.text((1750, 60), "LEGEND", font=FONT, fill="black")
    y_cursor = 100
    seen = set()
    for t in st.session_state.components["equipment"] + st.session_state.components["inline"]:
        if t["type"] not in seen:
            draw.text((1750, y_cursor), f"• {t['type']}", font=FONT, fill="black")
            seen.add(t["type"]); y_cursor += 30

    return img

# --- DXF EXPORT ---
def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, e in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(e["tag"], dxfattribs={"height": 1.5}).set_pos((x+15, -5))
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

# --- UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equip_df.empty:
        sel = st.selectbox("Type", equip_df["type"].unique())
        row = equip_df[equip_df["type"] == sel].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Tag", value=tag, disabled=True)
        if st.button("Add Equipment"):
            st.session_state.components["equipment"].append({
                "type": sel, "tag": tag,
                "symbol": row["Symbol_Image"]
            }); st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag])
        tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("Add Pipeline"):
            st.session_state.components["pipelines"].append({"from": from_tag, "to": to_tag, "tag": tag})
            st.rerun()

    st.header("Add Inline Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        sel = st.selectbox("Inline Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == sel].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        if st.button("Add Inline"):
            st.session_state.components["inline"].append({
                "type": sel, "tag": tag, "pipe_tag": pipe_tag,
                "symbol": row["Symbol_Image"]
            }); st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}; st.rerun()

# --- MAIN ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Project Components")
col1, col2, col3 = st.columns(3)
with col1: st.dataframe(st.session_state.components["equipment"])
with col2: st.dataframe(st.session_state.components["pipelines"])
with col3: st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🛠 P&ID Preview")
canvas = render_pid()
if canvas:
    st.image(canvas)
    c1, c2 = st.columns(2)
    with c1:
        buf = io.BytesIO(); canvas.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid.png", "image/png")
    with c2:
        st.download_button("Download DXF", generate_dxf(), "pid.dxf", "application/dxf")
