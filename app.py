import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from io import BytesIO

st.set_page_config(page_title="EPS Auto P&ID Generator", layout="centered")

st.title("📊 EPS Auto P&ID Generator")
st.markdown("Upload Excel File with Coordinates")

uploaded_file = st.file_uploader("Drag and drop file here", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Decode and clean label names
    df['Text'] = df['Text'].astype(str).apply(lambda x: x.encode('latin1', errors='ignore').decode('latin1'))

    all_labels = sorted(df['Text'].unique())
    selected_labels = st.multiselect("Choose components", all_labels, default=all_labels)

    filtered_df = df[df['Text'].isin(selected_labels)]

    st.subheader("Preview")
    st.dataframe(filtered_df)

    # Visual plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(filtered_df['X'], filtered_df['Y'], alpha=0.6)
    for _, row in filtered_df.iterrows():
        ax.text(row['X'] + 10, row['Y'] + 2, row['Text'], fontsize=8)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("P&ID Components by Coordinates")
    ax.grid(True)
    st.pyplot(fig)

    st.success("✅ Visual generated. Next: Add logic for shapes + DXF export.")

    # DXF Export button
    if st.button("📁 Generate DXF File"):
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        for _, row in filtered_df.iterrows():
            label = row["Text"]
            x = row["X"]
            y = row["Y"]
            msp.add_text(
                label,
                dxfattribs={"height": 5, "insert": (x + 12, y + 2)}
            )

        buffer = BytesIO()
        doc.write(buffer)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download DXF File",
            data=buffer,
            file_name="EPS_PnID_Generated.dxf",
            mime="application/dxf"
        )
