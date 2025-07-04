import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from PIL import Image
import ezdxf
import openai
import os
import requests

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide", page_icon="🧠")
openai.api_key = os.getenv("OPENAI_API_KEY")
SYMBOLS_DIR = Path("symbols")
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

# --- STATE ---
if "equipment" not in st.session_state:
    st.session_state.equipment = []
if "pipelines" not in st.session_state:
    st.session_state.pipelines = []
if "inline_components" not in st.session_state:
    st.session_state.inline_components = []

# --- LOAD UPDATED CSVs ---
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# --- SIDEBAR ADD COMPONENTS ---
with st.sidebar:
    st.header("🧱 Add Components")

    with st.expander("➕ Add Equipment", expanded=True):
        eq_type = st.selectbox("Type", equipment_df["Type"].tolist())
        eq_tag_prefix = equipment_df.set_index("Type").loc[eq_type]["Tag Prefix"]
        eq_tag = f"{eq_tag_prefix}-{len(st.session_state.equipment)+101}"
        eq_custom = st.text_input("Tag", value=eq_tag)
        if st.button("Add Equipment"):
            st.session_state.equipment.append({"tag": eq_custom, "type": eq_type})
            st.rerun()

    with st.expander("➕ Add Pipeline"):
        pipe_tag = st.text_input("Tag", value=f"E-{len(st.session_state.pipelines)+1}")
        from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment])
        to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment])
        if st.button("Add Pipeline"):
            st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
            st.rerun()

    with st.expander("➕ Add In-Line Component"):
        inline_type = st.selectbox("Type", inline_df["Type"].tolist())
        inline_tag_prefix = inline_df.set_index("Type").loc[inline_type]["Tag Prefix"]
        inline_tag = f"{inline_tag_prefix}-{len(st.session_state.inline_components)+301}"
        inline_custom = st.text_input("Tag (In-Line)", value=inline_tag)
        if st.button("Add In-Line Component"):
            st.session_state.inline_components.append({"tag": inline_custom, "type": inline_type})
            st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.equipment = []
        st.session_state.pipelines = []
        st.session_state.inline_components = []
        st.rerun()

# --- MAIN UI ---
st.title("🧠 EPS Interactive P&ID Generator")
cols = st.columns(3)

with cols[0]:
    st.markdown("### Equipment")
    st.dataframe(pd.DataFrame(st.session_state.equipment))

with cols[1]:
    st.markdown("### Pipelines")
    st.dataframe(pd.DataFrame(st.session_state.pipelines))

with cols[2]:
    st.markdown("### In-Line Components")
    st.dataframe(pd.DataFrame(st.session_state.inline_components))

st.markdown("### 🛠 Generated P&ID Preview")

def load_image_or_generate(symbol_file, label):
    img_path = SYMBOLS_DIR / symbol_file
    if img_path.exists():
        return Image.open(img_path)
    try:
        response = openai.Image.create(prompt=f"black and white P&ID icon for {label}", n=1, size="256x256")
        image_url = response["data"][0]["url"]
        return Image.open(BytesIO(requests.get(image_url).content))
    except:
        return Image.new("RGB", (200, 100), color="gray")

preview = Image.new("RGB", (1000, 600), "white")
y = 50
for i, comp in enumerate(st.session_state.equipment):
    eq_type = comp["type"]
    symbol_row = equipment_df[equipment_df["Type"] == eq_type]
    symbol_file = symbol_row["Symbol_Image"].values[0] if not symbol_row.empty else None
    img = load_image_or_generate(symbol_file, eq_type)
    preview.paste(img.resize((80, 80)), (50 + i * 150, y))

st.image(preview, caption="🧪 Live Process Preview")

# --- AI ENGINEER SUGGESTIONS ---
st.markdown("### 🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    try:
        prompt = f"Improve this P&ID setup:\nEquipment: {st.session_state.equipment}\nPipelines: {st.session_state.pipelines}"
        result = openai.ChatCompletion.create(model="gpt-4", messages=[
            {"role": "system", "content": "You're a chemical/process engineer."},
            {"role": "user", "content": prompt}
        ])
        st.success(result["choices"][0]["message"]["content"])
    except Exception as e:
        st.error(f"AI failed: {e}")

# --- EXPORT OPTIONS ---
st.markdown("### 📥 Export Options")

col1, col2 = st.columns(2)

with col1:
    if st.button("Download PNG"):
        preview_io = BytesIO()
        preview.save(preview_io, format="PNG")
        st.download_button("Download PNG", preview_io.getvalue(), file_name="p_id.png")

with col2:
    if st.button("Download DXF"):
        try:
            doc = ezdxf.new()
            msp = doc.modelspace()
            x, y = 0, 0
            for eq in st.session_state.equipment:
                msp.add_text(f'{eq["tag"]}: {eq["type"]}', dxfattribs={"height": 0.3}).set_pos((x, y))
                y -= 1
            stream = BytesIO()
            doc.write(stream)
            st.download_button("Download DXF", stream.getvalue(), file_name="p_id.dxf")
        except Exception as e:
            st.error(f"DXF export failed: {e}")
