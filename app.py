import streamlit as st
import pandas as pd
import os
import datetime
import json
import re
import psycopg2
import openai

st.set_page_config(layout="wide")

# --- Sidebar Controls ---
st.sidebar.markdown("### Layout & Visual Controls")
GRID_SPACING = st.sidebar.slider("Grid Spacing (px)", 60, 220, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 1.0, 2.0, 1.8, 0.05)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 6, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 16, 8)

# --- Constants ---
PADDING = 80
LEGEND_WIDTH = 300
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"
SVG_SYMBOLS_DIR = "symbols"
LAYOUT_DATA_DIR = "layout_data"

openai.api_key = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("DATABASE_URL")

# Normalize helper
def normalize(s): return s.replace(" ", "_").replace("-", "_").lower()

# Load symbol from PostgreSQL
def load_svg_from_db(subtype):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT svg_data FROM symbols WHERE subtype = %s", (subtype,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        st.error(f"PostgreSQL load error: {e}")
        return None

# Save symbol to PostgreSQL
def save_svg_to_db(subtype, svg_data):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO symbols (subtype, svg_data) VALUES (%s, %s) ON CONFLICT (subtype) DO NOTHING", (subtype, svg_data))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"PostgreSQL save error: {e}")

# Generate missing symbol using OpenAI
def generate_svg_via_openai(subtype):
    prompt = f"Draw a vector-based P&ID ISA-compliant symbol for a {subtype.replace('_', ' ')}. Black lines only, transparent background. Output: SVG."
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="b64_json"
        )
        img_b64 = response['data'][0]['b64_json']
        svg_data = f'<image href="data:image/png;base64,{img_b64}" width="100" height="100" />'
        return svg_data
    except Exception as e:
        st.error(f"OpenAI generation failed: {e}")
        return None

# Load data
@st.cache_data
def load_data():
    eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
    pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
    with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
        mapping = json.load(f)
    return eq_df, pipe_df, mapping

eq_df, pipe_df, mapping = load_data()
svg_defs = {}
svg_meta = {}

# Load or generate SVGs
for entry in mapping:
    subtype = normalize(entry["Component"])
    symbol_path = os.path.join(SVG_SYMBOLS_DIR, f"{subtype}.svg")

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

# Component + Pipe Classes
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
        return (self.x + self.width/2, self.y + self.height/2)

class PnidPipe:
    def __init__(self, row, components):
        self.label = row.get("Label", f"Pipe {row['Pipe No.']}")
        fc = components.get(row["From Component"])
        tc = components.get(row["To Component"])
        if fc and tc:
            self.points = [
                fc.get_port_coords(row["From Port"]),
                tc.get_port_coords(row["To Port"])
            ]
        else:
            self.points = []

# SVG Renderer
def render_svg(components, pipes):
    max_x = max((c.x + c.width) for c in components.values()) + PADDING
    max_y = max((c.y + c.height) for c in components.values()) + PADDING
    svg = []

    svg.append('''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200">''')
    svg.append('''
    <defs><marker id="arrowhead" markerWidth="10" markerHeight="7"
    refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black" /></marker></defs>
    ''')

    for c in components.values():
        if c.subtype in svg_defs:
            svg.append(f'<g transform="translate({c.x},{c.y}) scale({SYMBOL_SCALE})">{svg_defs[c.subtype]}</g>')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 12}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
        else:
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')

    for p in pipes:
        if len(p.points) == 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)" />')
            mx = (p.points[0][0] + p.points[1][0]) / 2
            my = (p.points[0][1] + p.points[1][1]) / 2
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')

    svg.append('</svg>')
    return "".join(svg)

# Build objects
components = {row['id']: PnidComponent(row) for _, row in eq_df.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df.iterrows()]
svg_output = render_svg(components, pipes)

# Display
st.markdown(svg_output, unsafe_allow_html=True)
st.download_button("Download SVG", svg_output, "pnid_output.svg", "image/svg+xml")
