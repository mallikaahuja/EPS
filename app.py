import streamlit as st
import pandas as pd
import os
import datetime
import io
import ezdxf
import openai
import requests
import base64
from streamlit_js_eval import streamlit_js_eval
import json
import re
import math

# --- SIDEBAR: Layout & Visual Controls ---
st.sidebar.markdown("### Layout & Visual Controls")
GRID_ROWS = st.sidebar.slider("Grid Rows", 6, 20, 12, 1)
GRID_COLS = st.sidebar.slider("Grid Columns", 6, 20, 12, 1)
GRID_SPACING = st.sidebar.slider("Grid Spacing (px)", 60, 220, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 1.0, 2.0, 1.8, 0.05)
MIN_WIDTH = st.sidebar.slider("Symbol Min Width", 100, 180, 132, 4)
MAX_WIDTH = st.sidebar.slider("Symbol Max Width", 132, 220, 180, 4)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 6, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)
ARROW_LENGTH = st.sidebar.slider("Arrow Length", 8, 40, 15)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 16, 8)
PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"

# --- NEW: Paths for Layout Data and SVG Symbols ---
SVG_SYMBOLS_DIR = "symbols"
LAYOUT_DATA_DIR = "layout_data" # This is your new folder name!

if 'svg_defs_added' not in st.session_state:
    st.session_state.svg_defs_added = set()

# --- UTILITY: Robust column finder ---
def find_column(df_or_series, target, alternatives=None):
    # Robustly find a column by ignoring case and whitespace
    normalized = lambda s: s.replace(" ", "").replace("_", "").replace("-", "").lower()
    target_norm = normalized(target)
    for col in df_or_series:
        if normalized(col) == target_norm:
            return col
    if alternatives:
        for alt in alternatives:
            alt_norm = normalized(alt)
            for col in df_or_series:
                if normalized(col) == alt_norm:
                    return col
    return None

# --- NEW: P&ID Component Class ---
class PnidComponent:
    def __init__(self, data_row, symbol_meta):
        self.id = data_row['id']
        self.tag = data_row.get('tag', self.id)
        self.name = data_row['Component']
        self.subtype = data_row['Component']
        self.x = data_row['x']
        self.y = data_row['y']
        self.width = data_row['Width']
        self.height = data_row['Height']
        self.properties = data_row.get('properties', {})
        if isinstance(self.properties, str):
            try:
                self.properties = json.loads(self.properties)
            except json.JSONDecodeError:
                self.properties = {}
        self.ports = symbol_meta.get('ports', {})

    def get_port_coords(self, port_name):
        port_def = self.ports.get(port_name)
        if port_def:
            return (self.x + port_def['dx'], self.y + port_def['dy'])
        else:
            st.warning(f"Port '{port_name}' not defined for component '{self.id}' ({self.name}). Check your component_mapping.json.")
            return (self.x + self.width / 2, self.y + self.height / 2)

# --- NEW: P&ID Pipe Class ---
class PnidPipe:
    def __init__(self, data_row, polyline_col):
        self.id = data_row['Pipe No.']
        self.from_comp_name = data_row['From Component']
        self.from_port_name = data_row['From Port']
        self.to_comp_name = data_row['To Component']
        self.to_port_name = data_row['To Port']
        raw_points = data_row[polyline_col]
        # Extract numbers: "(260, 200) → (330, 200) → (330, 280)"
        coords_list = re.findall(r'\((\d+),\s*(\d+)\)', raw_points)
        self.svg_polyline_points = " ".join([f"{x},{y}" for x, y in coords_list])
        self.line_weight = PIPE_WIDTH
        self.stroke_dasharray = ""
        self.flow_arrow_required = True
        self.label = data_row.get('Label', f"Pipe {self.id}")

