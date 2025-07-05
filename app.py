import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf import const as ezdxf_const
from PIL import Image, ImageDraw, ImageFont
import openai
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

# --- FONT ---
try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    FONT = ImageFont.load_default()

# --- LOAD CSV FILES ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
pipeline_df = load_csv("pipeline_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- UTILS ---
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

def generate_symbol_dalle(type_name, image_name):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found.")
        return
    client = openai.OpenAI(api_key=api_key)
    prompt = f"A technical black-and-white 2D ISA 5.1 P&ID schematic symbol for '{type_name}', in line-art style, transparent background, vector-like clarity. No text, no shading, no gradient."
    try:
        response = client.images.generate(
            model="image-alpha-001",
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="b64_json"
        )
        image_data = base64.b64decode(response.data[0].b64_json)
        path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
        with open(path, "wb") as f:
            f.write(image_data)
    except Exception as e:
        st.error(f"Image generation failed for {type_name}: {e}")

def get_symbol_image(image_name, type_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_symbol_dalle(type_name, image_name)
    try:
        return Image.open(path).convert("RGBA").resize((100, 100))
    except Exception as e:
        st.warning(f"Symbol load failed for {type_name}: {e}")
        return Image.new("RGBA", (100, 100), (255, 255, 255, 0))

# --- DIAGRAM LAYOUT ---
def render_pid_layout():
    canvas = Image.new("RGBA", (2000, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    spacing = 250
    positions = {}

    # Auto-layout equipment in grid
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 100 + (i % 4) * spacing
        y = 100 + (i // 4) * spacing
        positions[eq["tag"]] = (x, y)
        img = get_symbol_image(eq["symbol"], eq["type"])
        canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Pipelines with arrows on both ends
    for pipe in st.session_state.components["pipelines"]:
        a, b = pipe["from"], pipe["to"]
        if a in positions and b in positions:
            x1, y1 = positions[a][0] + 100, positions[a][1] + 50
            x2, y2 = positions[b][0], positions[b][1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # Inline components at midpoint
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if not pipe or pipe["from"] not in positions or pipe["to"] not in positions:
            continue
        x1, y1 = positions[pipe["from"]]
        x2, y2 = positions[pipe["to"]]
        mid_x = (x1 + x2) // 2 + 50
        mid_y = (y1 + y2) // 2 + 50
        img = get_symbol_image(comp["symbol"], comp["type"])
        canvas.paste(img, (mid_x - 50, mid_y - 50), img)
        draw.text((mid_x, mid_y + 60), comp["tag"], fill="black", font=FONT, anchor="ms")

    # Draw right-hand legend
    draw.rectangle([(1700, 60), (1980, 1400)], outline="black", width=2)
    draw.text((1750, 70), "LEGEND", font=FONT, fill="black")
    y = 110
    all_types = sorted(set(e["type"] for e in st.session_state.components["equipment"]) |
                       set(i["type"] for i in st.session_state.components["inline"]))
    for item in all_types:
        draw.text((1750, y), f"• {item}", font=FONT, fill="black")
        y += 25

    return canvas

def export_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(eq["tag"], dxfattribs={"height": 2.0}).set_pos((x + 15, -5), align="TOP_CENTER")
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode("utf-8")

def canvas_to_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

def get_ai_recommendations():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key: return "⚠️ Missing API key."
        client = openai.OpenAI(api_key=api_key)
        summary = ", ".join(f"{e['tag']} ({e['type']})" for e in st.session_state.components["equipment"])
        prompt = f"As a senior process engineer, suggest 5 improvements for this P&ID system: {summary}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔧 P&ID Builder")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("New Tag", tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({
                "type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]
            })
            st.rerun()

    if len(st.session_state.components["equipment"]) >= 2:
        st.markdown("---")
        st.subheader("🔗 Add Pipeline")
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag])
        pipe_tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("➕ Add Pipeline"):
            st.session_state.components["pipelines"].append({
                "tag": pipe_tag, "from": from_tag, "to": to_tag
            })
            st.rerun()

    if st.session_state.components["pipelines"] and not inline_df.empty:
        st.markdown("---")
        st.subheader("🧩 Add Inline Component")
        inline_type = st.selectbox("Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        inline_tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        if st.button("➕ Add Inline"):
            st.session_state.components["inline"].append({
                "type": inline_type, "tag": inline_tag, "pipe_tag": pipe, "symbol": row["Symbol_Image"]
            })
            st.rerun()

    if st.button("🔄 Reset"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN UI ---
st.title("🧠 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)
col1.dataframe(st.session_state.components["equipment"], use_container_width=True)
col2.dataframe(st.session_state.components["pipelines"], use_container_width=True)
col3.dataframe(st.session_state.components["inline"], use_container_width=True)

st.subheader("📊 P&ID Diagram")
image = render_pid_layout()
if image:
    st.image(image)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 PNG Export", canvas_to_bytes(image), "pnid_diagram.png", "image/png")
    with col_dl2:
        st.download_button("📐 DXF Export", export_dxf(), "pnid_diagram.dxf", "application/dxf")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing system..."):
        st.markdown(get_ai_recommendations())
