import streamlit as st
import pandas as pd
import os
import json
import datetime
import re
import openai
import psycopg2
from psycopg2 import sql
from io import BytesIO
import ezdxf
from cairosvg import svg2png
import math

# Import advanced features

from control_systems import (
    ControlSystemAnalyzer, PipeRouter, ProcessUnitTemplate,
    PnIDValidator, render_control_loop_overlay, render_validation_overlay
)

# --- CONFIGURATION ---

st.set_page_config(layout="wide", page_title="EPS Professional P&ID Generator",
                   initial_sidebar_state="expanded")

# Add custom CSS for professional styling

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 24px;
    }
    .validation-error {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 10px;
        margin: 5px 0;
    }
    .validation-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 10px;
        margin: 5px 0;
    }
    .control-loop-info {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🏭 EPS Professional P&ID Suite")

# Professional P&ID Standards

LINE_STANDARDS = {
    'process': {'width': 2, 'color': '#000000', 'style': 'solid'},
    'process_thick': {'width': 3, 'color': '#000000', 'style': 'solid'},
    'instrumentation': {'width': 0.7, 'color': '#000000', 'style': 'dashed', 'dash': '4,2'},
    'electrical': {'width': 0.7, 'color': '#000000', 'style': 'dashed', 'dash': '2,2'},
    'pneumatic': {'width': 0.7, 'color': '#000000', 'style': 'solid'},
    'hydraulic': {'width': 1.5, 'color': '#000000', 'style': 'solid'},
    'software': {'width': 0.5, 'color': '#0066cc', 'style': 'dotted', 'dash': '1,3'},
}

# Visual controls with professional defaults

st.sidebar.markdown("### 🎨 Drawing Standards")
drawing_standard = st.sidebar.selectbox(
    "Standard",
    ["ISA", "DIN", "ISO", "Custom"],
    help="Select P&ID drawing standard"
)

GRID_SPACING = st.sidebar.slider("Grid Spacing (mm)", 10, 50, 25, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.0, 1.0, 0.1)
PIPE_WIDTH = st.sidebar.slider("Line Weight", 1, 5, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 16, 11)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Line Label Size", 6, 14, 9)
INSTRUMENT_BUBBLE_SIZE = st.sidebar.slider("Instrument Bubble Size", 15, 30, 22)

# Advanced features toggles

st.sidebar.markdown("### 🔧 Advanced Features")
show_control_loops = st.sidebar.checkbox("Show Control Loops", True)
show_interlocks = st.sidebar.checkbox("Show Interlocks", True)
enable_smart_routing = st.sidebar.checkbox("Smart Pipe Routing", True)
enable_validation = st.sidebar.checkbox("Real-time Validation", True)
enable_templates = st.sidebar.checkbox("Use Templates", True)

# Global constants

PADDING = 100
BORDER_WIDTH = 1.5
TITLE_BLOCK_HEIGHT = 180
TITLE_BLOCK_WIDTH = 594  # A4 landscape
DRAWING_BORDER = True

# Directory paths

LAYOUT_DATA_DIR = "layout_data"
SYMBOLS_DIR = "symbols"
TEMPLATES_DIR = "templates"

# Initialize OpenAI and database

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ENHANCED ISA SYMBOLS (keeping existing + adding new ones) ---

ISA_SYMBOLS = {
    # [Previous symbols remain the same…]
    'pump': '''<symbol id="pump" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
    <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="2"/>
    <path d="M 30,5 L 30,55 M 5,30 L 55,30" stroke="black" stroke-width="2"/>
    </symbol>''',


    'pump_centrifugal': '''<symbol id="pump_centrifugal" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
        <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 30,5 L 30,55 M 5,30 L 55,30" stroke="black" stroke-width="2"/>
    </symbol>''',

    'valve': '''<symbol id="valve" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,15 L 5,25 L 35,25 L 35,15 Z" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 20,15 L 20,5" stroke="black" stroke-width="2"/>
    </symbol>''',

    'valve_gate': '''<symbol id="valve_gate" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,15 L 5,25 L 35,25 L 35,15 Z" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 20,15 L 20,5" stroke="black" stroke-width="2"/>
        <circle cx="20" cy="5" r="2" fill="black"/>
    </symbol>''',

    'valve_globe': '''<symbol id="valve_globe" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <circle cx="20" cy="20" r="10" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 10,10 L 30,30 M 30,10 L 10,30" stroke="black" stroke-width="1.5"/>
    </symbol>''',

    'valve_ball': '''<symbol id="valve_ball" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <circle cx="20" cy="20" r="10" fill="white" stroke="black" stroke-width="2"/>
        <circle cx="20" cy="20" r="5" fill="black"/>
    </symbol>''',

    'valve_check': '''<symbol id="valve_check" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,15 L 5,25 L 20,35 L 35,25 L 35,15 L 20,5 Z" fill="white" stroke="black" stroke-width="2"/>
        <line x1="20" y1="15" x2="20" y2="25" stroke="black" stroke-width="2"/>
    </symbol>''',

    'control_valve': '''<symbol id="control_valve" viewBox="0 0 40 50" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,25 L 5,35 L 35,35 L 35,25 Z" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 20,25 L 20,10" stroke="black" stroke-width="2"/>
        <path d="M 15,10 L 25,10" stroke="black" stroke-width="2"/>
        <circle cx="20" cy="10" r="2" fill="black"/>
    </symbol>''',

    'vessel': '''<symbol id="vessel" viewBox="0 0 60 100" preserveAspectRatio="xMidYMid meet">
        <ellipse cx="30" cy="20" rx="25" ry="15" fill="white" stroke="black" stroke-width="2"/>
        <rect x="5" y="20" width="50" height="60" fill="white" stroke="black" stroke-width="2"/>
        <ellipse cx="30" cy="80" rx="25" ry="15" fill="white" stroke="black" stroke-width="2"/>
        <line x1="5" y1="20" x2="5" y2="80" stroke="black" stroke-width="2"/>
        <line x1="55" y1="20" x2="55" y2="80" stroke="black" stroke-width="2"/>
    </symbol>''',

    'tank': '''<symbol id="tank" viewBox="0 0 80 60" preserveAspectRatio="xMidYMid meet">
        <rect x="5" y="10" width="70" height="40" rx="5" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 5,35 L 75,35" stroke="black" stroke-width="1" stroke-dasharray="3,3" opacity="0.5"/>
    </symbol>''',

    'heat_exchanger': '''<symbol id="heat_exchanger" viewBox="0 0 100 60" preserveAspectRatio="xMidYMid meet">
        <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="2"/>
        <rect x="30" y="5" width="60" height="50" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 40,15 L 80,15 M 40,25 L 80,25 M 40,35 L 80,35 M 40,45 L 80,45" stroke="black" stroke-width="1"/>
    </symbol>''',

    'filter': '''<symbol id="filter" viewBox="0 0 40 60" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,10 L 35,10 L 25,40 L 15,40 Z" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 10,20 L 30,20 M 12,25 L 28,25 M 14,30 L 26,30" stroke="black" stroke-width="1"/>
    </symbol>''',

    'compressor': '''<symbol id="compressor" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
        <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 15,15 L 30,30 L 15,45" stroke="black" stroke-width="2" fill="none"/>
        <path d="M 30,30 L 45,15 M 30,30 L 45,45" stroke="black" stroke-width="2"/>
    </symbol>''',

    # New safety symbols
    'psv': '''<symbol id="psv" viewBox="0 0 40 60" preserveAspectRatio="xMidYMid meet">
        <path d="M 5,40 L 5,50 L 35,50 L 35,40 Z" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 20,40 L 20,20 L 10,10 L 30,10 L 20,20" stroke="black" stroke-width="2" fill="white"/>
        <path d="M 20,10 L 20,0" stroke="black" stroke-width="2"/>
    </symbol>''',

    'rupture_disc': '''<symbol id="rupture_disc" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
        <circle cx="20" cy="20" r="15" fill="white" stroke="black" stroke-width="2"/>
        <path d="M 10,10 L 30,30 M 30,10 L 10,30" stroke="black" stroke-width="1"/>
    </symbol>''',

}

# Helper functions (keeping your existing ones)

def normalize(s):
    if not isinstance(s, str):
        return ""
    return s.lower().strip().replace(" ", "*").replace("-", "*")

def clean_component_id(s):
    if not isinstance(s, str):
        return ""
    return s.strip()

def parse_instrument_tag(tag):
    if not tag:
        return None

    patterns = [
        r'^([A-Z]{2,4})-?(\d{3,4})$',
        r'^([A-Z]{2,4})(\d{3,4})$',
    ]

    for pattern in patterns:
        match = re.match(pattern, str(tag))
        if match:
            letters = match.group(1)
            number = match.group(2)

            location = 'field'
            if letters.startswith('L'):
                location = 'local'
                letters = letters[1:]

            return {
                'letters': letters,
                'number': number,
                'location': location,
                'full_tag': tag,
                'is_instrument': True
            }

    return None

def create_instrument_bubble(tag, x, y, size=None):
    if size is None:
        size = INSTRUMENT_BUBBLE_SIZE

    tag_info = parse_instrument_tag(tag)
    if not tag_info:
        return ""

    svg = f'<g class="instrument-bubble">'

    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="1.5"/>'

    if tag_info['location'] == 'field':
        svg += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" stroke="black" stroke-width="1.5"/>'

    text_size = TAG_FONT_SIZE * 0.8
    svg += f'<text x="{x}" y="{y-3}" text-anchor="middle" font-size="{text_size}" font-family="Arial, sans-serif" font-weight="bold">{tag_info["letters"]}</text>'
    svg += f'<text x="{x}" y="{y+8}" text-anchor="middle" font-size="{text_size*0.9}" font-family="Arial, sans-serif">{tag_info["number"]}</text>'

    svg += '</g>'
    return svg

# Enhanced P&ID Component Class

class PnidComponent:
    def __init__(self, row):
        self.id = clean_component_id(row['id'])
        self.tag = row.get('tag', self.id)
        self.component_type = normalize(row.get('Component', 'valve'))
        self.x = float(row.get('x', 0))
        self.y = float(row.get('y', 0))
        self.rotation = float(row.get('rotation', 0))

        self.tag_info = parse_instrument_tag(self.tag)
        self.is_instrument = bool(self.tag_info)

        if self.is_instrument:
            self.width = INSTRUMENT_BUBBLE_SIZE * 2 * SYMBOL_SCALE
            self.height = INSTRUMENT_BUBBLE_SIZE * 2 * SYMBOL_SCALE
        else:
            self.symbol_id = self._get_symbol_id()

            if self.symbol_id in ISA_SYMBOLS:
                symbol = ISA_SYMBOLS[self.symbol_id]
                viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', symbol)
                if viewbox_match:
                    base_width = float(viewbox_match.group(1))
                    base_height = float(viewbox_match.group(2))
                else:
                    base_width, base_height = 40, 40
            else:
                base_width = float(row.get('Width', 40))
                base_height = float(row.get('Height', 40))

            self.width = base_width * SYMBOL_SCALE
            self.height = base_height * SYMBOL_SCALE

        self.ports = self._define_ports()

    def _get_symbol_id(self):
        if self.component_type in ISA_SYMBOLS:
            return self.component_type

        mappings = {
            'pump': 'pump_centrifugal',
            'centrifugal_pump': 'pump_centrifugal',
            'gate_valve': 'valve_gate',
            'globe_valve': 'valve_globe',
            'ball_valve': 'valve_ball',
            'check_valve': 'valve_check',
            'pressure_safety_valve': 'psv',
            'relief_valve': 'psv',
            'vessel_vertical': 'vessel',
            'vessel_horizontal': 'vessel',
            'storage_tank': 'tank',
            'heat_exchanger': 'heat_exchanger',
            'cooler': 'heat_exchanger',
            'heater': 'heat_exchanger',
        }

        return mappings.get(self.component_type, 'valve')

    def _define_ports(self):
        if self.is_instrument:
            return {
                'center': {'dx': self.width/2, 'dy': self.height/2},
                'top': {'dx': self.width/2, 'dy': 0},
                'bottom': {'dx': self.width/2, 'dy': self.height},
                'left': {'dx': 0, 'dy': self.height/2},
                'right': {'dx': self.width, 'dy': self.height/2},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }

        if self.symbol_id in ['valve', 'valve_gate', 'valve_globe', 'valve_ball', 'valve_check']:
            return {
                'inlet': {'dx': 0, 'dy': self.height/2},
                'outlet': {'dx': self.width, 'dy': self.height/2},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        elif self.symbol_id in ['pump', 'pump_centrifugal']:
            return {
                'suction': {'dx': 0, 'dy': self.height/2},
                'discharge': {'dx': self.width/2, 'dy': 0},
                'inlet': {'dx': 0, 'dy': self.height/2},
                'outlet': {'dx': self.width/2, 'dy': 0},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        elif self.symbol_id == 'vessel':
            return {
                'top': {'dx': self.width/2, 'dy': 0},
                'bottom': {'dx': self.width/2, 'dy': self.height},
                'side_top': {'dx': self.width, 'dy': self.height * 0.3},
                'side_bottom': {'dx': self.width, 'dy': self.height * 0.7},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        else:
            return {
                'center': {'dx': self.width/2, 'dy': self.height/2},
                'inlet': {'dx': 0, 'dy': self.height/2},
                'outlet': {'dx': self.width, 'dy': self.height/2},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }

    def get_port_coords(self, port_name):
        port = self.ports.get(port_name) or self.ports.get('default') or self.ports.get('center')
        if port:
            return (self.x + port['dx'], self.y + port['dy'])
        return (self.x + self.width/2, self.y + self.height/2)

# Enhanced Pipe Class with Smart Routing

class PnidPipe:
    def __init__(self, row, component_map, router=None):
        self.id = row.get('Pipe No.', '')
        self.label = row.get('Label', f"Line {self.id}")
        self.line_type = row.get('pipe_type', 'process')

        type_mapping = {
            'process_line': 'process',
            'instrumentation': 'instrumentation',
            'instrument_signal': 'instrumentation',
            'electrical': 'electrical',
            'pneumatic': 'pneumatic',
            'hydraulic': 'hydraulic'
        }
        self.line_type = type_mapping.get(self.line_type, self.line_type)

        from_comp_id = clean_component_id(row.get('From Component', ''))
        to_comp_id = clean_component_id(row.get('To Component', ''))

        self.from_comp = component_map.get(from_comp_id)
        self.to_comp = component_map.get(to_comp_id)

        self.from_port = row.get('From Port', 'default')
        self.to_port = row.get('To Port', 'default')

        # Use smart routing if enabled and router provided
        if enable_smart_routing and router and self.from_comp and self.to_comp:
            start = self.from_comp.get_port_coords(self.from_port)
            end = self.to_comp.get_port_coords(self.to_port)
            self.points = router.find_path(start, end)
        else:
            self.points = self._parse_points(row)

        self.with_arrow = self.line_type in ['process', 'process_thick']

    def _parse_points(self, row):
        points = []

        polyline_str = str(row.get('Polyline Points (x, y)', '')).strip()
        if polyline_str and polyline_str.lower() != 'nan':
            pts = re.findall(r"\(([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\)", polyline_str)
            if pts:
                points = [(float(x), float(y)) for x, y in pts]

        if not points and self.from_comp and self.to_comp:
            start = self.from_comp.get_port_coords(self.from_port)
            end = self.to_comp.get_port_coords(self.to_port)
            points = self._calculate_orthogonal_path(start, end)

        return points

    def _calculate_orthogonal_path(self, start, end):
        points = [start]

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        if abs(dx) > abs(dy):
            mid_x = start[0] + dx / 2
            points.append((mid_x, start[1]))
            points.append((mid_x, end[1]))
        else:
            mid_y = start[1] + dy / 2
            points.append((start[0], mid_y))
            points.append((end[0], mid_y))

        points.append(end)
        return points

# Main rendering function with advanced features

def render_professional_svg(components, pipes, router=None):
    if components:
        max_x = max(c.x + c.width for c in components.values()) + PADDING
        max_y = max(c.y + c.height for c in components.values()) + PADDING
    else:
        max_x, max_y = 1200, 800

    drawing_width = max(max_x, 1200)
    drawing_height = max(max_y + TITLE_BLOCK_HEIGHT, 800)

    svg_parts = [f'''<svg width="{drawing_width}" height="{drawing_height}"
                     viewBox="0 0 {drawing_width} {drawing_height}"
                     xmlns="http://www.w3.org/2000/svg"
                     style="font-family: Arial, sans-serif; background-color: white;">''']

    # Add definitions
    svg_parts.append('<defs>')
    svg_parts.append('''
        <marker id="arrow-process" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
            <polygon points="0,0 10,5 0,10" fill="black"/>
        </marker>
        <marker id="arrow-thick" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
            <polygon points="0,0 12,6 0,12" fill="black"/>
        </marker>
    ''')

    for symbol_id, symbol_def in ISA_SYMBOLS.items():
        svg_parts.append(symbol_def)

    svg_parts.append('</defs>')

    # Drawing border
    if DRAWING_BORDER:
        svg_parts.append(f'''<rect x="5" y="5" width="{drawing_width-10}" height="{drawing_height-10}"
                            fill="none" stroke="black" stroke-width="{BORDER_WIDTH}"/>''')

    # Grid
    svg_parts.append('<g class="grid" opacity="0.2">')
    for x in range(0, int(drawing_width), GRID_SPACING):
        svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{drawing_height}" stroke="#cccccc" stroke-width="0.5"/>')
    for y in range(0, int(drawing_height), GRID_SPACING):
        svg_parts.append(f'<line x1="0" y1="{y}" x2="{drawing_width}" y2="{y}" stroke="#cccccc" stroke-width="0.5"/>')
    svg_parts.append('</g>')

    # Render pipes
    svg_parts.append('<g class="pipes">')
    for pipe in pipes:
        if len(pipe.points) >= 2:
            line_style = LINE_STANDARDS.get(pipe.line_type, LINE_STANDARDS['process'])

            path_d = f"M {pipe.points[0][0]},{pipe.points[0][1]}"
            for point in pipe.points[1:]:
                path_d += f" L {point[0]},{point[1]}"

            stroke_props = f'stroke="{line_style["color"]}" stroke-width="{line_style["width"] * PIPE_WIDTH/2}"'
            if line_style.get('dash'):
                stroke_props += f' stroke-dasharray="{line_style["dash"]}"'

            marker = ''
            if pipe.with_arrow:
                marker = f'marker-end="url(#arrow-{"thick" if line_style["width"] > 2 else "process"})"'

            svg_parts.append(f'<path d="{path_d}" fill="none" {stroke_props} {marker}/>')

            if pipe.label and len(pipe.points) >= 2:
                mid_idx = len(pipe.points) // 2
                label_x = (pipe.points[mid_idx-1][0] + pipe.points[mid_idx][0]) / 2
                label_y = (pipe.points[mid_idx-1][1] + pipe.points[mid_idx][1]) / 2 - 5

                svg_parts.append(f'''<text x="{label_x}" y="{label_y}" text-anchor="middle"
                                    font-size="{PIPE_LABEL_FONT_SIZE}" fill="black">{pipe.label}</text>''')
    svg_parts.append('</g>')

    # Render components
    svg_parts.append('<g class="components">')
    for comp in components.values():
        if comp.is_instrument:
            svg_parts.append(create_instrument_bubble(comp.tag, comp.x + comp.width/2, comp.y + comp.height/2))
        else:
            transform = f'translate({comp.x},{comp.y})'
            if comp.rotation:
                cx = comp.width / 2
                cy = comp.height / 2
                transform += f' rotate({comp.rotation},{cx},{cy})'

            svg_parts.append(f'''<use href="#{comp.symbol_id}" transform="{transform}"
                                width="{comp.width}" height="{comp.height}"/>''')

            if comp.tag and not comp.is_instrument:
                tag_y = comp.y + comp.height + TAG_FONT_SIZE + 2
                svg_parts.append(f'''<text x="{comp.x + comp.width/2}" y="{tag_y}"
                                    text-anchor="middle" font-size="{TAG_FONT_SIZE}"
                                    font-weight="bold" fill="black">{comp.tag}</text>''')
    svg_parts.append('</g>')

    # Add control loops overlay if enabled
    if show_control_loops:
        analyzer = ControlSystemAnalyzer(components, pipes)
        svg_parts.append(render_control_loop_overlay(analyzer.control_loops, components))

    # Add validation overlay if enabled
    if enable_validation:
        validator = PnIDValidator(components, pipes)
        validation_results = validator.validate_all()
        if validation_results['errors'] or validation_results['warnings']:
            svg_parts.append(render_validation_overlay(validation_results, components))

    # Title block
    svg_parts.append(render_title_block(drawing_width, drawing_height))

    svg_parts.append('</svg>')
    return ''.join(svg_parts)

def render_title_block(width, height):
    tb_x = width - TITLE_BLOCK_WIDTH - 20
    tb_y = height - TITLE_BLOCK_HEIGHT - 20

    project_info = st.session_state.get('project_info', {
        'client': 'EPS Pvt. Ltd.',
        'project': 'P&ID Automation Project',
        'drawing_no': 'EPS-PID-001',
        'drawn_by': 'Engineer',
        'checked_by': 'Manager',
        'approved_by': 'Director',
        'revision': '0'
    })

    svg = f'<g class="title-block" transform="translate({tb_x},{tb_y})">'

    svg += f'<rect x="0" y="0" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT}" fill="white" stroke="black" stroke-width="{BORDER_WIDTH}"/>'

    divisions = [30, 60, 90, 120]
    for y in divisions:
        svg += f'<line x1="0" y1="{y}" x2="{TITLE_BLOCK_WIDTH}" y2="{y}" stroke="black" stroke-width="{BORDER_WIDTH*0.5}"/>'

    svg += f'<line x1="250" y1="0" x2="250" y2="120" stroke="black" stroke-width="{BORDER_WIDTH*0.5}"/>'

    svg += f'<text x="10" y="20" font-size="14" font-weight="bold">{project_info.get("client", "CLIENT")}</text>'
    svg += f'<text x="10" y="45" font-size="11">{project_info.get("project", "Project")}</text>'
    svg += f'<text x="10" y="75" font-size="10">DWG NO: {project_info.get("drawing_no", "XXX-XXX-XXX")}</text>'
    svg += f'<text x="10" y="105" font-size="10">DATE: {datetime.datetime.now().strftime("%Y-%m-%d")}</text>'
    svg += f'<text x="260" y="20" font-size="10">DRAWN: {project_info.get("drawn_by", "")}</text>'
    svg += f'<text x="260" y="50" font-size="10">CHECKED: {project_info.get("checked_by", "")}</text>'
    svg += f'<text x="260" y="80" font-size="10">APPROVED: {project_info.get("approved_by", "")}</text>'
    svg += f'<text x="260" y="110" font-size="10">REV: {project_info.get("revision", "0")}</text>'

    svg += f'<text x="{TITLE_BLOCK_WIDTH/2}" y="{TITLE_BLOCK_HEIGHT+20}" text-anchor="middle" font-size="16" font-weight="bold">PIPING AND INSTRUMENTATION DIAGRAM</text>'

    svg += '</g>'
    return svg

# --- MAIN APPLICATION ---

# Create tabs for different functionalities

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 P&ID Editor",
    "🔧 Control Systems",
    "📋 Templates",
    "✅ Validation",
    "📁 Data Management"
])

# Load data

if 'eq_df' not in st.session_state:
    @st.cache_data(show_spinner="Loading layout data…")
    def initial_load_layout_data():
        eq_file_path = os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv")
        pipe_file_path = os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv")

        if not os.path.exists(eq_file_path):
            st.error(f"Error: {eq_file_path} not found.")
            return pd.DataFrame(), pd.DataFrame(), []

        eq_df = pd.read_csv(eq_file_path)
        pipe_df = pd.read_csv(pipe_file_path, dtype={'Polyline Points (x, y)': str})

        if 'id' in eq_df.columns:
            eq_df['id'] = eq_df['id'].apply(clean_component_id)
        if 'From Component' in pipe_df.columns:
            pipe_df['From Component'] = pipe_df['From Component'].apply(clean_component_id)
        if 'To Component' in pipe_df.columns:
            pipe_df['To Component'] = pipe_df['To Component'].apply(clean_component_id)

        return eq_df, pipe_df, []

    st.session_state.eq_df, st.session_state.pipe_df, _ = initial_load_layout_data()

# Create components and pipes with smart routing

components = {c.id: c for c in [PnidComponent(row) for _, row in st.session_state.eq_df.iterrows()]}

# Initialize router if smart routing is enabled

router = None
if enable_smart_routing:
    router = PipeRouter()
    # Add component obstacles
    for comp in components.values():
        router.add_component_obstacle(comp.x, comp.y, comp.width, comp.height)

pipes = [PnidPipe(row, components, router) for _, row in st.session_state.pipe_df.iterrows()]

# Tab 1: P&ID Editor

with tab1:
    st.markdown("## Professional P&ID Editor")

    # Main P&ID display
    svg_output = render_professional_svg(components, pipes, router)
    st.components.v1.html(svg_output, height=800, scrolling=True)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Components", len(components))
    with col2:
        st.metric("Pipes", len(pipes))
    with col3:
        analyzer = ControlSystemAnalyzer(components, pipes)
        st.metric("Control Loops", len(analyzer.control_loops))
    with col4:
        validator = PnIDValidator(components, pipes)
        validation = validator.validate_all()
        st.metric("Validation Status", "✅ Pass" if validation['is_valid'] else "❌ Fail")

# Tab 2: Control Systems

with tab2:
    st.markdown("## Control Systems Analysis")

    analyzer = ControlSystemAnalyzer(components, pipes)

    if analyzer.control_loops:
        st.markdown("### Detected Control Loops")
        for loop in analyzer.control_loops:
            with st.expander(f"🔄 {loop.loop_type.value} - {loop.loop_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Primary Element:** {loop.primary_element}")
                    st.write(f"**Controller:** {loop.controller}")
                    st.write(f"**Final Element:** {loop.final_element}")
                with col2:
                    st.write(f"**Loop Type:** {loop.loop_type.value}")
                    st.write(f"**Components:** {', '.join(loop.components)}")
    else:
        st.info("No control loops detected in the current P&ID")

    if analyzer.interlocks:
        st.markdown("### Safety Interlocks")
        for interlock in analyzer.interlocks:
            st.write(f"⚡ {interlock['alarm']} → {interlock['action']} ({interlock['type']})")

# Tab 3: Templates

with tab3:
    st.markdown("## Process Unit Templates")

    col1, col2 = st.columns([1, 2])

    with col1:
        template_type = st.selectbox(
            "Select Template",
            ["Distillation Column", "Pump Station", "Heat Exchanger Train",
             "Compressor Station", "Tank Farm", "Reactor System"]
        )

        x_pos = st.number_input("X Position", 100, 2000, 500, 50)
        y_pos = st.number_input("Y Position", 100, 2000, 300, 50)
        tag_prefix = st.text_input("Tag Prefix", "T")

        if st.button("Add Template to P&ID"):
            if template_type == "Distillation Column":
                new_components, new_pipes = ProcessUnitTemplate.distillation_column(x_pos, y_pos, tag_prefix)
            elif template_type == "Pump Station":
                new_components, new_pipes = ProcessUnitTemplate.pump_station(x_pos, y_pos, tag_prefix, redundant=True)

            # Add components to dataframe
            for comp_data in new_components:
                new_row = pd.DataFrame([{
                    'id': comp_data['id'],
                    'tag': comp_data['tag'],
                    'Component': comp_data['type'],
                    'x': comp_data['x'],
                    'y': comp_data['y'],
                    'Width': comp_data.get('width', 60),
                    'Height': comp_data.get('height', 60),
                    'rotation': 0
                }])
                st.session_state.eq_df = pd.concat([st.session_state.eq_df, new_row], ignore_index=True)

            st.success(f"Added {template_type} template")
            st.rerun()

    with col2:
        st.markdown("### Template Preview")
        st.info("Templates include pre-configured equipment arrangements with standard instrumentation and piping")

        # Show template diagram preview here

# Tab 4: Validation

with tab4:
    st.markdown("## P&ID Validation Report")

    validator = PnIDValidator(components, pipes)
    validation_results = validator.validate_all()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ❌ Errors")
        if validation_results['errors']:
            for error in validation_results['errors']:
                st.markdown(f'<div class="validation-error">{error}</div>', unsafe_allow_html=True)
        else:
            st.success("No errors found")

    with col2:
        st.markdown("### ⚠️ Warnings")
        if validation_results['warnings']:
            for warning in validation_results['warnings']:
                st.markdown(f'<div class="validation-warning">{warning}</div>', unsafe_allow_html=True)
        else:
            st.success("No warnings found")

    # Validation summary
    st.markdown("### Validation Summary")
    st.write(f"- **Instrument Tags:** {len([c for c in components.values() if c.is_instrument])} instruments found")
    st.write(f"- **Control Loops:** {len(analyzer.control_loops)} loops detected")
    st.write(f"- **Line Sizing:** Validated {len(pipes)} pipe connections")
    st.write(f"- **Safety Systems:** Checked pressure relief and interlock systems")

# Tab 5: Data Management

with tab5:
    st.markdown("## Data Management")

    # Export options
    st.markdown("### Export Options")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button("📥 Download SVG", svg_output, "professional_pnid.svg", "image/svg+xml")

    with col2:
        if st.button("Generate PNG"):
            png_data = svg2png(bytestring=svg_output.encode('utf-8'), output_width=2000)
            st.download_button("📥 Download PNG", png_data, "professional_pnid.png", "image/png")

    with col3:
        if st.button("Generate Report"):
            report = f"""
# P&ID VALIDATION REPORT

Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- Total Components: {len(components)}
- Total Pipes: {len(pipes)}
- Control Loops: {len(analyzer.control_loops)}
- Validation Status: {'PASSED' if validation_results['is_valid'] else 'FAILED'}

## Errors

{chr(10).join(validation_results['errors']) if validation_results['errors'] else 'No errors found'}

## Warnings

{chr(10).join(validation_results['warnings']) if validation_results['warnings'] else 'No warnings found'}

## Control Loops

{chr(10).join([f"- {loop.loop_id}: {loop.loop_type.value}" for loop in analyzer.control_loops])}
"""
            st.download_button("📥 Download Report", report, "pnid_report.txt", "text/plain")

    with col4:
        if st.button("Save to Database"):
            st.info("Database save functionality would be implemented here")

    # Data tables
    with st.expander("Component Data"):
        st.dataframe(st.session_state.eq_df)

    with st.expander("Pipe Data"):
        st.dataframe(st.session_state.pipe_df)

# Sidebar component addition (enhanced)

st.sidebar.markdown("---")
st.sidebar.markdown("### ➕ Add Component")

symbol_types = list(ISA_SYMBOLS.keys()) + ['instrument']

with st.sidebar.form("add_component_form"):
    new_comp_id = st.text_input("Component ID", key="new_comp_id")
    new_comp_tag = st.text_input("Tag (e.g., P-001, FT-101)", key="new_comp_tag")
    new_comp_type = st.selectbox("Type", options=symbol_types, key="new_comp_type")

    col1, col2 = st.columns(2)
    with col1:
        new_comp_x = st.number_input("X", 0, 2000, 100, 25)
    with col2:
        new_comp_y = st.number_input("Y", 0, 2000, 100, 25)

    new_comp_rotation = st.slider("Rotation", 0, 360, 0, 45)

    if st.form_submit_button("Add Component"):
        if not new_comp_id:
            st.error("Component ID required")
        elif new_comp_id in st.session_state.eq_df['id'].values:
            st.error(f"ID '{new_comp_id}' already exists")
        else:
            new_row = {
                'id': new_comp_id.strip(),
                'tag': new_comp_tag or new_comp_id,
                'Component': new_comp_type,
                'x': new_comp_x,
                'y': new_comp_y,
                'Width': 60,
                'Height': 60,
                'rotation': new_comp_rotation
            }
            st.session_state.eq_df = pd.concat([st.session_state.eq_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Added {new_comp_type}: {new_comp_tag}")
            st.rerun()
