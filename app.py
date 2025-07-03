# app.py - FINAL Interactive P&ID Builder with Full Custom Symbol Library

import streamlit as st
import pandas as pd
from pid_drawer import generate_pid  # Your drawing engine remains the same!

st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator")
st.write("Follow the steps below to build your P&ID interactively.")

### --- MASTER COMPONENT LISTS --- ###
# This is built directly from your provided list.
# The filenames on the right MUST EXACTLY match the files in your 'PN&D-Symbols-library' folder.

AVAILABLE_EQUIPMENT = {
    # Dropdown Text                  # Exact Filename from your library
    "Air Cooler":                    "Air_Cooled.png",
    "Axial Flow Fan":                "Axial_flow_fan.png",
    "Bag Filter/Separator":          "Bag.png",
    "Bin/Silo":                      "Bin.png",
    "Briquetting Machine":           "Briquetting_Machine.png",
    "Catch Pot (Auto Drain)":        "Catch pot with auto drain.PNG",
    "Catch Pot (Auto, for Condenser)": "Catch pot with Auto drain for condenser.PNG",
    "Catch Pot (Manual Drain)":      "Catch pot with manual drain.PNG",
    "Catch Pot (Manual, for Condenser)": "Catch pot with manual drain for condenser.PNG",
    "Cavity Pump":                   "Cavity_pump.png",
    "Centrifugal Blower":            "Centrifugal_blower.png",
    "Centrifugal Compressor":        "Centrifugal_Compressor_2.png",
    "Centrifugal Pump":              "Centrifugal.png",
    "Column / Tower":                "Column.png",
    "Combustion Chamber":            "Combustion.png",
    "Compressor (Centrifugal Type)": "Compressor_Centrifugal.png",
    "Cone Crusher":                  "Cone_Crusher.png",
    "Control Panel":                 "Control panel.PNG",
    "Conveyor":                      "Conveyor.png",
    "Cooler":                        "Cooler.png",
    "Crane/Hoist":                   "Crane.png",
    "Discharge Condenser":           "Discharge condenser.jpg",
    "Double Pipe Heat Exchanger":    "Double_Pipe_Heat.png",
    "Dry Pump":                      "Dry pump model.PNG",
    "Dryer":                         "Dryer.png",
    "Ejector":                       "Ejector.png",
    "FLP Control Panel":             "FLP control panel.PNG",
    "Fan":                           "Fan.png",
    "Feeder":                        "Feeder.png",
    "Filter":                        "Filter.png",
    "Fin-Fan Cooler":                "Fin-fan_Cooler.png",
    "Finned Tube Exchanger":         "Finned_Tubes.png",
    "Floating Head Exchanger":       "Floating_Head.png",
    "Hammer Crusher":                "Hammer_Crusher.png",
    "Heater":                        "Heater.png",
    "Impact Crusher":                "Impact_Crusher.png",
    "Kettle Heat Exchanger":         "Kettle_Heat.png",
    "Lift":                          "Lift.png",
    "Liquid Ring Pump":              "Liquid_ring.png",
    "Mixer":                         "Mixer.png",
    "Motor":                         "Motor.PNG",
    "Open Tank":                     "Open_tank.png",
    "Overhead Conveyor":             "Overhead.png",
    "Panel":                         "Panel.png",
    "Peristaltic Pump":              "Peristaltic_pump.png",
    "Plate Heat Exchanger":          "Plate_Heat.png",
    "Reboiler Heat Exchanger":       "Reboiler_Heat.png",
    "Reciprocating Compressor":      "Reciprocating_Compressor_2.png",
    "Reciprocating Pump":            "Reciprocating_pump.png",
    "Roller Conveyor":               "Roller_Conveyor.png",
    "Roller Crusher":                "Roller_Crusher.png",
    "Roller Press":                  "Roller_Press.png",
    "Rotary Equipment":              "Rotary.png",
    "Scraper":                       "Scraper.png",
    "Screening Machine":             "Screening.png",
    "Screw Conveyor":                "Screw_Conveyor.png",
    "Screw Pump":                    "Screw_pump.png",
    "Scrubber":                      "Scrubber.PNG",
    "Selectable Compressor":         "Selectable_Compressor.png",
    "Shell and Tube Exchanger":      "Shell_and_Tube.png",
    "Single Pass Heat Exchanger":    "Single_Pass_Heat.png",
    "Spray Nozzle":                  "Spray.png",
    "Submersible Pump":              "Submersible_pump.png",
    "Suction Filter":                "Suction filter.PNG",
    "TEMA Type AEL Exchanger":       "TEMA_TYPE_AEL.png",
    "TEMA Type AEM Exchanger":       "TEMA_TYPE_AEM.png",
    "TEMA Type BEU Exchanger":       "TEMA_TYPE_BEU.png",
    "TEMA Type NEN Exchanger":       "TEMA_TYPE_NEN.png",
    "Thin-Film Dryer":               "Thin-Film.png",
    "U-Tube Heat Exchanger":         "U-tube_Heat.png",
    "VFD Panel":                     "VFD.jpg",
    "Vertical Pump":                 "Vertical_pump.png",
    "Vertical Vessel":               "Vertical vessel.jpg",
}

