import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai
import ezdxf
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- INITIALIZE SESSION STATE ---
if 'equipment' not in st.session_state:
    st.session_state.equipment = []
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []
if 'inline_components' not in st.session_state:
    st.session_state.inline_components = []

# --- HELPER FUNCTIONS ---

def create_placeholder_image(text, path):
    try:
        img = Image.new('RGB', (100, 75), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except IOError:
            font = ImageFont.load_default()
        d.rectangle([0, 0, 99, 74], outline="black")
        d.text((10, 30), f"MISSING:\n{text}", fill=(0, 0, 0), font=font)
        img.save(path)
        return str(path)
    except Exception as e:
        st.error(f"Failed to create placeholder image: {e}")
        return None

def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in environment variables."

    client = openai.OpenAI(api_key=api_key)
    description = "EQUIPMENT:\n" + "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state.equipment]) + "\n"
    description += "PIPELINES:\n" + "\n".join([f"- {p['tag']} (from {p['from']} to {p['to']})" for p in st.session_state.pipelines]) + "\n"
    description += "IN-LINE:\n" + "\n".join([f"- {i['tag']} ({i['type']}) on {i['pipe_tag']}" for i in st.session_state.inline_components])

    prompt = (
        "You are a senior process engineer. Based on the following P&ID structure, "
        "recommend 3 safety or operability improvements:\n\n"
        f"{description}"
    )

    try:
        with st.spinner("Analyzing with AI..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=250
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI failed: {e}"

def generate_graphviz():
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', labelloc='t', label="Main Process Area", fontsize='16')

    for eq in st.session_state.equipment:
        img_path = SYMBOLS_DIR / f"{eq['type'].replace(' ', '_')}.png"
        if not img_path.exists():
            placeholder = TEMP_DIR / f"{eq['type'].replace(' ', '_')}.png"
            create_placeholder_image(eq['type'], placeholder)
            img_path = placeholder
        dot.node(eq['tag'], label=eq['tag'], image=str(img_path), shape="none", imagepos='tc', labelloc='b')

    for pipe in st.session_state.pipelines:
        components = [c for c in st.session_state.inline_components if c['pipe_tag'] == pipe['tag']]
        last_node = pipe['from']
        for comp in components:
            comp_id = f"{comp['tag']}_{pipe['tag']}"
            img_path = SYMBOLS_DIR / f"{comp['type'].replace(' ', '_')}.png"
            if not img_path.exists():
                placeholder = TEMP_DIR / f"{comp['type'].replace(' ', '_')}.png"
                create_placeholder_image(comp['type'], placeholder)
                img_path = placeholder
            dot.node(comp_id, label=comp['tag'], image=str(img_path), shape="none", imagepos='tc', labelloc='b')
            dot.edge(last_node, comp_id, label=pipe['tag'])
            last_node = comp_id
        dot.edge(last_node, pipe['to'], label=pipe['tag'])

    return dot

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0
    for eq in st.session_state.equipment:
        msp.add_circle((0, y), 2)
        msp.add_text(eq['tag'], dxfattribs={'height': 0.5}).set_pos((3, y))
        y -= 10
    return doc.encode()

# --- SIDEBAR ENTRY ---
st.sidebar.title("🧱 Add Components")

with st.sidebar.expander("➕ Add Equipment"):
    tag = st.text_input("Equipment Tag", key="eq_tag")
    type_ = st.text_input("Equipment Type", key="eq_type")
    if st.button("Add Equipment"):
        st.session_state.equipment.append({"tag": tag, "type": type_})
        st.experimental_rerun()

with st.sidebar.expander("➕ Add Pipeline"):
    tag = st.text_input("Pipeline Tag", key="pipe_tag")
    from_ = st.selectbox("From Equipment", [e['tag'] for e in st.session_state.equipment], key="from_tag")
    to_ = st.selectbox("To Equipment", [e['tag'] for e in st.session_state.equipment], key="to_tag")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"tag": tag, "from": from_, "to": to_})
        st.experimental_rerun()

with st.sidebar.expander("➕ Add In-Line Component"):
    type_ = st.text_input("Component Type", key="inline_type")
    tag = st.text_input("Component Tag", key="inline_tag")
    pipe_tag = st.selectbox("On Pipeline", [p['tag'] for p in st.session_state.pipelines], key="on_pipe")
    if st.button("Add In-Line"):
        st.session_state.inline_components.append({"tag": tag, "type": type_, "pipe_tag": pipe_tag})
        st.experimental_rerun()

if st.sidebar.button("🔄 Reset All"):
    for key in ['equipment', 'pipelines', 'inline_components']:
        st.session_state[key] = []
    st.experimental_rerun()

# --- MAIN INTERFACE ---
st.title("🧠 EPS Interactive P&ID Generator")

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

st.subheader("🛠️ Generated P&ID Preview")
with st.container(height=600, border=True):
    dot = generate_graphviz()
    st.graphviz_chart(dot)

st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_suggestions())

st.subheader("⬇️ Export Options")
col1, col2 = st.columns(2)
with col1:
    png = dot.pipe(format='png')
    st.download_button("Download PNG", png, file_name="p_id.png", mime="image/png")
with col2:
    dxf = generate_dxf()
    st.download_button("Download DXF", dxf, file_name="p_id.dxf", mime="application/dxf")
