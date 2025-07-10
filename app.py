import streamlit as st
import pandas as pd
import os
import datetime
import json
import re
import openai
import requests
import psycopg2
import ezdxf
from io import BytesIO

# === CONFIG ===
st.set_page_config(layout="wide")
st.sidebar.markdown("## EPS Interactive P&ID Generator")
GRID_SPACING = st.sidebar.slider("Grid Spacing", 60, 200, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.5, 1.0, 0.1)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 5, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 18, 10)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)

PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "EPS Pvt. Ltd."
SVG_SYMBOLS_DIR = "symbols"
LAYOUT_DATA_DIR = "layout_data"

openai.api_key = os.getenv("OPENAI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# === UTILS ===
def normalize(s):
    if not isinstance(s, str): return ""
    return s.lower().strip().replace(" ", "_").replace("-", "_")

def clean_svg(svg):
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg, flags=re.MULTILINE).strip()
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg, flags=re.MULTILINE).strip()
    return svg

def load_svg_from_db(subtype):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT svg_data FROM generated_symbols WHERE subtype = %s", (subtype,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

def save_svg_to_db(subtype, svg_data):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO generated_symbols (subtype, svg_data) VALUES (%s, %s) ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data",
            (subtype, svg_data)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

def generate_svg_via_openai(subtype):
    prompt = f"Generate a simple SVG symbol in ISA P&ID style for a {subtype.replace('_', ' ')}. Transparent background. Use black lines only."
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
    except Exception:
        return None

def generate_svg_via_stability(subtype):
    # Uses Stability API to generate an SVG (returns SVG as string or None)
    try:
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "application/json"
        }
        json_data = {
            "prompt": f"ISA P&ID style SVG technical drawing of a {subtype.replace('_',' ')}. Only SVG. Transparent background. Black lines.",
            "output_format": "svg"
        }
        response = requests.post(url, headers=headers, json=json_data, timeout=30)
        if response.status_code == 200 and "svg" in response.json():
            return response.json()["svg"]
    except Exception:
        pass
    return None

# === DATA LOAD ===
def load_layout_data():
    try:
        eq_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"))
        pipe_df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"))
        with open(os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")) as f:
            mapping = json.load(f)
        return eq_df, pipe_df, mapping
    except Exception as e:
        st.error(f"Critical layout loading error: {e}")
        return None, None, None

def load_dropdown_options():
    def safe_load(fname, col):
        try:
            df = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, fname))
            return sorted(df[col].dropna().unique())
        except Exception:
            return []
    equipment_types = safe_load("equipment_list.csv", "subtype")
    pipeline_types = safe_load("pipeline_list.csv", "id")
    inline_types = safe_load("inline_component_list.csv", "subtype")
    return equipment_types, pipeline_types, inline_types

eq_df, pipe_df, mapping = load_layout_data()
if eq_df is None or pipe_df is None or mapping is None:
    st.stop()
equipment_types, pipeline_types, inline_types = load_dropdown_options()

# === SVG SYMBOL LOADING WITH FALLBACK ===
def get_svg_symbol(subtype):
    if not subtype:
        return None
    svg_file = os.path.join(SVG_SYMBOLS_DIR, f"{subtype}.svg")
    # 1. Try local file
    if os.path.exists(svg_file):
        with open(svg_file) as f:
            svg = clean_svg(f.read())
            if "<svg" in svg:
                return svg
    # 2. Try DB
    svg = load_svg_from_db(subtype)
    if svg and "<svg" in svg:
        return clean_svg(svg)
    # 3. Try OpenAI
    svg = generate_svg_via_openai(subtype)
    if svg and "<svg" in svg:
        with open(svg_file, "w") as f:
            f.write(svg)
        save_svg_to_db(subtype, svg)
        return clean_svg(svg)
    # 4. Try Stability AI
    svg = generate_svg_via_stability(subtype)
    if svg and "<svg" in svg:
        with open(svg_file, "w") as f:
            f.write(svg)
        save_svg_to_db(subtype, svg)
        return clean_svg(svg)
    # 5. Fallback: simple rectangle
    return f'<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="80" fill="none" stroke="red" stroke-width="3"/></svg>'

# Build all unique subtypes from equipment + mapping
all_subtypes = set()
for _, row in eq_df.iterrows():
    if row.get('block', ''):
        all_subtypes.add(normalize(row.get('block', '')))
for entry in mapping:
    if entry.get("Component", ""):
        all_subtypes.add(normalize(entry.get("Component", "")))
all_subtypes = sorted(all_subtypes)

# Load SVGs for all subtypes
svg_defs, svg_meta = {}, {}
for subtype in all_subtypes:
    svg = get_svg_symbol(subtype)
    match = re.search(r'viewBox="([\d.\s\-]+)"', svg)
    viewbox = match.group(1) if match else "0 0 100 100"
    symbol = re.sub(r"<svg[^>]*>", f'<symbol id="{subtype}" viewBox="{viewbox}">', svg)
    symbol = symbol.replace("</svg>", "</symbol>")
    svg_defs[subtype] = symbol
    svg_meta[subtype] = {'viewBox': viewbox}