AVAILABLE_INLINE_COMPONENTS = {
    # Dropdown Text                  # Exact Filename from your library
    "50mm Fitting":                  "50.png",
    "ACG Filter (Suction)":          "ACG filter at suction .PNG",
    "Averaging Pitot Tube":          "Averaging_Pitot_Tube.png",
    "Butterfly Valve":               "Butterfly valve.PNG",
    "Check Valve":                   "Check valve.PNG",
    "Compressor Silencer":           "Compressor_silencers.png",
    "Control Valve":                 "Control valve.PNG",
    "Diaphragm Meter":               "Diaphragm_D_Meter.png",
    "Discharge Silencer":            "Discharge silencer.PNG",
    "EPO Valve":                     "EPO valve.PNG",
    "Flame Arrestor (Discharge)":    "Flame arrestor at discharge.PNG",
    "Flame Arrestor (Suction)":      "Flame arrestor at suction.PNG",
    "Flexible Connection (Discharge)": "Flexible connection at discharge.PNG",
    "Flexible Connection (Suction)": "Flexible connection at suction.PNG",
    "Flow Switch (Cooling Water)":   "Flow switch for cooling water line.PNG",
    "Flowmeter":                     "Flowmeter.png",
    "Flume Meter":                   "Fiume_Meter.png",
    "Gate Valve":                    "Gate valve.PNG",
    "General Connection":            "General.png",
    "Globe Valve":                   "Globe valve.PNG",
    "Hose":                          "Hose.png",
    "Level Switch (Purge Tank)":     "Level switch for liquid purge tank.PNG",
    "Liquid Flushing Assembly":      "Liquid flushing assembly.PNG",
    "N2 Purge Assembly":             "N2 Purge assembly.PNG",
    "Needle Valve":                  "Needel_Valve.png",
    "One-to-Many Splitter":          "One-to-Many.png",
    "Pressure Gauge":                "Pressure_Gauges.png",
    "Pressure Switch (N2 Purge)":    "Pressure switch at nitrogen purge line.PNG",
    "Pressure Transmitter (Discharge)": "Pressure transmitter at discharge.PNG",
    "Pressure Transmitter (Suction)": "Pressure transmitter at suction.PNG",
    "Rotary Meter":                  "Rotary_Meter_R.png",
    "Rotometer":                     "Rotometer.png",
    "Silencer":                      "Silencer.png",
    "Solenoid Valve":                "Solenoid valve.PNG",
    "Steam Traced Line":             "Steam_Traced.png",
    "Strainer (Cooling Water)":      "Strainer for cooling water line.PNG",
    "T-Junction":                    "T.png",
    "TCV (Thermostatic Valve)":      "TCV.PNG",
    "Temperature Gauge (Discharge)": "Temperature gauge at discharge.PNG",
    "Temperature Gauge (Suction)":   "Temperature gauge at suction .PNG",
    "Temperature Transmitter (Discharge)": "Temperature transmitter at discharge.jpg",
    "Temperature Transmitter (Suction)": "Temperature transmitter at suction.PNG",
    "Thermometer":                   "Thermometers.png",
    "Traced Line":                   "Traced_Line.png",
    "Valves (General Symbol)":       "Valves.png",
    "Y-Strainer":                    "Y-strainer.png",
}

