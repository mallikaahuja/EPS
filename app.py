import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import openai
import os
import ezdxf
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- LOAD COMPONENT LISTS ---
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# --- SESSION STATE ---
for key in ["equipment", "pipelines", "inline_components"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- HELPERS ---
def get_symbol_image(symbol_name):
    img_path = SYMBOLS_DIR / symbol_name
    if img_path.exists():
        return str(img_path)
    else:
        placeholder = TEMP_DIR / symbol_name
        if not placeholder.exists():
            img = Image.new("RGB", (100, 75), color="white")
            d = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            d.rectangle([0, 0, 99, 74], outline="black")
            d.text((5, 25), "MISSING:\n" + symbol_name, fill="black", font=font)
            img.save(placeholder)
        return str(placeholder)

def auto_tag(type_name, tag_prefix):
    existing = [e["tag"] for e in st.session_state["equipment"] if e["tag"].startswith(tag_prefix)]
    number = len(existing) + 1
    return f"{tag_prefix}-{100 + number}"

def generate_graphviz():
    dot = Digraph("P&ID", format="png")
    dot.attr(rankdir="LR", nodesep="1.0")

    # Place equipment
    for eq in st.session_state["equipment"]:
        img = get_symbol_image(eq["image"])
        dot.node(eq["tag"], label=eq["tag"], image=img, shape="none", imagepos="tc", labelloc="b")

    # Draw pipelines and inline components
    for pipe in st.session_state["pipelines"]:
        from_node = pipe["from"]
        to_node = pipe["to"]
        components = [c for c in st.session_state["inline_components"] if c["pipe"] == pipe["tag"]]
        last_node = from_node
        for comp in components:
            comp_id = comp["tag"]
            img = get_symbol_image(comp["image"])
            dot.node(comp_id, label=comp["tag"], image=img, shape="none", imagepos="tc", labelloc="b")
            dot.edge(last_node, comp_id)
            last_node = comp_id
        dot.edge(last_node, to_node, label=pipe["tag"])
    return dot

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    y = 0
    for eq in st.session_state["equipment"]:
        msp.add_circle((0, y), 2)
        msp.add_text(eq["tag"], dxfattribs={"height": 0.5}).set_pos((3, y))
        y -= 10
    return doc.write()

def get_ai_suggestions():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ OpenAI API key not set."
    client = openai.OpenAI(api_key=api_key)
    description = "EQUIPMENT:\n" + "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state["equipment"]])
    prompt = f"You are a senior process engineer. Based on the following P&ID, suggest 3 improvements:\n\n{description}"
    try:
        with st.spinner("Getting AI suggestions..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {e}"

# --- UI ---
st.title("🧠 EPS Interactive P&ID Generator")

with st.sidebar:
    st.header("➕ Add Equipment")
    selected_type = st.selectbox("Type", equipment_df["Type"])
    type_row = equipment_df[equipment_df["Type"] == selected_type].iloc[0]
    auto_id = auto_tag(selected_type, type_row["Tag Prefix"])
    tag = st.text_input("Tag", value=auto_id)
    if st.button("Add Equipment"):
        st.session_state["equipment"].append({
            "tag": tag,
            "type": selected_type,
            "image": type_row["Symbol_Image"]
        })
        st.rerun()

    st.header("➕ Add Pipeline")
    if len(st.session_state["equipment"]) >= 2:
        pipe_tag = st.text_input("Pipeline Tag", key="pipe_tag")
        from_eq = st.selectbox("From", [e["tag"] for e in st.session_state["equipment"]], key="from_eq")
        to_eq = st.selectbox("To", [e["tag"] for e in st.session_state["equipment"]], key="to_eq")
        if st.button("Add Pipeline"):
            st.session_state["pipelines"].append({
                "tag": pipe_tag,
                "from": from_eq,
                "to": to_eq
            })
            st.rerun()

    st.header("➕ Add In-Line Component")
    if st.session_state["pipelines"]:
        selected_ic = st.selectbox("Component Type", inline_df["Type"])
        ic_row = inline_df[inline_df["Type"] == selected_ic].iloc[0]
        pipe_choice = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state["pipelines"]])
        comp_tag = st.text_input("Tag", value=ic_row["Tag Prefix"] + "-I")
        if st.button("Add In-Line"):
            st.session_state["inline_components"].append({
                "tag": comp_tag,
                "type": selected_ic,
                "pipe": pipe_choice,
                "image": ic_row["Symbol_Image"]
            })
            st.rerun()

    if st.button("🔄 Reset All"):
        for key in ["equipment", "pipelines", "inline_components"]:
            st.session_state[key] = []
        st.rerun()

# --- MAIN VIEW ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Equipment")
    st.dataframe(pd.DataFrame(st.session_state["equipment"]))
with col2:
    st.subheader("Pipelines")
    st.dataframe(pd.DataFrame(st.session_state["pipelines"]))
with col3:
    st.subheader("In-Line Components")
    st.dataframe(pd.DataFrame(st.session_state["inline_components"]))

st.subheader("🛠️ Generated P&ID Preview")
dot = generate_graphviz()
st.graphviz_chart(dot)

st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_suggestions())

st.subheader("⬇️ Export Options")
col1, col2 = st.columns(2)
with col1:
    try:
        png = dot.pipe(format="png")
        st.download_button("Download PNG", png, file_name="p_id.png", mime="image/png")
    except Exception as e:
        st.error(f"PNG export failed: {e}")
with col2:
    try:
        dxf = generate_dxf()
        st.download_button("Download DXF", dxf, file_name="p_id.dxf", mime="application/dxf")
    except Exception as e:
        st.error(f"DXF export failed: {e}")
