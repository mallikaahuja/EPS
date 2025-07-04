import streamlit as st
import openai
import os
from graphviz import Digraph
from PIL import Image
from pathlib import Path
import base64

# Setup API Key from Railway Environment Variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- CONFIG ---
st.set_page_config(page_title="EPS P&ID Generator", layout="wide")
SYMBOLS_DIR = Path("symbols")

# --- HARD-CODED OPTIONS (from your Excel files) ---
equipment_options = [
    "Dry Vacuum Pump", "Condenser", "Receiver", "Column", "Cooling Coil"
]

piping_options = [
    "Line", "Jacketed Line", "Vacuum Line", "Drain Line", "Steam Line"
]

inline_component_options = [
    "Valve", "Check Valve", "Ball Valve", "Temperature Transmitter",
    "Pressure Indicator", "Sight Glass", "Filter", "Strainer"
]

# --- STATE MANAGEMENT ---
if "components" not in st.session_state:
    st.session_state.components = []

# --- UI ---
st.title("⚙️ EPS Interactive P&ID Generator")

# Step 1: Component Input
st.subheader("Step 1: Select and Add Component")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    comp_type = st.selectbox("Component Type", ["Equipment", "Piping", "In-line Component"])
with col2:
    if comp_type == "Equipment":
        comp_name = st.selectbox("Component Name", equipment_options)
    elif comp_type == "Piping":
        comp_name = st.selectbox("Component Name", piping_options)
    else:
        comp_name = st.selectbox("Component Name", inline_component_options)
with col3:
    if st.button("➕ Add"):
        st.session_state.components.append({"type": comp_type, "name": comp_name})

# Step 1b: Display Current Sequence
st.subheader("Current Sequence")
for i, comp in enumerate(st.session_state.components, 1):
    st.markdown(f"{i}. **{comp['type']}** – {comp['name']}")

# Step 2: Generate & Download
st.subheader("Step 2: Generate Preview & Export")

if st.button("🛠 Generate P&ID Diagram"):
    dot = Digraph(format='png')
    dot.attr(rankdir="LR", size="10,5")

    for idx, comp in enumerate(st.session_state.components):
        label = f"{comp['name']}\n({comp['type']})"
        dot.node(str(idx), label)

    for idx in range(len(st.session_state.components) - 1):
        dot.edge(str(idx), str(idx + 1))

    diagram_path = "pnid_preview.png"
    dot.render("pnid_preview", format="png", cleanup=True)
    st.image(diagram_path, caption="Generated P&ID Diagram")

    # Download button
    with open(diagram_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="pnid_preview.png">📥 Download PNG</a>'
        st.markdown(href, unsafe_allow_html=True)

# Step 3 (Optional): AI Suggestions
st.subheader("💡 AI Suggestion (Optional)")

if st.button("Suggest Next Component with AI"):
    try:
        prompt = "Suggest the next component in a vacuum P&ID sequence after: " + \
                 ", ".join([c['name'] for c in st.session_state.components])
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        suggestion = response["choices"][0]["message"]["content"]
        st.success(f"🤖 Suggested: {suggestion}")
    except Exception as e:
        st.error(f"AI Suggestion failed: {e}")

# Step 4: Reset
if st.button("♻️ Reset Components"):
    st.session_state.components = []
    st.success("Component sequence reset.")
