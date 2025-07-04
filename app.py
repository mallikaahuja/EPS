import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai
import ezdxf
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- SESSION STATE INITIALIZATION ---
if 'equipment' not in st.session_state:
    st.session_state.equipment = []
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []
if 'inline_components' not in st.session_state:
    st.session_state.inline_components = []

# --- PLACEHOLDER IMAGE CREATOR ---
def create_placeholder_image(text, path):
    img = Image.new('RGB', (120, 90), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, 119, 89], outline="black")
    draw.text((10, 35), f"MISSING:\n{text}", fill=(0, 0, 0), font=font)
    img.save(path)
    return str(path)

# --- AI RECOMMENDATION ENGINE ---
def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in environment variables."

    client = openai.OpenAI(api_key=api_key)
    desc = "EQUIPMENT:\n" + "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state.equipment]) + "\n"
    desc += "PIPELINES:\n" + "\n".join([f"- {p['tag']} (from {p['from']} to {p['to']})" for p in st.session_state.pipelines]) + "\n"
    desc += "IN-LINE:\n" + "\n".join([f"- {i['tag']} ({i['type']}) on {i['pipe_tag']}" for i in st.session_state.inline_components])

    try:
        with st.spinner("🔍 Analyzing with AI..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Suggest 3 improvements based on this P&ID:\n\n{desc}"}],
                temperature=0.4,
                max_tokens=300,
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI failed: {e}"

# --- GRAPHVIZ RENDERING ---
def generate_graphviz():
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', labelloc='t', label="Main Process Area", fontsize='16')

    for eq in st.session_state.equipment:
        image_path = SYMBOLS_DIR / f"{eq['type'].replace(' ', '_')}.png"
        if not image_path.exists():
            placeholder = TEMP_DIR / f"{eq['type'].replace(' ', '_')}.png"
            image_path = Path(create_placeholder_image(eq['type'], placeholder))
        dot.node(eq['tag'], label=eq['tag'], image=str(image_path), shape="none", imagepos='tc', labelloc='b')

    for pipe in st.session_state.pipelines:
        inline = [i for i in st.session_state.inline_components if i['pipe_tag'] == pipe['tag']]
        last = pipe['from']
        for comp in inline:
            node_id = f"{comp['tag']}_{pipe['tag']}"
            img_path = SYMBOLS_DIR / f"{comp['type'].replace(' ', '_')}.png"
            if not img_path.exists():
                placeholder = TEMP_DIR / f"{comp['type'].replace(' ', '_')}.png"
                img_path = Path(create_placeholder_image(comp['type'], placeholder))
            dot.node(node_id, label=comp['tag'], image=str(img_path), shape="none", imagepos='tc', labelloc='b')
            dot.edge(last, node_id, label=pipe['tag'])
            last = node_id
        dot.edge(last, pipe['to'], label=pipe['tag'])

    return dot

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

# --- SIDEBAR: COMPONENT ENTRY ---
st.sidebar.title("🧱 Add Components")

with st.sidebar.expander("➕ Add Equipment"):
    eq_tag = st.text_input("Equipment Tag", key="eq_tag")
    eq_type = st.text_input("Equipment Type", key="eq_type")
    if st.button("Add Equipment"):
        if eq_tag and eq_type:
            st.session_state.equipment.append({"tag": eq_tag, "type": eq_type})
            st.rerun()

with st.sidebar.expander("➕ Add Pipeline"):
    if st.session_state.equipment:
        pipe_tag = st.text_input("Pipeline Tag", key="pipe_tag")
        from_eq = st.selectbox("From", [e['tag'] for e in st.session_state.equipment], key="from_tag")
        to_eq = st.selectbox("To", [e['tag'] for e in st.session_state.equipment], key="to_tag")
        if st.button("Add Pipeline"):
            if pipe_tag and from_eq and to_eq:
                st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
                st.rerun()
    else:
        st.info("Please add equipment first.")

with st.sidebar.expander("➕ Add In-Line Component"):
    if st.session_state.pipelines:
        inline_type = st.text_input("Component Type", key="inline_type")
        inline_tag = st.text_input("Component Tag", key="inline_tag")
        pipe_select = st.selectbox("On Pipeline", [p['tag'] for p in st.session_state.pipelines], key="inline_pipe")
        if st.button("Add In-Line"):
            if inline_type and inline_tag and pipe_select:
                st.session_state.inline_components.append({"tag": inline_tag, "type": inline_type, "pipe_tag": pipe_select})
                st.rerun()
    else:
        st.info("Please add a pipeline first.")

if st.sidebar.button("🔄 Reset All"):
    st.session_state.equipment.clear()
    st.session_state.pipelines.clear()
    st.session_state.inline_components.clear()
    st.rerun()

# --- MAIN UI ---
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
    try:
        dot = generate_graphviz()
        st.graphviz_chart(dot)
    except Exception as e:
        st.error(f"Graphviz error: {e}")

st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_suggestions())

st.subheader("⬇️ Export Options")
c1, c2 = st.columns(2)
with c1:
    try:
        png = dot.pipe(format='png')
        st.download_button("Download PNG", png, file_name="p_id.png", mime="image/png")
    except Exception as e:
        st.error(f"PNG export failed: {e}")
with c2:
    try:
        dxf = generate_dxf()
        st.download_button("Download DXF", dxf, file_name="p_id.dxf", mime="application/dxf")
    except Exception as e:
        st.error(f"DXF export failed: {e}")
