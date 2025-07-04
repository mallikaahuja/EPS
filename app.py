import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import base64
import io
import ezdxf
from openai import OpenAI

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = Path("symbols")
client = OpenAI()

# --- LOAD COMPONENT DATA ---
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# --- SESSION STATE SETUP ---
if "equipment" not in st.session_state: st.session_state.equipment = []
if "pipelines" not in st.session_state: st.session_state.pipelines = []
if "inline" not in st.session_state: st.session_state.inline = []

# --- UI HEADER ---
st.title("🧠 EPS Interactive P&ID Generator")

# --- COMPONENT ADDERS ---
with st.sidebar:
    st.subheader("➕ Add Equipment")
    selected_eq_type = st.selectbox("Type", equipment_df["Type"])
    eq_tag = st.text_input("Tag", key="eq_tag")
    if st.button("Add Equipment"):
        symbol = equipment_df[equipment_df["Type"] == selected_eq_type]["Symbol_Image"].values[0]
        st.session_state.equipment.append({
            "tag": eq_tag,
            "type": selected_eq_type,
            "symbol": symbol
        })
        st.rerun()

    st.subheader("➕ Add Pipeline")
    pipe_tag = st.text_input("Tag", key="pipe_tag")
    from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment], key="from_eq")
    to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], key="to_eq")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({
            "tag": pipe_tag,
            "from": from_eq,
            "to": to_eq
        })
        st.rerun()

    st.subheader("➕ Add In-Line Component")
    selected_inline_type = st.selectbox("Type", inline_df["Type"])
    inline_tag = st.text_input("Tag (In-Line)", key="inline_tag")
    if st.button("Add In-Line Component"):
        symbol = inline_df[inline_df["Type"] == selected_inline_type]["Symbol_Image"].values[0]
        st.session_state.inline.append({
            "tag": inline_tag,
            "type": selected_inline_type,
            "symbol": symbol
        })
        st.rerun()

    if st.button("🔁 Reset All"):
        st.session_state.equipment = []
        st.session_state.pipelines = []
        st.session_state.inline = []
        st.rerun()

# --- TABLE DISPLAY ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Equipment")
    st.table(pd.DataFrame(st.session_state.equipment))
with col2:
    st.subheader("Pipelines")
    st.table(pd.DataFrame(st.session_state.pipelines))
with col3:
    st.subheader("In-Line Components")
    st.table(pd.DataFrame(st.session_state.inline))

# --- VISUAL PREVIEW ---
st.markdown("### 🛠 Generated P&ID Preview")
preview_area = st.empty()
with preview_area:
    cols = st.columns(len(st.session_state.equipment))
    for idx, eq in enumerate(st.session_state.equipment):
        image_path = SYMBOLS_DIR / eq["symbol"]
        if image_path.exists():
            cols[idx].image(Image.open(image_path), caption=eq["tag"])
        else:
            cols[idx].markdown(f"❌ {eq['symbol']} not found")

# --- AI Suggestions ---
st.markdown("### 🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful process engineer."},
                {"role": "user", "content": f"Suggest improvements for this P&ID: {st.session_state.equipment}, {st.session_state.pipelines}, {st.session_state.inline}"}
            ]
        )
        st.success(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI failed: {e}")

# --- EXPORT OPTIONS ---
st.markdown("### 📤 Export Options")

def generate_png():
    img = Image.new("RGB", (500, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button("Download PNG", buf.getvalue(), file_name="pnid.png")

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    x = 10
    for comp in st.session_state.equipment:
        msp.add_text(comp["tag"]).set_pos((x, 10))
        x += 30
    buf = io.BytesIO()
    doc.write(buf)
    st.download_button("Download DXF", buf.getvalue(), file_name="pnid.dxf")

generate_png()
generate_dxf()
