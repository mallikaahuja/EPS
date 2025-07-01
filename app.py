import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.title("📊 EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read file from memory buffer
        bytes_data = uploaded_file.read()
        df = pd.read_excel(BytesIO(bytes_data))

        # Component dropdown
        all_components = sorted(df["Text"].astype(str).unique())
        selected_components = st.multiselect("Choose components", options=all_components, default=all_components)

        df = df[df["Text"].astype(str).isin(selected_components)]
        st.write("### Preview", df.head())

        # Plotting
        fig, ax = plt.subplots()
        for _, row in df.iterrows():
            ax.text(row["X"], row["Y"], str(row["Text"]), fontsize=8, ha='center')
            ax.plot(row["X"], row["Y"], 'o', markersize=3)

        ax.set_title("P&ID Components by Coordinates")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.invert_yaxis()
        st.pyplot(fig)

        st.success("✅ Visual generated. Next: Add logic for shapes + DXF export.")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
else:
    st.warning("📎 Upload an Excel file to get started.")
