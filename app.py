import streamlit as st
import pandas as pd
import os
import datetime
import json
import re
import openai
import psycopg2
import ezdxf
from io import BytesIO
from PIL import Image
import base64

# Streamlit Config
st.set_page_config(layout="wide")

# Sidebar Controls
st.sidebar.markdown("### Layout & Visual Controls")
GRID_SPACING = st.sidebar.slider("Grid Spacing", 60, 200, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.5, 1.0, 0.1)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 5, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 18, 10)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)

# Constants
PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "EPS Pvt. Ltd."
SVG_SYMBOLS_DIR = "symbols"
LAYOUT_DATA_DIR = "layout_data"

openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Utility
def normalize(s):
    return s.lower().strip().replace(" ", "_").replace("-", "_")

# PostgreSQL functions
def load_svg_from_db(subtype):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT svg_data FROM generated_symbols WHERE subtype = %s", (subtype,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        st.error(f"[DB LOAD ERROR] {e}")
        return None

def save_svg_to_db(subtype, svg_data):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO generated_symbols (subtype, svg_data) VALUES (%s, %s) ON CONFLICT (subtype) DO NOTHING", (subtype, svg_data))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"[DB SAVE ERROR] {e}")
        def generate_svg_via_openai(subtype):
    prompt = f"Generate an SVG symbol in ISA P&ID style for a {subtype.replace('_', ' ')}. Transparent background. Use black lines only."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a process engineer who outputs ISA-style SVG technical drawings."},
                {"role": "user", "content": prompt}
            ]
        )
        svg = response['choices'][0]['message']['content']
        return svg if "<svg" in svg else None
    except Exception as e:
        st.error(f"[OpenAI SVG Gen Error] {e}")
        return None

@st.cache_data
def load_layout_data():
    eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
    pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
    with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
        mapping = json.load(f)
    return eq_df, pipe_df, mapping

eq_df, pipe_df, mapping = load_layout_data()
svg_defs, svg_meta = {}, {}

for entry in mapping:
    subtype = normalize(entry["Component"])
    symbol_path = os.path.join(SVG_SYMBOLS_DIR, f"{subtype}.svg")
    svg = None

    if os.path.exists(symbol_path):
        with open(symbol_path) as f:
            svg = f.read()
    else:
        svg = load_svg_from_db(subtype)
        if not svg:
            svg = generate_svg_via_openai(subtype)
            if svg:
                with open(symbol_path, "w") as f:
                    f.write(svg)
                save_svg_to_db(subtype, svg)

    if svg:
        svg_defs[subtype] = svg
        if subtype not in svg_meta:
            svg_meta[subtype] = {"ports": {}}
            class PnidComponent:
    def __init__(self, row):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.subtype = normalize(row.get('Component'))
        self.x = row['x']
        self.y = row['y']
        self.width = row['Width'] * SYMBOL_SCALE
        self.height = row['Height'] * SYMBOL_SCALE
        self.ports = svg_meta.get(self.subtype, {}).get('ports', {})

    def get_port_coords(self, port_name):
        port = self.ports.get(port_name)
        if port:
            return (self.x + port['dx'] * SYMBOL_SCALE, self.y + port['dy'] * SYMBOL_SCALE)
        return (self.x + self.width / 2, self.y + self.height / 2)

class PnidPipe:
    def __init__(self, row, component_map):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        from_comp = component_map.get(row['From Component'])
        to_comp = component_map.get(row['To Component'])
        self.points = []
        if from_comp and to_comp:
            self.points = [
                from_comp.get_port_coords(row['From Port']),
                to_comp.get_port_coords(row['To Port'])
            ]

def render_svg(components, pipes):
    max_x = max(c.x + c.width for c in components.values()) + PADDING + LEGEND_WIDTH
    max_y = max(c.y + c.height for c in components.values()) + PADDING + TITLE_BLOCK_HEIGHT
    svg = []

    svg.append(f'<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black"/></marker></defs>')

    for i in range(0, int(max_x), GRID_SPACING):
        svg.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{max_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, int(max_y), GRID_SPACING):
        svg.append(f'<line x1="0" y1="{i}" x2="{max_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')

    for c in components.values():
        if c.subtype in svg_defs:
            svg.append(f'<g transform="translate({c.x},{c.y}) scale({SYMBOL_SCALE})">{svg_defs[c.subtype]}</g>')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 14}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
        else:
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')

    for p in pipes:
        if len(p.points) == 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)"/>')
            mx = (p.points[0][0] + p.points[1][0]) / 2
            my = (p.points[0][1] + p.points[1][1]) / 2
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')

    svg.append('</svg>')
    return "".join(svg)
    components = {row['id']: PnidComponent(row) for _, row in eq_df.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df.iterrows()]
svg_output = render_svg(components, pipes)

st.markdown(svg_output, unsafe_allow_html=True)

# PNG Export (via Pillow)
def export_png(svg_data):
    from cairosvg import svg2png
    output = BytesIO()
    svg2png(bytestring=svg_data.encode(), write_to=output)
    return output.getvalue()

# DXF Export
def export_dxf(components, pipes):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for c in components.values():
        msp.add_text(c.tag).set_pos((c.x, c.y))
    for p in pipes:
        if len(p.points) == 2:
            msp.add_lwpolyline(p.points)
    output = BytesIO()
    doc.write(output)
    return output.getvalue()

# Export buttons
st.download_button("📥 Download SVG", svg_output, "pnid.svg", "image/svg+xml")
st.download_button("📥 Download PNG", export_png(svg_output), "pnid.png", "image/png")
st.download_button("📥 Download DXF", export_dxf(components, pipes), "pnid.dxf", "application/dxf")