for entry in mapping:
    subtype = normalize(entry.get("Component", ""))
    if not subtype:
        continue
    port_name = entry.get("Port Name", "default")
    dx = entry.get("dx", 0)
    dy = entry.get("dy", 0)
    if subtype not in svg_meta:
        svg_meta[subtype] = {"ports": {}}
    if "ports" not in svg_meta[subtype]:
        svg_meta[subtype]["ports"] = {}
    svg_meta[subtype]["ports"][port_name] = {
        "dx": float(dx),
        "dy": float(dy)
    }

class PnidComponent:
    def __init__(self, row):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.subtype = normalize(row.get('block', ''))
        self.x = row['x']
        self.y = row['y']
        self.width = row.get('Width', 60) * SYMBOL_SCALE if 'Width' in row else 60 * SYMBOL_SCALE
        self.height = row.get('Height', 60) * SYMBOL_SCALE if 'Height' in row else 60 * SYMBOL_SCALE
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
        self.points = []
        from_comp = component_map.get(row['From Component'])
        to_comp = component_map.get(row['To Component'])
        if 'Polyline Points (x, y)' in row and isinstance(row['Polyline Points (x, y)'], str) and row['Polyline Points (x, y)']:
            pts = re.findall(r"\(([\d\.\-]+),\s*([\d\.\-]+)\)", row['Polyline Points (x, y)'])
            self.points = [(float(x), float(y)) for x, y in pts]
            if self.points:
                if from_comp: self.points[0] = from_comp.get_port_coords(row.get('From Port'))
                if to_comp: self.points[-1] = to_comp.get_port_coords(row.get('To Port'))
        else:
            if from_comp and to_comp:
                self.points = [
                    from_comp.get_port_coords(row.get('From Port')),
                    to_comp.get_port_coords(row.get('To Port'))
                ]

def render_svg(components, pipes):
    max_x = max((c.x + c.width for c in components.values()), default=0) + PADDING + LEGEND_WIDTH
    max_y = max((c.y + c.height for c in components.values()), default=0) + PADDING + TITLE_BLOCK_HEIGHT
    pipe_max_x = max((x for p in pipes for x, _ in getattr(p, 'points', [])), default=0)
    pipe_max_y = max((y for p in pipes for _, y in getattr(p, 'points', [])), default=0)
    max_x = max(max_x, pipe_max_x + PADDING + LEGEND_WIDTH)
    max_y = max(max_y, pipe_max_y + PADDING + TITLE_BLOCK_HEIGHT)

    svg = []
    svg.append(f'<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">')
    svg.append("<defs>")
    svg.append('<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black"/></marker>')
    for val in svg_defs.values():
        if val: svg.append(val)
    svg.append("</defs>")

    for i in range(0, int(max_x), GRID_SPACING):
        svg.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{max_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, int(max_y), GRID_SPACING):
        svg.append(f'<line x1="0" y1="{i}" x2="{max_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')

    legend_x = max_x - LEGEND_WIDTH + 30
    legend_y = 50
    svg.append(f'<rect x="{legend_x-10}" y="{legend_y-30}" width="{LEGEND_WIDTH-40}" height="{min(650, max_y-60)}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    svg.append(f'<text x="{legend_x+80}" y="{legend_y-10}" font-size="{LEGEND_FONT_SIZE+4}" font-weight="bold">Legend</text>')

    legend_entries = {}
    for c in components.values():
        if not c.subtype:
            continue
        key = (c.tag, c.subtype)
        if key not in legend_entries:
            legend_entries[key] = c.subtype.replace("_", " ").title()
    legend_y_pos = legend_y + 20
    for i, ((tag, subtype), name) in enumerate(legend_entries.items()):
        if not subtype or subtype not in svg_defs:
            continue
        sym_pos_y = legend_y_pos + i*28 - 10
        if svg_defs.get(subtype):
            try:
                viewBox = svg_meta[subtype]["viewBox"].split(" ")
                vb_w = float(viewBox[2])
                vb_h = float(viewBox[3])
                scale_factor = min(25 / vb_w, 25 / vb_h)
                width = vb_w * scale_factor
                height = vb_h * scale_factor
            except Exception:
                width = height = 20
            svg.append(f'<use href="#{subtype}" x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" />')
        else:
            svg.append(f'<rect x="{legend_x}" y="{sym_pos_y}" width="20" height="20" fill="#eee" stroke="red"/>')
        svg.append(f'<text x="{legend_x+32}" y="{sym_pos_y+16}" font-size="{LEGEND_FONT_SIZE}">{tag} — {name}</text>')

    svg.append(f'<rect x="10" y="{max_y-TITLE_BLOCK_HEIGHT}" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT-10}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+30}" font-size="14" font-weight="bold">{TITLE_BLOCK_CLIENT}</text>')
    svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+55}" font-size="12">Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</text>')

    for c in components.values():
        if not c.subtype or c.subtype not in svg_defs:
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')
        elif svg_defs[c.subtype]:
            svg.append(f'<use href="#{c.subtype}" x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" />')
            svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 14}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
        else:
            svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')

    for p in pipes:
        if len(p.points) >= 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)"/>')
            mx = sum(x for x, y in p.points) / len(p.points)
            my = sum(y for x, y in p.points) / len(p.points)
            svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')

    svg.append('</svg>')
    return "".join(svg)