# --- NEW: Data Loading Function (Loads your PRE-CALCULATED Layout Data) ---
@st.cache_data
def load_layout_data():
    try:
        enhanced_equipment_layout_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, 'enhanced_equipment_layout.csv'))
        pipe_connections_layout_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, 'pipe_connections_layout.csv'))
        with open(os.path.join(LAYOUT_DATA_DIR, 'component_mapping.json'), 'r') as f:
            component_mapping_data = json.load(f)
        piping_df = pd.DataFrame({'type_id': [], 'line_weight': [], 'stroke_dasharray': [], 'flow_arrow_required': []}) 
    except FileNotFoundError as e:
        st.error(f"Error loading layout data files. Make sure they are in the '{LAYOUT_DATA_DIR}' folder. Missing: {e}")
        st.stop()

    svg_symbols_library = {}
    svg_symbol_metadata = {}
    for filename in os.listdir(SVG_SYMBOLS_DIR):
        if filename.endswith(".svg"):
            subtype = filename.replace(".svg", "")
            filepath = os.path.join(SVG_SYMBOLS_DIR, filename)
            with open(filepath, 'r') as f:
                svg_content = f.read()
                svg_symbols_library[subtype] = svg_content
                viewbox_match = re.search(r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg_content)
                viewBox = [float(x) for x in viewbox_match.groups()] if viewbox_match else [0, 0, 100, 100]
                ports = {}
                for port_entry in component_mapping_data:
                    if port_entry.get('Component') == subtype:
                        port_name = port_entry.get('Port Name')
                        if port_name and port_name != '—':
                            try:
                                ports[port_name] = {
                                    'dx': float(port_entry.get('dx', 0)),
                                    'dy': float(port_entry.get('dy', 0))
                                }
                            except (ValueError, TypeError):
                                st.warning(f"Invalid dx/dy for port {port_name} in {subtype}.")
                svg_symbol_metadata[subtype] = {
                    'viewBox': viewBox,
                    'default_width_px': viewBox[2],
                    'default_height_px': viewBox[3],
                    'ports': ports
                }

    return (enhanced_equipment_layout_df, pipe_connections_layout_df,
            component_mapping_data, piping_df,
            svg_symbols_library, svg_symbol_metadata)

# --- Call the new data loading function ---
(enhanced_equipment_layout_df, pipe_connections_layout_df,
 component_mapping_data, piping_df,
 svg_symbols_library, svg_symbol_metadata) = load_layout_data()

# --- Polyline column robust check ---
polyline_col = find_column(
    pipe_connections_layout_df.columns,
    "Polyline Points (x, y)",
    alternatives=["polylinepoints(x,y)", "polylinepoints"]
)
if polyline_col is None:
    st.error(
        f"❌ Could not find the 'Polyline Points (x, y)' column in your pipe_connections_layout.csv file. " +
        f"Columns found: {list(pipe_connections_layout_df.columns)}. Please ensure the header matches exactly."
    )
    st.stop()

