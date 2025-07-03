# app.py - FINAL, COMPLETE, AND VERIFIED VERSION

import streamlit as st
import pandas as pd
from graphviz import Digraph

st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator")
st.write("Follow the steps below to build your P&ID interactively.")

### --- MASTER COMPONENT LIST (This is the complete list) --- ###
AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png", "ACG Filter (Suction)": "ACG filter at suction .PNG",
    "ACG Filter (Suction, underscore)": "ACG filter at suction_PNG", "Air Cooler": "Air_Cooled.png",
    "Averaging Pitot Tube": "Averaging_Pitot_Tube.png", "Averaging PHot Tube": "Averaging_PHot_Tube.png",
    "Averaging PHot Tube (double underscore)": "Averaging_PHot__Tube.png",
    "Averaging Pltot Tube": "Averaging_Pltot_Tube.png", "Axial Flow Fan": "Axial_flow_fan.png",
    "Bag Filter/Separator": "Bag.png", "Bin/Silo": "Bin.png", "Briquetting Machine": "Briquetting_Machine.png",
    "Briquetting Machine (typo)": "Briguetting_Machine.png",
    "Briquetting Machine (double underscore)": "Briquetting__Machine.png", "Butterfly Valve": "Butterfly valve.PNG",
    "Catch Pot (Auto, for Condenser)": "Catch pot with Auto drain for condenser.PNG",
    "Catch Pot (Auto Drain)": "Catch pot with auto drain.PNG",
    "Catch Pot (Manual, for Condenser)": "Catch pot with manual drain for condenser.PNG",
    "Catch Pot (Manual Drain)": "Catch pot with manual drain.PNG", "Cavity Pump": "Cavity_pump.png",
    "Centrifugal Pump": "Centrifugal.png", "Centrifugal Blower": "Centrifugal_blower.png",
    "Centrifugal Compressor": "Centrifugal_Compressor_2.png", "Centrifugal T-Compressor": "Centrifugal_T_Compressor.png",
    "Check Valve": "Check valve.PNG", "Column / Tower": "Column.png", "Combustion Chamber": "Combustion.png",
    "Compressor (Centrifugal Type)": "Compressor_Centrifugal.png", "Compressor Silencer": "Compressor_silencers.png",
    "Cone Crusher": "Cone_Crusher.png", "Control Panel": "Control panel.PNG", "Control Valve": "Control valve.PNG",
    "Conveyor": "Conveyor.png", "Cooler": "Cooler.png", "Crane/Hoist": "Crane.png",
    "Diaphragm Meter": "Diaphragm_D_Meter.png", "Discharge Condenser": "Discharge condenser.jpg",
    "Discharge Silencer": "Discharge silencer.PNG", "Double Pipe Heat Exchanger": "Double_Pipe_Heat.png",
    "Dry Pump Model": "Dry pump model.PNG", "Dryer": "Dryer.png", "EPO Valve": "EPO valve.PNG", "Ejector": "Ejector.png",
    "FLP Control Panel": "FLP control panel.PNG", "Fan": "Fan.png", "Fan Blades": "Fan_blades.png",
    "Feeder": "Feeder.png", "Filter": "Filter.png", "Filters (Multiple)": "Filters.png",
    "Fin-Fan Cooler": "Fin-fan_Cooler.png", "Finned Tube Exchanger": "Finned_Tubes.png",
    "Flame Arrestor (Discharge)": "Flame arrestor at discharge.PNG",
    "Flame Arrestor (Suction)": "Flame arrestor at suction.PNG",
    "Flexible Connection (Discharge)": "Flexible connection at discharge.PNG",
    "Flexible Connection (Suction)": "Flexible connection at suction.PNG", "Floating Head Exchanger": "Floating_Head.png",
    "Flow Switch (Cooling Water)": "Flow switch for cooling water line.PNG", "Flowmeter": "Flowmeter.png",
    "Flowmeter (typo)": "Flowneter.png", "Game Meter": "Game_Meter.png", "Gate Valve": "Gate valve.PNG",
    "General Connection": "General.png", "Globe Valve": "Globe valve.PNG", "Hammer Crusher": "Hammer_Crusher.png",
    "Heater": "Heater.png", "Hose": "Hose.png", "Impact Crusher": "Impact_Crusher.png",
    "Kettle Heat Exchanger": "Kettle_Heat.png", "Level Switch (Purge Tank)": "Level switch for liquid purge tank.PNG",
    "Lift": "Lift.png", "Liquid Flushing Assembly": "Liquid flushing assembly.PNG", "Liquid Ring Pump": "Liquid_ring.png",
    "Mixer": "Mixer.png", "Motor": "Motor.PNG", "N2 Purge Assembly": "N2 Purge assembly.PNG",
    "Needle Valve": "Needel_Valve.png", "One-to-Many Splitter": "One-to-Many.png", "Open Tank": "Open_tank.png",
    "Overhead Conveyor": "Overhead.png", "Panel": "Panel.png", "Peristaltic Pump": "Peristaltic_pump.png",
    "Plate Heat Exchanger": "Plate_Heat.png", "Pressure Switch (N2 Purge)": "Pressure switch at nitrogen purge line.PNG",
    "Pressure Transmitter (Discharge)": "Pressure transmitter at discharge.PNG",
    "Pressure Transmitter (Suction)": "Pressure transmitter at suction.PNG", "Pressure Gauge": "Pressure_Gauges.png",
    "Reboiler Heat Exchanger": "Reboiler_Heat.png", "Reciprocating Compressor": "Reciprocating_Compressor_2.png",
    "Reciprocating Pump": "Reciprocating_pump.png", "Roller Conveyor": "Roller_Conveyor.png",
    "Roller Crusher": "Roller_Crusher.png", "Roller Press": "Roller_Press.png", "Rotary Equipment": "Rotary.png",
    "Rotary Meter": "Rotary_Meter_R.png", "Rotometer": "Rotometer.png", "Rotary (typo)": "Rotory.png",
    "Scraper": "Scraper.png", "Screening Machine": "Screening.png", "Screw Conveyor": "Screw_Conveyor.png",
    "Screw Pump": "Screw_pump.png", "Scrubber": "Scrubber.PNG", "Section Filter": "Section filter.PNG",
    "Selectable Compressor": "Selectable_Compressor.png", "Shell and Tube Exchanger": "Shell_and_Tube.png",
    "Silencer": "Silencer.png", "Single Pass Heat Exchanger": "Single_Pass_Heat.png", "Solenoid Valve": "Solenoid valve.PNG",
    "Spray Nozzle": "Spray.png", "Steam Traced Line": "Steam_Traced.png",
    "Strainer (Cooling Water)": "Strainer for cooling water line.PNG", "Submersible Pump": "Submersible_pump.png",
    "Suction Filter": "Suction filter.PNG", "T-Junction": "T.png", "TCV (Thermostatic Valve)": "TCV.PNG",
    "TEMA Type AEL Exchanger": "TEMA_TYPE_AEL.png", "TEMA Type AEM Exchanger": "TEMA_TYPE_AEM.png",
    "TEMA Type BEU Exchanger": "TEMA_TYPE_BEU.png", "TEMA Type NEN Exchanger": "TEMA_TYPE_NEN.png",
    "Temperature Gauge (Discharge)": "Temperature gauge at discharge.PNG", "Temperature Gauge (Suction)": "Temperature gauge at suction .PNG",
    "Temperature Gauge (Suction, underscore)": "Temperature gauge at suction_PNG",
    "Temperature Transmitter (Discharge)": "Temperature transmitter at discharge.jpg",
    "Temperature Transmitter (Suction)": "Temperature transmitter at suction.PNG", "Thermometer": "Thermometers.png",
    "Thin-Film Dryer": "Thin-Film.png", "Traced Line": "Traced_Line.png", "Traced Line (lowercase)": "Traced_line.png",
    "U-Tube Heat Exchanger": "U-tube_Heat.png", "VFD Panel": "VFD.jpg", "Valves (General Symbol)": "Valves.png",
    "Vertical Pump": "Vertical_pump.png", "Vertical Vessel": "Vertical vessel.jpg", "Y-Strainer": "Y-strainer.png",
}
### --- END OF MASTER LIST --- ###


