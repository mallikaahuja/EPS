import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
from streamlit_elements import elements, mui

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols") 

# --- COMPLETE COMPONENT LIBRARY (STANDARDIZED) ---
# All filenames are lowercase, use underscores for spaces, and are .png
AVAILABLE_COMPONENTS = {
    "50mm Fitting": "50.png",
    "ACG Filter (Suction)": "acg_filter_at_suction.png",
    "Air Cooler": "air_cooled.png",
    "Averaging Pitot Tube": "averaging_pitot_tube.png",
    "Axial Flow Fan": "axial_flow_fan.png",
    "Bag Filter/Separator": "bag.png",
    "Base Plate": "base_plate.png",
    "Bin/Silo": "bin.png",
    "Briquetting Machine": "briquetting_machine.png",
    "Butterfly Valve": "butterfly_valve.png",
    "Catch Pot (Auto, for Condenser)": "catch_pot_with_auto_drain_for_condenser.png",
    "Catch Pot (Auto Drain)": "catch_pot_with_auto_drain.png",
    "Check Valve": "check_valve.png",
    "Column / Tower": "column.png",
    "Combustion Chamber": "combustion.png",
    "Compressor (Centrifugal Type)": "compressor_centrifugal.png",
    "Compressor Silencer": "compressor_silencers.png",
    "Cone Crusher": "cone_crusher.png",
    "Control Panel": "control_panel.png",
    "Control Valve": "control_valve.png",
    "Conveyor": "conveyor.png",
    "Cooler": "cooler.png",
    "Crane/Hoist": "crane.png",
    "Diaphragm Meter": "diaphragm_d_meter.png",
    "Discharge Condenser": "discharge_condenser.png",
    "Discharge Silencer": "discharge_silencer.png",
    "Double Pipe Heat Exchanger": "double_pipe_heat.png",
    "Dry Pump Model": "dry_pump_model.png",
    "Dryer": "dryer.png",
    "EPO Valve": "epo_valve.png",
    "Ejector": "ejector.png",
    "FLP Control Panel": "flp_control_panel.png",
    "Fan": "fan.png",
    "Feeder": "feeder.png",
    "Filter": "filter.png",
    "Fin-Fan Cooler": "fin-fan_cooler.png",
    "Finned Tube Exchanger": "finned_tubes.png",
    "Flame Arrestor (Discharge)": "flame_arrestor_at_discharge.png",
    "Flame Arrestor (Suction)": "flame_arrestor_at_suction.png",
    "Flexible Connection (Discharge)": "flexible_connection_at_discharge.png",
    "Flexible Connection (Suction)": "flexible_connection_at_suction.png",
    "Floating Head Exchanger": "floating_head.png",
    "Flow Switch (Cooling Water)": "flow_switch_for_cooling_water_line.png",
    "Flowmeter": "flowmeter.png",
    "Gate Valve": "gate_valve.png",
    "General Connection": "general.png",
    "Globe Valve": "globe_valve.png",
    "Hammer Crusher": "hammer_crusher.png",
    "Heater": "heater.png",
    "Hose": "hose.png",
    "Impact Crusher": "impact_crusher.png",
    "Kettle Heat Exchanger": "kettle_heat.png",
    "Level Switch (Purge Tank)": "level_switch_for_liquid_purge_tank.png",
    "Lift": "lift.png",
    "Liquid Flushing Assembly": "liquid_flushing_assembly.png",
    "Liquid Ring Pump": "liquid_ring.png",
    "Mixer": "mixer.png",
    "Motor": "motor.png",
    "N2 Purge Assembly": "n2_purge_assembly.png",
    "Needle Valve": "needel_valve.png",
    "One-to-Many Splitter": "one-to-many.png",
    "Open Tank": "open_tank.png",
    "Overhead Conveyor": "overhead.png",
    "Panel": "panel.png",
    "Peristaltic Pump": "peristaltic_pump.png",
    "Plate Heat Exchanger": "plate_heat.png",
    "Pressure Switch (N2 Purge)": "pressure_switch_at_nitrogen_purge_line.png",
    "Pressure Transmitter (Discharge)": "pressure_transmitter_at_discharge.png",
    "Pressure Transmitter (Suction)": "pressure_transmitter_at_suction.png",
    "Pressure Gauge": "pressure_gauges.png",
    "Reboiler Heat Exchanger": "reboiler_heat.png",
    "Reciprocating Compressor": "reciprocating_compressor_2.png",
    "Reciprocating Pump": "reciprocating_pump.png",
    "Roller Conveyor": "roller_conveyor.png",
    "Roller Crusher": "roller_crusher.png",
    "Roller Press": "roller_press.png",
    "Rotary Equipment": "rotary.png",
    "Rotary Meter": "rotary_meter_r.png",
    "Rotometer": "rotometer.png",
    "Scraper": "scraper.png",
    "Screening Machine": "screening.png",
    "Screw Conveyor": "screw_conveyor.png",
    "Screw Pump": "screw_pump.png",
    "Scrubber": "scrubber.png",
    "Section Filter": "section_filter.png",
    "Selectable Compressor": "selectable_compressor.png",
    "Shell and Tube Exchanger": "shell_and_tube.png",
    "Silencer": "silencer.png",
    "Single Pass Heat Exchanger": "single_pass_heat.png",
    "Solenoid Valve": "solenoid_valve.png",
    "Spray Nozzle": "spray.png",
    "Steam Traced Line": "steam_traced.png",
    "Strainer (Cooling Water)": "strainer_for_cooling_water_line.png",
    "Submersible Pump": "submersible_pump.png",
    "Suction Filter": "suction_filter.png",
    "T-Junction": "t.png",
    "TCV (Thermostatic Valve)": "tcv.png",
    "TEMA Type AEL Exchanger": "tema_type_ael.png",
    "TEMA Type AEM Exchanger": "tema_type_aem.png",
    "TEMA Type BEU Exchanger": "tema_type_beu.png",
    "TEMA Type NEN Exchanger": "tema_type_nen.png",
    "Temperature Gauge (Discharge)": "temperature_gauge_at_discharge.png",
    "Temperature Gauge (Suction)": "temperature_gauge_at_suction.png",
    "Temperature Transmitter (Discharge)": "temperature_transmitter_at_discharge.png",
    "Temperature Transmitter (Suction)": "temperature_transmitter_at_suction.png",
    "Thermometer": "thermometers.png",
    "Thin-Film Dryer": "thin-film.png",
    "Traced Line": "traced_line.png",
    "U-Tube Heat Exchanger": "u-tube_heat.png",
    "VFD Panel": "vfd_panel.png",
    "Valves (General Symbol)": "valves.png",
    "Vertical Pump": "vertical_pump.png",
    "Vertical Vessel": "vertical_vessel.png",
    "Y-Strainer": "y-strainer.png"
}

