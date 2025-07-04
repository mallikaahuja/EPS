import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai # We will use the OpenAI library for suggestions

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
    "Pressure Transmitter": "pressure_transmitter_suction.png", # Using a generic one
    "Temperature Gauge": "temperature_gauge_suction.png", # Using a generic one
    "Strainer": "y-strainer.png"
}
EQUIPMENT_TYPES = ["Vertical Vessel", "Dry Pump Model", "Discharge Condenser", "Scrubber"]
INLINE_TYPES = [comp for comp in AVAILABLE_COMPONENTS if comp not in EQUIPMENT_TYPES]

# --- INITIALIZE SESSION STATE ---
if 'equipment' not in st.session_state:
    st.session_state.equipment = []
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []
if 'inline_components' not in st.session_state:
    st.session_state.inline_components = []

# --- AI SUGGESTION FUNCTION ---
# NOTE: This requires you to set up an OpenAI API key in your Streamlit secrets.
# In your app settings on Streamlit Cloud or Railway, add a secret named "OPENAI_API_KEY".
def get_ai_suggestions(p_and_id_data):
    if not st.secrets.get("OPENAI_API_KEY"):
        return "AI suggestions disabled. Please add OPENAI_API_KEY to your secrets."

    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    # Create a simple text description of the P&ID for the AI
    description = "This P&ID contains the following:\n"
    description += "Equipment: " + ", ".join([f"{e['tag']} ({e['type']})" for e in p_and_id_data['equipment']]) + "\n"
    description += "Pipelines: " + ", ".join([f"{p['tag']} from {p['from']} to {p['to']}" for p in p_and_id_data['pipelines']]) + "\n"
    
    prompt = (
        "You are an expert chemical process engineer reviewing a P&ID. "
        "Based on the following description, provide 2-3 actionable suggestions for standard, missing components "
        "that would improve safety or operability. Be concise. For example, 'Add isolation valves around Pump-101' "
        "or 'Consider a check valve on the discharge of Pump-101'.\n\n"
        f"P&ID Description:\n{description}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not get AI suggestions. Error: {e}"

# --- DRAWING FUNCTION ---
def generate_p_and_id(equipment, pipelines, inline_components):
    dot = Digraph(comment='P&ID')
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5')
    dot.attr('node', shape='box', style='rounded')

    # Group equipment into subgraphs for better layout
    with dot.subgraph(name='cluster_main_process') as c:
        c.attr(style='filled', color='lightgrey')
        c.attr(label='Main Process Area')
        for item in equipment:
            img_path = str(SYMBOLS_DIR / AVAILABLE_COMPONENTS.get(item['type'], "general.png"))
            if os.path.exists(img_path):
                c.node(item['tag'], label=item['tag'], image=img_path, shape='none')
            else:
                c.node(item['tag'], f"{item['tag']}\n({item['type']})")
    
    # Create connections with in-line components
    for pipe in pipelines:
        # Create a chain of nodes for the pipeline's inline components
        components_on_this_pipe = [c for c in inline_components if c['pipe_tag'] == pipe['tag']]
        
        last_node_in_chain = pipe['from']
        
        for comp in components_on_this_pipe:
            comp_node_name = f"{comp['tag']}_{pipe['tag']}" # Make the node name unique
            img_path = str(SYMBOLS_DIR / AVAILABLE_COMPONENTS.get(comp['type'], "general.png"))
            if os.path.exists(img_path):
                dot.node(comp_node_name, label=comp['tag'], image=img_path, shape='none')
            else:
                 dot.node(comp_node_name, f"{comp['tag']}\n({comp['type']})")
            
            dot.edge(last_node_in_chain, comp_node_name)
            last_node_in_chain = comp_node_name
            
        # Connect the end of the chain to the destination equipment
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
            if st.form_submit_button("Add Equipment"):
                st.session_state.equipment.append({'tag': eq_tag, 'type': eq_type})

    equipment_tags = [e['tag'] for e in st.session_state.equipment]
    if len(equipment_tags) >= 2:
        with st.expander("2. Define Pipelines"):
            with st.form("add_pipeline", clear_on_submit=True):
                pipe_tag = st.text_input("Pipeline Tag (e.g., 100-B-1)")
                pipe_from = st.selectbox("From Equipment", equipment_tags)
                pipe_to = st.selectbox("To Equipment", equipment_tags)
                if st.form_submit_button("Add Pipeline"):
                    st.session_state.pipelines.append({'tag': pipe_tag, 'from': pipe_from, 'to': pipe_to})

    pipeline_tags = [p['tag'] for p in st.session_state.pipelines]
    if pipeline_tags:
        with st.expander("3. Add In-Line Components"):
            with st.form("add_inline", clear_on_submit=True):
                inline_type = st.selectbox("Component Type", INLINE_TYPES)
                inline_pipe = st.selectbox("On Pipeline", pipeline_tags)
                inline_tag = st.text_input("Component Tag (e.g., HV-101)")
                if st.form_submit_button("Add In-Line Component"):
                    st.session_state.inline_components.append({'tag': inline_tag, 'type': inline_type, 'pipe_tag': inline_pipe})

# Main display area
st.subheader("Current P&ID Data")
col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.write("**Equipment**")
        st.dataframe(pd.DataFrame(st.session_state.equipment), use_container_width=True)
with col2:
    with st.container(border=True):
        st.write("**Pipelines**")
        st.dataframe(pd.DataFrame(st.session_state.pipelines), use_container_width=True)
with col3:
    with st.container(border=True):
        st.write("**In-Line Components**")
        st.dataframe(pd.DataFrame(st.session_state.inline_components), use_container_width=True)

st.markdown("---")
st.subheader("Generated P&ID Preview")
if st.session_state.equipment:
    final_dot = generate_p_and_id(st.session_state.equipment, st.session_state.pipelines, st.session_state.inline_components)
    st.graphviz_chart(final_dot)
    
    # AI Suggestions
    with st.container(border=True):
        st.subheader("🤖 AI Engineer Suggestions")
        p_and_id_data = {
            'equipment': st.session_state.equipment,
            'pipelines': st.session_state.pipelines
        }
        if st.button("Get Suggestions"):
            with st.spinner("Analyzing P&ID..."):
                suggestions = get_ai_suggestions(p_and_id_data)
                st.info(suggestions)

else:
    st.info("Add equipment in the sidebar to begin.")
