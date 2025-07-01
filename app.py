import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📐 Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Preview", df.head())

    # Plotting
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        ax.text(row["X"], row["Y"], str(row["Text"]), fontsize=8, ha='center')
        ax.plot(row["X"], row["Y"], 'o', markersize=3)

    ax.set_title("P&ID Components by Coordinates")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.invert_yaxis()  # DXF-style top-down
    st.pyplot(fig)

    st.success("Visual generated. Next: Add logic for shapes + DXF export")
