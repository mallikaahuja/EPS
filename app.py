import streamlit as st
import pandas as pd
import json
import os
import math
import base64

# --- PAGE CONFIG ---

st.set_page_config(page_title="EPS P&ID Suite", layout="wide", initial_sidebar_state="expanded")

# --- SVG SYMBOL DEFINITIONS ---

def get_pump_symbol():
    return '''<g>
    <circle cx="0" cy="0" r="30" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M -15,-20 Q 0,-25 15,-20 Q 20,-5 15,10 Q 0,15 -15,10 Q -20,-5 -15,-20 Z"
    fill="none" stroke="black" stroke-width="2"/>
    <circle cx="0" cy="0" r="4" fill="black"/>
    <line x1="-30" y1="0" x2="-40" y2="0" stroke="black" stroke-width="3"/>
    <line x1="30" y1="0" x2="40" y2="0" stroke="black" stroke-width="3"/>
    </g>'''

def get_valve_symbol():
    return '''<g>
    <path d="M -20,-10 L -20,10 L 0,0 L 20,10 L 20,-10 L 0,0 Z"
    fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="-25" y1="0" x2="-20" y2="0" stroke="black" stroke-width="3"/>
    <line x1="20" y1="0" x2="25" y2="0" stroke="black" stroke-width="3"/>
    </g>'''

def get_vessel_symbol():
    return '''<g>
    <ellipse cx="0" cy="-35" rx="25" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="-25" y="-35" width="50" height="70" fill="white" stroke="black" stroke-width="2.5"/>
    <ellipse cx="0" cy="35" rx="25" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="0" y1="-45" x2="0" y2="-55" stroke="black" stroke-width="3"/>
    <line x1="0" y1="45" x2="0" y2="55" stroke="black" stroke-width="3"/>
    </g>'''

def get_filter_symbol():
    return '''<g>
    <path d="M -20,-30 L 20,-30 L 15,20 L 10,30 L -10,30 L -15,20 Z"
    fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="-15" y1="-20" x2="15" y2="-20" stroke="black" stroke-width="1.5"/>
    <line x1="-13" y1="-15" x2="13" y2="-15" stroke="black" stroke-width="1.5"/>
    <line x1="-11" y1="-10" x2="11" y2="-10" stroke="black" stroke-width="1.5"/>
    <line x1="-9" y1="-5" x2="9" y2="-5" stroke="black" stroke-width="1.5"/>
    <line x1="0" y1="-40" x2="0" y2="-30" stroke="black" stroke-width="3"/>
    <line x1="0" y1="30" x2="0" y2="40" stroke="black" stroke-width="3"/>
    </g>'''

def get_control_valve_symbol():
    return '''<g>
    <path d="M -20,-10 L -20,10 L 0,0 L 20,10 L 20,-10 L 0,0 Z"
    fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="-15" y="-35" width="30" height="25" rx="5" fill="white" stroke="black" stroke-width="2"/>
    <line x1="0" y1="-10" x2="0" y2="-25" stroke="black" stroke-width="1.5"/>
    <line x1="-25" y1="0" x2="-20" y2="0" stroke="black" stroke-width="3"/>
    <line x1="20" y1="0" x2="25" y2="0" stroke="black" stroke-width="3"/>
    </g>'''

def get_instrument_symbol():
    return '''<g>
    <circle cx="0" cy="0" r="20" fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="-20" y1="0" x2="20" y2="0" stroke="black" stroke-width="2"/>
    </g>'''

def get_heat_exchanger_symbol():
    return '''<g>
    <rect x="-40" y="-20" width="80" height="40" fill="white" stroke="black" stroke-width="2.5"/>
    <circle cx="-20" cy="0" r="15" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="20" cy="0" r="15" fill="none" stroke="black" stroke-width="1.5"/>
    <line x1="-40" y1="0" x2="-50" y2="0" stroke="black" stroke-width="3"/>
    <line x1="40" y1="0" x2="50" y2="0" stroke="black" stroke-width="3"/>
    <line x1="0" y1="-20" x2="0" y2="-30" stroke="black" stroke-width="3"/>
    <line x1="0" y1="20" x2="0" y2="30" stroke="black" stroke-width="3"/>
    </g>'''

# Component class

