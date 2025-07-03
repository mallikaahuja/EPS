import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
from PIL import Image, ImageDraw  # For creating default images

# --- CONFIGURATION ---
SYMBOLS_DIR = Path("PN&D-Symbols-library")  # Keep exact name with &
DEFAULT_IMAGE = "default_component.png"

# --- COMPONENT LIBRARY (COMPLETE LIST) ---
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

# --- INITIALIZATION ---
def create_default_image():
    """Create a simple default image if missing"""
    try:
        img = Image.new('RGB', (200, 100), color='lightgray')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "MISSING COMPONENT", fill='black')
        img.save(SYMBOLS_DIR / DEFAULT_IMAGE)
    except Exception as e:
        st.error(f"Could not create default image: {str(e)}")

# --- STREAMLIT APP ---
st.set_page_config(layout="wide")
st.title("Interactive P&ID Generator")

# Verify environment
if not SYMBOLS_DIR.exists():
    st.error(f"Symbols directory not found at: {SYMBOLS_DIR.absolute()}")
    st.stop()

if not (SYMBOLS_DIR / DEFAULT_IMAGE).exists():
    create_default_image()

# Initialize session state
if 'component_list' not in st.session_state:
    st.session_state.component_list = []

# --- UI ---
st.header("Step 1: Add Components")
col1, col2 = st.columns([1, 2])

with col1:
    with st.form("component_form"):
        comp_type = st.selectbox("Component Type", sorted(AVAILABLE_COMPONENTS.keys()))
        comp_tag = st.text_input("Tag (MUST BE UNIQUE)", f"Comp-{len(st.session_state.component_list)+1}")
        
        if st.form_submit_button("Add Component"):
            if any(c['Tag'] == comp_tag for c in st.session_state.component_list):
                st.error(f"Tag '{comp_tag}' already exists!")
            else:
                st.session_state.component_list.append({
                    "Tag": comp_tag,
                    "Type": comp_type,
                    "Image": AVAILABLE_COMPONENTS[comp_type]
                })
                st.rerun()

with col2:
    st.write("### Current Components")
    if st.session_state.component_list:
        st.dataframe(
            pd.DataFrame(st.session_state.component_list)[['Tag', 'Type']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No components added yet")

# --- DIAGRAM GENERATION ---
st.header("Step 2: Generate P&ID")

def generate_pnid():
    dot = Digraph(comment='P&ID')
    dot.attr(rankdir='LR', ranksep='0.5')
    dot.attr('node', shape='none', margin='0')
    
    # Add inlet/outlet
    dot.node("INLET", "INLET", shape='plaintext')
    dot.node("OUTLET", "OUTLET", shape='plaintext')
    
    # Add components
    for component in st.session_state.component_list:
        img_path = SYMBOLS_DIR / component['Image']
        if not img_path.exists():
            img_path = SYMBOLS_DIR / DEFAULT_IMAGE
            
        dot.node(
            component['Tag'],
            label='',
            image=str(img_path.absolute()),
            labelloc='b',
            labeljust='c'
        )
    
    # Connect components
    nodes = ["INLET"] + [c['Tag'] for c in st.session_state.component_list] + ["OUTLET"]
    for i in range(len(nodes)-1):
        dot.edge(nodes[i], nodes[i+1])
    
    return dot

if st.button("Generate P&ID", type="primary"):
    if not st.session_state.component_list:
        st.error("Please add components first!")
    else:
        with st.spinner("Generating diagram..."):
            try:
                dot = generate_pnid()
                st.graphviz_chart(dot)
                
                # Export functionality
                dot.render('temp_pnid', format='png', cleanup=True)
                with open('temp_pnid.png', 'rb') as f:
                    st.download_button(
                        "Download P&ID",
                        f,
                        file_name="pnid_diagram.png",
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

if st.button("Start Over", type="secondary"):
    st.session_state.component_list = []
    st.rerun()
