import streamlit as st
import pandas as pd
import os
import json
import datetime
import re
import math
from io import BytesIO
import ezdxf
from cairosvg import svg2png

# — CONFIGURATION —

st.set_page_config(
layout=“wide”,
page_title=“EPS Professional P&ID Generator”,
page_icon=“🏭”,
initial_sidebar_state=“expanded”
)

# Custom CSS

st.markdown(”””

<style>
    .main { padding: 1rem; }
    .stButton > button {
        background-color: #0066cc;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
    }
    .pnid-container {
        background-color: white;
        border: 2px solid #000;
        padding: 0;
        margin: 1rem 0;
        overflow: auto;
    }
</style>

“””, unsafe_allow_html=True)

# Sidebar

st.sidebar.title(“🏭 EPS P&ID Suite”)
st.sidebar.markdown(”—”)
st.sidebar.markdown(”### 📐 Drawing Standards”)
drawing_standard = st.sidebar.selectbox(“Standard”, [“ISA”, “DIN”, “ISO”, “JIS”])
drawing_size = st.sidebar.selectbox(“Size”, [“A3”, “A2”, “A1”, “A0”])

st.sidebar.markdown(”### 🎨 Visual Controls”)
GRID_VISIBLE = st.sidebar.checkbox(“Show Grid”, True)
LEGEND_VISIBLE = st.sidebar.checkbox(“Show Legend”, True)
BOM_VISIBLE = st.sidebar.checkbox(“Show BOM”, True)

GRID_SPACING = st.sidebar.slider(“Grid Spacing (mm)”, 10, 50, 25, 5)
SYMBOL_SCALE = st.sidebar.slider(“Symbol Scale”, 0.5, 2.0, 1.0, 0.1)

st.sidebar.markdown(”### 📏 Line Weights”)
line_weights = {
“Major Process”: st.sidebar.slider(“Major Process”, 2.0, 5.0, 3.0, 0.5),
“Minor Process”: st.sidebar.slider(“Minor Process”, 1.5, 3.0, 2.0, 0.5),
“Instrument Signal”: st.sidebar.slider(“Instrument Signal”, 0.5, 1.5, 0.7, 0.1),
}

# — COMPLETE ISA SYMBOLS INLINE —

# Define all symbols directly in the code to ensure they render

ISA_SYMBOLS = {
‘filter’: ‘’’
<path d="M 20,20 L 80,20 L 70,70 L 65,90 L 35,90 L 30,70 Z" fill="white" stroke="black" stroke-width="2.5"/>
<line x1="25" y1="30" x2="75" y2="30" stroke="black" stroke-width="2"/>
<line x1="27" y1="35" x2="73" y2="35" stroke="black" stroke-width="2"/>
<line x1="29" y1="40" x2="71" y2="40" stroke="black" stroke-width="2"/>
<line x1="31" y1="45" x2="69" y2="45" stroke="black" stroke-width="2"/>
<path d="M 30,30 L 40,40 M 35,30 L 45,40 M 40,30 L 50,40 M 45,30 L 55,40 M 50,30 L 60,40 M 55,30 L 65,40 M 60,30 L 70,40" stroke="black" stroke-width="0.5"/>
<rect x="35" y="10" width="30" height="10" fill="white" stroke="black" stroke-width="2.5"/>
<rect x="35" y="90" width="30" height="10" fill="white" stroke="black" stroke-width="2.5"/>
‘’’,

```
'pump': '''
    <circle cx="50" cy="50" r="35" fill="white" stroke="black" stroke-width="3"/>
    <path d="M 50,15 L 50,85 M 15,50 L 85,50" stroke="black" stroke-width="2.5"/>
    <rect x="0" y="45" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="45" y="0" width="10" height="15" fill="white" stroke="black" stroke-width="2.5"/>
''',

'valve_gate': '''
    <rect x="20" y="35" width="60" height="30" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="45" y="40" width="10" height="20" fill="white" stroke="black" stroke-width="2"/>
    <rect x="48" y="15" width="4" height="25" fill="black"/>
    <circle cx="50" cy="15" r="8" fill="none" stroke="black" stroke-width="2"/>
    <line x1="42" y1="15" x2="58" y2="15" stroke="black" stroke-width="2"/>
    <rect x="5" y="45" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="80" y="45" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

'strainer_y': '''
    <path d="M 50,20 L 50,50 L 70,70 L 70,80 L 60,80 L 40,60 L 40,50 L 40,20" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 35,20 L 65,20" stroke="black" stroke-width="2.5"/>
    <path d="M 45,55 L 65,75" stroke="black" stroke-width="1.5"/>
    <path d="M 45,60 L 60,75" stroke="black" stroke-width="1.5"/>
    <path d="M 45,65 L 55,75" stroke="black" stroke-width="1.5"/>
    <rect x="40" y="10" width="20" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="55" y="75" width="20" height="10" fill="white" stroke="black" stroke-width="2.5"/>
''',

'expansion_bellows': '''
    <path d="M 20,30 Q 25,25 30,30 Q 35,35 40,30 Q 45,25 50,30 Q 55,35 60,30 Q 65,25 70,30 Q 75,35 80,30" fill="none" stroke="black" stroke-width="2.5"/>
    <path d="M 20,50 Q 25,55 30,50 Q 35,45 40,50 Q 45,55 50,50 Q 55,45 60,50 Q 65,55 70,50 Q 75,45 80,50" fill="none" stroke="black" stroke-width="2.5"/>
    <line x1="20" y1="30" x2="20" y2="50" stroke="black" stroke-width="2.5"/>
    <line x1="80" y1="30" x2="80" y2="50" stroke="black" stroke-width="2.5"/>
    <rect x="5" y="35" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="80" y="35" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
''',

'pressure_regulator': '''
    <rect x="25" y="45" width="50" height="30" rx="5" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="35" y="20" width="30" height="25" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 45,25 Q 50,30 45,35 Q 55,30 50,35 Q 45,40 50,45" stroke="black" stroke-width="2" fill="none"/>
    <rect x="48" y="10" width="4" height="10" fill="black"/>
    <circle cx="50" cy="10" r="5" fill="none" stroke="black" stroke-width="2"/>
    <rect x="5" y="55" width="20" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="75" y="55" width="20" height="10" fill="white" stroke="black" stroke-width="2.5"/>
''',

'catch_pot': '''
    <rect x="30" y="40" width="40" height="50" rx="5" fill="white" stroke="black" stroke-width="2.5"/>
    <ellipse cx="50" cy="40" rx="20" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
    <ellipse cx="50" cy="90" rx="20" ry="10" fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="35" y1="65" x2="65" y2="65" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
    <rect x="45" y="25" width="10" height="15" fill="white" stroke="black" stroke-width="2"/>
    <rect x="70" y="60" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="45" y="90" width="10" height="15" fill="white" stroke="black" stroke-width="2"/>
''',

'control_panel': '''
    <rect x="10" y="10" width="180" height="230" rx="5" fill="white" stroke="black" stroke-width="3"/>
    <rect x="20" y="20" width="160" height="210" fill="none" stroke="black" stroke-width="2"/>
    <rect x="30" y="30" width="140" height="30" fill="white" stroke="black" stroke-width="1.5"/>
    <text x="100" y="50" text-anchor="middle" font-size="12" font-weight="bold">CONTROL PANEL</text>
    <rect x="40" y="70" width="60" height="45" fill="#e0e0e0" stroke="black" stroke-width="2"/>
    <text x="70" y="95" text-anchor="middle" font-size="10">HMI</text>
    <rect x="110" y="70" width="60" height="45" fill="#e0e0e0" stroke="black" stroke-width="2"/>
    <text x="140" y="95" text-anchor="middle" font-size="10">VFD</text>
    <circle cx="50" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
    <circle cx="75" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
    <circle cx="100" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
    <circle cx="125" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
    <circle cx="150" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
''',

'valve_drain': '''
    <rect x="30" y="35" width="40" height="30" fill="white" stroke="black" stroke-width="2"/>
    <line x1="50" y1="35" x2="50" y2="20" stroke="black" stroke-width="2"/>
    <circle cx="50" cy="20" r="5" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="48" y="65" width="4" height="15" fill="white" stroke="black" stroke-width="2"/>
''',

'solenoid_valve': '''
    <rect x="30" y="45" width="40" height="20" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="40" y="25" width="20" height="20" rx="3" fill="white" stroke="black" stroke-width="2"/>
    <line x1="45" y1="30" x2="55" y2="30" stroke="black" stroke-width="1"/>
    <line x1="45" y1="35" x2="55" y2="35" stroke="black" stroke-width="1"/>
    <line x1="45" y1="40" x2="55" y2="40" stroke="black" stroke-width="1"/>
    <circle cx="50" cy="20" r="3" fill="black"/>
    <line x1="50" y1="20" x2="50" y2="25" stroke="black" stroke-width="2"/>
    <rect x="15" y="50" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="70" y="50" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

'psv': '''
    <path d="M 30,60 L 30,70 L 70,70 L 70,60 Z" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 50,60 L 50,40 L 40,30 L 60,30 L 50,40" stroke="black" stroke-width="2.5" fill="white"/>
    <path d="M 50,30 L 50,20" stroke="black" stroke-width="2.5"/>
    <circle cx="50" cy="15" r="5" fill="none" stroke="black" stroke-width="2"/>
''',
```

}

# Project info

if ‘project_info’ not in st.session_state:
st.session_state.project_info = {
‘client’: ‘EPS Pvt. Ltd.’,
‘project’: ‘SUCTION FILTER + KDP-330’,
‘drawing_no’: ‘EPSPL-V2526-TP-01’,
‘drawn_by’: ‘ABC’,
‘checked_by’: ‘XYZ’,
‘approved_by’: ‘PQR’,
‘revision’: ‘0’,
‘date’: datetime.datetime.now().strftime(”%Y-%m-%d”)
}

# — EXACT REFERENCE DATA —

# Equipment matching the reference P&ID

REFERENCE_EQUIPMENT = pd.DataFrame([
# Main flow path equipment
{‘id’: ‘EB-001’, ‘tag’: ‘EXPANSION BELLOWS’, ‘type’: ‘expansion_bellows’, ‘x’: 150, ‘y’: 340, ‘width’: 100, ‘height’: 80},
{‘id’: ‘Y-001’, ‘tag’: ‘Y-STRAINER’, ‘type’: ‘strainer_y’, ‘x’: 280, ‘y’: 320, ‘width’: 100, ‘height’: 100},
{‘id’: ‘V-001’, ‘tag’: ‘CW-001’, ‘type’: ‘valve_gate’, ‘x’: 420, ‘y’: 330, ‘width’: 100, ‘height’: 100},
{‘id’: ‘F-001’, ‘tag’: ‘FILTER’, ‘type’: ‘filter’, ‘x’: 560, ‘y’: 280, ‘width’: 100, ‘height’: 150},
{‘id’: ‘V-002’, ‘tag’: ‘CW-002’, ‘type’: ‘valve_gate’, ‘x’: 720, ‘y’: 340, ‘width’: 100, ‘height’: 100},
{‘id’: ‘P-001’, ‘tag’: ‘KDP-330’, ‘type’: ‘pump’, ‘x’: 880, ‘y’: 320, ‘width’: 120, ‘height’: 120},
{‘id’: ‘CT-001’, ‘tag’: ‘CATCH POT’, ‘type’: ‘catch_pot’, ‘x’: 1080, ‘y’: 380, ‘width’: 100, ‘height’: 120},

```
# Auxiliary equipment
{'id': 'PR-001', 'tag': 'N2-001 REGULATOR', 'type': 'pressure_regulator', 'x': 560, 'y': 480, 'width': 100, 'height': 80},
{'id': 'PSV-001', 'tag': 'PRESSURE REGULATOR', 'type': 'psv', 'x': 660, 'y': 200, 'width': 100, 'height': 100},
{'id': 'V-003', 'tag': 'DRAIN VALVE', 'type': 'valve_drain', 'x': 560, 'y': 560, 'width': 100, 'height': 80},
{'id': 'SV-001', 'tag': 'SR-001', 'type': 'solenoid_valve', 'x': 560, 'y': 680, 'width': 100, 'height': 80},

# Control Panel
{'id': 'CP-001', 'tag': 'CONTROL PANEL', 'type': 'control_panel', 'x': 1300, 'y': 200, 'width': 200, 'height': 250},

# Instruments
{'id': 'PI-001', 'tag': 'PI-001', 'type': 'instrument', 'x': 480, 'y': 280, 'width': 44, 'height': 44},
{'id': 'PI-002', 'tag': 'PI-002', 'type': 'instrument', 'x': 820, 'y': 370, 'width': 44, 'height': 44},
{'id': 'PT-001', 'tag': 'PT-001', 'type': 'instrument', 'x': 940, 'y': 420, 'width': 44, 'height': 44},
{'id': 'TI-001', 'tag': 'TI-001', 'type': 'instrument', 'x': 940, 'y': 260, 'width': 44, 'height': 44},
{'id': 'FI-001', 'tag': 'FI-001', 'type': 'instrument', 'x': 1140, 'y': 320, 'width': 44, 'height': 44},
```

])

# Piping data

REFERENCE_PIPING = pd.DataFrame([
# Main process flow
{‘id’: ‘L-001’, ‘from’: ‘INLET’, ‘to’: ‘EB-001’, ‘label’: ‘10”-PG-001-CS’, ‘type’: ‘process’},
{‘id’: ‘L-002’, ‘from’: ‘EB-001’, ‘to’: ‘Y-001’, ‘label’: ‘10”-PG-002-CS’, ‘type’: ‘process’},
{‘id’: ‘L-003’, ‘from’: ‘Y-001’, ‘to’: ‘V-001’, ‘label’: ‘10”-PG-003-CS’, ‘type’: ‘process’},
{‘id’: ‘L-004’, ‘from’: ‘V-001’, ‘to’: ‘F-001’, ‘label’: ‘10”-PG-004-CS’, ‘type’: ‘process’},
{‘id’: ‘L-005’, ‘from’: ‘F-001’, ‘to’: ‘V-002’, ‘label’: ‘10”-PS-005-CS’, ‘type’: ‘process’},
{‘id’: ‘L-006’, ‘from’: ‘V-002’, ‘to’: ‘P-001’, ‘label’: ‘10”-PS-006-CS’, ‘type’: ‘process’},
{‘id’: ‘L-007’, ‘from’: ‘P-001’, ‘to’: ‘CT-001’, ‘label’: ‘8”-PD-007-CS’, ‘type’: ‘process’},
{‘id’: ‘L-008’, ‘from’: ‘CT-001’, ‘to’: ‘OUTLET’, ‘label’: ‘8”-PD-008-CS’, ‘type’: ‘process’},

```
# Auxiliary lines
{'id': 'L-009', 'from': 'F-001', 'to': 'PSV-001', 'label': '2"-PR-009-CS', 'type': 'process_small'},
{'id': 'L-010', 'from': 'F-001', 'to': 'V-003', 'label': '2"-DR-010-CS', 'type': 'process_small'},
{'id': 'L-011', 'from': 'V-003', 'to': 'SV-001', 'label': '2"-DR-011-CS', 'type': 'process_small'},

# Instrument connections
{'id': 'IS-001', 'from': 'PI-001', 'to': 'CP-001', 'label': '', 'type': 'instrument'},
{'id': 'IS-002', 'from': 'PT-001', 'to': 'CP-001', 'label': '', 'type': 'instrument'},
```

])

# — MAIN RENDERING FUNCTION —

def render_professional_pnid():
“”“Render the complete P&ID with legend and BOM”””

```
# Drawing dimensions
width = 1800
height = 1000

svg_parts = []
svg_parts.append(f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
                 xmlns="http://www.w3.org/2000/svg" style="background-color: white;">''')

# Definitions
svg_parts.append('<defs>')
svg_parts.append('''
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
        <polygon points="0,0 10,5 0,10" fill="black"/>
    </marker>
''')
svg_parts.append('</defs>')

# Border
svg_parts.append(f'<rect x="10" y="10" width="{width-20}" height="{height-20}" fill="none" stroke="black" stroke-width="3"/>')
svg_parts.append(f'<rect x="15" y="15" width="{width-30}" height="{height-30}" fill="none" stroke="black" stroke-width="1"/>')

# Grid
if GRID_VISIBLE:
    svg_parts.append('<g opacity="0.2">')
    for x in range(0, width, GRID_SPACING * 4):
        svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#cccccc" stroke-width="0.5"/>')
    for y in range(0, height, GRID_SPACING * 4):
        svg_parts.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#cccccc" stroke-width="0.5"/>')
    svg_parts.append('</g>')

# Equipment
for _, equip in REFERENCE_EQUIPMENT.iterrows():
    if equip['type'] == 'instrument':
        # Instrument bubble
        cx = equip['x'] + equip['width']/2
        cy = equip['y'] + equip['height']/2
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="white" stroke="black" stroke-width="2.5"/>')
        svg_parts.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="bold">{equip["tag"]}</text>')
    else:
        # Equipment symbol
        svg_parts.append(f'<g transform="translate({equip["x"]},{equip["y"]})">')
        if equip['type'] in ISA_SYMBOLS:
            svg_parts.append(ISA_SYMBOLS[equip['type']])
        svg_parts.append(f'<text x="{equip["width"]/2}" y="{equip["height"]+15}" text-anchor="middle" font-size="11">{equip["tag"]}</text>')
        svg_parts.append('</g>')

# Piping (simplified)
for _, pipe in REFERENCE_PIPING.iterrows():
    # This is simplified - you'd need proper routing logic
    if pipe['type'] == 'process':
        stroke_width = line_weights['Major Process']
    elif pipe['type'] == 'process_small':
        stroke_width = line_weights['Minor Process']
    else:
        stroke_width = line_weights['Instrument Signal']
    
    # Example connection lines (would need proper routing)
    # Add actual pipe paths based on equipment positions
    
# Legend
if LEGEND_VISIBLE:
    legend_x = 1550
    legend_y = 50
    svg_parts.append(f'<g transform="translate({legend_x},{legend_y})">')
    svg_parts.append('<rect x="0" y="0" width="230" height="400" fill="white" stroke="black" stroke-width="2"/>')
    svg_parts.append('<text x="115" y="25" text-anchor="middle" font-size="14" font-weight="bold">LEGEND</text>')
    
    # Legend entries
    legend_items = [
        ('EXPANSION BELLOWS', 'expansion_bellows'),
        ('Y-STRAINER', 'strainer_y'),
        ('GATE VALVE', 'valve_gate'),
        ('FILTER', 'filter'),
        ('PUMP', 'pump'),
        ('CATCH POT', 'catch_pot'),
        ('CONTROL PANEL', 'control_panel'),
    ]
    
    y_pos = 50
    for name, symbol_type in legend_items:
        svg_parts.append(f'<text x="10" y="{y_pos}" font-size="11">{name}</text>')
        y_pos += 25
    
    svg_parts.append('</g>')

# Title block
tb_x = width - 600
tb_y = height - 200
svg_parts.append(f'<g transform="translate({tb_x},{tb_y})">')
svg_parts.append('<rect x="0" y="0" width="580" height="180" fill="white" stroke="black" stroke-width="2"/>')
svg_parts.append(f'<text x="290" y="30" text-anchor="middle" font-size="16" font-weight="bold">{st.session_state.project_info["client"]}</text>')
svg_parts.append('<text x="290" y="60" text-anchor="middle" font-size="14">PIPING AND INSTRUMENTATION DIAGRAM</text>')
svg_parts.append(f'<text x="290" y="85" text-anchor="middle" font-size="12">{st.session_state.project_info["project"]}</text>')
svg_parts.append(f'<text x="50" y="120" font-size="10">DWG NO: {st.session_state.project_info["drawing_no"]}</text>')
svg_parts.append(f'<text x="50" y="140" font-size="10">DATE: {st.session_state.project_info["date"]}</text>')
svg_parts.append(f'<text x="300" y="120" font-size="10">DRAWN: {st.session_state.project_info["drawn_by"]}</text>')
svg_parts.append(f'<text x="300" y="140" font-size="10">CHECKED: {st.session_state.project_info["checked_by"]}</text>')
svg_parts.append(f'<text x="450" y="120" font-size="10">REV: {st.session_state.project_info["revision"]}</text>')
svg_parts.append('</g>')

# BOM Table
if BOM_VISIBLE:
    bom_x = 50
    bom_y = height - 300
    svg_parts.append(f'<g transform="translate({bom_x},{bom_y})">')
    svg_parts.append('<rect x="0" y="0" width="700" height="250" fill="white" stroke="black" stroke-width="2"/>')
    svg_parts.append('<text x="350" y="25" text-anchor="middle" font-size="14" font-weight="bold">BILL OF MATERIALS</text>')
    
    # Table headers
    svg_parts.append('<line x1="0" y1="40" x2="700" y2="40" stroke="black" stroke-width="1"/>')
    svg_parts.append('<text x="20" y="35" font-size="10" font-weight="bold">ITEM</text>')
    svg_parts.append('<text x="80" y="35" font-size="10" font-weight="bold">TAG</text>')
    svg_parts.append('<text x="200" y="35" font-size="10" font-weight="bold">DESCRIPTION</text>')
    svg_parts.append('<text x="400" y="35" font-size="10" font-weight="bold">SIZE</text>')
    svg_parts.append('<text x="500" y="35" font-size="10" font-weight="bold">MATERIAL</text>')
    svg_parts.append('<text x="600" y="35" font-size="10" font-weight="bold">QTY</text>')
    
    # BOM entries
    bom_items = [
        ('1', 'EB-001', 'EXPANSION BELLOWS', '10"', 'CS', '1'),
        ('2', 'Y-001', 'Y-STRAINER', '10"', 'CS', '1'),
        ('3', 'V-001/002', 'GATE VALVE', '10"', 'CS', '2'),
        ('4', 'F-001', 'SUCTION FILTER', '10"', 'CS', '1'),
        ('5', 'P-001', 'CENTRIFUGAL PUMP', 'KDP-330', 'CS', '1'),
        ('6', 'CT-001', 'CATCH POT', '8"', 'CS', '1'),
    ]
    
    y_pos = 60
    for item in bom_items:
        svg_parts.append(f'<text x="20" y="{y_pos}" font-size="10">{item[0]}</text>')
        svg_parts.append(f'<text x="80" y="{y_pos}" font-size="10">{item[1]}</text>')
        svg_parts.append(f'<text x="200" y="{y_pos}" font-size="10">{item[2]}</text>')
        svg_parts.append(f'<text x="400" y="{y_pos}" font-size="10">{item[3]}</text>')
        svg_parts.append(f'<text x="500" y="{y_pos}" font-size="10">{item[4]}</text>')
        svg_parts.append(f'<text x="600" y="{y_pos}" font-size="10">{item[5]}</text>')
        y_pos += 20
    
    svg_parts.append('</g>')

svg_parts.append('</svg>')
return ''.join(svg_parts)
```

# — MAIN APP —

st.title(“🏭 EPS Professional P&ID Generator”)

# Header

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
st.markdown(f”**Project:** {st.session_state.project_info[‘project’]}”)
with col2:
st.markdown(f”**Drawing:** {st.session_state.project_info[‘drawing_no’]}”)
with col3:
st.markdown(f”**Rev:** {st.session_state.project_info[‘revision’]}”)

# Main P&ID display

st.markdown(’<div class="pnid-container">’, unsafe_allow_html=True)
svg_output = render_professional_pnid()
st.components.v1.html(svg_output, height=1000, scrolling=True)
st.markdown(’</div>’, unsafe_allow_html=True)

# Export options

col1, col2, col3 = st.columns(3)
with col1:
st.download_button(
“📥 Download SVG”,
svg_output,
“EPSPL-V2526-TP-01.svg”,
“image/svg+xml”
)
with col2:
if st.button(“📥 Generate PNG”):
try:
png_data = svg2png(bytestring=svg_output.encode(‘utf-8’), output_width=3000)
st.download_button(
“Download PNG”,
png_data,
“EPSPL-V2526-TP-01.png”,
“image/png”
)
except Exception as e:
st.error(f”PNG generation error: {e}”)

# Footer

st.markdown(”—”)
st.markdown(
“””<div style="text-align: center; color: #666;">
EPS Professional P&ID Generator | © 2024 EPS Pvt. Ltd.
</div>”””,
unsafe_allow_html=True
)