class Component:
    def __init__(self, id, tag, type, x, y, description=""):
        self.id = id
        self.tag = tag
        self.type = type
        self.x = x
        self.y = y
        self.description = description

    def get_svg(self):
        """Get SVG representation with proper symbol"""
        symbol_map = {
            'pump': get_pump_symbol(),
            'valve': get_valve_symbol(),
            'vessel': get_vessel_symbol(),
            'tank': get_vessel_symbol(),
            'filter': get_filter_symbol(),
            'control_valve': get_control_valve_symbol(),
            'instrument': get_instrument_symbol(),
            'heat_exchanger': get_heat_exchanger_symbol(),
        }

        # Find matching symbol
        symbol = None
        for key in symbol_map:
            if key in self.type.lower():
                symbol = symbol_map[key]
                break

        if not symbol:
            # Default rectangle
            symbol = f'<rect x="-25" y="-20" width="50" height="40" fill="white" stroke="black" stroke-width="2"/>'

        # Add text for instruments
        text_addon = ""
        if 'instrument' in self.type.lower() or any(x in self.tag for x in ['PT', 'TT', 'FT', 'LT']):
            parts = self.tag.split('-')
            if len(parts) == 2:
                text_addon = f'''
                <text x="0" y="-5" text-anchor="middle" font-size="10" font-weight="bold">{parts[0]}</text>
                <text x="0" y="8" text-anchor="middle" font-size="8">{parts[1]}</text>'''

        return f'''<g transform="translate({self.x},{self.y})">
            {symbol}
            {text_addon}
            <text x="0" y="50" text-anchor="middle" font-size="10" font-weight="bold">{self.tag}</text>
        </g>'''

class Pipe:
    def __init__(self, from_comp, to_comp, from_port="center", to_port="center", label=""):
        self.from_comp = from_comp
        self.to_comp = to_comp
        self.from_port = from_port
        self.to_port = to_port
        self.label = label

    def get_svg(self):
        """Get pipe SVG with orthogonal routing"""
        # Calculate port positions
        from_x, from_y = self._get_port_position(self.from_comp, self.from_port)
        to_x, to_y = self._get_port_position(self.to_comp, self.to_port)

        # Simple orthogonal routing
        path_points = []
        if abs(from_x - to_x) > abs(from_y - to_y):
            # Horizontal first
            mid_x = (from_x + to_x) / 2
            path_points = [(from_x, from_y), (mid_x, from_y), (mid_x, to_y), (to_x, to_y)]
        else:
            # Vertical first
            mid_y = (from_y + to_y) / 2
            path_points = [(from_x, from_y), (from_x, mid_y), (to_x, mid_y), (to_x, to_y)]

        # Build path
        path_d = f"M {path_points[0][0]},{path_points[0][1]}"
        for point in path_points[1:]:
            path_d += f" L {point[0]},{point[1]}"

        svg = f'<path d="{path_d}" fill="none" stroke="black" stroke-width="2" />'

        # Add arrow
        if len(path_points) >= 2:
            p1, p2 = path_points[-2], path_points[-1]
            angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
            arrow_x = p2[0] - 20 * math.cos(math.radians(angle))
            arrow_y = p2[1] - 20 * math.sin(math.radians(angle))

            svg += f'''<polygon points="-8,-4 0,0 -8,4" fill="black"
                      transform="translate({arrow_x},{arrow_y}) rotate({angle})"/>'''

        # Add label
        if self.label and len(path_points) >= 2:
            mid_idx = len(path_points) // 2
            label_x = (path_points[mid_idx-1][0] + path_points[mid_idx][0]) / 2
            label_y = (path_points[mid_idx-1][1] + path_points[mid_idx][1]) / 2

            svg += f'''<rect x="{label_x - 40}" y="{label_y - 10}" width="80" height="20"
                      fill="white" stroke="none"/>
                      <text x="{label_x}" y="{label_y + 3}" text-anchor="middle"
                      font-size="9">{self.label}</text>'''

        return svg

    def _get_port_position(self, comp, port):
        """Get position of a port on a component"""
        offsets = {
            'center': (0, 0),
            'top': (0, -40),
            'bottom': (0, 40),
            'left': (-40, 0),
            'right': (40, 0),
            'inlet': (-40, 0),
            'outlet': (40, 0),
            'suction': (-40, 0),
            'discharge': (40, 0),
        }
        offset = offsets.get(port, (0, 0))
        return (comp.x + offset[0], comp.y + offset[1])

