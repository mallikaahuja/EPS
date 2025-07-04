import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import ezdxf
from PIL import Image, ImageDraw, ImageFont
import openai
import io

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- INIT STATE ---
for key in ['equipment', 'pipelines', 'inline_components']:
    if key not in st.session_state:
        st.session_state[key] = []

# --- HELPERS ---
def create_placeholder_image(label, path):
    img = Image.new('RGB', (100, 75), color=(230, 240, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, 99, 74], outline="black")
    draw.text((5, 25), f"MISSING\n{label}", fill="black", font=font)
    img.save(path)
    return str(path)

def generate_graph():
    dot = Digraph("P&ID")
    dot.attr(rankdir="LR", splines="ortho", labelloc='t', label="EPS Auto P&ID", fontsize="18")

    # Ordered layout: Pump → Column → Condenser → Receiver
    ordered_types = ["Pump", "Column", "Condenser", "Receiver"]
    ordered_eqs = []
    for t in ordered_types:
        for eq in st.session_state.equipment:
            if eq["type"].lower().startswith(t.lower()):
                ordered_eqs.append(eq)

    # Add equipment nodes
    for eq in ordered_eqs:
        file_name = f"{eq['type'].replace(' ', '_')}.png"
        img_path = SYMBOLS_DIR / file_name
        if not img_path.exists():
            placeholder_path = TEMP_DIR / file_name
            create_placeholder_image(eq['type'], placeholder_path)
            img_path = placeholder_path
        dot.node(eq["tag"], label=eq["tag"], image=str(img_path), shape="none", imagepos="tc", labelloc="b")

    # Add pipelines and in-line components
    for pipe in st.session_state.pipelines:
        from_ = pipe["from"]
        to_ = pipe["to"]
        inlines = [i for i in st.session_state.inline_components if i["pipe_tag"] == pipe["tag"]]
        last = from_
        for inline in inlines:
            node_id = f"{inline['tag']}_{pipe['tag']}"
            file_name = f"{inline['type'].replace(' ', '_')}.png"
            img_path = SYMBOLS_DIR / file_name
            if not img_path.exists():
                placeholder = TEMP_DIR / file_name
                create_placeholder_image(inline['type'], placeholder)
                img_path = placeholder
            dot.node(node_id, label=inline["tag"], image=str(img_path), shape="none", imagepos="tc", labelloc="b")
            dot.edge(last, node_id, label=pipe['tag'])
            last = node_id
        dot.edge(last, to_, label=pipe['tag'])

    return dot

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    x, y = 0, 0
    for eq in st.session_state.equipment:
        msp.add_circle((x, y), 2)
        msp.add_text(eq['tag'], dxfattribs={'height': 0.5}).set_pos((x + 3, y))
        y -= 10
    return doc.encode()

def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "❌ OPENAI_API_KEY not set in Railway environment variables."

    client = openai.OpenAI(api_key=api_key)
    prompt = (
        "You are a senior process engineer. Based on the P&ID below, suggest 3 improvements:\n\n"
        + "EQUIPMENT:\n" + "\n".join([f"{e['tag']} ({e['type']})" for e in st.session_state.equipment]) + "\n\n"
        + "PIPELINES:\n" + "\n".join([f"{p['tag']}: {p['from']} → {p['to']}" for p in st.session_state.pipelines]) + "\n\n"
        + "IN-LINE:\n" + "\n".join([f"{i['tag']} ({i['type']}) on {i['pipe_tag']}" for i in st.session_state.inline_components])
    )

    try:
        with st.spinner("🔍 AI analyzing your P&ID..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250
            )
        return res.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

# --- SIDEBAR ---
st.sidebar.title("🧱 Add Components")

with st.sidebar.expander("➕ Add Equipment"):
    eq_tag = st.text_input("Tag", key="eq_tag")
    eq_type = st.selectbox("Type", ["Pump", "Column", "Condenser", "Receiver", "Tank", "Dryer", "Custom"], key="eq_type")
    if st.button("Add Equipment"):
        st.session_state.equipment.append({"tag": eq_tag, "type": eq_type})
        st.experimental_rerun()

with st.sidebar.expander("➕ Add Pipeline"):
    if st.session_state.equipment:
        pipe_tag = st.text_input("Pipeline Tag", key="pipe_tag")
        from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment], key="from_eq")
        to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], key="to_eq")
        if st.button("Add Pipeline"):
            st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
            st.experimental_rerun()

with st.sidebar.expander("➕ Add In-line Component"):
    if st.session_state.pipelines:
        inline_type = st.selectbox("Type", ["Valve", "Sight Glass", "Thermowell", "Filter", "Custom"], key="inline_type")
        inline_tag = st.text_input("Tag", key="inline_tag")
        pipe_for_inline = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines], key="pipe_inline")
        if st.button("Add In-Line"):
            st.session_state.inline_components.append({
                "tag": inline_tag, "type": inline_type, "pipe_tag": pipe_for_inline
            })
            st.experimental_rerun()

if st.sidebar.button("🔄 Reset All"):
    for k in ['equipment', 'pipelines', 'inline_components']:
        st.session_state[k] = []
    st.experimental_rerun()

# --- MAIN UI ---
st.title("💡 EPS Interactive P&ID Generator")

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📦 Equipment")
    st.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True)
with c2:
    st.subheader("🔗 Pipelines")
    st.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True)
with c3:
    st.subheader("🔍 In-Line Components")
    st.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True)

st.subheader("🧩 P&ID Diagram Preview")
with st.container(height=600, border=True):
    dot = generate_graph()
    st.graphviz_chart(dot)

st.subheader("🤖 AI Engineering Suggestions")
if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())

st.subheader("⬇️ Export Files")
col1, col2 = st.columns(2)
with col1:
    st.download_button("📷 Download PNG", dot.pipe(format="png"), file_name="pid.png", mime="image/png")
with col2:
    st.download_button("📐 Download DXF", generate_dxf(), file_name="pid.dxf", mime="application/dxf")
