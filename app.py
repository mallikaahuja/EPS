import streamlit as st
import pandas as pd
import os
import datetime
import json
import re

st.set_page_config(layout="wide")

# --- Sidebar Controls ---
st.sidebar.markdown("### Layout & Visual Controls")
GRID_SPACING = st.sidebar.slider("Grid Spacing (px)", 60, 220, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 1.0, 2.0, 1.8, 0.05)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 6, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 16, 8)

PADDING = 80
LEGEND_WIDTH = 300
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"

SVG_SYMBOLS_DIR = "symbols"
LAYOUT_DATA_DIR = "layout_data"

if 'svg_defs_added' not in st.session_state:
    st.session_state.svg_defs_added = set()

# Utility: Normalize field names
def normalize(s):
    return s.replace(" ", "").replace("_", "").replace("-", "").lower()

# Load Data
@st.cache_data
def load_layout_data():
    eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
    pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
    with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
        mapping = json.load(f)

    svg_meta = {}
    svg_defs = {}
    for file in os.listdir(SVG_SYMBOLS_DIR):
        if file.endswith(".svg"):
            subtype = file.replace(".svg", "").strip().lower()
            with open(os.path.join(SVG_SYMBOLS_DIR, file)) as f:
                svg = f.read()
            match = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', svg)
            viewbox = list(map(float, match.groups())) if match else [0, 0, 100, 100]
            ports = {}
            for entry in mapping:
                if normalize(entry["Component"]) == subtype:
                    ports[entry["Port Name"]] = {
                        "dx": float(entry["dx"]),
                        "dy": float(entry["dy"])
                    }
            svg_meta[subtype] = {"viewBox": viewbox, "ports": ports}
            svg_defs[subtype] = svg
    return eq_df, pipe_df, mapping, svg_meta, svg_defs

eq_df, pipe_df, mapping, svg_meta, svg_defs = load_layout_data()

# Component class
class PnidComponent:
    def __init__(self, row, symbol_meta):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.name = row.get('Component')
        self.subtype = normalize(row.get('subtype') or row.get('Component') or row.get('name'))
        self.x = row['x']
        self.y = row['y']
        self.width = row['Width']
        self.height = row['Height']
        self.ports = symbol_meta.get('ports', {})

    def get_port_coords(self, port_name):
        port = self.ports.get(port_name)
        if port:
            return (self.x + port['dx'], self.y + port['dy'])
        return (self.x + self.width / 2, self.y + self.height / 2)

# Pipe class
class PnidPipe:
    def __init__(self, row):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        self.points = re.findall(r'\((\d+),\s*(\d+)\)', row['Polyline Points (x, y)'])
        self.points = [(int(x), int(y)) for x, y in self.points]

# Polyline check
poly_col = next((col for col in pipe_df.columns if normalize(col) == "polylinepoints(x,y)"), None)
if not poly_col:
    st.error("❌ 'Polyline Points (x, y)' column not found.")
    st.stop()

# Generate SVG
def generate_svg(components, pipes):
    max_x = max(c.x + c.width for c in components) + PADDING + LEGEND_WIDTH
    max_y = max(c.y + c.height for c in components) + PADDING + TITLE_BLOCK_HEIGHT

    svg = []

    # Arrowhead marker
    svg.append('''
    <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="black" />
    </marker>
    </defs>
    ''')

    # Add <symbol> defs
    for subtype, svg_code in svg_defs.items():
        if subtype not in st.session_state.svg_defs_added:
            svg_sym = re.sub(r'<svg[^>]*>', f'<symbol id="{subtype}">', svg_code, 1)
            svg_sym = svg_sym.replace('</svg>', '</symbol>')
            svg.append(svg_sym)
            st.session_state.svg_defs_added.add(subtype)

    # Render components
    for c in components:
        svg.append(f'<use href="#{c.subtype}" x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" />')
        svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + TAG_FONT_SIZE + 4}" '
                   f'text-anchor="middle" font-size="{TAG_FONT_SIZE}">{c.tag}</text>')

    # Render pipes
    for p in pipes:
        pts = " ".join(f"{x},{y}" for x, y in p.points)
        svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" '
                   f'marker-end="url(#arrowhead)"/>')
        if len(p.points) >= 2:
            mx = (p.points[0][0] + p.points[-1][0]) // 2
            my = (p.points[0][1] + p.points[-1][1]) // 2
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" '
                       f'text-anchor="middle">{p.label}</text>')

    # Title Block
    svg.append(f'''
    <rect x="{max_x - TITLE_BLOCK_WIDTH}" y="{max_y - TITLE_BLOCK_HEIGHT}" width="{TITLE_BLOCK_WIDTH}"
          height="{TITLE_BLOCK_HEIGHT}" stroke="black" fill="none"/>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 20}"
          font-size="14">Client: {TITLE_BLOCK_CLIENT}</text>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 40}"
          font-size="14">Date: {datetime.date.today()}</text>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 60}"
          font-size="14">P&ID Version: 1.0</text>
    ''')

    return f'<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">{"".join(svg)}</svg>'

# Build components and pipes
components = [PnidComponent(row, svg_meta.get(normalize(row.get("Component", "")), {})) for _, row in eq_df.iterrows()]
pipes = [PnidPipe(row) for _, row in pipe_df.iterrows()]

# Render SVG
svg_out = generate_svg(components, pipes)
st.markdown(svg_out, unsafe_allow_html=True)
st.download_button("Download SVG", svg_out, "pnid_output.svg", "image/svg+xml")
