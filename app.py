import streamlit as st
import pandas as pd
import os
import json
import datetime
import re
import openai
import psycopg2
from io import BytesIO
import ezdxf
from cairosvg import svg2png

# CONFIG
st.set_page_config(layout="wide")
st.sidebar.title("EPS Interactive P&ID Generator")

GRID_SPACING = st.sidebar.slider("Grid Spacing", 60, 200, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.5, 1.0, 0.1)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 5, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 18, 10)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)

# GLOBALS
PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "EPS Pvt. Ltd."

LAYOUT_DATA_DIR = "layout_data"
SYMBOLS_DIR = "symbols"
openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# HELPERS
def normalize(s): return s.lower().strip().replace(" ", "_").replace("-", "_") if isinstance(s, str) else ""

def load_svg_from_db(subtype):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT svg_data FROM generated_symbols WHERE subtype = %s", (subtype,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else None
    except Exception as e:
        st.error(f"[DB LOAD ERROR] {e}")
        return None

def save_svg_to_db(subtype, svg):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO generated_symbols (subtype, svg_data)
            VALUES (%s, %s)
            ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data
        """, (subtype, svg))
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        st.error(f"[DB SAVE ERROR] {e}")

def generate_svg_openai(subtype):
    prompt = f"Generate an SVG symbol in ISA P&ID style for a {subtype.replace('_', ' ')}. Transparent background. Use black lines only."
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a process engineer who outputs SVG drawings using ISA symbols."},
                {"role": "user", "content": prompt}
            ]
        )
        svg = res["choices"][0]["message"]["content"]
        return svg if "<svg" in svg else None
    except Exception as e:
        st.error(f"[OpenAI Fallback Error: {subtype}]: {e}")
        return None

def load_symbol(subtype):
    svg_path = os.path.join(SYMBOLS_DIR, f"{subtype}.svg")
    svg = None

    if os.path.exists(svg_path):
        with open(svg_path) as f:
            svg = f.read()
    else:
        svg = load_svg_from_db(subtype)

    if not svg:
        svg = generate_svg_openai(subtype)
        if svg:
            with open(svg_path, "w") as f:
                f.write(svg)
            save_svg_to_db(subtype, svg)
    return svg
    # LOAD LAYOUT DATA
@st.cache_data
def load_data():
    eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
    pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
    try:
        with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
            mapping = json.load(f)
    except Exception as e:
        st.error(f"component_mapping.json loading failed: {e}")
        mapping = []
    return eq_df, pipe_df, mapping

eq_df, pipe_df, mapping = load_data()
all_subtypes = sorted({normalize(row.get("block", "")) for _, row in eq_df.iterrows() if normalize(row.get("block", ""))})

# SYMBOLS and PORTS
svg_defs = {}
svg_meta = {}
for subtype in all_subtypes:
    svg = load_symbol(subtype)
    if svg:
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg)
        viewbox = viewbox_match.group(1) if viewbox_match else "0 0 100 100"
        symbol = re.sub(r"<svg[^>]*>", f'<symbol id="{subtype}" viewBox="{viewbox}">', svg)
        symbol = symbol.replace("</svg>", "</symbol>")
        svg_defs[subtype] = symbol
        svg_meta[subtype] = {"viewBox": viewbox, "ports": {}}
    else:
        svg_defs[subtype] = None
        svg_meta[subtype] = {"viewBox": "0 0 100 100", "ports": {}}

# Populate ports from component_mapping.json
for entry in mapping:
    subtype = normalize(entry.get("Component", ""))
    port_name = entry.get("Port Name", "default")
    dx, dy = float(entry.get("dx", 0)), float(entry.get("dy", 0))
    if subtype:
        svg_meta[subtype]["ports"][port_name] = {"dx": dx, "dy": dy}
        # COMPONENT + PIPE CLASSES
class PnidComponent:
    def __init__(self, row):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.subtype = normalize(row.get('block', ''))
        self.x = row['x']
        self.y = row['y']
        self.width = row.get('Width', 60) * SYMBOL_SCALE
        self.height = row.get('Height', 60) * SYMBOL_SCALE
        self.ports = svg_meta.get(self.subtype, {}).get('ports', {})

    def get_port_coords(self, port_name):
        port = self.ports.get(port_name)
        if port:
            return (self.x + port["dx"] * SYMBOL_SCALE, self.y + port["dy"] * SYMBOL_SCALE)
        return (self.x + self.width / 2, self.y + self.height / 2)

class PnidPipe:
    def __init__(self, row, component_map):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        self.points = []
        from_comp = component_map.get(row['From Component'])
        to_comp = component_map.get(row['To Component'])
        # Manual override
        if 'Polyline Points (x, y)' in row and isinstance(row['Polyline Points (x, y)'], str):
            pts = re.findall(r"\(([\d\.\-]+),\s*([\d\.\-]+)\)", row['Polyline Points (x, y)'])
            self.points = [(float(x), float(y)) for x, y in pts]
            if self.points:
                if from_comp: self.points[0] = from_comp.get_port_coords(row.get("From Port"))
                if to_comp: self.points[-1] = to_comp.get_port_coords(row.get("To Port"))
        elif from_comp and to_comp:
            self.points = [
                from_comp.get_port_coords(row.get("From Port")),
                to_comp.get_port_coords(row.get("To Port"))
            ]

# MOCK ISA LOGIC BLOCK
def render_isa_logic_block():
    block = []
    block.append('<div style="background:#f8f8f8;border:1px solid #ccc;padding:8px;font-size:14px;">')
    block.append("<b>ISA PID Logic</b><br>")
    block.append("PT-001 → PID → CV-001 (LOOP-001)<br>")
    block.append("LT-001 → PID → CV-002 (LOOP-002)")
    block.append("</div>")
    return "".join(block)
    def render_svg(components, pipes):
    max_x = max((c.x + c.width for c in components.values()), default=0) + PADDING + LEGEND_WIDTH
    max_y = max((c.y + c.height for c in components.values()), default=0) + PADDING + TITLE_BLOCK_HEIGHT
    pipe_max_x = max((x for p in pipes for x, _ in getattr(p, 'points', [])), default=0)
    pipe_max_y = max((y for p in pipes for _, y in getattr(p, 'points', [])), default=0)
    max_x = max(max_x, pipe_max_x + PADDING + LEGEND_WIDTH)
    max_y = max(max_y, pipe_max_y + PADDING + TITLE_BLOCK_HEIGHT)

    svg = []
    svg.append(f'<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">')

    # Defs
    svg.append("<defs>")
    svg.append('<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black"/></marker>')
    for symbol in svg_defs.values():
        if symbol: svg.append(symbol)
    svg.append("</defs>")

    # Grid
    for i in range(0, int(max_x), GRID_SPACING):
        svg.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{max_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, int(max_y), GRID_SPACING):
        svg.append(f'<line x1="0" y1="{i}" x2="{max_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')

    # Legend box
    legend_x = max_x - LEGEND_WIDTH + 30
    legend_y = 50
    svg.append(f'<rect x="{legend_x-10}" y="{legend_y-30}" width="{LEGEND_WIDTH-40}" height="600" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    svg.append(f'<text x="{legend_x+80}" y="{legend_y-10}" font-size="{LEGEND_FONT_SIZE+4}" font-weight="bold">Legend</text>')

    # Legend entries
    legend_entries = {}
    for c in components.values():
        key = (c.tag, c.subtype)
        if key not in legend_entries:
            legend_entries[key] = c.subtype.replace("_", " ").title()
    for i, ((tag, subtype), name) in enumerate(legend_entries.items()):
        sym_pos_y = legend_y + i*28
        viewbox = svg_meta.get(subtype, {}).get("viewBox", "0 0 100 100").split(" ")
        vb_w = float(viewbox[2])
        vb_h = float(viewbox[3])
        scale_factor = min(25 / vb_w, 25 / vb_h)
        width, height = vb_w * scale_factor, vb_h * scale_factor
        svg.append(f'<use href="#{subtype}" x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" />')
        svg.append(f'<text x="{legend_x+32}" y="{sym_pos_y+16}" font-size="{LEGEND_FONT_SIZE}">{tag} — {name}</text>')

    # Title block
    svg.append(f'<rect x="10" y="{max_y-TITLE_BLOCK_HEIGHT}" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT-10}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+30}" font-size="14" font-weight="bold">{TITLE_BLOCK_CLIENT}</text>')
    svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+55}" font-size="12">Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</text>')

    # Components
    for c in components.values():
        if c.subtype in svg_defs and svg_defs[c.subtype]:
            svg.append(f'<use href="#{c.subtype}" x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" />')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 14}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
        else:
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')

    # Pipes
    for p in pipes:
        if len(p.points) >= 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)"/>')
            mx = sum(x for x, _ in p.points) / len(p.points)
            my = sum(y for _, y in p.points) / len(p.points)
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')

    svg.append("</svg>")
    return "".join(svg)
    # COMPONENT MAPPING
components = {row['id']: PnidComponent(row) for _, row in eq_df.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df.iterrows()]

# SVG OUTPUT
svg_output = render_svg(components, pipes)
st.markdown(svg_output, unsafe_allow_html=True)

# ISA LOGIC PANEL
st.markdown("---")
st.markdown("### 🔧 Instrumentation Control Logic")
st.markdown(render_isa_logic_block(), unsafe_allow_html=True)

# PNG Export
def export_png(svg_data):
    output = BytesIO()
    svg2png(bytestring=svg_data.encode(), write_to=output)
    return output.getvalue()

# DXF Export — FIXED (return bytes not str)
def export_dxf(components, pipes):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for c in components.values():
        msp.add_text(c.tag, dxfattribs={'height': 2.5}).set_pos((c.x, c.y))
    for p in pipes:
        if len(p.points) >= 2:
            msp.add_lwpolyline(p.points)
    output = BytesIO()
    doc.write(output)
    return output.getvalue()

# DOWNLOADS
st.download_button("📥 Download SVG", svg_output, "pnid.svg", "image/svg+xml")
st.download_button("📥 Download PNG", export_png(svg_output), "pnid.png", "image/png")
st.download_button("📥 Download DXF", export_dxf(components, pipes), "pnid.dxf", "application/dxf")
