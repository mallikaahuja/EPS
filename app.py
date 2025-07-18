import streamlit as st
import pandas as pd
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import ezdxf
import cairosvg
from io import BytesIO
from professional_symbols import PROFESSIONAL_ISA_SYMBOLS, get_component_symbol
import json

# Load component port mapping
with open("component_mapping.json", "r") as f:
    COMPONENT_PORTS = json.load(f)
    # Transform for fast lookup
    PORT_MAP = {}
    for item in COMPONENT_PORTS:
        comp = item["Component"]
        if comp not in PORT_MAP:
            PORT_MAP[comp] = {}
        PORT_MAP[comp][item["Port Name"]] = (item["dx"], item["dy"])

# Load equipment, pipeline, and in-line lists
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# Helper: Get all components with types and tags
def get_all_components():
    return pd.concat([
        equipment_df.assign(Type="Equipment"),
        pipeline_df.assign(Type="Pipeline"),
        inline_df.assign(Type="Inline")
    ], ignore_index=True)

# Define flow order for auto-placement
DEFAULT_LAYOUT_ORDER = [
    "pump", "scrubber", "condenser", "catch pot", "receiver", "silencer"
]

# --- Layout logic ---
def auto_place_components(equipment_df):
    """
    Auto-assign coordinates to components based on DEFAULT_LAYOUT_ORDER.
    Returns: dict of component ID to (x, y)
    """
    x0, y0, x_spacing, y_spacing = 180, 320, 280, 120
    positions = {}
    y_offsets = {}
    i = 0
    for order in DEFAULT_LAYOUT_ORDER:
        found = equipment_df[equipment_df['ID'].str.lower().str.contains(order)]
        for j, (_, row) in enumerate(found.iterrows()):
            positions[row['ID']] = (x0 + i * x_spacing, y0 + j * y_spacing)
            y_offsets[row['ID']] = j * y_spacing
        i += 1
    # Fallback for unplaced
    for _, row in equipment_df.iterrows():
        if row['ID'] not in positions:
            positions[row['ID']] = (x0 + i * x_spacing, y0)
            i += 1
    return positions

# --- Drawing ---
def render_equipment_list_svg(equipment_df):
    # Draws a legend table block, returns SVG string
    header = ["Tag", "Description", "Spec"]
    x0, y0, row_h, col_w = 30, 40, 22, [60, 170, 120]
    svg = f'<g id="equipment-list"><text x="{x0}" y="{y0}" font-size="18" font-weight="bold">EQUIPMENT LIST</text>'
    y = y0 + 24
    svg += f'<rect x="{x0-8}" y="{y0+5}" width="{sum(col_w)}" height="{row_h}" fill="#eee" stroke="#222"/>'  # header bg
    for c, head in enumerate(header):
        svg += f'<text x="{x0 + sum(col_w[:c]) + 5}" y="{y}" font-size="12" font-weight="bold">{head}</text>'
    y += row_h
    for _, row in equipment_df.iterrows():
        svg += f'<rect x="{x0-8}" y="{y-row_h+5}" width="{sum(col_w)}" height="{row_h}" fill="#fff" stroke="#bbb"/>'
        for c, key in enumerate(["ID", "Description", "Specs"]):
            val = str(row[key]) if key in row else ""
            svg += f'<text x="{x0 + sum(col_w[:c]) + 5}" y="{y}" font-size="12">{val}</text>'
        y += row_h
    svg += '</g>'
    return svg

