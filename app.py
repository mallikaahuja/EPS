import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
from streamlit_elements import elements, mui, dashboard
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, svg
import tempfile
import cairosvg
import io

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols")

# --- FULL COMPONENT LIBRARY ---
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

# --- GRAPHVIZ PREVIEW ---
def generate_graphviz_dot(component_list):
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', ranksep='0.75', nodesep='0.5')
    dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
    dot.node("INLET", "INLET", shape='point', width='0.1')
    last_node = "INLET"
    for comp in component_list:
        tag = comp['tag']
        img_path = f"./symbols/{AVAILABLE_COMPONENTS.get(comp['type'], 'general.png')}"
        if os.path.exists(img_path):
            dot.node(tag, label=tag, image=img_path)
        else:
            dot.node(tag, label=f"{tag}\n(img missing)", shape='box', style='dashed')
        dot.edge(last_node, tag)
        last_node = tag
    dot.node("OUTLET", "OUTLET", shape='point', width='0.1')
    dot.edge(last_node, "OUTLET")
    return dot

# --- DXF EXPORT ---
def create_dxf_data(component_list):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for idx, c in enumerate(component_list):
        y = -idx * 2
        msp.add_lwpolyline([(0, y), (2, y), (2, y+1), (0, y+1), (0, y)], dxfattribs={"layer": "Component"})
        msp.add_text(f"{c['tag']}: {c['type']}", dxfattribs={
            'height': 0.3,
            'insert': (2.5, y + 0.5)
        })
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')

# --- PDF EXPORT ---
def create_pdf_data(component_list):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for idx, c in enumerate(component_list):
        y = -idx * 2
        msp.add_lwpolyline([(0, y), (2, y), (2, y+1), (0, y+1), (0, y)])
        msp.add_text(f"{c['tag']}: {c['type']}", dxfattribs={
            'height': 0.3,
            'insert': (2.5, y + 0.5)
        })

    context = RenderContext(doc)
    backend = svg.SVGBackend()
    Frontend(context, backend).draw_layout(msp)
    svg_string = backend.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        cairosvg.svg2pdf(bytestring=svg_string.encode('utf-8'), write_to=tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            pdf_bytes = f.read()
    os.unlink(tmpfile.name)
    return pdf_bytes

# --- MAIN UI ---
st.title("EPS Interactive P&ID Generator")

with elements("main_frame"):
    with st.sidebar:
        st.subheader("P&ID Builder")
        if mui.Button("➕ Add New Component", variant="contained", sx={"width": "100%"}):
            st.session_state.show_modal = True

    with mui.Modal(
        "Add a New Component",
        open=st.session_state.show_modal,
        onClose=lambda: setattr(st.session_state, 'show_modal', False)
    ):
        with mui.Box(sx={"p": 4}):
            ctype = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()), key="modal_ctype")
            tag = st.text_input("Tag / Label (must be unique)", value=f"Comp-{len(st.session_state.components)+1}", key="modal_tag")

            if st.button("Save Component", key="modal_save"):
                if any(c['tag'] == tag for c in st.session_state.components):
                    st.error(f"Tag '{tag}' already exists!")
                else:
                    st.session_state.components.append({"type": ctype, "tag": tag})
                    st.session_state.show_modal = False
                    st.rerun()

    st.subheader("Component Sequence (Drag to Reorder)")
    layout = [
        dashboard.Item(c["tag"], 0, i, 12, 1) for i, c in enumerate(st.session_state.components)
    ]

    with dashboard.Grid(layout):
        for c in st.session_state.components:
            mui.Paper(f"{c['tag']} — {c['type']}", key=c["tag"], sx={"p": 1, "textAlign": "center"})

    st.markdown("---")

    if st.session_state.components:
        st.subheader("Live Preview & Export")
        dot = generate_graphviz_dot(st.session_state.components)
        st.graphviz_chart(dot)

        col1, col2 = st.columns(2)
        with col1:
            try:
                pdf_data = create_pdf_data(st.session_state.components)
                st.download_button("📄 Download PDF", pdf_data, "p-and-id.pdf", "application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF Export Failed: {e}")
        with col2:
            try:
                dxf_data = create_dxf_data(st.session_state.components)
                st.download_button("📐 Download DXF", dxf_data, "p-and-id.dxf", "application/dxf", use_container_width=True)
            except Exception as e:
                st.error(f"DXF Export Failed: {e}")
