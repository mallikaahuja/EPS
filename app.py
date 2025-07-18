import streamlit as st
import pandas as pd
import math
import base64
import os

st.set_page_config(page_title="EPS P&ID Suite", layout="wide", initial_sidebar_state="expanded")

# --- SHEET SIZES (A3/A2) ---
SHEET_SIZES = {
    "A3": (1122, 793),   # px at 96dpi
    "A2": (1587, 1122),
    "A1": (2245, 1587),
    "A0": (3179, 2245),
}

# --- SVG SYMBOL DEFINITIONS ---

def get_symbol_svg(comp_type):
    # Central place for symbol SVGs, can be expanded
    symbols = {
        'pump_centrifugal': '''<g>
            <ellipse cx="0" cy="0" rx="32" ry="32" fill="white" stroke="black" stroke-width="2.5"/>
            <path d="M -16,-19 Q 0,-25 16,-19 Q 18,0 16,19 Q 0,25 -16,19 Q -18,0 -16,-19 Z"
                fill="none" stroke="black" stroke-width="2"/>
            <circle cx="0" cy="0" r="8" fill="white" stroke="black" stroke-width="2"/>
            <circle cx="0" cy="0" r="3" fill="black"/>
            <line x1="-32" y1="0" x2="-48" y2="0" stroke="black" stroke-width="3"/>
            <line x1="32" y1="0" x2="48" y2="0" stroke="black" stroke-width="3"/>
        </g>''',
        'valve_gate': '''<g>
            <rect x="-20" y="-10" width="40" height="20" fill="white" stroke="black" stroke-width="2.5"/>
            <line x1="-20" y1="0" x2="20" y2="0" stroke="black" stroke-width="3"/>
            <line x1="-30" y1="0" x2="-20" y2="0" stroke="black" stroke-width="3"/>
            <line x1="20" y1="0" x2="30" y2="0" stroke="black" stroke-width="3"/>
        </g>''',
        'instrument': '''<g>
            <circle cx="0" cy="0" r="18" fill="white" stroke="black" stroke-width="2.5"/>
            <line x1="-18" y1="0" x2="18" y2="0" stroke="black" stroke-width="2"/>
        </g>''',
        'filter_suction': '''<g>
            <rect x="-15" y="-30" width="30" height="60" fill="white" stroke="black" stroke-width="2.5"/>
            <polygon points="-15,-30 0,-50 15,-30" fill="white" stroke="black" stroke-width="2.5"/>
            <polygon points="-15,30 0,50 15,30" fill="white" stroke="black" stroke-width="2.5"/>
        </g>''',
        'vessel_vertical': '''<g>
            <ellipse cx="0" cy="-40" rx="30" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="-30" y="-40" width="60" height="80" fill="white" stroke="black" stroke-width="2.5"/>
            <ellipse cx="0" cy="40" rx="30" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
        </g>''',
        'vessel_horizontal': '''<g>
            <ellipse cx="-32" cy="0" rx="10" ry="24" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="-32" y="-24" width="64" height="48" fill="white" stroke="black" stroke-width="2.5"/>
            <ellipse cx="32" cy="0" rx="10" ry="24" fill="white" stroke="black" stroke-width="2.5"/>
        </g>''',
        # Add other symbols as needed...
    }
    # Use vessel_vertical for vessel, vessel_horizontal for silencer, etc.
    return symbols.get(comp_type, symbols.get('vessel_vertical'))

# --- COMPONENT CLASS ---
class Component:
    def __init__(self, id, tag, type, x, y, width, height, description=None, rotation=0):
        self.id = id
        self.tag = tag
        self.type = type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.description = description or ""
        self.rotation = rotation

    def get_svg(self, scale=1.0):
        symbol = get_symbol_svg(self.type)
        # Text below symbol
        return f'''
        <g transform="translate({self.x},{self.y}) scale({scale}) rotate({self.rotation})">
            {symbol}
            <text x="0" y="{self.height//2+22}" text-anchor="middle" font-size="11" font-family="Arial" font-weight="bold">{self.tag}</text>
            <text x="0" y="{self.height//2+36}" text-anchor="middle" font-size="9" font-family="Arial">{self.description}</text>
        </g>
        '''

