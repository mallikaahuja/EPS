pimport streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from io import BytesIO
import re

st.set_page_config(page_title="EPS Auto P&ID Generator", layout="centered")
st.title("📊 EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File with Coordinates", type=["xlsx"])

# Decode U+0041 to A etc.
def decode_uplus(text):
    if isinstance(text, str):
        matches = re.findall(r'U\+([0-9A-Fa-f]{4})', text)
        if matches:
            return ''.join(chr(int(m, 16)) for m in matches)
        return text.strip()
    return str(text)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Normalize text field
        df["Text"] = df["Text"].apply(decode_uplus)

        # Ensure coordinates are clean
        df = df.dropna(subset=["X", "Y"])

        if df.empty:
            st.warning("📭 No coordinate data found.")
        else:
            labels = sorted(df["Text"].dropna().unique())
            selected = st.multiselect("Select component labels", labels, default=labels)

            filtered_df = df[df["Text"].isin(selected)]

            if filtered_df is not None and not filtered_df.empty:
                st.subheader("🧾 Component Table")
                st.dataframe(filtered_df)

                # Preview Plot
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.scatter(filtered_df["X"], filtered_df["Y"], color="blue", s=10)

                for _, row in filtered_df.iterrows():
                    ax.text(row["X"] + 5, row["Y"] + 2, str(row["Text"]), fontsize=7)

                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                ax.set_title("P&ID Preview")
                ax.grid(True)
                st.pyplot(fig)

                if st.button("📁 Generate DXF"):
                    try:
                        doc = ezdxf.new(dxfversion="R2010")
                        msp = doc.modelspace()

                        for _, row in filtered_df.iterrows():
                            label = str(row["Text"])
                            x, y = float(row["X"]), float(row["Y"])
                            msp.add_text(label, dxfattribs={"height": 5}).set_pos((x + 12, y + 2))

                        buffer = BytesIO()
                        doc.write(buffer)
                        buffer.seek(0)

                        st.download_button(
                            label="⬇️ Download DXF File",
                            data=buffer,
                            file_name="EPS_PnID_Output.dxf",
                            mime="application/dxf"
                        )
                    except Exception as dxf_err:
                        st.error(f"❌ DXF generation failed: {dxf_err}")
            else:
                st.warning("⚠️ No matching components after filtering.")
    except Exception as e:
        st.error(f"❌ File processing failed: {e}")
