import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from io import BytesIO

st.set_page_config(page_title="EPS Auto P&ID Generator", layout="centered")
st.title("📊 EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Clean and decode components
    def decode_text(s):
        try:
            return s.encode().decode('unicode_escape')
        except:
            return s

    df["Text"] = df["Text"].astype(str).apply(decode_text)

    # Remove whitespace + weird chars
    df["Text"] = df["Text"].str.strip()

    # Drop missing X or Y just in case
    df = df.dropna(subset=["X", "Y"])

    all_labels = sorted(df["Text"].unique())
    selected_labels = st.multiselect("Choose components", all_labels, default=all_labels)

    if selected_labels:
        filtered_df = df[df["Text"].isin(selected_labels)]

        st.subheader("Preview")
        st.dataframe(filtered_df)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(filtered_df["X"], filtered_df["Y"], alpha=0.6)
        for _, row in filtered_df.iterrows():
            ax.text(row["X"] + 10, row["Y"] + 2, row["Text"], fontsize=8)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("P&ID Components by Coordinates")
        ax.grid(True)
        st.pyplot(fig)

        st.success("✅ Visual generated. Ready for DXF export!")

        if st.button("📁 Generate DXF File"):
            doc = ezdxf.new(dxfversion="R2010")
            msp = doc.modelspace()

            for _, row in filtered_df.iterrows():
                label = str(row["Text"])
                x = float(row["X"])
                y = float(row["Y"])
                msp.add_text(label, dxfattribs={"height": 5, "insert": (x + 12, y + 2)})

            buffer = BytesIO()
            doc.write(buffer)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download DXF File",
                data=buffer,
                file_name="EPS_PnID_Generated.dxf",
                mime="application/dxf"
            )
    else:
        st.warning("⚠️ No components selected.")
