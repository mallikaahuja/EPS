import streamlit as st
import pandas as pd
import ezdxf
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(layout="wide")
st.title("EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ✅ Component mapping
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
        "A": "Receiver Tank"
    }

    # ✅ Map readable names
    df["Component"] = df["Text"].astype(str).map(component_mapping).fillna(df["Text"].astype(str))

    st.subheader("Preview Data (with Component Names)")
    st.dataframe(df[["Component", "X", "Y", "Layer", "Type"]])

    # ✅ Filter valid coordinates
    filtered_df = df[df["X"].notna() & df["Y"].notna()]

    # ✅ Try plotting safely
    try:
        fig, ax = plt.subplots()
        ax.scatter(filtered_df["X"], filtered_df["Y"], color="blue", s=10)
        for _, row in filtered_df.iterrows():
            ax.text(row["X"] + 10, row["Y"] + 10, str(row["Component"]), fontsize=6)
        ax.set_title("P&ID Preview")
        ax.set_aspect('equal')
        ax.grid(True)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Plot failed: {e}")

    # ✅ Try DXF export
    try:
        if st.button("Download DXF"):
            doc = ezdxf.new(dxfversion="R2010")
            msp = doc.modelspace()
            for _, row in filtered_df.iterrows():
                x, y = row["X"], row["Y"]
                label = str(row["Component"])
                msp.add_text(label, dxfattribs={"height": 5}).set_pos((x, y))

            buffer = BytesIO()
            doc.write(buffer)
            st.download_button(
                label="Click to Download DXF",
                data=buffer.getvalue(),
                file_name="EPS_PnID.dxf",
                mime="application/dxf"
            )
    except Exception as e:
        st.error(f"DXF generation failed: {e}")
