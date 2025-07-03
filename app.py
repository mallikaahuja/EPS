import streamlit as st
from graphviz import Digraph

st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator (Barebones)")

AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png", "ACG Filter (Suction)": "ACG filter at suction .PNG",
    "Air Cooler": "Air_Cooled.png", "Averaging Pitot Tube": "Averaging_Pitot_Tube.png",
    "General Connection": "General.png", "Gate Valve": "Gate valve.PNG",
    "Vertical Vessel": "Vertical vessel.jpg",
    # ... PASTE YOUR FULL LIST HERE ...
}

if 'component_list' not in st.session_state: st.session_state.component_list = []

st.header("Step 1: Add Components in Sequence")
with st.form("component_form", clear_on_submit=True):
    comp_type = st.selectbox("Component Type", options=sorted(list(AVAILABLE_COMPONENTS.keys())))
    comp_label = st.text_input("Component Label / Tag (e.g., V-101, 25)")
    submitted = st.form_submit_button("Add Component")
    if submitted and comp_label:
        st.session_state.component_list.append({
            "Tag": comp_label, "Symbol_Image": AVAILABLE_COMPONENTS[comp_type]
        })
        st.rerun()

st.header("Step 2: Generate the P&ID")
if st.button("Generate P&ID", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add at least one component.")
    else:
        with st.spinner("Drawing P&ID..."):
            dot = Digraph()
            dot.attr(rankdir='LR')
            
            # Define INLET and OUTLET nodes
            dot.node("INLET", "INLET", shape='plaintext')
            dot.node("OUTLET", "OUTLET", shape='plaintext')
            
            # Chain everything together
            all_tags = ["INLET"] + [c['Tag'] for c in st.session_state.component_list] + ["OUTLET"]
            
            for component in st.session_state.component_list:
                image_path = f"PN&D-Symbols-library/{component['Symbol_Image']}"
                dot.node(name=component['Tag'], label=component['Tag'], image=image_path, shape='none')

            for i in range(len(all_tags) - 1):
                dot.edge(all_tags[i], all_tags[i+1])

            st.graphviz_chart(dot)

if st.button("Start Over"):
    st.session_state.component_list = []
    st.rerun()
