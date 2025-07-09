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

# Streamlit Config
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
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Utility ---
def normalize(s):
    if not isinstance(s, str): return ""
    return s.lower().strip().replace(" ", "_").replace("-", "_")

def clean_svg(svg: str):
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
    except Exception as e:
        st.error(f"[DB LOAD ERROR] {e}")
        return None

def save_svg_to_db(subtype, svg_data):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO generated_symbols (subtype, svg_data) 
            VALUES (%s, %s) 
            ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data
        """, (subtype, svg_data))
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
        st.error(f"[OpenAI SVG Gen Error for '{subtype}']: {e}")
        return None
        # Continue from previous part — Component + Pipe Rendering already done

# Auto-generate ISA Control Logic Box
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

# Load dropdown options from CSVs in layout_data
def load_dropdown_options():
    try:
        eq = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "equipment_list.csv"))
        pipe = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "pipeline_list.csv"))
        inline = pd.read_csv(os.path.join(LAYOUT_DATA_DIR, "inline_component_list.csv"))

        equipment_types = sorted(eq['block'].dropna().unique())
        pipeline_types = sorted(pipe['block'].dropna().unique())
        inline_types = sorted(inline['block'].dropna().unique())

        return equipment_types, pipeline_types, inline_types
    except Exception as e:
        st.error(f"Dropdown loading error: {e}")
        return [], [], []

equipment_types, pipeline_types, inline_types = load_dropdown_options()

# --- UI Dropdowns (real from CSV) ---
st.sidebar.markdown("### Add Components")
with st.sidebar.expander("➕ Equipment"):
    selected_eq = st.selectbox("Select Equipment Type", equipment_types)
    st.write(f"Selected: {selected_eq}")

with st.sidebar.expander("➕ In-line Component"):
    selected_inline = st.selectbox("Select Inline Component", inline_types)
    st.write(f"Selected: {selected_inline}")

with st.sidebar.expander("➕ Pipeline"):
    selected_pipe = st.selectbox("Select Pipeline Type", pipeline_types)
    st.write(f"Selected: {selected_pipe}")

# Final re-processing after optional add
components = {row['id']: PnidComponent(row) for _, row in eq_df.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df.iterrows()]
svg_output = render_svg(components, pipes)

# Show diagram
st.markdown("## Preview: Auto-Generated P&ID")
st.markdown(svg_output, unsafe_allow_html=True)

# Show ISA control logic
logic_block = generate_control_logic_box(components)
st.text_area("ISA Instrumentation Control Logic", value=logic_block, height=160)

# PNG Export
def export_png(svg_data):
    from cairosvg import svg2png
    output = BytesIO()
    svg2png(bytestring=clean_svg(svg_data).encode(), write_to=output)
    return output.getvalue()

# DXF Export
def export_dxf(components, pipes):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for c in components.values():
        msp.add_text(c.tag, dxfattribs={'height': 2.5}).set_placement((c.x, c.y))
    for p in pipes:
        if len(p.points) >= 2:
            msp.add_lwpolyline(p.points)
    output = BytesIO()
    doc.write(output)
    return output.getvalue()

# Download buttons
st.download_button("📥 Download SVG", svg_output, "pnid.svg", "image/svg+xml")
st.download_button("📥 Download PNG", export_png(svg_output), "pnid.png", "image/png")
st.download_button("📥 Download DXF", export_dxf(components, pipes), "pnid.dxf", "application/dxf")
# --- Legend Enhancements (Optional: Export Legend PNG) ---
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

# Optional: Display standalone legend
with st.expander("🧾 Show Only Legend", expanded=False):
    st.markdown(render_legend_only(), unsafe_allow_html=True)

# Optional debugging/logs
with st.expander("🔍 Debug Info"):
    st.write("Loaded Subtypes:", all_subtypes)
    st.write("SVG Meta:", svg_meta)
    st.write("Total Components:", len(components))
    st.write("Total Pipes:", len(pipes))
    st.code(logic_block, language="text")
