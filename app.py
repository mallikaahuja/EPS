import streamlit as st
import pandas as pd
from layout_engine import compute_positions_and_routing
from drawing_engine import render_svg, svg_to_png, export_dxf
from validation import validate_pid

# Load core data
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# Compute advanced layout/routing
positions, pipelines, inlines = compute_positions_and_routing(
    equipment_df, pipeline_df, inline_df
)

# Draw SVG and PNG
pid_svg = render_svg(equipment_df, pipeline_df, inline_df, positions, pipelines, inlines)
pid_png = svg_to_png(pid_svg)

# Streamlit UI
st.set_page_config(layout="wide")
st.title("EPS Interactive P&ID Generator (Modular/Advanced)")

tab1, tab2 = st.tabs(["Diagram Preview", "Equipment/Legend"])

with tab1:
    st.markdown(
        f"""
        <div style="border:1px solid #aaa; overflow:scroll; width:1200px; height:720px">
            <div style="width:2000px; height:1000px">
                {pid_svg}
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    st.download_button("Download PNG", pid_png, file_name="pid_diagram.png")
    st.download_button("Download DXF", export_dxf(positions, pipelines), file_name="pid_diagram.dxf")

    errors = validate_pid(equipment_df, pipeline_df, positions, pipelines)
    if errors:
        st.warning("Validation issues detected:\n" + "\n".join(errors))
    else:
        st.success("All components connected and validated.")

with tab2:
    st.subheader("Equipment List Table")
    st.dataframe(equipment_df)
    st.markdown("#### Legend")
    st.markdown("_(Rendered in SVG legend at lower center of P&ID)_")
