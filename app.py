import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
from professional_symbols import PROFESSIONAL_ISA_SYMBOLS
with open("component_prompt_map.json", "r") as f:
    COMPONENT_PROMPT_MAP = json.load(f)
from advanced_rendering import ProfessionalRenderer
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client
import io

# --- CONFIG ---
st.set_page_config(page_title="EPS P&ID Generator", layout="wide")
renderer = ProfessionalRenderer()
symbols_folder = "symbols"
os.makedirs(symbols_folder, exist_ok=True)
STABILITY_KEY = os.getenv("STABILITY_API_KEY")

# --- LOAD COMPONENTS ---
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# --- IMAGE GENERATION ---
def generate_svg(component_id, prompt):
    if not STABILITY_KEY:
        st.error("Stability AI key missing.")
        return None
    stability_api = client.StabilityInference(key=STABILITY_KEY)
    answers = stability_api.generate(
        prompt=prompt,
        steps=30,
        width=512,
        height=512,
        samples=1,
        cfg_scale=8.0,
        sampler=generation.SAMPLER_K_DPMPP_2M
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                svg_path = os.path.join(symbols_folder, f"{component_id}.png")
                img.save(svg_path)
                return svg_path
    return None

def load_symbol(component_id):
    svg_path = os.path.join(symbols_folder, f"{component_id}.png")
    if os.path.exists(svg_path):
        return svg_path
    if component_id in COMPONENT_PROMPT_MAP:
        return generate_svg(component_id, COMPONENT_PROMPT_MAP[component_id])
    return None

# --- STREAMLIT UI ---
st.title("🔧 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)

equipment_id = col1.selectbox("Equipment", equipment_df["ID"].tolist())
pipeline_id = col2.selectbox("Pipeline", pipeline_df["ID"].tolist())
inline_id = col3.selectbox("Inline Component", inline_df["ID"].tolist())

# Show previews
def preview_symbol(component_id):
    symbol_path = load_symbol(component_id)
    if symbol_path:
        st.image(symbol_path, width=100, caption=component_id)
    else:
        st.warning(f"No symbol for {component_id}")

with st.expander("🖼️ Preview Selected Symbols"):
    col4, col5, col6 = st.columns(3)
    with col4:
        preview_symbol(equipment_id)
    with col5:
        preview_symbol(pipeline_id)
    with col6:
        preview_symbol(inline_id)

# --- ACTION ---
if st.button("Render Preview"):
    components = {
        "E1": equipment_id,
        "P1": pipeline_id,
        "I1": inline_id
    }
    pipes = []  # Add routing if needed

    svg_output = renderer.render_professional_pnid(components, pipes)
    st.markdown("### 🧪 Rendered SVG Output")
    st.components.v1.html(svg_output, height=600, scrolling=True)

# --- DOWNLOAD ---
if st.button("Export SVG"):
    with open("output.svg", "w") as f:
        f.write(svg_output)
    st.success("✅ Exported to output.svg")
