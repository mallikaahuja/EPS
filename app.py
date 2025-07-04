import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os

# --- CONFIGURATION (USING YOUR EXACT FOLDER NAME) ---
SYMBOLS_DIR = Path("PN&D-Symbols-library")
DEFAULT_IMAGE = "General.png"  # Ensure this file exists in your library

# --- YOUR COMPLETE COMPONENT LIBRARY ---
# This uses your exact filenames. Please ensure they match what's on GitHub.
AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png",
    "ACG Filter (Suction)": "ACG filter at suction .PNG",
    "Air Cooler": "Air_Cooled.png",
    "Averaging Pitot Tube": "Averaging_Pitot_Tube.png",
    "Axial Flow Fan": "Axial_flow_fan.png",
    "Bag Filter/Separator": "Bag.png",
    "Bin/Silo": "Bin.png",
    "Briquetting Machine": "Briquetting_Machine.png",
    "Butterfly Valve": "Butterfly valve.PNG",
    "Catch Pot (Auto, for Condenser)": "Catch pot with Auto drain for condenser.PNG",
    "Catch Pot (Auto Drain)": "Catch pot with auto drain.PNG",
    "Check Valve": "Check valve.PNG",
    "Column / Tower": "Column.png",
    "Combustion Chamber": "Combustion.png",
    "Compressor (Centrifugal Type)": "Compressor_Centrifugal.png",
    "Compressor Silencer": "Compressor_silencers.png",
    "Cone Crusher": "Cone_Crusher.png",
    "Control Panel": "Control panel.PNG",
    "Control Valve": "Control valve.PNG",
    "Conveyor": "Conveyor.png",
    "Cooler": "Cooler.png",
    "Crane/Hoist": "Crane.png",
    "Diaphragm Meter": "Diaphragm_D_Meter.png",
    "Discharge Condenser": "Discharge condenser.jpg",
    "Discharge Silencer": "Discharge silencer.PNG",
    "Double Pipe Heat Exchanger": "Double_Pipe_Heat.png",
    "Dry Pump Model": "Dry pump model.PNG",
    "Dryer": "Dryer.png",
    "EPO Valve": "EPO valve.PNG",
    "Ejector": "Ejector.png",
    "FLP Control Panel": "FLP control panel.PNG",
    "Fan": "Fan.png",
    "Feeder": "Feeder.png",
    "Filter": "Filter.png",
    "Fin-Fan Cooler": "Fin-fan_Cooler.png",
    "Finned Tube Exchanger": "Finned_Tubes.png",
    "Flame Arrestor (Discharge)": "Flame arrestor at discharge.PNG",
    "Flame Arrestor (Suction)": "Flame arrestor at suction.PNG",
    "Flexible Connection (Discharge)": "Flexible connection at discharge.PNG",
    "Flexible Connection (Suction)": "Flexible connection at suction.PNG",
    "Floating Head Exchanger": "Floating_Head.png",
    "Flow Switch (Cooling Water)": "Flow switch for cooling water line.PNG",
    "Flowmeter": "Flowmeter.png",
    "Gate Valve": "Gate valve.PNG",
    "General Connection": "General.png",
    "Globe Valve": "Globe valve.PNG",
    "Hammer Crusher": "Hammer_Crusher.png",
    "Heater": "Heater.png",
    "Hose": "Hose.png",
    "Impact Crusher": "Impact_Crusher.png",
    "Kettle Heat Exchanger": "Kettle_Heat.png",
    "Level Switch (Purge Tank)": "Level switch for liquid purge tank.PNG",
    "Lift": "Lift.png",
    "Liquid Flushing Assembly": "Liquid flushing assembly.PNG",
    "Liquid Ring Pump": "Liquid_ring.png",
    "Mixer": "Mixer.png",
    "Motor": "Motor.PNG",
    "N2 Purge Assembly": "N2 Purge assembly.PNG",
    "Needle Valve": "Needel_Valve.png",
    "One-to-Many Splitter": "One-to-Many.png",
    "Open Tank": "Open_tank.png",
    "Overhead Conveyor": "Overhead.png",
    "Panel": "Panel.png",
    "Peristaltic Pump": "Peristaltic_pump.png",
    "Plate Heat Exchanger": "Plate_Heat.png",
    "Pressure Switch (N2 Purge)": "Pressure switch at nitrogen purge line.PNG",
    "Pressure Transmitter (Discharge)": "Pressure transmitter at discharge.PNG",
    "Pressure Transmitter (Suction)": "Pressure transmitter at suction.PNG",
    "Pressure Gauge": "Pressure_Gauges.png",
    "Reboiler Heat Exchanger": "Reboiler_Heat.png",
    "Reciprocating Compressor": "Reciprocating_Compressor_2.png",
    "Reciprocating Pump": "Reciprocating_pump.png",
    "Roller Conveyor": "Roller_Conveyor.png",
    "Roller Crusher": "Roller_Crusher.png",
    "Roller Press": "Roller_Press.png",
    "Rotary Equipment": "Rotary.png",
    "Rotary Meter": "Rotary_Meter_R.png",
    "Rotometer": "Rotometer.png",
    "Scraper": "Scraper.png",
    "Screening Machine": "Screening.png",
    "Screw Conveyor": "Screw_Conveyor.png",
    "Screw Pump": "Screw_pump.png",
    "Scrubber": "Scrubber.PNG",
    "Section Filter": "Section filter.PNG",
    "Selectable Compressor": "Selectable_Compressor.png",
    "Shell and Tube Exchanger": "Shell_and_Tube.png",
    "Silencer": "Silencer.png",
    "Single Pass Heat Exchanger": "Single_Pass_Heat.png",
    "Solenoid Valve": "Solenoid valve.PNG",
    "Spray Nozzle": "Spray.png",
    "Steam Traced Line": "Steam_Traced.png",
    "Strainer (Cooling Water)": "Strainer for cooling water line.PNG",
    "Submersible Pump": "Submersible_pump.png",
    "Suction Filter": "Suction filter.PNG",
    "T-Junction": "T.png",
    "TCV (Thermostatic Valve)": "TCV.PNG",
    "TEMA Type AEL Exchanger": "TEMA_TYPE_AEL.png",
    "TEMA Type AEM Exchanger": "TEMA_TYPE_AEM.png",
    "TEMA Type BEU Exchanger": "TEMA_TYPE_BEU.png",
    "TEMA Type NEN Exchanger": "TEMA_TYPE_NEN.png",
    "Temperature Gauge (Discharge)": "Temperature gauge at discharge.PNG",
    "Temperature Gauge (Suction)": "Temperature gauge at suction .PNG",
    "Temperature Transmitter (Discharge)": "Temperature transmitter at discharge.jpg",
    "Temperature Transmitter (Suction)": "Temperature transmitter at suction.PNG",
    "Thermometer": "Thermometers.png",
    "Thin-Film Dryer": "Thin-Film.png",
    "Traced Line": "Traced_Line.png",
    "U-Tube Heat Exchanger": "U-tube_Heat.png",
    "VFD Panel": "VFD.jpg",
    "Valves (General Symbol)": "Valves.png",
    "Vertical Pump": "Vertical_pump.png",
    "Vertical Vessel": "Vertical vessel.jpg",
    "Y-Strainer": "Y-strainer.png"
}