### --- APP LOGIC (No changes needed below this line) --- ###

# Initialize Session State
if 'equipment_list' not in st.session_state:
    st.session_state.equipment_list = []
if 'piping_list' not in st.session_state:
    st.session_state.piping_list = []
if 'inline_list' not in st.session_state:
    st.session_state.inline_list = []

# UI Section
st.header("Step 1: Add Major Equipment")
col1, col2 = st.columns([1, 2])
with col1:
    with st.form("equipment_form", clear_on_submit=True):
        equip_tag = st.text_input("Equipment Tag (e.g., V-101)")
        equip_type = st.selectbox("Equipment Type", options=sorted(list(AVAILABLE_EQUIPMENT.keys())))
        submitted = st.form_submit_button("Add Equipment")
        if submitted and equip_tag:
            st.session_state.equipment_list.append({
                "Tag": equip_tag, "Description": equip_type, "Symbol_Image": AVAILABLE_EQUIPMENT[equip_type]
            })
with col2:
    st.write("Current Equipment:")
    st.dataframe(pd.DataFrame(st.session_state.equipment_list), use_container_width=True)

if len(st.session_state.equipment_list) >= 2:
    st.header("Step 2: Connect Equipment with Piping")
    pipe_col1, pipe_col2 = st.columns([1, 2])
    equipment_tags = [eq['Tag'] for eq in st.session_state.equipment_list]
    with pipe_col1:
        with st.form("piping_form", clear_on_submit=True):
            pipe_tag = st.text_input("Pipe Tag (e.g., P-01)")
            from_tag = st.selectbox("From", options=equipment_tags)
            to_tag = st.selectbox("To", options=equipment_tags)
            submitted = st.form_submit_button("Add Pipe")
            if submitted and pipe_tag and from_tag and to_tag:
                if from_tag == to_tag: st.error("Equipment cannot be connected to itself.")
                else: st.session_state.piping_list.append({
                    "PipeTag": pipe_tag, "From_Tag": from_tag, "To_Tag": to_tag
                })
    with pipe_col2:
        st.write("Current Piping:")
        st.dataframe(pd.DataFrame(st.session_state.piping_list), use_container_width=True)

if st.session_state.piping_list:
    st.header("Step 3: Add Valves and Instruments to Pipes")
    inline_col1, inline_col2 = st.columns([1, 2])
    pipe_tags = [p['PipeTag'] for p in st.session_state.piping_list]
    with inline_col1:
        with st.form("inline_form", clear_on_submit=True):
            on_pipe = st.selectbox("Select Pipe", options=pipe_tags)
            comp_type = st.selectbox("Component Type", options=sorted(list(AVAILABLE_INLINE_COMPONENTS.keys())))
            comp_label = st.text_input("Component Label (e.g., PT-101, 25)")
            submitted = st.form_submit_button("Add Component to Pipe")
            if submitted and on_pipe and comp_label:
                st.session_state.inline_list.append({
                    "Component_Tag": f"{on_pipe}_{comp_label}", "Description": comp_type, "On_PipeTag": on_pipe,
                    "Symbol_Image": AVAILABLE_INLINE_COMPONENTS[comp_type], "Label": comp_label
                })
    with inline_col2:
        st.write("Current In-Line Components:")
        st.dataframe(pd.DataFrame(st.session_state.inline_list), use_container_width=True)

st.header("Step 4: Generate the P&ID")
if st.button("Generate Detailed P&ID", type="primary"):
    if not st.session_state.equipment_list: st.error("Please add at least one piece of equipment.")
    else:
        with st.spinner("Drawing detailed P&ID..."):
            df_equipment = pd.DataFrame(st.session_state.equipment_list)
            df_piping = pd.DataFrame(st.session_state.piping_list)
            df_inline = pd.DataFrame(st.session_state.inline_list)
            pid_diagram = generate_pid(df_equipment, df_piping, df_inline)
            st.subheader("Generated P&ID")
            st.graphviz_chart(pid_diagram)

if st.button("Start Over / Clear All"):
    st.session_state.equipment_list = []; st.session_state.piping_list = []; st.session_state.inline_list = []
    st.rerun()
