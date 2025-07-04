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

# --- SESSION STATE ---
for key in ['equipment', 'pipelines', 'inline_components']:
    if key not in st.session_state:
        st.session_state[key] = []

# --- HELPER FUNCTIONS ---

def create_placeholder_image(text, path):
    img = Image.new('RGB', (100, 75), color='white')
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except IOError:
        font = ImageFont.load_default()
    d.rectangle([0, 0, 99, 74], outline="black")
    d.text((10, 30), f"{text}", fill="black", font=font)
    img.save(path)

def generate_graphviz():
    dot = Digraph('P&ID', format='png')
    dot.attr(rankdir='LR', splines='ortho', labelloc='t', label="Main Process Area", fontsize='16')

    for eq in st.session_state.equipment:
        img_path = SYMBOLS_DIR / f"{eq['type'].replace(' ', '_')}.png"
        if not img_path.exists():
            img_path = TEMP_DIR / f"{eq['type'].replace(' ', '_')}.png"
            create_placeholder_image(eq['type'], img_path)
        dot.node(eq['tag'], label=eq['tag'], image=str(img_path), shape='none', imagepos='tc', labelloc='b')

    for pipe in st.session_state.pipelines:
        last = pipe['from']
        for comp in [c for c in st.session_state.inline_components if c['pipe_tag'] == pipe['tag']]:
            comp_id = f"{comp['tag']}_{pipe['tag']}"
            img_path = SYMBOLS_DIR / f"{comp['type'].replace(' ', '_')}.png"
            if not img_path.exists():
                img_path = TEMP_DIR / f"{comp['type'].replace(' ', '_')}.png"
                create_placeholder_image(comp['type'], img_path)
            dot.node(comp_id, label=comp['tag'], image=str(img_path), shape="none", imagepos="tc", labelloc="b")
            dot.edge(last, comp_id, label=pipe['tag'])
            last = comp_id
        dot.edge(last, pipe['to'], label=pipe['tag'])
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

def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in environment variables."

    client = openai.OpenAI(api_key=api_key)
    description = (
        "EQUIPMENT:\n" + "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state.equipment]) + "\n"
        "PIPELINES:\n" + "\n".join([f"- {p['tag']} (from {p['from']} to {p['to']})" for p in st.session_state.pipelines]) + "\n"
        "IN-LINE:\n" + "\n".join([f"- {i['tag']} ({i['type']}) on {i['pipe_tag']}" for i in st.session_state.inline_components])
    )

    prompt = f"You are a senior process engineer. Suggest 3 improvements:\n\n{description}"

    try:
        with st.spinner("Analyzing with AI..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250
            )
        return res.choices[0].message.content
    except Exception as e:
        return f"AI failed: {e}"

# --- SIDEBAR UI ---
st.sidebar.title("🧱 Add Components")

with st.sidebar.expander("➕ Add Equipment"):
    tag = st.text_input("Equipment Tag", key="eq_tag")
    type_ = st.text_input("Equipment Type", key="eq_type")
    if st.button("Add Equipment"):
        if tag and type_:
            st.session_state.equipment.append({"tag": tag, "type": type_})
            st.rerun()

with st.sidebar.expander("➕ Add Pipeline"):
    tag = st.text_input("Pipeline Tag", key="pipe_tag")
    from_ = st.selectbox("From Equipment", [e['tag'] for e in st.session_state.equipment], key="from_tag")
    to_ = st.selectbox("To Equipment", [e['tag'] for e in st.session_state.equipment], key="to_tag")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"tag": tag, "from": from_, "to": to_})
        st.rerun()

with st.sidebar.expander("➕ Add In-Line Component"):
    type_ = st.text_input("Component Type", key="inline_type")
    tag = st.text_input("Component Tag", key="inline_tag")
    pipe_tag = st.selectbox("On Pipeline", [p['tag'] for p in st.session_state.pipelines], key="on_pipe")
    if st.button("Add In-Line"):
        st.session_state.inline_components.append({"tag": tag, "type": type_, "pipe_tag": pipe_tag})
        st.rerun()

if st.sidebar.button("🔄 Reset All"):
    for k in ['equipment', 'pipelines', 'inline_components']:
        st.session_state[k] = []
    st.rerun()

# --- MAIN ---
st.title("🧠 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)
col1.subheader("Equipment")
col1.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True)

col2.subheader("Pipelines")
col2.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True)

col3.subheader("In-Line Components")
col3.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True)

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
    st.download_button("Download PNG", dot.pipe(format='png'), file_name="p_id.png", mime="image/png")
with col2:
    st.download_button("Download DXF", generate_dxf(), file_name="p_id.dxf", mime="application/dxf")