# --- PIPE CLASS ---
class Pipe:
    def __init__(self, from_comp, to_comp, from_port, to_port, line_type, label, with_arrow=True, waypoints=None):
        self.from_comp = from_comp
        self.to_comp = to_comp
        self.from_port = from_port
        self.to_port = to_port
        self.line_type = line_type
        self.label = label
        self.with_arrow = with_arrow
        self.waypoints = waypoints or []

    def get_svg(self, comp_lookup, line_weights):
        # Basic straight line logic (expand to use waypoints if needed)
        x1, y1 = comp_lookup[self.from_comp].x, comp_lookup[self.from_comp].y
        x2, y2 = comp_lookup[self.to_comp].x, comp_lookup[self.to_comp].y
        # Offset ports if you want advanced, but for now just center-to-center

        # Style by type
        if self.line_type == 'process':
            style = f'stroke:black;stroke-width:{line_weights["major_process"]}'
        elif self.line_type == 'instrument_signal':
            style = f'stroke:black;stroke-width:{line_weights["instrument_signal"]};stroke-dasharray:8,5'
        else:
            style = f'stroke:black;stroke-width:{line_weights["utility"]}'

        # Arrow
        arrow_svg = ""
        if self.with_arrow:
            # Arrowhead at (x2,y2), direction from (x1,y1)
            dx, dy = x2-x1, y2-y1
            length = math.hypot(dx, dy)
            if length:
                ux, uy = dx/length, dy/length
                ax, ay = x2 - ux*18, y2 - uy*18
                arrow_svg = f'<polygon points="{x2},{y2} {ax-uy*6},{ay+ux*6} {ax+uy*6},{ay-ux*6}" fill="black"/>'

        # Label at midpoint
        mx, my = (x1+x2)/2, (y1+y2)/2

        return f'''
        <g>
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="{style}"/>
            {arrow_svg}
            {"<rect x='%s' y='%s' width='56' height='18' fill='white' stroke='none'/><text x='%s' y='%s' font-size='10' font-family='Arial' text-anchor='middle'>%s</text>" % (mx-28, my-16, mx, my-4, self.label) if self.label else ""}
        </g>
        '''

# --- LOAD COMPONENTS FROM CSV ---
def load_components_from_csv(csv_path, grid=25):
    df = pd.read_csv(csv_path)
    comps = []
    for _, row in df.iterrows():
        # Snap to grid
        x = round(row['x'] / grid) * grid
        y = round(row['y'] / grid) * grid
        comps.append(Component(
            id=row['id'],
            tag=row['tag'],
            type=row['Component'],
            x=x,
            y=y,
            width=row['Width'],
            height=row['Height'],
            description=row.get('Description', ''),
            rotation=row.get('rotation', 0)
        ))
    return comps

def load_pipes_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    pipes = []
    for _, row in df.iterrows():
        pipes.append(Pipe(
            from_comp=row['from_component'],
            to_comp=row['to_component'],
            from_port=row['from_port'],
            to_port=row['to_port'],
            line_type=row['line_type'],
            label=row['line_number'] if pd.notnull(row['line_number']) else '',
            with_arrow=row.get('with_arrow', True),
            waypoints=[] # not used in basic version
        ))
    return pipes

