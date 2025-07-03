# app.py - FINAL, FINAL version using Embedded Base64 Image Data

import streamlit as st
import pandas as pd
from graphviz import Digraph
import base64
import os

st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator")

# This is the full, verified component list.
AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png", "ACG Filter (Suction)": "ACG filter at suction .PNG", "Air Cooler": "Air_Cooled.png",
    "Averaging Pitot Tube": "Averaging_Pitot_Tube.png", "Axial Flow Fan": "Axial_flow_fan.png", "Bag Filter/Separator": "Bag.png",
    "Bin/Silo": "Bin.png", "Briquetting Machine": "Briquetting_Machine.png", "Butterfly Valve": "Butterfly valve.PNG",
    "Catch Pot (Auto, for Condenser)": "Catch pot with Auto drain for condenser.PNG", "Catch Pot (Auto Drain)": "Catch pot with auto drain.PNG",
    "Check Valve": "Check valve.PNG", "Column / Tower": "Column.png", "Combustion Chamber": "Combustion.png",
    "Compressor (Centrifugal Type)": "Compressor_Centrifugal.png", "Compressor Silencer": "Compressor_silencers.png",
    "Cone Crusher": "Cone_Crusher.png", "Control Panel": "Control panel.PNG", "Control Valve": "Control valve.PNG",
    "Conveyor": "Conveyor.png", "Cooler": "Cooler.png", "Crane/Hoist": "Crane.png",
    "Diaphragm Meter": "Diaphragm_D_Meter.png", "Discharge Condenser": "Discharge condenser.jpg",
    "Discharge Silencer": "Discharge silencer.PNG", "Double Pipe Heat Exchanger": "Double_Pipe_Heat.png",
    "Dry Pump Model": "Dry pump model.PNG", "Dryer": "Dryer.png", "EPO Valve": "EPO valve.PNG", "Ejector": "Ejector.png",
    "FLP Control Panel": "FLP control panel.PNG", "Fan": "Fan.png", "Feeder": "Feeder.png", "Filter": "Filter.png",
    "Fin-Fan Cooler": "Fin-fan_Cooler.png", "Finned Tube Exchanger": "Finned_Tubes.png",
    "Flame Arrestor (Discharge)": "Flame arrestor at discharge.PNG", "Flame Arrestor (Suction)": "Flame arrestor at suction.PNG",
    "Flexible Connection (Discharge)": "Flexible connection at discharge.PNG", "Flexible Connection (Suction)": "Flexible connection at suction.PNG",
    "Floating Head Exchanger": "Floating_Head.png", "Flow Switch (Cooling Water)": "Flow switch for cooling water line.PNG",
    "Flowmeter": "Flowmeter.png", "Gate Valve": "Gate valve.PNG", "General Connection": "General.png",
    "Globe Valve": "Globe valve.PNG", "Hammer Crusher": "Hammer_Crusher.png", "Heater": "Heater.png",
    "Hose": "Hose.png", "Impact Crusher": "Impact_Crusher.png", "Kettle Heat Exchanger": "Kettle_Heat.png",
    "Level Switch (Purge Tank)": "Level switch for liquid purge tank.PNG", "Lift": "Lift.png",
    "Liquid Flushing Assembly": "Liquid flushing assembly.PNG", "Liquid Ring Pump": "Liquid_ring.png", "Mixer": "Mixer.png",
    "Motor": "Motor.PNG", "N2 Purge Assembly": "N2 Purge assembly.PNG", "Needle Valve": "Needel_Valve.png",
    "One-to-Many Splitter": "One-to-Many.png", "Open Tank": "Open_tank.png", "Overhead Conveyor": "Overhead.png",
    "Panel": "Panel.png", "Peristaltic Pump": "Peristaltic_pump.png", "Plate Heat Exchanger": "Plate_Heat.png",
    "Pressure Switch (N2 Purge)": "Pressure switch at nitrogen purge line.PNG",
    "Pressure Transmitter (Discharge)": "Pressure transmitter at discharge.PNG",
    "Pressure Transmitter (Suction)": "Pressure transmitter at suction.PNG", "Pressure Gauge": "Pressure_Gauges.png",
    "Reboiler Heat Exchanger": "Reboiler_Heat.png", "Reciprocating Compressor": "Reciprocating_Compressor_2.png",
    "Reciprocating Pump": "Reciprocating_pump.png", "Roller Conveyor": "Roller_Conveyor.png",
    "Roller Crusher": "Roller_Crusher.png", "Roller Press": "Roller_Press.png", "Rotary Equipment": "Rotary.png",
    "Rotary Meter": "Rotary_Meter_R.png", "Rotometer": "Rotometer.png", "Scraper": "Scraper.png",
    "Screening Machine": "Screening.png", "Screw Conveyor": "Screw_Conveyor.png", "Screw Pump": "Screw_pump.png",
    "Scrubber": "Scrubber.PNG", "Section Filter": "Section filter.PNG", "Selectable Compressor": "Selectable_Compressor.png",
    "Shell and Tube Exchanger": "Shell_and_Tube.png", "Silencer": "Silencer.png",
    "Single Pass Heat Exchanger": "Single_Pass_Heat.png", "Solenoid Valve": "Solenoid valve.PNG",
    "Spray Nozzle": "Spray.png", "Steam Traced Line": "Steam_Traced.png",
    "Strainer (Cooling Water)": "Strainer for cooling water line.PNG", "Submersible Pump": "Submersible_pump.png",
    "Suction Filter": "Suction filter.PNG", "T-Junction": "T.png", "TCV (Thermostatic Valve)": "TCV.PNG",
    "TEMA Type AEL Exchanger": "TEMA_TYPE_AEL.png", "TEMA Type AEM Exchanger": "TEMA_TYPE_AEM.png",
    "TEMA Type BEU Exchanger": "TEMA_TYPE_BEU.png", "TEMA Type NEN Exchanger": "TEMA_TYPE_NEN.png",
    "Temperature Gauge (Discharge)": "Temperature gauge at discharge.PNG",
    "Temperature Gauge (Suction)": "Temperature gauge at suction .PNG",
    "Temperature Transmitter (Discharge)": "Temperature transmitter at discharge.jpg",
    "Temperature Transmitter (Suction)": "Temperature transmitter at suction.PNG", "Thermometer": "Thermometers.png",
    "Thin-Film Dryer": "Thin-Film.png", "Traced Line": "Traced_Line.png", "U-Tube Heat Exchanger": "U-tube_Heat.png",
    "VFD Panel": "VFD.jpg", "Valves (General Symbol)": "Valves.png", "Vertical Pump": "Vertical_pump.png",
    "Vertical Vessel": "Vertical vessel.jpg", "Y-Strainer": "Y-strainer.png",
}

