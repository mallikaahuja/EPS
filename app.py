import streamlit as st
import pandas as pd
import ezdxf
import io

st.set_page_config(page_title="EPS Auto P&ID Generator")

st.title("📊 EPS Auto P&ID Generator")
st.write("Upload Excel File with Coordinates")

uploaded_file = st.file_uploader("Upload an Excel file to get started.", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Preview")
    st.dataframe(df)

    # Create DXF
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    try:
        for i, row in df.iterrows():
            x = float(row['X'])
            y = float(row['Y'])
            label = str(row['Text'])

            # Draw circle for each component
            msp.add_circle(center=(x, y), radius=10, dxfattribs={"layer": "Components"})
            # Add text
            msp.add_text(label, dxfattribs={"height": 5}).set_pos((x + 12, y + 2))

            # Draw arrowed line to next component
            if i < len(df) - 1:
                next_x = float(df.loc[i + 1, 'X'])
                next_y = float(df.loc[i + 1, 'Y'])
                msp.add_lwpolyline([(x, y), (next_x, next_y)], dxfattribs={"layer": "Connections"})
                msp.add_arrow((x, y), (next_x, next_y))

        # Save DXF to BytesIO
        dxf_bytes = io.BytesIO()
        doc.write(dxf_bytes)
        dxf_bytes.seek(0)

        st.success("✅ P&ID DXF generated successfully!")

        st.download_button(
            label="⬇️ Download DXF File",
            data=dxf_bytes,
            file_name="EPS_PnID.dxf",
            mime="application/dxf"
        )

    except Exception as e:
        st.error(f"❌ Error while generating DXF: {e}")