def render_pid_svg(equipment_df, pipeline_df, inline_df):
    # High-level function to render entire P&ID SVG layout
    component_positions = auto_place_components(equipment_df)
    svg_equip = ""
    symbol_size = 80  # px square for symbol box
    port_radius = 7

    # Draw all equipment
    for _, row in equipment_df.iterrows():
        comp_id = row["ID"]
        desc = row["Description"]
        x, y = component_positions.get(comp_id, (100, 100))
        symbol_svg = get_component_symbol(comp_id, width=symbol_size, height=symbol_size)
        svg_equip += f'<g id="{comp_id}"><g transform="translate({x},{y})">{symbol_svg}</g>'
        # Draw tag label under symbol
        svg_equip += f'<text x="{x + symbol_size/2 - 15}" y="{y + symbol_size + 20}" font-size="13">{comp_id}</text>'
        svg_equip += '</g>'
        # Draw spec info (optional): f'<text x="{x}" y="{y + symbol_size + 40}" ...>'

    # Draw pipelines (use mapping for precise connection)
    svg_pipes = ""
    for _, row in pipeline_df.iterrows():
        src, dst = row["Source"], row["Destination"]
        src_port, dst_port = row.get("Source Port", "discharge"), row.get("Destination Port", "suction")
        # Lookup absolute positions of the ports
        src_xy = tuple(map(sum, zip(component_positions.get(src, (0, 0)), PORT_MAP.get(src, {}).get(src_port, (0, 0)))))
        dst_xy = tuple(map(sum, zip(component_positions.get(dst, (0, 0)), PORT_MAP.get(dst, {}).get(dst_port, (0, 0)))))
        # Draw pipe
        if src_xy and dst_xy:
            svg_pipes += f'<polyline points="{src_xy[0]},{src_xy[1]} {dst_xy[0]},{dst_xy[1]}" stroke="#222" stroke-width="6" fill="none" marker-end="url(#arrowhead)" />'
            # Optionally: break into elbows for L-shaped lines, if needed

    # Draw inline components (valves, meters)
    svg_inline = ""
    for _, row in inline_df.iterrows():
        comp_id = row["ID"]
        # For now, randomly assign on first available pipeline midpoint
        # (Advanced: map to exact pipeline based on process design)
        # Here, just skip, or implement as needed
        pass

    # SVG header and defs (arrowhead, etc)
    svg_header = """
    <svg width="1700" height="900" viewBox="0 0 1700 900" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrowhead" markerWidth="14" markerHeight="12" refX="14" refY="6" orient="auto" markerUnits="strokeWidth">
          <polygon points="2,2 14,6 2,10" fill="#222" />
        </marker>
      </defs>
    """

    # Equipment List Table (top left)
    svg_legend = render_equipment_list_svg(equipment_df)

    # Combine SVG parts
    svg = svg_header + svg_legend + svg_pipes + svg_equip + svg_inline + "</svg>"
    return svg

def validate_pid(equipment_df, pipeline_df):
    # Validation: all components are connected, no floating, etc.
    errors = []
    # Check that each equipment appears in at least one pipeline
    all_equipment = set(equipment_df["ID"])
    pipeline_src = set(pipeline_df["Source"])
    pipeline_dst = set(pipeline_df["Destination"])
    unconnected = all_equipment - (pipeline_src | pipeline_dst)
    if unconnected:
        errors.append(f"Unconnected equipment: {', '.join(unconnected)}")
    return errors

def svg_to_png(svg_string, scale=1.5):
    # Convert SVG string to PNG for display/export
    png_bytes = cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)
    return png_bytes

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("EPS Interactive P&ID Generator (Standards Compliant)")

tab1, tab2 = st.tabs(["Diagram Preview", "Equipment Table"])
with tab1:
    st.subheader("P&ID Diagram")
    pid_svg = render_pid_svg(equipment_df, pipeline_df, inline_df)
    # Display SVG with pan/zoom
    st.markdown(
        f"""
        <div style="border:1px solid #aaa; overflow:scroll; width:1200px; height:720px">
            <div style="width:1700px; height:900px">
                {pid_svg}
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    # PNG preview for download
    png_bytes = svg_to_png(pid_svg)
    st.download_button("Download PNG", png_bytes, file_name="pid_diagram.png")

    # DXF export (optional, not shown here for brevity)

    # Validation Output
    errors = validate_pid(equipment_df, pipeline_df)
    if errors:
        st.warning("Validation issues detected:\n" + "\n".join(errors))
    else:
        st.success("All components connected and validated.")

with tab2:
    st.subheader("Equipment List Table")
    st.dataframe(equipment_df)

# --- End of file ---
