# EPS Interactive P&ID Generator — Full Revised app.py
# Merged UI features from app_Version40.py + SVG Rendering + Port Mapping

import streamlit as st
import pandas as pd
import os
import datetime
import json
import re

st.set_page_config(layout="wide")

# Sidebar UI
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

def normalize(s): return s.replace(" ", "").replace("_", "").replace("-", "").lower()

@st.cache_data
def load_data():
    eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
    pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
    with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
        mapping = json.load(f)

    svg_defs = {}
    svg_meta = {}
    for file in os.listdir(SVG_SYMBOLS_DIR):
        if file.endswith(".svg"):
            subtype = re.sub(r'[^a-z0-9]', '_', file.replace(".svg", "").strip().lower())
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
            svg_defs[subtype] = svg
            svg_meta[subtype] = {"viewBox": viewbox, "ports": ports}
    return eq_df, pipe_df, svg_defs, svg_meta

eq_df, pipe_df, svg_defs, svg_meta = load_data()

class PnidComponent:
    def __init__(self, row, symbol_meta):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.name = row.get('Component')
        self.subtype = normalize(row.get('subtype') or row.get('Component'))
        self.x = row['x']
        self.y = row['y']
        self.width = row['Width'] * SYMBOL_SCALE
        self.height = row['Height'] * SYMBOL_SCALE
        self.ports = symbol_meta.get(self.subtype, {}).get('ports', {})

    def get_port_coords(self, port_name):
        port = self.ports.get(port_name)
        if port:
            return (self.x + port['dx'] * SYMBOL_SCALE, self.y + port['dy'] * SYMBOL_SCALE)
        return (self.x + self.width / 2, self.y + self.height / 2)

class PnidPipe:
    def __init__(self, row, component_map):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        self.from_id = row['From Component']
        self.from_port = row['From Port']
        self.to_id = row['To Component']
        self.to_port = row['To Port']
        from_comp = component_map.get(self.from_id)
        to_comp = component_map.get(self.to_id)
        self.points = []
        if from_comp and to_comp:
            self.points = [
                from_comp.get_port_coords(self.from_port),
                to_comp.get_port_coords(self.to_port)
            ]

def generate_svg(components, pipes, svg_defs, svg_meta):
    max_x = max((c.x + c.width) for c in components) + PADDING + LEGEND_WIDTH
    max_y = max((c.y + c.height) for c in components) + PADDING + TITLE_BLOCK_HEIGHT

    svg = []

    # Grid Lines
    for i in range(0, int(max_x), GRID_SPACING):
        svg.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{max_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, int(max_y), GRID_SPACING):
        svg.append(f'<line x1="0" y1="{i}" x2="{max_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')

    # Arrowhead
    svg.append('''
    <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="black" /></marker></defs>
    ''')

    # Add <symbol> for each SVG
    for subtype, raw in svg_defs.items():
        if subtype not in st.session_state.svg_defs_added:
            use_def = re.sub(r'<svg[^>]*>', f'<symbol id="{subtype}">', raw, 1).replace('</svg>', '</symbol>')
            svg.append(use_def)
            st.session_state.svg_defs_added.add(subtype)

    # Components
    for c in components:
        if c.subtype in svg_defs:
            svg.append(f'<use href="#{c.subtype}" x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}"/>')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + TAG_FONT_SIZE + 4}" '
                       f'text-anchor="middle" font-size="{TAG_FONT_SIZE}">{c.tag}</text>')
        else:
            st.warning(f"Missing SVG: {c.subtype}")
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height/2}" text-anchor="middle" font-size="10" fill="red">?</text>')

    # Pipes
    for p in pipes:
        if len(p.points) == 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)"/>')
            mx = (p.points[0][0] + p.points[1][0]) / 2
            my = (p.points[0][1] + p.points[1][1]) / 2
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')

    # Legend
    legend_x = max_x - LEGEND_WIDTH
    legend_y = PADDING
    svg.append(f'<rect x="{legend_x}" y="{legend_y}" width="{LEGEND_WIDTH - 10}" '
               f'height="{len(svg_defs) * 20 + 40}" stroke="black" fill="none"/>')
    svg.append(f'<text x="{legend_x + 10}" y="{legend_y + 20}" font-size="14" font-weight="bold">Legend</text>')
    y_off = legend_y + 40
    for subtype in svg_defs:
        svg.append(f'<text x="{legend_x + 10}" y="{y_off}" font-size="12">{subtype.replace("_", " ").title()}</text>')
        y_off += 20

    # Title Block
    svg.append(f'''
    <rect x="{max_x - TITLE_BLOCK_WIDTH}" y="{max_y - TITLE_BLOCK_HEIGHT}"
          width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT}" stroke="black" fill="none"/>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 20}"
          font-size="14">Client: {TITLE_BLOCK_CLIENT}</text>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 40}"
          font-size="14">Date: {datetime.date.today()}</text>
    <text x="{max_x - TITLE_BLOCK_WIDTH + 10}" y="{max_y - TITLE_BLOCK_HEIGHT + 60}"
          font-size="14">P&ID Version: 1.0</text>
    ''')

    return f'<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">{"".join(svg)}</svg>'

# Build
components = [PnidComponent(row, svg_meta) for _, row in eq_df.iterrows()]
component_map = {c.id: c for c in components}
pipes = [PnidPipe(row, component_map) for _, row in pipe_df.iterrows()]

# Render
svg = generate_svg(components, pipes, svg_defs, svg_meta)
st.markdown(svg, unsafe_allow_html=True)
st.download_button("Download SVG", svg, "pnid_output.svg", "image/svg+xml")
