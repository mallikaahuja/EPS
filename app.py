
import streamlit as st
import pandas as pd

st.image("eps_logo.png", width=200)
st.title("EPS Vacuum System Configurator")

with st.form("form"):
    name = st.text_input("Customer Name")
    vac = st.number_input("Vacuum Level (mbar)", value=10.0)
    temp = st.number_input("Operating Temperature (°C)", value=80)
    flow = st.number_input("Flow Rate (m³/h)", value=100)
    pump = st.selectbox("Pump Type", ["Dry Screw", "Liquid Ring", "Rotary Vane"])
    cooler = st.checkbox("Include Cooler")
    condenser = st.checkbox("Include Condenser")
    filter_ = st.checkbox("Include Filter")
    valve = st.checkbox("Include Valve")
    submit = st.form_submit_button("Generate")

if submit:
    tags = ["VP-101"]
    if cooler: tags.append("CO-102")
    if condenser: tags.append("CN-103")
    if filter_: tags.append("FS-104")
    if valve: tags.append("VL-105")
    product = {
        "Dry Screw": "EPS-DV240 Dry Screw Pump",
        "Liquid Ring": "EPS-LR310 Liquid Ring Pump",
        "Rotary Vane": "EPS-VN200 Rotary Vane Pump"
    }[pump]
    df = pd.DataFrame({
        "Customer Name": [name],
        "Vacuum Level (mbar)": [vac],
        "Temperature (°C)": [temp],
        "Flow Rate (m³/h)": [flow],
        "Pump Type": [pump],
        "Suggested Product": [product],
        "Tag List": [", ".join(tags)],
        "Notes": [""]
    })
    file = f"EPS_{name or 'Client'}.xlsx"
    df.to_excel(file, index=False)
    with open(file, "rb") as f:
        st.download_button("📥 Download Excel", f, file_name=file)
