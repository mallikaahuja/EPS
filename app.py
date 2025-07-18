import streamlit as st
import os
import json
import requests
from pathlib import Path
from stability_sdk import client
import pandas as pd

from professional_symbols import get_component_symbol
from advanced_rendering import ProfessionalRenderer
from control_systems import ControlSystemAnalyzer, PnIDValidator, render_control_loop_overlay, render_validation_overlay

# Load prompts
with open("component_prompt_map.json", "r") as f:
    PROMPT_MAP = json.load(f)

# Stability API
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
STABILITY_ENGINE = "stable-diffusion-xl-1024-v1-0"  # Your selected engine
STABILITY_CLIENT = client.StabilityInference(
    key=STABILITY_API_KEY,
    engine=STABILITY_ENGINE,
    verbose=True,
)

def generate_symbol_svg(component_name: str, prompt: str) -> str:
    """Use Stability AI to generate SVG-style symbol from prompt"""
    print(f"Generating symbol for: {component_name}")
    answers = STABILITY_CLIENT.generate(
        prompt=prompt,
        width=512,
        height=512,
        cfg_scale=7.0,
        steps=30,
        samples=1,
    )

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == 0:
                continue
            if artifact.type == 1:
                # Save to file
                svg_path = Path("symbols") / f"{component_name}.svg"
                with open(svg_path, "wb") as f:
                    f.write(artifact.binary)
                return str(svg_path)
    return None

def ensure_symbol_exists(component_name: str):
    """Check for symbol, generate if missing"""
    symbol_path = Path("symbols") / f"{component_name}.svg"
    if not symbol_path.exists():
        prompt = PROMPT_MAP.get(component_name)
        if prompt:
            return generate_symbol_svg(component_name, prompt)
        else:
            st.warning(f"No prompt found for missing symbol: {component_name}")
    return str(symbol_path)

# App UI
st.set_page_config(layout="wide", page_title="EPS P&ID Generator")

st.title("📘 EPS Interactive P&ID Generator")

col1, col2, col3 = st.columns(3)

# Load component data
equipment_list = pd.read_csv("equipment_list.csv")
pipeline_list = pd.read_csv("pipeline_list.csv")
inline_list = pd.read_csv("inline_component_list.csv")

equipment = col1.selectbox("Equipment", equipment_list["Component"].tolist())
pipeline = col2.selectbox("Pipeline", pipeline_list["Component"].tolist())
inline = col3.selectbox("Inline Component", inline_list["Component"].tolist())

# Load layout data
equipment_df = pd.read_csv("enhanced_equipment_layout.csv")
pipe_df = pd.read_csv("pipe_connections_layout.csv")

# Ensure all required symbols exist
for comp in equipment_df["Component"].unique():
    ensure_symbol_exists(comp)

# Convert layout into usable component + pipe structures
components = {}  # id: ProfessionalPnidComponent-like objects
pipes = []       # List of Pipe-like dicts

# Placeholder component data
for _, row in equipment_df.iterrows():
    cid = row["ID"]
    components[cid] = type("Comp", (), {
        "id": cid,
        "tag": row.get("Tag", cid),
        "component_type": row["Component"],
        "x": row.get("x", 0),
        "y": row.get("y", 0),
        "width": row.get("Width", 80),
        "height": row.get("Height", 60),
        "is_instrument": "instrument" in row["Component"].lower(),
        "symbol": get_component_symbol(row["Component"]),
    })()

# Pipe rendering
for _, row in pipe_df.iterrows():
    pipe = type("Pipe", (), {
        "from_comp": components.get(row["From Component"]),
        "to_comp": components.get(row["To Component"]),
        "from_port": row["From Port"],
        "to_port": row["To Port"],
        "line_type": row.get("pipe_type", "process"),
        "label": row.get("Label", ""),
        "polyline": row.get("Polyline Points (x, y)", ""),
    })()
    pipes.append(pipe)

# Render layout
renderer = ProfessionalRenderer()
svg_output = renderer.render_professional_pnid(components, pipes)

# Add control logic overlays
analyzer = ControlSystemAnalyzer(components, pipes)
svg_output += render_control_loop_overlay(analyzer.control_loops, components)

# Validation
validator = PnIDValidator(components, pipes)
validation = validator.validate_all()
svg_output += render_validation_overlay(validation, components)

# Display SVG
st.subheader("P&ID Layout")
st.components.v1.html(f"<div style='overflow-x:scroll'>{svg_output}</div>", height=800, scrolling=True)

# BOM
st.subheader("Bill of Materials")
bom_data = pd.DataFrame([
    {"Tag": c.tag, "Component": c.component_type, "Type": "Instrument" if c.is_instrument else "Equipment"}
    for c in components.values()
])
st.dataframe(bom_data)

# Footer
st.markdown("---")
st.caption("Built with ❤️ by EPS Engineering")
