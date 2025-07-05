import streamlit as st
import pandas as pd
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import ezdxf
import openai
import base64

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- SESSION STATE ---
for key in ["equipment", "pipelines", "inline_components"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- CSV DATA LOAD ---
@st.cache_data
def load_component_data():
    try:
        eq = pd.read_csv("equipment_list.csv")
        pl = pd.read_csv("pipeline_list.csv")
        il = pd.read_csv("inline_component_list.csv")
        return eq, pl, il
    except Exception as e:
        st.error(f"Failed to load dropdown CSVs: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

equipment_data, pipeline_data, inline_data = load_component_data()

# --- IMAGE HANDLING ---
def get_symbol_image_path(symbol_name):
    img_path = SYMBOLS_DIR / f"{symbol_name}.png"
    if img_path.exists():
        return str(img_path)
    return create_missing_image(symbol_name)

def create_missing_image(text):
    path = TEMP_DIR / f"{text}.png"
    if path.exists():
        return str(path)
    img = Image.new('RGB', (100, 75), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.rectangle([0, 0, 99, 74], outline="black")
    draw.text((5, 30), f"MISSING\n{text}", fill="black", font=font)
    img.save(path)
    return str(path)

# --- AUTO-TAGGING ---
def auto_tag(prefix, existing):
    i = 1
    while True:
        tag = f"{prefix}-{str(i).zfill(3)}"
        if not any(item['tag'] == tag for item in existing):
            return tag
        i += 1

# --- UI ---
st.title("🧠 EPS Interactive P&ID Generator")

with st.sidebar:
    st.header("➕ Add Equipment")
    eq_type = st.selectbox("Equipment Type", equipment_data["type"] if not equipment_data.empty else [])
    if st.button("Add Equipment"):
        tag = auto_tag("EQ", st.session_state.equipment)
        st.session_state.equipment.append({"tag": tag, "type": eq_type})
        st.rerun()

    st.header("➕ Add Pipeline")
    from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.equipment], key="from_eq")
    to_tag = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], key="to_eq")
    pipe_tag = auto_tag("P", st.session_state.pipelines)
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"tag": pipe_tag, "from": from_tag, "to": to_tag})
        st.rerun()

    st.header("➕ Add In-Line Component")
    inline_type = st.selectbox("In-line Type", inline_data["type"] if not inline_data.empty else [])
    pipe = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines])
    inline_tag = auto_tag("C", st.session_state.inline_components)
    if st.button("Add In-Line"):
        st.session_state.inline_components.append({
            "tag": inline_tag, "type": inline_type, "pipe_tag": pipe
        })
        st.rerun()

    if st.button("🔄 Reset All"):
        for key in ["equipment", "pipelines", "inline_components"]:
            st.session_state[key] = []
        st.rerun()

# --- DISPLAY TABLES ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Equipment")
    st.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True)
with col2:
    st.subheader("Pipelines")
    st.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True)
with col3:
    st.subheader("In-Line Components")
    st.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True)

# --- VISUAL PREVIEW ---
st.subheader("🖼️ P&ID Diagram Preview (Mockup Layout)")
preview = st.container(border=True)

with preview:
    for eq in st.session_state.equipment:
        img_path = get_symbol_image_path(eq['type'].replace(" ", "_"))
        st.image(img_path, width=100, caption=eq['tag'])

# --- AI SUGGESTIONS ---
st.subheader("🤖 AI Engineer Suggestions")

def get_ai_suggestions():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return "⚠️ OpenAI API key not found."
    client = openai.OpenAI(api_key=key)
    description = "EQUIPMENT:\n" + "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state.equipment])
    description += "\nPIPELINES:\n" + "\n".join([f"- {p['tag']} (from {p['from']} to {p['to']})" for p in st.session_state.pipelines])
    description += "\nINLINE:\n" + "\n".join([f"- {c['tag']} ({c['type']}) on {c['pipe_tag']}" for c in st.session_state.inline_components])
    prompt = f"You are a senior P&ID engineer. Review and recommend 3 improvements:\n{description}"
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Error from OpenAI: {e}"

if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())

# --- DXF EXPORT ---
def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0
    for eq in st.session_state.equipment:
        msp.add_circle((0, y), 2)
        msp.add_text(eq['tag'], dxfattribs={'height': 0.5}).set_pos((3, y))
        y -= 10
    return doc.encode()

# --- EXPORTS ---
st.subheader("⬇️ Export P&ID")
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    try:
        dummy = Image.new('RGB', (300, 100), (255, 255, 255))
        buffer = Path("preview_export.png")
        dummy.save(buffer)
        with open(buffer, "rb") as f:
            st.download_button("Download PNG", f.read(), "p_id.png", mime="image/png")
    except Exception as e:
        st.error(f"PNG Export failed: {e}")

with col_exp2:
    try:
        dxf = generate_dxf()
        st.download_button("Download DXF", dxf, "p_id.dxf", mime="application/dxf")
    except Exception as e:
        st.error(f"DXF Export failed: {e}")
