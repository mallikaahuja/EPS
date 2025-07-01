import streamlit as st
import pandas as pd
import ezdxf
import matplotlib.pyplot as plt
from io import BytesIO

st.title("EPS Auto P&ID Generator")

# Upload Excel file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Step 1: Define your component name mapping here
    component_mapping = {
        "1": "Dry Pump",
        "2": "Liquid Ring Pump",
        "3": "Filter",
        "4": "Cooler",
        "5": "Condenser",
        "6": "Vacuum Gauge",
        "7": "Temperature Gauge",
        "8": "Check Valve",
        "9": "Ball Valve",
        "A": "Receiver Tank",
        # Add more as needed
    }

    # Step 2: Replace values in 'Text' column using the mapping
    df["Component"] = df["Text"].astype(str).map(component_mapping).fillna(df["Text"].astype(str))

    st.write("📄 Preview of Uploaded Data with Mapped Component Names:")
    st.dataframe(df[["Component", "X", "Y", "Layer", "Type"]])

    # Step 3: Filter valid rows for plotting and DXF export
    filtered_df = df[df["X"].notna() & df["Y"].notna()]

    # Step 4: Preview with matplotlib
    fig, ax = plt.subplots()
    ax.scatter(filtered_df["X"], filtered_df["Y"], color="blue", s=10)
    for _, row in filtered_df.iterrows():
        ax.text(row["X"] + 10, row["Y"] + 10, str(row["Component"]), fontsize=6)
    ax.set_title("P&ID Component Preview")
    ax.set_aspect('equal')
    ax.grid(True)
    st.pyplot(fig)

    # Step 5: DXF Export
    if st.button("Download DXF"):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        for _, row in filtered_df.iterrows():
            label = str(row["Component"])
            x, y = row["X"], row["Y"]
            msp.add_text(label, dxfattribs={"height": 5}).set_pos((x, y))

        dxf_buffer = BytesIO()
        doc.write(dxf_buffer)
        st.download_button(
            label="Click to Download DXF File",
            data=dxf_buffer.getvalue(),
            file_name="P&ID_Output.dxf",
            mime="application/dxf"
        )