# --- SVG RENDERING ---
def render_svg(components, pipes, width, height, show_legend, show_bom, grid_spacing, symbol_scale, line_weights):
    svg_parts = []

    # SVG header
    svg_parts.append(f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg" style="background-color: white; font-family: Arial;">''')

    # Draw border and title block
    svg_parts.append(f'<rect x="6" y="6" width="{width-12}" height="{height-12}" fill="none" stroke="black" stroke-width="2"/>')
    svg_parts.append(f'''
    <g id="title-block">
        <rect x="6" y="{height-92}" width="{width-12}" height="86" fill="none" stroke="black" stroke-width="2"/>
        <text x="30" y="{height-70}" font-size="18" font-weight="bold">TENTATIVE P&ID DRAWING FOR SUCTION FILTER + KDP-330</text>
        <text x="30" y="{height-48}" font-size="13">Sheet: 1/1  |  Scale: 1:1  |  Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}</text>
        <text x="30" y="{height-28}" font-size="13">Economy Process Solutions Pvt. Ltd.</text>
    </g>
    ''')

    # Draw grid
    if st.session_state.show_grid:
        for gx in range(0, width, grid_spacing):
            svg_parts.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{height}" stroke="#e0e0e0" stroke-width="1"/>')
        for gy in range(0, height, grid_spacing):
            svg_parts.append(f'<line x1="0" y1="{gy}" x2="{width}" y2="{gy}" stroke="#e0e0e0" stroke-width="1"/>')

    # Build lookup for pipes to find coordinates
    comp_lookup = {comp.id: comp for comp in components}

    # Draw pipes below everything
    svg_parts.append('<g id="pipes">')
    for pipe in pipes:
        if pipe.from_comp in comp_lookup and pipe.to_comp in comp_lookup:
            svg_parts.append(pipe.get_svg(comp_lookup, line_weights))
    svg_parts.append('</g>')

    # Draw components
    svg_parts.append('<g id="components">')
    for comp in components:
        svg_parts.append(comp.get_svg(scale=symbol_scale))
    svg_parts.append('</g>')

    # Equipment List (BOM)
    if show_bom:
        svg_parts.append(f'''
        <g id="equipment-list" transform="translate(40,36)">
            <rect x="0" y="0" width="320" height="260" fill="white" stroke="black" stroke-width="2"/>
            <text x="160" y="22" font-size="13" font-weight="bold" text-anchor="middle">EQUIPMENT LIST</text>
            <line x1="0" y1="34" x2="320" y2="34" stroke="black"/>
            <text x="16" y="54" font-size="11" font-weight="bold">TAG</text>
            <text x="80" y="54" font-size="11" font-weight="bold">DESCRIPTION</text>
            <line x1="0" y1="60" x2="320" y2="60" stroke="black"/>
        ''')
        y = 78
        for comp in components[:12]:
            svg_parts.append(f'<text x="16" y="{y}" font-size="10">{comp.tag}</text>')
            svg_parts.append(f'<text x="80" y="{y}" font-size="10">{comp.description}</text>')
            y += 16
        svg_parts.append('</g>')

    # Legend
    if show_legend:
        svg_parts.append(f'''
        <g id="legend" transform="translate({width-380},{36})">
            <rect x="0" y="0" width="340" height="210" fill="white" stroke="black" stroke-width="2"/>
            <text x="170" y="22" font-size="13" font-weight="bold" text-anchor="middle">LEGEND</text>
            <line x1="0" y1="34" x2="340" y2="34" stroke="black"/>
            <text x="20" y="56" font-size="11">P - Pump</text>
            <text x="20" y="76" font-size="11">V - Valve</text>
            <text x="20" y="96" font-size="11">SF - Suction Filter</text>
            <text x="20" y="116" font-size="11">TK - Tank</text>
            <text x="20" y="136" font-size="11">HX - Heat Exchanger</text>
            <text x="20" y="156" font-size="11">PT - Pressure Transmitter</text>
            <text x="20" y="176" font-size="11">FT - Flow Transmitter</text>
            <text x="20" y="196" font-size="11">TT - Temperature Transmitter</text>
        </g>
        ''')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

# --- STREAMLIT UI ---

st.title("🏭 EPS P&ID Suite")

# Sidebar
with st.sidebar:
    st.header("📐 Drawing Standards")
    drawing_standard = st.selectbox("Standard", ["ISA", "ISO", "DIN", "JIS"])
    drawing_size = st.selectbox("Size", ["A3", "A2", "A1", "A0"])
    width, height = SHEET_SIZES[drawing_size]

    st.header("🎨 Visual Controls")
    st.session_state.show_grid = st.checkbox("Show Grid", value=True)
    st.session_state.show_legend = st.checkbox("Show Legend", value=True)
    st.session_state.show_bom = st.checkbox("Show BOM", value=True)
    grid_spacing = st.slider("Grid Spacing (mm)", 10, 50, 25)
    symbol_scale = st.slider("Symbol Scale", 0.5, 2.0, 1.0, 0.1)

# Use professional line weights
line_weights = {
    'major_process': 3.0,
    'minor_process': 2.0,
    'utility': 2.0,
    'instrument_signal': 1.2,
    'border': 2.0,
    'equipment': 2.5,
    'text': 0.5
}

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### P&ID Drawing")
    # Load components and pipes from CSVs
    components = load_components_from_csv("enhanced_equipment_layout.csv", grid=grid_spacing)
    pipes = load_pipes_from_csv("pipes_connections.csv")
    svg_content = render_svg(
        components, pipes, width, height,
        show_legend=st.session_state.show_legend,
        show_bom=st.session_state.show_bom,
        grid_spacing=grid_spacing,
        symbol_scale=symbol_scale,
        line_weights=line_weights
    )
    st.components.v1.html(f'''
    <div style="background: white; border: 1px solid #ccc; width: 100%; height: 900px; overflow: auto;">
        {svg_content}
    </div>
    ''', height=900)

with col2:
    st.markdown("### Component Library")
    category = st.selectbox("Category", ["Pumps", "Valves", "Vessels", "Instruments", "Piping"])
    if category == "Pumps":
        st.write("🔄 Centrifugal Pump")
        st.write("🔄 Vacuum Pump")
        st.write("🔄 Positive Displacement Pump")
    elif category == "Valves":
        st.write("🔧 Gate Valve")
        st.write("🔧 Globe Valve")
        st.write("🔧 Control Valve")
    elif category == "Vessels":
        st.write("🏗️ Vertical Tank")
        st.write("🏗️ Horizontal Vessel")
        st.write("🏗️ Separator")
    elif category == "Instruments":
        st.write("📟 Pressure Transmitter")
        st.write("📟 Flow Transmitter")
    elif category == "Piping":
        st.write("➖ Process Line")
        st.write("➖ Instrument Signal")

# Footer and Export
col3, col4, col5 = st.columns(3)
with col3:
    if st.button("💾 Export SVG"):
        b64 = base64.b64encode(svg_content.encode()).decode()
        href = f'<a href="data:image/svg+xml;base64,{b64}" download="pnid_drawing.svg">Download SVG</a>'
        st.markdown(href, unsafe_allow_html=True)
with col4:
    if st.button("📊 Component Count"):
        st.info(f"Total Components: {len(components)} | Total Pipes: {len(pipes)}")
with col5:
    if st.button("🔄 Refresh"):
        st.rerun()

st.markdown("---")
st.markdown("EPS Process Solutions Pvt. Ltd. - P&ID Automation Platform")