# --- NEW HELPER FUNCTION TO ENCODE IMAGES ---
def get_image_as_data_uri(filename):
    """Reads an image file and returns it as a base64-encoded data URI."""
    filepath = os.path.join("PN&D-Symbols-library", filename)
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        # Determine the correct mime type
        if filename.lower().endswith(".png"):
            mime_type = "image/png"
        elif filename.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        else:
            mime_type = "application/octet-stream" # Fallback
        return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        print(f"!!! FILE NOT FOUND ERROR: Cannot find {filepath}")
        return None

if 'component_list' not in st.session_state: st.session_state.component_list = []

st.header("Step 1: Add Components in Sequence")
# ... (The rest of the UI code is the same)
col1, col2 = st.columns(2)
with col1:
    with st.form("component_form", clear_on_submit=True):
        comp_type = st.selectbox("Component Type", options=sorted(list(AVAILABLE_COMPONENTS.keys())))
        comp_label = st.text_input("Component Label / Tag", "1")
        submitted = st.form_submit_button("Add Component")
        if submitted and comp_label:
            st.session_state.component_list.append({
                "Tag": comp_label, "Symbol_Image": AVAILABLE_COMPONENTS[comp_type], "Description": comp_type
            })
            st.rerun()
with col2:
    st.write("Current P&ID Components")
    if st.session_state.component_list:
        display_df = pd.DataFrame(st.session_state.component_list)[['Tag', 'Description']]
        st.dataframe(display_df, use_container_width=True)

st.header("Step 2: Generate the P&ID")
if st.button("Generate P&ID", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add at least one component.")
    else:
        with st.spinner("Drawing P&ID..."):
            dot = Digraph()
            dot.attr(rankdir='LR')
            dot.attr('node', shape='none')

            dot.node("INLET", "INLET", shape='plaintext')
            dot.node("OUTLET", "OUTLET", shape='plaintext')
            
            all_tags = ["INLET"] + [c['Tag'] for c in st.session_state.component_list] + ["OUTLET"]
            
            for component in st.session_state.component_list:
                # --- THIS IS THE CRITICAL FIX ---
                # We now get the encoded image data directly
                data_uri = get_image_as_data_uri(component['Symbol_Image'])
                
                if data_uri:
                    # Pass the data URI to the image attribute
                    dot.node(name=component['Tag'], label=component['Tag'], image=data_uri)
                else:
                    # Fallback if the image file is truly missing
                    dot.node(name=component['Tag'], label=f"{component['Tag']}\n(FILE MISSING)", shape='box', style='dashed', color='red')

            for i in range(len(all_tags) - 1):
                dot.edge(all_tags[i], all_tags[i+1])

            st.graphviz_chart(dot)

if st.button("Start Over"):
    st.session_state.component_list = []
    st.rerun()
