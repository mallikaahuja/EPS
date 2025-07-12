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

# — CONFIGURATION —

st.set_page_config(layout=“wide”, page_title=“Professional P&ID Generator”)
st.sidebar.title(“Professional P&ID Generator”)

# Professional P&ID Standards

st.sidebar.markdown(”### P&ID Standards & Controls”)
LINE_STANDARDS = {
‘process’: {‘width’: 2, ‘color’: ‘black’, ‘style’: ‘solid’},
‘instrument_signal’: {‘width’: 0.5, ‘color’: ‘black’, ‘style’: ‘dashed’, ‘dash’: ‘3,3’},
‘electrical’: {‘width’: 0.5, ‘color’: ‘black’, ‘style’: ‘dashed’, ‘dash’: ‘1,1’},
‘pneumatic’: {‘width’: 0.5, ‘color’: ‘black’, ‘style’: ‘solid’},
‘hydraulic’: {‘width’: 1, ‘color’: ‘black’, ‘style’: ‘solid’},
‘software’: {‘width’: 0.5, ‘color’: ‘black’, ‘style’: ‘dotted’}
}

# Enhanced visual controls

GRID_SPACING = st.sidebar.slider(“Grid Spacing (mm)”, 10, 50, 25, 5)
SYMBOL_SCALE = st.sidebar.slider(“Symbol Scale”, 0.5, 2.0, 1.0, 0.1)
TEXT_HEIGHT = st.sidebar.slider(“Text Height (mm)”, 2.5, 5.0, 3.5, 0.5)
INSTRUMENT_BUBBLE_SIZE = st.sidebar.slider(“Instrument Bubble Size”, 15, 30, 20)

# Global constants for professional drawings

PADDING = 50
BORDER_WIDTH = 0.7
TITLE_BLOCK_HEIGHT = 180
TITLE_BLOCK_WIDTH = 594  # A4 width in landscape
DRAWING_SCALE = “1:1”

# Initialize OpenAI

openai_client = openai.OpenAI(api_key=os.getenv(“OPENAI_API_KEY”))
DATABASE_URL = os.getenv(“DATABASE_URL”)

# — ISA SYMBOL DEFINITIONS —

# Professional ISA symbols as SVG definitions

ISA_SYMBOLS = {
‘pump_centrifugal’: ‘’’<symbol id="pump_centrifugal" viewBox="0 0 50 50">
<circle cx="25" cy="25" r="20" fill="none" stroke="black" stroke-width="1.5"/>
<path d="M 25,5 L 25,45" stroke="black" stroke-width="1.5"/>
<path d="M 5,25 L 45,25" stroke="black" stroke-width="1.5"/>
</symbol>’’’,

```
'valve_gate': '''<symbol id="valve_gate" viewBox="0 0 40 40">
    <path d="M 10,10 L 10,30 L 30,30 L 30,10 Z" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 20,10 L 20,0" stroke="black" stroke-width="1.5"/>
    <path d="M 0,20 L 10,20 M 30,20 L 40,20" stroke="black" stroke-width="2"/>
</symbol>''',

'valve_globe': '''<symbol id="valve_globe" viewBox="0 0 40 40">
    <circle cx="20" cy="20" r="10" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 10,10 L 30,30 M 30,10 L 10,30" stroke="black" stroke-width="1.5"/>
    <path d="M 0,20 L 10,20 M 30,20 L 40,20" stroke="black" stroke-width="2"/>
</symbol>''',

'valve_ball': '''<symbol id="valve_ball" viewBox="0 0 40 40">
    <circle cx="20" cy="20" r="10" fill="white" stroke="black" stroke-width="1.5"/>
    <circle cx="20" cy="20" r="5" fill="black"/>
    <path d="M 0,20 L 10,20 M 30,20 L 40,20" stroke="black" stroke-width="2"/>
</symbol>''',

'valve_butterfly': '''<symbol id="valve_butterfly" viewBox="0 0 40 40">
    <circle cx="20" cy="20" r="10" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 20,10 L 20,30" stroke="black" stroke-width="3"/>
    <path d="M 0,20 L 10,20 M 30,20 L 40,20" stroke="black" stroke-width="2"/>
</symbol>''',

'valve_check': '''<symbol id="valve_check" viewBox="0 0 40 40">
    <path d="M 10,10 L 10,30 L 30,20 L 30,10 Z" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 20,15 L 20,25" stroke="black" stroke-width="1.5"/>
    <path d="M 0,20 L 10,20 M 30,20 L 40,20" stroke="black" stroke-width="2"/>
</symbol>''',

'vessel_vertical': '''<symbol id="vessel_vertical" viewBox="0 0 60 100">
    <ellipse cx="30" cy="20" rx="25" ry="15" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="5" y="20" width="50" height="60" fill="white" stroke="black" stroke-width="1.5"/>
    <ellipse cx="30" cy="80" rx="25" ry="15" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 5,20 L 5,80" stroke="black" stroke-width="1.5"/>
    <path d="M 55,20 L 55,80" stroke="black" stroke-width="1.5"/>
</symbol>''',

'heat_exchanger': '''<symbol id="heat_exchanger" viewBox="0 0 80 60">
    <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="30" y="5" width="40" height="50" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 40,15 L 60,15 L 60,45 L 40,45" stroke="black" stroke-width="1" fill="none"/>
    <path d="M 0,30 L 5,30" stroke="black" stroke-width="2"/>
    <path d="M 70,30 L 80,30" stroke="black" stroke-width="2"/>
    <path d="M 50,0 L 50,5" stroke="black" stroke-width="2"/>
    <path d="M 50,55 L 50,60" stroke="black" stroke-width="2"/>
</symbol>''',

'filter': '''<symbol id="filter" viewBox="0 0 40 60">
    <path d="M 5,10 L 35,10 L 25,40 L 15,40 Z" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 20,0 L 20,10" stroke="black" stroke-width="2"/>
    <path d="M 20,40 L 20,60" stroke="black" stroke-width="2"/>
    <path d="M 10,20 L 30,20" stroke="black" stroke-width="0.5"/>
    <path d="M 12,25 L 28,25" stroke="black" stroke-width="0.5"/>
    <path d="M 14,30 L 26,30" stroke="black" stroke-width="0.5"/>
</symbol>''',

'tank': '''<symbol id="tank" viewBox="0 0 80 60">
    <rect x="10" y="10" width="60" height="40" rx="5" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 10,35 L 70,35" stroke="black" stroke-width="0.5" stroke-dasharray="3,3"/>
</symbol>''',

'compressor': '''<symbol id="compressor" viewBox="0 0 60 60">
    <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 15,15 L 30,30 L 15,45" stroke="black" stroke-width="2" fill="none"/>
    <path d="M 30,30 L 45,15" stroke="black" stroke-width="2"/>
    <path d="M 30,30 L 45,45" stroke="black" stroke-width="2"/>
    <path d="M 0,30 L 5,30" stroke="black" stroke-width="2"/>
    <path d="M 55,30 L 60,30" stroke="black" stroke-width="2"/>
</symbol>''',

'control_valve': '''<symbol id="control_valve" viewBox="0 0 40 60">
    <path d="M 10,30 L 10,50 L 30,50 L 30,30 Z" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 20,30 L 20,10" stroke="black" stroke-width="1.5"/>
    <path d="M 15,10 L 25,10" stroke="black" stroke-width="1.5"/>
    <path d="M 0,40 L 10,40 M 30,40 L 40,40" stroke="black" stroke-width="2"/>
    <circle cx="20" cy="10" r="2" fill="black"/>
</symbol>'''
```

}

# — INSTRUMENT BUBBLE FUNCTION —

def create_instrument_bubble(tag, x, y, size=20):
“”“Creates an ISA standard instrument bubble with tag”””
tag_parts = parse_instrument_tag(tag)

```
svg = f'<g transform="translate({x},{y})">'
svg += f'<circle cx="0" cy="0" r="{size}" fill="white" stroke="black" stroke-width="1.5"/>'

# Add horizontal line if field mounted
if tag_parts.get('location') == 'field':
    svg += f'<line x1="{-size}" y1="0" x2="{size}" y2="0" stroke="black" stroke-width="1.5"/>'

# Add tag text
svg += f'<text x="0" y="-5" text-anchor="middle" font-size="{TEXT_HEIGHT * 3}" font-family="Arial">{tag_parts["letters"]}</text>'
svg += f'<text x="0" y="7" text-anchor="middle" font-size="{TEXT_HEIGHT * 2.5}" font-family="Arial">{tag_parts["number"]}</text>'

svg += '</g>'
return svg
```

def parse_instrument_tag(tag):
“”“Parses ISA instrument tag (e.g., FT-101, PIC-102)”””
match = re.match(r’^([A-Z]+)-?(\d+)$’, tag)
if match:
letters = match.group(1)
number = match.group(2)

```
    # Determine if local (L prefix) or field mounted
    location = 'field' if not letters.startswith('L') else 'local'
    
    return {
        'letters': letters,
        'number': number,
        'location': location,
        'function': get_instrument_function(letters)
    }
return {'letters': tag, 'number': '', 'location': 'field', 'function': 'unknown'}
```

def get_instrument_function(letters):
“”“Determines instrument function from ISA letter code”””
first_letter_meaning = {
‘F’: ‘Flow’, ‘L’: ‘Level’, ‘P’: ‘Pressure’, ‘T’: ‘Temperature’,
‘A’: ‘Analysis’, ‘E’: ‘Voltage’, ‘I’: ‘Current’, ‘S’: ‘Speed’
}

```
modifier_letters = {
    'I': 'Indicator', 'C': 'Controller', 'T': 'Transmitter', 
    'V': 'Valve', 'E': 'Element', 'R': 'Recorder', 'A': 'Alarm'
}

# Parse the tag
if len(letters) >= 2:
    variable = first_letter_meaning.get(letters[0], 'Unknown')
    function = modifier_letters.get(letters[-1], 'Unknown')
    return f"{variable} {function}"
return "Unknown"
```

# — ENHANCED LINE DRAWING —

def draw_process_line(points, line_type=‘process’, with_arrow=True):
“”“Draws a process line with proper P&ID conventions”””
if len(points) < 2:
return “”

```
line_def = LINE_STANDARDS.get(line_type, LINE_STANDARDS['process'])

svg = '<g>'

# Create path
path_d = f"M {points[0][0]},{points[0][1]}"
for point in points[1:]:
    path_d += f" L {point[0]},{point[1]}"

stroke_dasharray = f'stroke-dasharray="{line_def.get("dash", "")}"' if line_def.get("dash") else ""

svg += f'<path d="{path_d}" stroke="{line_def["color"]}" stroke-width="{line_def["width"]}" fill="none" {stroke_dasharray}/>'

# Add flow arrow if needed
if with_arrow and len(points) >= 2:
    # Calculate arrow position and angle
    last_segment = (points[-2], points[-1])
    angle = math.atan2(last_segment[1][1] - last_segment[0][1], 
                      last_segment[1][0] - last_segment[0][0])
    angle_deg = math.degrees(angle)
    
    arrow_x = points[-1][0] - 10 * math.cos(angle)
    arrow_y = points[-1][1] - 10 * math.sin(angle)
    
    svg += f'<g transform="translate({arrow_x},{arrow_y}) rotate({angle_deg})">'
    svg += '<polygon points="0,-4 8,0 0,4" fill="black"/>'
    svg += '</g>'

svg += '</g>'
return svg
```

# — TITLE BLOCK GENERATION —

def create_title_block(width, height, project_info):
“”“Creates a professional title block”””
tb_x = width - TITLE_BLOCK_WIDTH - PADDING
tb_y = height - TITLE_BLOCK_HEIGHT - PADDING

```
svg = f'<g transform="translate({tb_x},{tb_y})">'

# Main border
svg += f'<rect x="0" y="0" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT}" fill="white" stroke="black" stroke-width="{BORDER_WIDTH}"/>'

# Horizontal divisions
divisions = [40, 80, 120, 140]
for y in divisions:
    svg += f'<line x1="0" y1="{y}" x2="{TITLE_BLOCK_WIDTH}" y2="{y}" stroke="black" stroke-width="{BORDER_WIDTH}"/>'

# Vertical divisions
svg += f'<line x1="400" y1="0" x2="400" y2="140" stroke="black" stroke-width="{BORDER_WIDTH}"/>'

# Add text
svg += f'<text x="10" y="25" font-size="16" font-weight="bold">{project_info.get("client", "CLIENT NAME")}</text>'
svg += f'<text x="10" y="60" font-size="12">{project_info.get("project", "Project Description")}</text>'
svg += f'<text x="10" y="100" font-size="10">Drawing No: {project_info.get("drawing_no", "XXXX-XX-XX")}</text>'
svg += f'<text x="10" y="130" font-size="10">Date: {datetime.datetime.now().strftime("%Y-%m-%d")}</text>'
svg += f'<text x="410" y="25" font-size="12">Scale: {DRAWING_SCALE}</text>'
svg += f'<text x="410" y="60" font-size="10">Drawn: {project_info.get("drawn_by", "Engineer")}</text>'
svg += f'<text x="410" y="95" font-size="10">Checked: {project_info.get("checked_by", "Checker")}</text>'
svg += f'<text x="410" y="130" font-size="10">Rev: {project_info.get("revision", "0")}</text>'

svg += '</g>'
return svg
```

# — P&ID COMPONENT CLASS —

class PnidComponent:
“”“Enhanced P&ID component with ISA standards”””
def **init**(self, row):
self.id = row[‘id’].strip()
self.tag = row.get(‘tag’, self.id)
self.component_type = row.get(‘type’, ‘valve_gate’)  # Use ISA type
self.x = row[‘x’]
self.y = row[‘y’]
self.rotation = row.get(‘rotation’, 0)

```
    # Parse instrument tags
    self.tag_info = parse_instrument_tag(self.tag) if self._is_instrument() else None
    
    # Get symbol dimensions
    if self._is_instrument():
        self.width = INSTRUMENT_BUBBLE_SIZE * 2
        self.height = INSTRUMENT_BUBBLE_SIZE * 2
    else:
        # Get from symbol viewBox
        symbol = ISA_SYMBOLS.get(self.component_type, ISA_SYMBOLS['valve_gate'])
        viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', symbol)
        if viewbox_match:
            self.width = float(viewbox_match.group(1)) * SYMBOL_SCALE
            self.height = float(viewbox_match.group(2)) * SYMBOL_SCALE
        else:
            self.width = 40 * SYMBOL_SCALE
            self.height = 40 * SYMBOL_SCALE
    
    # Define connection points
    self.ports = self._define_ports()

def _is_instrument(self):
    """Check if component is an instrument based on tag"""
    return bool(re.match(r'^[A-Z]{2,4}-?\d{3,4}$', self.tag))

def _define_ports(self):
    """Define standard connection ports based on component type"""
    if self.component_type in ['valve_gate', 'valve_globe', 'valve_ball', 'valve_butterfly', 'valve_check']:
        return {
            'inlet': {'dx': 0, 'dy': self.height/2},
            'outlet': {'dx': self.width, 'dy': self.height/2}
        }
    elif self.component_type == 'pump_centrifugal':
        return {
            'suction': {'dx': 0, 'dy': self.height/2},
            'discharge': {'dx': self.width/2, 'dy': 0}
        }
    elif self.component_type == 'vessel_vertical':
        return {
            'top': {'dx': self.width/2, 'dy': 0},
            'bottom': {'dx': self.width/2, 'dy': self.height},
            'side_top': {'dx': self.width, 'dy': self.height * 0.3},
            'side_bottom': {'dx': self.width, 'dy': self.height * 0.7}
        }
    else:
        # Default ports
        return {
            'center': {'dx': self.width/2, 'dy': self.height/2}
        }

def get_port_coords(self, port_name):
    """Get absolute coordinates for a port"""
    port = self.ports.get(port_name, self.ports.get('center'))
    if port:
        # Apply rotation if needed
        return (self.x + port['dx'], self.y + port['dy'])
    return (self.x + self.width/2, self.y + self.height/2)

def render(self):
    """Render the component as SVG"""
    if self._is_instrument():
        return create_instrument_bubble(self.tag, self.x + self.width/2, self.y + self.height/2, INSTRUMENT_BUBBLE_SIZE)
    else:
        transform = f'translate({self.x},{self.y})'
        if self.rotation:
            transform += f' rotate({self.rotation},{self.width/2},{self.height/2})'
        
        return f'<use href="#{self.component_type}" transform="{transform}" width="{self.width}" height="{self.height}"/>'
```

# — ENHANCED PIPE CLASS —

class PnidPipe:
“”“Enhanced P&ID pipe with line standards”””
def **init**(self, row, component_map):
self.id = row[‘id’]
self.from_comp_id = row[‘from_component’].strip()
self.to_comp_id = row[‘to_component’].strip()
self.from_port = row.get(‘from_port’, ‘outlet’)
self.to_port = row.get(‘to_port’, ‘inlet’)
self.line_type = row.get(‘line_type’, ‘process’)
self.line_number = row.get(‘line_number’, ‘’)
self.with_arrow = row.get(‘with_arrow’, True)

```
    # Get components
    self.from_comp = component_map.get(self.from_comp_id)
    self.to_comp = component_map.get(self.to_comp_id)
    
    # Calculate path
    self.points = self._calculate_path(row.get('waypoints', []))

def _calculate_path(self, waypoints):
    """Calculate pipe path with orthogonal routing"""
    if not self.from_comp or not self.to_comp:
        return []
    
    start = self.from_comp.get_port_coords(self.from_port)
    end = self.to_comp.get_port_coords(self.to_port)
    
    if waypoints:
        # Use provided waypoints
        return [start] + waypoints + [end]
    else:
        # Auto-route with orthogonal lines
        points = [start]
        
        # Simple orthogonal routing
        if abs(start[0] - end[0]) > abs(start[1] - end[1]):
            # Horizontal first
            mid_x = (start[0] + end[0]) / 2
            points.append((mid_x, start[1]))
            points.append((mid_x, end[1]))
        else:
            # Vertical first
            mid_y = (start[1] + end[1]) / 2
            points.append((start[0], mid_y))
            points.append((end[0], mid_y))
        
        points.append(end)
        return points

def render(self):
    """Render the pipe as SVG"""
    if len(self.points) < 2:
        return ""
    
    svg = draw_process_line(self.points, self.line_type, self.with_arrow)
    
    # Add line number if specified
    if self.line_number and len(self.points) >= 2:
        mid_idx = len(self.points) // 2
        mid_x = (self.points[mid_idx-1][0] + self.points[mid_idx][0]) / 2
        mid_y = (self.points[mid_idx-1][1] + self.points[mid_idx][1]) / 2
        
        svg += f'<text x="{mid_x}" y="{mid_y - 5}" text-anchor="middle" font-size="{TEXT_HEIGHT * 2.5}" font-family="Arial">{self.line_number}</text>'
    
    return svg
```

# — MAIN RENDERING FUNCTION —

def render_professional_pnid(components, pipes, project_info):
“”“Render a professional P&ID drawing”””
# Calculate drawing size
max_x = max([c.x + c.width for c in components] + [800])
max_y = max([c.y + c.height for c in components] + [600])

```
width = max_x + PADDING * 2 + 200  # Extra space for annotations
height = max_y + PADDING * 2 + TITLE_BLOCK_HEIGHT

# Start SVG
svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
          xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">'''

# Add definitions
svg += '<defs>'
for symbol_id, symbol_def in ISA_SYMBOLS.items():
    svg += symbol_def
svg += '</defs>'

# Add border
svg += f'<rect x="{PADDING/2}" y="{PADDING/2}" width="{width-PADDING}" height="{height-PADDING}" '
svg += f'fill="none" stroke="black" stroke-width="{BORDER_WIDTH}"/>'

# Add grid
svg += '<g opacity="0.3">'
for x in range(0, int(width), GRID_SPACING * 4):
    svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="gray" stroke-width="0.5"/>'
for y in range(0, int(height), GRID_SPACING * 4):
    svg += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="gray" stroke-width="0.5"/>'
svg += '</g>'

# Render pipes (behind components)
for pipe in pipes:
    svg += pipe.render()

# Render components
for comp in components:
    svg += comp.render()

# Add title block
svg += create_title_block(width, height, project_info)

# Add notes section
notes_y = height - TITLE_BLOCK_HEIGHT - PADDING - 100
svg += f'<text x="{PADDING}" y="{notes_y}" font-size="{TEXT_HEIGHT * 3}" font-weight="bold">NOTES:</text>'
svg += f'<text x="{PADDING}" y="{notes_y + 20}" font-size="{TEXT_HEIGHT * 2.5}">1. All dimensions in mm unless noted otherwise</text>'
svg += f'<text x="{PADDING}" y="{notes_y + 40}" font-size="{TEXT_HEIGHT * 2.5}">2. Refer to equipment datasheet for details</text>'

svg += '</svg>'
return svg
```

# — STREAMLIT INTERFACE —

# Project Information Form

st.sidebar.markdown(”### Project Information”)
project_info = {
‘client’: st.sidebar.text_input(“Client Name”, “EPS Pvt. Ltd.”),
‘project’: st.sidebar.text_input(“Project”, “Suction Filter + KDP-330”),
‘drawing_no’: st.sidebar.text_input(“Drawing No.”, “EPSPL-V2526-TP-01”),
‘drawn_by’: st.sidebar.text_input(“Drawn By”, “Engineer”),
‘checked_by’: st.sidebar.text_input(“Checked By”, “Manager”),
‘revision’: st.sidebar.text_input(“Revision”, “0”)
}

# Initialize session state

if ‘components_df’ not in st.session_state:
# Sample data - replace with your actual data loading
st.session_state.components_df = pd.DataFrame([
{‘id’: ‘P-001’, ‘tag’: ‘P-001’, ‘type’: ‘pump_centrifugal’, ‘x’: 200, ‘y’: 300, ‘rotation’: 0},
{‘id’: ‘FT-001’, ‘tag’: ‘FT-001’, ‘type’: ‘instrument’, ‘x’: 150, ‘y’: 280, ‘rotation’: 0},
{‘id’: ‘V-001’, ‘tag’: ‘V-001’, ‘type’: ‘valve_gate’, ‘x’: 300, ‘y’: 300, ‘rotation’: 0},
{‘id’: ‘TK-001’, ‘tag’: ‘TK-001’, ‘type’: ‘vessel_vertical’, ‘x’: 500, ‘y’: 200, ‘rotation’: 0},
])

if ‘pipes_df’ not in st.session_state:
st.session_state.pipes_df = pd.DataFrame([
{‘id’: ‘L-001’, ‘from_component’: ‘P-001’, ‘to_component’: ‘V-001’,
‘from_port’: ‘discharge’, ‘to_port’: ‘inlet’, ‘line_type’: ‘process’,
‘line_number’: ‘2”-PG-001’, ‘with_arrow’: True, ‘waypoints’: []},
{‘id’: ‘L-002’, ‘from_component’: ‘V-001’, ‘to_component’: ‘TK-001’,
‘from_port’: ‘outlet’, ‘to_port’: ‘side_bottom’, ‘line_type’: ‘process’,
‘line_number’: ‘2”-PG-002’, ‘with_arrow’: True, ‘waypoints’: []},
])

# Create components and pipes

components = [PnidComponent(row) for _, row in st.session_state.components_df.iterrows()]
component_map = {c.id: c for c in components}
pipes = [PnidPipe(row, component_map) for _, row in st.session_state.pipes_df.iterrows()]

# Main display

st.markdown(”## Professional P&ID Drawing”)

# Render the P&ID

svg_output = render_professional_pnid(components, pipes, project_info)
st.components.v1.html(svg_output, height=800, scrolling=True)

# Component addition form

st.sidebar.markdown(”—”)
st.sidebar.markdown(”### Add Component”)
with st.sidebar.form(“add_component”):
new_id = st.text_input(“Component ID”)
new_tag = st.text_input(“Tag (e.g., P-001, FT-101)”)
new_type = st.selectbox(“Type”, list(ISA_SYMBOLS.keys()) + [‘instrument’])
new_x = st.number_input(“X Position”, 0, 1000, 100)
new_y = st.number_input(“Y Position”, 0, 1000, 100)
new_rotation = st.slider(“Rotation”, 0, 360, 0)

```
if st.form_submit_button("Add Component"):
    new_comp = {
        'id': new_id,
        'tag': new_tag,
        'type': new_type,
        'x': new_x,
        'y': new_y,
        'rotation': new_rotation
    }
    st.session_state.components_df = pd.concat([
        st.session_state.components_df,
        pd.DataFrame([new_comp])
    ], ignore_index=True)
    st.rerun()
```

# Export options

st.markdown(”—”)
col1, col2, col3 = st.columns(3)

with col1:
st.download_button(“📥 Download SVG”, svg_output, “professional_pnid.svg”, “image/svg+xml”)

with col2:
if st.button(“📥 Generate PNG”):
png_data = export_png(svg_output)
if png_data:
st.download_button(“Download PNG”, png_data, “professional_pnid.png”, “image/png”)

with col3:
if st.button(“📥 Generate DXF”):
# Add DXF export logic here
st.info(“DXF export requires additional implementation”)

# Data management

with st.expander(“Component Data”):
st.dataframe(st.session_state.components_df)

with st.expander(“Pipe Data”):
st.dataframe(st.session_state.pipes_df)