# --- APP LAYOUT AND LOGIC ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")

# Initialize session state
if 'component_list' not in st.session_state:
    st.session_state.component_list = []
if 'generated_dot' not in st.session_state:
    st.session_state.generated_dot = None

st.title("EPS Interactive P&ID Generator")
st.markdown("Build your process flow diagram by adding components in sequence, then generate the P&ID.")

# --- Step 1: Component Input Panel ---
with st.container(border=True):
    st.subheader("⚙️ Step 1: Build Your Process Flow")
    col1, col2 = st.columns([1, 1.5]) # Give more space to the list

    with col1:
        st.caption("Select a component, give it a unique tag, and add it to the sequence.")
        with st.form("component_form", clear_on_submit=True):
            comp_type = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()))
            comp_tag = st.text_input("Component Tag (UNIQUE)", value=f"Comp-{len(st.session_state.component_list) + 1}")
            
            if st.form_submit_button("Add Component", use_container_width=True):
                if any(c['Tag'] == comp_tag for c in st.session_state.component_list):
                    st.error(f"Tag '{comp_tag}' already exists!")
                else:
                    st.session_state.component_list.append({
                        "Tag": comp_tag,
                        "Type": comp_type,
                        "Image": AVAILABLE_COMPONENTS[comp_type]
                    })
                    st.session_state.generated_dot = None # Clear old diagram on change
    
    with col2:
        st.write("##### Current Sequence")
        if st.session_state.component_list:
            df_display = pd.DataFrame(st.session_state.component_list)
            st.dataframe(df_display[['Tag', 'Type']], use_container_width=True, hide_index=True)
            if st.button("Clear All Components", use_container_width=True):
                st.session_state.component_list = []
                st.session_state.generated_dot = None
                st.rerun()
        else:
            st.info("No components added yet. Add a component to begin. ⬅️")

# --- Step 2: Generation Panel ---
with st.container(border=True):
    st.subheader("✨ Step 2: Generate and Download")
    if not st.session_state.component_list:
        st.warning("Please add at least one component in Step 1 to generate a P&ID.")
    else:
        if st.button("Generate P&ID", type="primary", use_container_width=True):
            with st.spinner("Generating diagram..."):
                dot = Digraph('P&ID')
                dot.attr(rankdir='LR', ranksep='0.75', nodesep='0.5')
                dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
                
                dot.node("INLET", "INLET", shape='point', width='0.1')
                dot.node("OUTLET", "OUTLET", shape='point', width='0.1')
                
                last_node = "INLET"
                
                for component in st.session_state.component_list:
                    tag = component['Tag']
                    img_path_str = str(SYMBOLS_DIR / component['Image'])

                    if os.path.exists(img_path_str):
                        dot.node(tag, label=tag, image=img_path_str)
                    else:
                        st.warning(f"Image not found: '{img_path_str}'. Using placeholder.")
                        dot.node(tag, label=f"{tag}\n(img missing)", shape='box', style='dashed')
                    
                    dot.edge(last_node, tag)
                    last_node = tag
                
                dot.edge(last_node, "OUTLET")
                st.session_state.generated_dot = dot

# --- Display Panel ---
if st.session_state.generated_dot:
    with st.container(border=True):
        st.subheader("🖼️ Generated Diagram")
        st.graphviz_chart(st.session_state.generated_dot)
        
        try:
            png_data = st.session_state.generated_dot.pipe(format='png')
            st.download_button(
                "Download as PNG",
                data=png_data,
                file_name="generated_pnid.png",
                mime="image/png",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Could not render PNG. This can happen if an image format (like .jpg) is not supported by the Graphviz engine. Error: {e}")
