import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import io
import ezdxf
import openai
from PIL import Image
import base64

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")

# --- LOAD DATA ---
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# --- SESSION STATE ---
for key in ['equipment', 'pipelines', 'inline_components']:
    if key not in st.session_state:
        st.session_state[key] = []

# --- HELPERS ---
def get_symbol_path(component_type):
    file = SYMBOLS_DIR / f"{component_type.lower().replace(' ', '_')}.png"
    return file if file.exists() else None

def generate_graph():
    dot = Digraph("P&ID")
    dot.attr(rankdir="LR", labelloc="t", label="Main Process Area", fontsize='16')

    for eq in st.session_state.equipment:
        img = get_symbol_path(eq['type'])
        dot.node(eq['tag'], label=eq['tag'], image=str(img) if img else "", shape="box" if not img else "none")

    for pipe in st.session_state.pipelines:
        comps = [c for c in st.session_state.inline_components if c['pipe_tag'] == pipe['tag']]
        from_node = pipe['from']
        for comp in comps:
            comp_node = f"{comp['tag']}_{pipe['tag']}"
            img = get_symbol_path(comp['type'])
            dot.node(comp_node, label=comp['tag'], image=str(img) if img else "", shape="box" if not img else "none")
            dot.edge(from_node, comp_node, label=pipe['tag'])
            from_node = comp_node
        dot.edge(from_node, pipe['to'], label=pipe['tag'])

    return dot

def auto_generate_tag(component_type, df):
    prefix = df[df["Type"] == component_type]["Tag Prefix"].values
    base = prefix[0] if len(prefix) else component_type[:2].upper()
    count = sum(c["type"] == component_type for c in st.session_state.equipment + st.session_state.inline_components + st.session_state.pipelines)
    return f"{base}-{101 + count}"

def get_ai_recommendation():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ Missing OpenAI API key in environment."

    client = openai.OpenAI(api_key=api_key)
    prompt = "Based on this P&ID, suggest improvements:\n\n"
    for eq in st.session_state.equipment:
        prompt += f"Equipment: {eq['tag']} - {eq['type']}\n"
    for p in st.session_state.pipelines:
        prompt += f"Pipeline: {p['tag']} from {p['from']} to {p['to']}\n"
    for c in st.session_state.inline_components:
        prompt += f"In-line: {c['tag']} ({c['type']}) on {c['pipe_tag']}\n"

    try:
        with st.spinner("🧠 Thinking..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ AI failed: {e}"

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0
    for eq in st.session_state.equipment:
        msp.add_circle((0, y), 2)
        msp.add_text(eq['tag'], dxfattribs={'height': 0.5}).set_pos((3, y))
        y -= 10
    stream = io.BytesIO()
    doc.write(stream)
    stream.seek(0)
    return stream

# --- SIDEBAR ---
st.sidebar.header("➕ Add Components")

with st.sidebar.expander("📦 Add Equipment"):
    eq_type = st.selectbox("Type", equipment_df["Type"].tolist(), key="eq_type")
    eq_tag = st.text_input("Tag", value=auto_generate_tag(eq_type, equipment_df), key="eq_tag")
    if st.button("Add Equipment"):
        st.session_state.equipment.append({"tag": eq_tag, "type": eq_type})
        st.rerun()

with st.sidebar.expander("🧵 Add Pipeline"):
    pipe_tag = st.text_input("Tag", key="pipe_tag")
    eq_tags = [e['tag'] for e in st.session_state.equipment]
    from_ = st.selectbox("From", eq_tags, key="from_eq")
    to_ = st.selectbox("To", eq_tags, key="to_eq")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"tag": pipe_tag, "from": from_, "to": to_})
        st.rerun()

with st.sidebar.expander("🔗 Add In-Line Component"):
    in_type = st.selectbox("Type", inline_df["Type"].tolist(), key="in_type")
    in_tag = st.text_input("Tag (In-Line)", value=auto_generate_tag(in_type, inline_df), key="in_tag")
    pipe_options = [p['tag'] for p in st.session_state.pipelines]
    pipe_tag = st.selectbox("On Pipeline", pipe_options, key="pipe_ref")
    if st.button("Add In-Line Component"):
        st.session_state.inline_components.append({"tag": in_tag, "type": in_type, "pipe_tag": pipe_tag})
        st.rerun()

if st.sidebar.button("🔄 Reset All"):
    for key in ['equipment', 'pipelines', 'inline_components']:
        st.session_state[key] = []
    st.rerun()

# --- MAIN INTERFACE ---
st.title("🧠 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)
col1.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True)
col2.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True)
col3.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True)

st.subheader("🛠️ Generated P&ID Preview")
with st.container(height=500, border=True):
    try:
        dot = generate_graph()
        st.graphviz_chart(dot)
    except Exception as e:
        st.error(f"Rendering failed: {e}")

st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_recommendation())

st.subheader("📤 Export Options")
colA, colB = st.columns(2)
with colA:
    try:
        st.download_button("Download PNG", dot.pipe(format='png'), "pid.png", "image/png")
    except Exception as e:
        st.error(f"PNG export failed: {e}")
with colB:
    try:
        dxf_stream = generate_dxf()
        st.download_button("Download DXF", dxf_stream, file_name="pid.dxf", mime="application/dxf")
    except Exception as e:
        st.error(f"DXF export failed: {e}")
