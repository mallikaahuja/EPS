import streamlit as st
import pandas as pd
import ezdxf
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="EPS Auto P&ID Generator")
st.title("📊 EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Choose components")
    unique_components = df['Text'].astype(str).unique()
    selected_components = st.multiselect("Filter components to include", unique_components, default=unique_components)

    df = df[df['Text'].astype(str).isin(selected_components)]

    st.subheader("Preview")
    st.dataframe(df)

    # Optional: Visual preview in Streamlit
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["X"], df["Y"], c='blue')
    for _, row in df.iterrows():
        ax.text(row["X"] + 5, row["Y"] + 5, str(row["Text"]), fontsize=9)
    ax.set_title("P&ID Component Layout Preview")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    st.pyplot(fig)

    # DXF generation
    doc = ezdxf.new()
    msp = doc.modelspace()

    for i, row in df.iterrows():
        x, y = float(row["X"]), float(row["Y"])
        label = str(row["Text"])

        # Add a circle for the component
        msp.add_circle((x, y), radius=10)

        # Add label next to the component
        msp.add_text(label, dxfattribs={"height": 5}).set_pos((x + 12, y + 2))

        # Add line to next component
        if i < len(df) - 1:
            next_x = float(df.iloc[i + 1]["X"])
            next_y = float(df.iloc[i + 1]["Y"])
            msp.add_lwpolyline([(x, y), (next_x, next_y)], dxfattribs={"layer": "FlowLine"})

    # Save DXF to BytesIO
    dxf_io = io.BytesIO()
    doc.write(dxf_io)
    dxf_io.seek(0)

    st.success("✅ DXF file generated! Download below:")
    st.download_button("⬇️ Download DXF", data=dxf_io, file_name="EPS_PnID.dxf", mime="application/dxf")