# --- NEW: Function to Generate SVG ---
def generate_pnid_svg(
    components, pipes, svg_symbols_library, svg_symbol_metadata,
    grid_spacing, symbol_scale, pipe_width, tag_font_size, pipe_label_font_size,
    arrow_length, legend_width, title_block_height, title_block_width, client_name
):
    max_x = max([c.x + c.width for c in components]) if components else 0
    max_y = max([c.y + c.height for c in components]) if components else 0
    canvas_width = max_x + PADDING + legend_width
    canvas_height = max_y + PADDING + title_block_height

    svg_elements = []

    # 2. Draw Components
    for component in components:
        symbol_data = svg_symbol_metadata.get(component.subtype)
        if not symbol_data:
            st.warning(f"SVG symbol '{component.subtype}.svg' not found in '{SVG_SYMBOLS_DIR}'. Skipping '{component.id}'.")
            continue

        viewBox_width = symbol_data['viewBox'][2]
        viewBox_height = symbol_data['viewBox'][3]

        transform_scale_x = component.width / viewBox_width if viewBox_width > 0 else 1
        transform_scale_y = component.height / viewBox_height if viewBox_height > 0 else 1

        if component.subtype not in st.session_state.svg_defs_added:
            symbol_content = svg_symbols_library[component.subtype]
            symbol_content = re.sub(r'<svg(.*?)>', f'<symbol id="{component.subtype}"\\1>', symbol_content, count=1)
            symbol_content = symbol_content.replace('</svg>', '</symbol>', count=1)
            svg_elements.append(symbol_content)
            st.session_state.svg_defs_added.add(component.subtype)

        svg_elements.append(
            f'<use href="#{component.subtype}" '
            f'x="{component.x}" y="{component.y}" '
            f'width="{component.width}" height="{component.height}" '
            f'fill="black" stroke="black" stroke-width="1"/>'
        )

        svg_elements.append(
            f'<text x="{component.x + component.width / 2}" y="{component.y + component.height + tag_font_size + 5}" '
            f'text-anchor="middle" font-size="{tag_font_size}" fill="black">{component.tag}</text>'
        )

    # 3. Draw Pipes
    component_map = {c.name: c for c in components}
    component_id_map = {c.id: c for c in components}

    for pipe in pipes:
        from_comp = component_map.get(pipe.from_comp_name) or component_id_map.get(pipe.from_comp_name)
        to_comp = component_map.get(pipe.to_comp_name) or component_id_map.get(pipe.to_comp_name)

        if not from_comp:
            st.warning(f"Source component '{pipe.from_comp_name}' for pipe '{pipe.id}' not found. Skipping pipe.")
            continue
        if not to_comp:
            st.warning(f"Target component '{pipe.to_comp_name}' for pipe '{pipe.id}' not found. Skipping pipe.")
            continue

        raw_points = pipe.svg_polyline_points
        coords_list = [tuple(map(int, pair.split(','))) for pair in raw_points.split()]
        svg_polyline_points = " ".join([f"{x},{y}" for x, y in coords_list])

        svg_elements.append(
            f'<polyline points="{svg_polyline_points}" '
            f'fill="none" stroke="black" stroke-width="{pipe_width}" '
            f'stroke-dasharray="{pipe.stroke_dasharray}" marker-end="url(#arrowhead)"/>'
        )

        if pipe.flow_arrow_required and coords_list and len(coords_list) >= 2:
            pass # marker-end above handles arrows

        mid_point_index = int(len(coords_list) / 2) -1
        if mid_point_index >= 0:
            mid_segment_start_x, mid_segment_start_y = coords_list[mid_point_index]
            mid_segment_end_x, mid_segment_end_y = coords_list[mid_point_index+1]
            mid_x = (mid_segment_start_x + mid_segment_end_x) / 2
            mid_y = (mid_segment_start_y + mid_segment_end_y) / 2
            svg_elements.append(
                f'<text x="{mid_x}" y="{mid_y - 5}" '
                f'text-anchor="middle" font-size="{pipe_label_font_size}" fill="black">{pipe.label}</text>'
            )

    full_svg = f'''
    <svg width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7"
                    refX="0" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="black" />
            </marker>
            {"".join([el for el in svg_elements if '<symbol id=' in el])}
        </defs>
        {"".join([el for el in svg_elements if '<symbol id=' not in el and '<marker id=' not in el])}
        <rect x="{canvas_width - title_block_width}" y="{canvas_height - title_block_height}" 
              width="{title_block_width}" height="{title_block_height}" 
              fill="none" stroke="black" stroke-width="1"/>
        <text x="{canvas_width - title_block_width + 10}" y="{canvas_height - title_block_height + 20}" 
              font-size="14" fill="black">Client: {client_name}</text>
        <text x="{canvas_width - title_block_width + 10}" y="{canvas_height - title_block_height + 40}" 
              font-size="14" fill="black">Date: {datetime.date.today().strftime('%Y-%m-%d')}</text>
        <text x="{canvas_width - title_block_width + 10}" y="{canvas_height - title_block_height + 60}" 
              font-size="14" fill="black">P&ID Version: 1.0</text>

        <rect x="{canvas_width - legend_width}" y="10" 
              width="{legend_width - 20}" height="150" 
              fill="none" stroke="black" stroke-width="1"/>
        <text x="{canvas_width - legend_width + 10}" y="30" font-size="{LEGEND_FONT_SIZE}" fill="black">Legend:</text>
        <text x="{canvas_width - legend_width + 10}" y="50" font-size="{LEGEND_FONT_SIZE}" fill="black">--- Process Line</text>
        <text x="{canvas_width - legend_width + 10}" y="70" font-size="{LEGEND_FONT_SIZE}" fill="black">-- -- Instrument Line</text>
        <text x="{canvas_width - legend_width + 10}" y="90" font-size="{LEGEND_FONT_SIZE}" fill="black">-- • -- Electrical Line</text>
    </svg>
    '''
    return full_svg

# --- Generate and Display SVG ---
all_components = []
for index, row in enhanced_equipment_layout_df.iterrows():
    subtype = row['Component']
    symbol_meta = svg_symbol_metadata.get(subtype, {})
    all_components.append(PnidComponent(row, symbol_meta))

all_pipes = []
for index, row in pipe_connections_layout_df.iterrows():
    all_pipes.append(PnidPipe(row, polyline_col))

pnid_svg_content = generate_pnid_svg(
    components=all_components,
    pipes=all_pipes,
    svg_symbols_library=svg_symbols_library,
    svg_symbol_metadata=svg_symbol_metadata,
    grid_spacing=GRID_SPACING,
    symbol_scale=SYMBOL_SCALE,
    pipe_width=PIPE_WIDTH,
    tag_font_size=TAG_FONT_SIZE,
    pipe_label_font_size=PIPE_LABEL_FONT_SIZE,
    arrow_length=ARROW_LENGTH,
    legend_width=LEGEND_WIDTH,
    title_block_height=TITLE_BLOCK_HEIGHT,
    title_block_width=TITLE_BLOCK_WIDTH,
    client_name=TITLE_BLOCK_CLIENT
)

st.markdown(pnid_svg_content, unsafe_allow_html=True)

st.download_button(
    label="Download P&ID as SVG",
    data=pnid_svg_content,
    file_name="pnid_layout.svg",
    mime="image/svg+xml"
)