def create_pnid():
    """Create P&ID with properly positioned components"""
    components = []
    pipes = []

    # Create main process components with adjusted positions to fit on screen
    components.extend([
        Component("P-001", "P-001", "pump", 400, 300, "KDP-330 Vacuum Pump"),
        Component("V-001", "V-001", "valve", 250, 300, "Inlet Valve"),
        Component("V-002", "V-002", "valve", 550, 300, "Outlet Valve"),
        Component("F-001", "F-001", "filter", 400, 150, "Suction Filter"),
        Component("TK-001", "TK-001", "vessel", 700, 300, "Process Tank"),
        Component("HX-001", "HX-001", "heat_exchanger", 400, 450, "Heat Exchanger"),

        # Instruments
        Component("PT-001", "PT-001", "instrument", 200, 200, "Pressure Transmitter"),
        Component("PT-002", "PT-002", "instrument", 600, 200, "Pressure Transmitter"),
        Component("FT-001", "FT-001", "instrument", 500, 150, "Flow Transmitter"),
        Component("TT-001", "TT-001", "instrument", 300, 450, "Temperature Transmitter"),
        Component("LT-001", "LT-001", "instrument", 800, 300, "Level Transmitter"),

        # Control valves
        Component("FCV-001", "FCV-001", "control_valve", 550, 400, "Flow Control Valve"),
        Component("TCV-001", "TCV-001", "control_valve", 300, 550, "Temperature Control Valve"),

        # Additional equipment
        Component("SF-001", "SF-001", "filter", 100, 300, "Suction Filter"),
        Component("YS-001", "YS-001", "valve", 100, 200, "Y-Strainer"),
        Component("C-001", "C-001", "vessel", 700, 150, "Condenser"),
        Component("SCR-001", "SCR-001", "vessel", 850, 300, "Scrubber"),
        Component("SIL-001", "SIL-001", "vessel", 950, 300, "Silencer"),
        Component("DP-001", "DP-001", "vessel", 700, 500, "Drain Point"),

        # Control panel
        Component("CP-001", "CP-001", "instrument", 950, 150, "Control Panel"),
        Component("RM-001", "RM-001", "instrument", 200, 400, "Rotameter"),
        Component("PR-001", "PR-001", "valve", 100, 400, "Pressure Regulator"),
        Component("GV-001", "GV-001", "valve", 300, 200, "Gate Valve"),
        Component("FA-001", "FA-001", "filter", 850, 200, "Flame Arrestor"),
        Component("LS-001", "LS-001", "instrument", 750, 250, "Level Switch"),
        Component("FS-001", "FS-001", "instrument", 650, 100, "Flow Switch"),
        Component("CPT-001", "CPT-001", "vessel", 600, 450, "Catch Pot"),
    ])

    # Create pipes
    pipes.extend([
        Pipe(components[0], components[2], "outlet", "inlet", "2\"-PG-001"),
        Pipe(components[2], components[4], "outlet", "inlet", "2\"-PG-002"),
        Pipe(components[3], components[0], "bottom", "inlet", "2\"-PG-003"),
        Pipe(components[1], components[0], "outlet", "inlet", "2\"-PG-004"),
        Pipe(components[4], components[17], "bottom", "top", "3\"-PG-005"),
        Pipe(components[5], components[11], "outlet", "inlet", "2\"-PG-006"),
    ])

    return components, pipes