# --- INITIALIZE SESSION STATE ---
if 'components' not in st.session_state:
    st.session_state.components = []
if "show_modal" not in st.session_state:
    st.session_state.show_modal = False
if 'generated_dot' not in st.session_state:
    st.session_state.generated_dot = None

# --- P&ID GENERATION FUNCTION ---
def generate_pnid_graph(component_list):
    """Generates a Graphviz object from a list of components."""
    if not component_list:
        return None
        
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', ranksep='0.75', nodesep='0.5')
    dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
    
    dot.node("INLET", "INLET", shape='point', width='0.1')
    last_node = "INLET"
    
    for i, component in enumerate(component_list):
        tag = component['Tag']
        img_path = str(SYMBOLS_DIR / component['Image'])

        if os.path.exists(img_path):
            dot.node(tag, label=tag, image=img_path)
        else:
            # Fallback for missing images
            st.warning(f"Image not found: '{img_path}'. Using placeholder.")
            dot.node(tag, label=f"{tag}\n(img missing)", shape='box', style='dashed')
        
        dot.edge(last_node, tag)
        last_node = tag
        
    dot.node("OUTLET", "OUTLET", shape='point', width='0.1')
    dot.edge(last_node, "OUTLET")
    return dot

# --- SIDEBAR & MODAL FOR ADDING COMPONENTS ---
with st.sidebar:
    st.subheader("P&ID Builder")
    if st.button("➕ Add New Component", use_container_width=True):
        st.session_state.show_modal = True

with mui.Modal(
    "Add a New Component to the Sequence",
    open=st.session_state.show_modal,
    onClose=lambda: setattr(st.session_state, 'show_modal', False),
):
    with elements(f"add_component_modal_{len(st.session_state.components)}"):
        with mui.Box(sx={"p": 2}):
            ctype = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()), key="ctype_modal")
            tag = st.text_input("Component Tag / Label (must be unique)", value=f"Comp-{len(st.session_state.components) + 1}", key="tag_modal")
            
            if st.button("Save Component", key="save_modal"):
                if any(c['Tag'] == tag for c in st.session_state.components):
                    st.error(f"Tag '{tag}' already exists!")
                else:
                    st.session_state.components.append({
                        "Tag": tag,
                        "Type": ctype,
                        "Image": AVAILABLE_COMPONENTS[ctype]
                    })
                    st.session_state.show_modal = False
                    st.rerun()

# --- MAIN PAGE LAYOUT ---
st.title("EPS Interactive P&ID Generator")
st.markdown("Use the sidebar to add components, then view the live preview and download the final diagram.")

col1, col2 = st.columns([1, 1.5])

with col1:
    with st.container(border=True):
        st.subheader("Component Sequence")
        if st.session_state.components:
            df = pd.DataFrame(st.session_state.components)
            st.dataframe(df[['Tag', 'Type']], use_container_width=True, hide_index=True)
            if st.button("Clear All", use_container_width=True, type="secondary"):
                st.session_state.components = []
                st.session_state.generated_dot = None
                st.rerun()
        else:
            st.info("No components added. Click 'Add New Component' in the sidebar to start.")

with col2:
    with st.container(border=True):
        st.subheader("Live P&ID Preview")
        if st.session_state.components:
            # Generate the graph immediately for live preview
            p_and_id_graph = generate_pnid_graph(st.session_state.components)
            if p_and_id_graph:
                st.graphviz_chart(p_and_id_graph)
                
                # --- Download Button Logic ---
                try:
                    png_data = p_and_id_graph.pipe(format='png')
                    st.download_button(
                        label="⬇️ Download P&ID as PNG",
                        data=png_data,
                        file_name="generated_pnid.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Could not render PNG. This can happen if an image format (like .jpg) is not supported by the Graphviz engine. Error: {e}")
        else:
            st.info("Your diagram will appear here once you add components.")
