import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from io import BytesIO
import re

st.set_page_config(page_title="EPS Auto P&ID Generator", layout="centered")
st.title("📊 EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

def decode_uplus(text):
    """Convert strings like 'U+0031 U+0041' → '1A'"""
    if isinstance(text, str):
        matches = re.findall(r'U\+([0-9A-Fa-f]{4})', text)
        if matches:
            return ''.join(chr(int(code, 16)) for code in matches)
        return text.strip()
    return str(text)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Decode label names
        df["Text"] = df["Text"].apply(decode_uplus)

        # Drop rows with invalid or missing coordinates
        df.dropna(subset=["X", "Y"], inplace=True)

        all_labels = sorted(df["Text"].dropna().unique())
        selected_labels = st.multiselect("Select components to include", all_labels, default=all_labels)

        if selected_labels:
            filtered_df = df[df["Text"].isin(selected_labels)]

            if not filtered_df.empty:
                st.subheader("🧾 Component Table")
                st.dataframe(filtered_df)

                try:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.scatter(filtered_df["X"], filtered_df["Y"], alpha=0.6)

                    for _, row in filtered_df.iterrows():
                        ax.text(row["X"] + 10, row["Y"] + 2, row["Text"], fontsize=8)

                    ax.set_xlabel("X")
                    ax.set_ylabel("Y")
                    ax.set_title("P&ID Coordinates Preview")
                    ax.grid(True)

                    st.pyplot(fig)
                except Exception as plot_err:
                    st.error(f"Plotting failed: {plot_err}")

                if st.button("📁 Generate DXF"):
                    try:
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
                    except Exception as dxf_err:
                        st.error(f"DXF generation failed: {dxf_err}")
            else:
                st.warning("No matching rows for selected components.")
        else:
            st.info("👈 Please select one or more components to continue.")
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