def render_svg(components, pipes, width=1200, height=700):
    """Render complete P&ID as SVG"""
    svg_parts = []

    # SVG header
    svg_parts.append(f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
                         xmlns="http://www.w3.org/2000/svg" style="background-color: white">''')

    # Add definitions for arrow markers
    svg_parts.append('''
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto">
            <polygon points="0,0 8,4 0,8" fill="black"/>
        </marker>
    </defs>''')

    # Draw border
    svg_parts.append(f'''<rect x="5" y="5" width="{width-10}" height="{height-10}"
                         fill="none" stroke="black" stroke-width="2"/>''')

    # Title block
    svg_parts.append(f'''
    <rect x="5" y="{height-85}" width="{width-10}" height="80" fill="none" stroke="black" stroke-width="2"/>
    <text x="20" y="{height-60}" font-size="14" font-weight="bold">P&amp;ID DRAWING - EPS PROCESS SOLUTIONS</text>
    <text x="20" y="{height-40}" font-size="11">Drawing No: AUTO-001 | Rev: 00</text>
    <text x="20" y="{height-20}" font-size="10">Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}</text>
    ''')

    # Draw pipes first
    svg_parts.append('<g id="pipes">')
    for pipe in pipes:
        svg_parts.append(pipe.get_svg())
    svg_parts.append('</g>')

    # Draw components
    svg_parts.append('<g id="components">')
    for comp in components:
        svg_parts.append(comp.get_svg())
    svg_parts.append('</g>')

    # Legend
    if st.session_state.get('show_legend', False):
        svg_parts.append(f'''
        <g id="legend" transform="translate({width-200},20)">
            <rect x="0" y="0" width="180" height="200" fill="white" stroke="black" stroke-width="1"/>
            <text x="90" y="20" text-anchor="middle" font-size="12" font-weight="bold">LEGEND</text>
            <line x1="10" y1="30" x2="170" y2="30" stroke="black"/>
            <text x="10" y="50" font-size="10">P - Pump</text>
            <text x="10" y="70" font-size="10">V - Valve</text>
            <text x="10" y="90" font-size="10">F - Filter</text>
            <text x="10" y="110" font-size="10">TK - Tank</text>
            <text x="10" y="130" font-size="10">HX - Heat Exchanger</text>
            <text x="10" y="150" font-size="10">PT - Pressure Transmitter</text>
            <text x="10" y="170" font-size="10">FT - Flow Transmitter</text>
            <text x="10" y="190" font-size="10">TT - Temperature Transmitter</text>
        </g>''')

    # Equipment list
    if st.session_state.get('show_bom', False):
        svg_parts.append(f'''
        <g id="equipment-list" transform="translate(20,20)">
            <rect x="0" y="0" width="250" height="150" fill="white" stroke="black" stroke-width="1"/>
            <text x="125" y="20" text-anchor="middle" font-size="12" font-weight="bold">EQUIPMENT LIST</text>
            <line x1="0" y1="30" x2="250" y2="30" stroke="black"/>
            <text x="10" y="50" font-size="9">TAG         DESCRIPTION</text>
            <line x1="0" y1="55" x2="250" y2="55" stroke="black" stroke-width="0.5"/>
        </g>''')

        # Add first few equipment items
        y_pos = 70
        for i, comp in enumerate(components[:5]):
            svg_parts.append(f'<text x="30" y="{y_pos}" font-size="9">{comp.tag}      {comp.description}</text>')
            y_pos += 15

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

# --- STREAMLIT UI ---

st.title("🏭 EPS P&ID Suite")

# Sidebar

with st.sidebar:
    st.header("📐 Drawing Standards")
    drawing_standard = st.selectbox("Standard", ["ISA", "ISO", "DIN", "JIS"])
    drawing_size = st.selectbox("Size", ["A3", "A2", "A1", "A0"])

    st.header("🎨 Visual Controls")
    st.session_state.show_grid = st.checkbox("Show Grid", value=False)
    st.session_state.show_legend = st.checkbox("Show Legend", value=True)
    st.session_state.show_bom = st.checkbox("Show BOM", value=True)

    grid_spacing = st.slider("Grid Spacing (mm)", 10, 50, 25)
    symbol_scale = st.slider("Symbol Scale", 0.5, 2.0, 1.0, 0.1)

# Main content area

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### P&ID Drawing")

    # Create P&ID
    components, pipes = create_pnid()

    # Render SVG
    svg_content = render_svg(components, pipes)

    # Display using HTML component
    st.components.v1.html(f'''
    <div style="background: white; border: 1px solid #ccc; width: 100%; height: 750px; overflow: auto;">
        {svg_content}
    </div>
    ''', height=750)

with col2:
    st.markdown("### Component Library")

    category = st.selectbox("Category", ["Pumps", "Valves", "Vessels", "Instruments", "Piping"])

    if category == "Pumps":
        st.write("🔄 Centrifugal Pump")
        st.write("🔄 Vacuum Pump")
        st.write("🔄 Positive Displacement")
    elif category == "Valves":
        st.write("🔧 Gate Valve")
        st.write("🔧 Globe Valve")
        st.write("🔧 Control Valve")
    elif category == "Vessels":
        st.write("🏗️ Vertical Tank")
        st.write("🏗️ Horizontal Vessel")
        st.write("🏗️ Separator")

# Bottom toolbar

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
        st.rerun() # Use st.rerun() instead of st.experimental_rerun() for newer Streamlit versions

# Footer

st.markdown("---")
st.markdown("EPS Process Solutions Pvt. Ltd. - P&ID Automation Platform")
