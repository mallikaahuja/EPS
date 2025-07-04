import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Intelligent P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = Path("symbols") 

# This uses your standardized filenames.
AVAILABLE_COMPONENTS = {
    # Major Equipment
    "Vertical Vessel": "vertical_vessel.png",
    "Dry Pump Model": "dry_pump_model.png",
    "Discharge Condenser": "discharge_condenser.png",
    "Scrubber": "scrubber.png",
    # In-Line Components
    "Butterfly Valve": "butterfly_valve.png",
    "Gate Valve": "gate_valve.png",
    "Check Valve": "check_valve.png",
    "Globe Valve": "globe_valve.png",
    "Flexible Connection": "flexible_connection_suction.png",
    "Pressure Transmitter": "pressure_transmitter_suction.png",
    "Temperature Gauge": "temperature_gauge_suction.png",
    "Strainer": "y-strainer.png"
}
EQUIPMENT_TYPES = sorted(["Vertical Vessel", "Dry Pump Model", "Discharge Condenser", "Scrubber"])
INLINE_TYPES = sorted([comp for comp in AVAILABLE_COMPONENTS if comp not in EQUIPMENT_TYPES])

# --- INITIALIZE SESSION STATE ---
if 'equipment' not in st.session_state:
    st.session_state.equipment = []
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []
if 'inline_components' not in st.session_state:
    st.session_state.inline_components = []

# --- AI SUGGESTION FUNCTION ---
def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in Railway variables."

    client = openai.OpenAI(api_key=api_key)
    
    description = "Review this P&ID data:\n"
    description += "Equipment: " + ", ".join([f"{e['tag']} ({e['type']})" for e in st.session_state.equipment]) + "\n"
    description += "Pipelines: " + ", ".join([f"{p['tag']} (from {p['from']} to {p['to']})" for p in st.session_state.pipelines]) + "\n"
    description += "Inline Items: " + ", ".join([f"{c['tag']} ({c['type']}) on {c['pipe_tag']}" for c in st.session_state.inline_components]) + "\n"
    
    prompt = f"You are an expert process engineer. Based on the following P&ID data, provide 3 concise, actionable recommendations for improving safety or operability. Focus on missing items like isolation valves, check valves, or basic instrumentation.\n\nP&ID DATA:\n{description}"
    
    try:
        with st.spinner("🤖 AI Engineer is analyzing the P&ID..."):
            response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.5, max_tokens=200)
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not get AI suggestions. Error: {e}"

# --- DRAWING FUNCTION ---
def generate_p_and_id():
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.5')
    dot.attr('node', shape='box', style='rounded')

    # Group equipment in a subgraph
    with dot.subgraph(name='cluster_main_process') as c:
        c.attr(label='Main Process Area', style='filled', color='lightgrey')
        for item in st.session_state.equipment:
            img_path = str(SYMBOLS_DIR / AVAILABLE_COMPONENTS.get(item['type'], "general.png"))
            if os.path.exists(img_path):
                c.node(item['tag'], label=item['tag'], image=img_path, shape='none')
            else:
                c.node(item['tag'], f"{item['tag']}\n({item['type']})")

    # Connect pipelines and insert inline components
    for pipe in st.session_state.pipelines:
        components_on_this_pipe = [c for c in st.session_state.inline_components if c['pipe_tag'] == pipe['tag']]
        
        last_node_in_chain = pipe['from']
        
        for comp in components_on_this_pipe:
            comp_node_name = f"{comp['tag']}_{pipe['tag']}"
            img_path = str(SYMBOLS_DIR / AVAILABLE_COMPONENTS.get(comp['type'], "general.png"))
            if os.path.exists(img_path):
                dot.node(comp_node_name, label=comp['tag'], image=img_path, shape='none')
            else:
                dot.node(comp_node_name, f"{comp['tag']}\n({comp['type']})")
            
            dot.edge(last_node_in_chain, comp_node_name, label=pipe['tag'])
            last_node_in_chain = comp_node_name
            
        dot.edge(last_node_in_chain, pipe['to'])

    return dot

# --- UI LAYOUT ---
st.title("🧠 Intelligent P&ID Generator")

with st.sidebar:
    st.subheader("P&ID Builder")
    with st.expander("1. Add Major Equipment", expanded=True):
        with st.form("add_equipment", clear_on_submit=True):
            eq_type = st.selectbox("Equipment Type", EQUIPMENT_TYPES)
            eq_tag = st.text_input("Equipment Tag (e.g., P-101)")
            if st.form_submit_button("Add Equipment", use_container_width=True):
                if eq_tag and not any(e['tag'] == eq_tag for e in st.session_state.equipment):
                    st.session_state.equipment.append({'tag': eq_tag, 'type': eq_type})
                else:
                    st.warning("Tag is empty or already exists.")

    equipment_tags = [e['tag'] for e in st.session_state.equipment]
    if len(equipment_tags) >= 2:
        with st.expander("2. Define Pipelines"):
            with st.form("add_pipeline", clear_on_submit=True):
                pipe_tag = st.text_input("Pipeline Tag (e.g., 100-B-1)")
                pipe_from = st.selectbox("From Equipment", equipment_tags)
                pipe_to = st.selectbox("To Equipment", equipment_tags)
                if st.form_submit_button("Add Pipeline", use_container_width=True):
                    if pipe_tag and pipe_from != pipe_to:
                        st.session_state.pipelines.append({'tag': pipe_tag, 'from': pipe_from, 'to': pipe_to})
                    else:
                        st.warning("Tag is empty or 'From' and 'To' are the same.")

    pipeline_tags = [p['tag'] for p in st.session_state.pipelines]
    if pipeline_tags:
        with st.expander("3. Add In-Line Components"):
            with st.form("add_inline", clear_on_submit=True):
                inline_type = st.selectbox("Component Type", INLINE_TYPES)
                inline_pipe = st.selectbox("On Pipeline", pipeline_tags)
                inline_tag = st.text_input("Component Tag (e.g., HV-101)")
                if st.form_submit_button("Add In-Line Component", use_container_width=True):
                    if inline_tag:
                         st.session_state.inline_components.append({'tag': inline_tag, 'type': inline_type, 'pipe_tag': inline_pipe})
                    else:
                        st.warning("Please provide a tag for the component.")

# Main display area
st.subheader("Current P&ID Data")
col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.write("**Equipment**")
        st.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True, hide_index=True)
with col2:
    with st.container(border=True):
        st.write("**Pipelines**")
        st.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True, hide_index=True)
with col3:
    with st.container(border=True):
        st.write("**In-Line Components**")
        st.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Generated P&ID Preview")
if st.session_state.equipment:
    final_dot = generate_p_and_id()
    st.graphviz_chart(final_dot)
    
    with st.container(border=True):
        st.subheader("🤖 AI Engineer Suggestions")
        if st.button("Get Suggestions"):
            suggestions = get_ai_suggestions()
            st.info(suggestions)
else:
    st.info("Add equipment in the sidebar to begin building your P&ID.")