# === UI DROPDOWNS ===
st.sidebar.markdown("---")
st.sidebar.markdown("### Add Components")
with st.sidebar.expander("➕ Equipment"):
    selected_eq = st.selectbox("Equipment Type", equipment_types)
    st.write(f"Selected: {selected_eq}")

with st.sidebar.expander("➕ In-line Component"):
    selected_inline = st.selectbox("Inline Component Type", inline_types)
    st.write(f"Selected: {selected_inline}")

with st.sidebar.expander("➕ Pipeline"):
    selected_pipe = st.selectbox("Pipeline Type", pipeline_types)
    st.write(f"Selected: {selected_pipe}")

components = {row['id']: PnidComponent(row) for _, row in eq_df.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df.iterrows()]
svg_output = render_svg(components, pipes)

st.markdown("## Preview: Auto-Generated P&ID")
st.markdown(svg_output, unsafe_allow_html=True)

def generate_control_logic_box(components):
    logic_lines = []
    logic_lines.append("INSTRUMENTATION CONTROL LOGIC")
    logic_lines.append("──────────────────────────────")
    loop_counter = 1
    for comp in components.values():
        if any(code in comp.tag for code in ['PT', 'TT', 'FT', 'LT']):
            loop_id = f"LOOP-{loop_counter:03d}"
            logic_lines.append(f"{comp.tag} → PID → CV-{loop_counter:03d} ({loop_id})")
            loop_counter += 1
    return "\n".join(logic_lines)

logic_block = generate_control_logic_box(components)
st.text_area("ISA Instrumentation Control Logic", value=logic_block, height=160)

def export_png(svg_data):
    from cairosvg import svg2png
    output = BytesIO()
    svg2png(bytestring=clean_svg(svg_data).encode(), write_to=output)
    return output.getvalue()

def export_dxf(components, pipes):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for c in components.values():
        txt = msp.add_text(c.tag, dxfattribs={'height': 2.5})
        txt.dxf.insert = (c.x, c.y)
    for p in pipes:
        if len(p.points) >= 2:
            msp.add_lwpolyline(p.points)
    output = BytesIO()
    doc.write(output)
    return output.getvalue()

st.download_button("📥 Download SVG", svg_output, "pnid.svg", "image/svg+xml")
st.download_button("📥 Download PNG", export_png(svg_output), "pnid.png", "image/png")
st.download_button("📥 Download DXF", export_dxf(components, pipes), "pnid.dxf", "application/dxf")

def render_legend_only():
    svg = []
    svg.append(f'<svg width="{LEGEND_WIDTH}" height="800" xmlns="http://www.w3.org/2000/svg">')
    svg.append("<defs>")
    for val in svg_defs.values():
        if val:
            svg.append(val)
    svg.append("</defs>")

    legend_x = 10
    legend_y = 30
    svg.append(f'<text x="{legend_x+80}" y="{legend_y}" font-size="{LEGEND_FONT_SIZE+4}" font-weight="bold">Legend</text>')

    legend_entries = {}
    for c in components.values():
        if not c.subtype:
            continue
        key = (c.tag, c.subtype)
        if key not in legend_entries:
            legend_entries[key] = c.subtype.replace("_", " ").title()

    legend_y_pos = legend_y + 20
    for i, ((tag, subtype), name) in enumerate(legend_entries.items()):
        if not subtype or subtype not in svg_defs:
            continue
        sym_pos_y = legend_y_pos + i*30
        if svg_defs.get(subtype):
            try:
                viewBox = svg_meta[subtype]["viewBox"].split(" ")
                vb_w = float(viewBox[2])
                vb_h = float(viewBox[3])
                scale_factor = min(25 / vb_w, 25 / vb_h)
                width = vb_w * scale_factor
                height = vb_h * scale_factor
            except Exception:
                width = height = 20
            svg.append(f'<use href="#{subtype}" x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" />')
        else:
            svg.append(f'<rect x="{legend_x}" y="{sym_pos_y}" width="20" height="20" fill="#eee" stroke="red"/>')
        svg.append(f'<text x="{legend_x+32}" y="{sym_pos_y+16}" font-size="{LEGEND_FONT_SIZE}">{tag} — {name}</text>')

    svg.append("</svg>")
    return "".join(svg)

with st.expander("🧾 Show Only Legend", expanded=False):
    st.markdown(render_legend_only(), unsafe_allow_html=True)

with st.expander("🔍 Debug Info"):
    st.write("Loaded Subtypes:", all_subtypes)
    st.write("SVG Meta:", svg_meta)
    st.write("Total Components:", len(components))
    st.write("Total Pipes:", len(pipes))
    st.code(logic_block, language="text")
