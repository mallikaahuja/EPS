
import streamlit as st
import ezdxf
import pandas as pd

def generate_dxf(components, filename):
    doc = ezdxf.new()
    msp = doc.modelspace()
    x, y = 0, 0
    for i, comp in enumerate(components, start=1):
        msp.add_text(f"{i}. {comp}", dxfattribs={"height": 0.5}).set_pos((x, y))
        y -= 1
    doc.saveas(filename)

# EPS Dry Pump KDP330 System Components
components = [
    "Dry pump Model KDP330",
    "Motor – 10HP, 2 POLE , B5",
    "VFD",
    "EPO valve",
    "N2 purge assembly",
    "Liquid flushing assembly",
    "Suction condenser",
    "Catch pot for above with manual drain",
    "Catch pot for above with Auto drain",
    "Suction filter",
    "Scrubber",
    "Flame arrestor at suction",
    "Flame arrestor at discharge",
    "Flexible connection at suction",
    "Flexible connection at discharge",
    "Pressure transmitter at discharge",
    "Discharge condenser",
    "Catch pot for above with manual drain",
    "Catch pot for above with Auto drain",
    "Discharge silencer",
    "Temperature transmitter at suction",
    "Temperature transmitter at discharge",
    "Temperature gauge at suction",
    "Temperature gauge at discharge",
    "ACG filter at suction",
    "TCV for cooling water line",
    "Level switch for liquid purge tank",
    "Flow switch for cooling water line",
    "Strainer for cooling water line",
    "Base plate",
    "Interconnecting piping with line size",
    "FLP Control panel – mounted on skid",
    "Control panel – split",
    "Temperature transmitter at Cooling Jacket",
    "Pressure transmitter at Suction",
    "Pressure switch at nitrogen Purge line"
]

st.title("EPS Auto P&ID Generator")
st.markdown("Select components to include in your system and generate a P&ID (DXF format).")

selected = st.multiselect("Choose components:", components)

if selected:
    filename = "EPS_PnID.dxf"
    generate_dxf(selected, filename)
    with open(filename, "rb") as f:
        st.download_button("📥 Download DXF P&ID", f, file_name=filename)
