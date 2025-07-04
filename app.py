import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import tempfile
import io
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, svg
import cairosvg
import streamlit.components.v1 as components

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="⚙️")
SYMBOLS_DIR = Path("symbols")

# --- ALL COMPONENTS ---
AVAILABLE_COMPONENTS = {
    "Air Cooler": "air_cooled.png",
    "Averaging Pitot Tube": "averaging_pitot_tube.png",
    "ACG Filter (Suction)": "acg_filter_at_suction.png",
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
    "Fan": "fan.png",
    "Feeder": "feeder.png",
    "Filter": "filter.png",
    "Fin-Fan Cooler": "fin-fan_cooler.png",
    "Finned Tube Exchanger": "finned_tubes.png",
    "FLP Control Panel": "flp_control_panel.png",
    "Flame Arrestor (Discharge)": "flame_arrestor_at_discharge.png",
    "Flame Arrestor (Suction)": "flame_arrestor_at_suction.png",
    "Flexible Connection (Discharge)": "flexible_connection_at_discharge.png",
    "Flexible Connection (Suction)": "flexible_connection_at_suction.png",
    "Floating Head Exchanger": "floating_head.png",
    "Flowmeter": "flowmeter.png",
    "Flow Switch (Cooling Water)": "flow_switch_for_cooling_water_line.png",
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
    "Pressure Gauge": "pressure_gauges.png",
    "Pressure Switch (N2 Purge)": "pressure_switch_at_nitrogen_purge_line.png",
    "Pressure Transmitter (Discharge)": "pressure_transmitter_at_discharge.png",
    "Pressure Transmitter (Suction)": "pressure_transmitter_at_suction.png",
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
    "Y-Strainer": "y-strainer.png",
    "50mm Fitting": "50.png"
}

# --- SESSION ---
if 'components' not in st.session_state:
    st.session_state.components = []

# --- AUTODETECT ORDER FUNCTION ---
def sort_by_process_order(components):
    order = ["Pump", "Column", "Condenser", "Receiver"]
    def get_order_index(name):
        for i, keyword in enumerate(order):
            if keyword.lower() in name.lower():
                return i
        return len(order)
    return sorted(components, key=lambda x: get_order_index(x["type"]))

# --- GENERATE GRAPH ---
def generate_graphviz(components):
    dot = Digraph("P&ID")
    dot.attr(rankdir="LR", ranksep="0.75", nodesep="0.5", concentrate="true")
    dot.attr("node", shape="none", fontsize="10", labelloc="b", imagepos="tc")
    dot.node("INLET", "INLET", shape="point", width="0.1")

    last = "INLET"
    for comp in components:
        tag, typ = comp["tag"], comp["type"]
        path = str(SYMBOLS_DIR / AVAILABLE_COMPONENTS.get(typ, "general.png"))
        if os.path.exists(path):
            dot.node(tag, label=tag, image=path)
        else:
            dot.node(tag, f"{tag}\n(missing)", shape="box", style="dashed")
        dot.edge(last, tag)
        last = tag

    dot.node("OUTLET", "OUTLET", shape="point", width="0.1")
    dot.edge(last, "OUTLET")
    return dot

# --- EXPORT DXF ---
def export_dxf(components):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, c in enumerate(components):
        y = -i * 2
        msp.add_lwpolyline([(0, y), (2, y), (2, y+1), (0, y+1)], dxfattribs={"layer": "Box"})
        msp.add_text(f"{c['tag']}: {c['type']}", dxfattribs={"height": 0.3}).set_pos((2.5, y + 0.5))
    out = io.StringIO()
    doc.write(out)
    return out.getvalue().encode()

# --- MAIN UI ---
st.title("EPS Interactive P&ID Generator")

with st.expander("Add Component"):
    ctype = st.selectbox("Component Type", options=sorted(AVAILABLE_COMPONENTS.keys()))
    tag = st.text_input("Tag", value=f"Comp-{len(st.session_state.components)+1}")
    if st.button("Add"):
        if tag in [c["tag"] for c in st.session_state.components]:
            st.warning("Tag must be unique.")
        else:
            st.session_state.components.append({"type": ctype, "tag": tag})

if st.session_state.components:
    st.subheader("Component Sequence")
    sorted_components = sort_by_process_order(st.session_state.components)
    df = pd.DataFrame(sorted_components)
    st.dataframe(df)

    dot = generate_graphviz(sorted_components)
    svg_code = dot.pipe(format="svg").decode()
    components.html(f"""
    <div style="width:100%; height:600px; overflow:auto; border:1px solid #ccc">
        {svg_code}
    </div>
    """, height=600)

    col1, col2 = st.columns(2)
    with col1:
        dxf_data = export_dxf(sorted_components)
        st.download_button("📐 Download DXF", dxf_data, "pnid.dxf", "application/dxf")

    with col2:
        st.button("🔄 Clear All", on_click=lambda: st.session_state.components.clear())