### --- APP LOGIC --- ###
if 'component_list' not in st.session_state: st.session_state.component_list = []

st.header("Step 1: Add Components in Sequence")

col1, col2 = st.columns(2)

with col1:
    with st.form("component_form", clear_on_submit=True):
        comp_type = st.selectbox("Component Type", options=sorted(list(AVAILABLE_COMPONENTS.keys())))
        comp_label = st.text_input("Component Label / Tag (e.g., V-101, 25)")
        submitted = st.form_submit_button("Add Component")
        if submitted and comp_label:
            st.session_state.component_list.append({
                "Tag": comp_label, "Symbol_Image": AVAILABLE_COMPONENTS[comp_type], "Description": comp_type
            })
            st.rerun()

with col2:
    st.write("Current P&ID Components (in order)")
    if st.session_state.component_list:
        # Displaying the list of added components
        display_df = pd.DataFrame(st.session_state.component_list)[['Tag', 'Description']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No components added yet.")

st.header("Step 2: Generate the P&ID")
if st.button("Generate P&ID", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add at least one component.")
    else:
        with st.spinner("Drawing P&ID..."):
            dot = Digraph()
            dot.attr(rankdir='LR')
            
            dot.node("INLET", "INLET", shape='plaintext')
            dot.node("OUTLET", "OUTLET", shape='plaintext')
            
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
