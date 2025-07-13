“””
Ultra-professional P&ID symbols matching industry standards
These symbols include detailed internals, proper proportions, and connection points
“””

PROFESSIONAL_SYMBOLS = {
# Enhanced Pump Symbols
‘pump_centrifugal_detailed’: ‘’’<symbol id="pump_centrifugal_detailed" viewBox="0 0 80 80">
<!-- Pump casing -->
<circle cx="40" cy="40" r="30" fill="white" stroke="black" stroke-width="2"/>
<!-- Impeller representation -->
<path d="M 40,10 Q 50,40 40,70 Q 30,40 40,10" fill="none" stroke="black" stroke-width="1.5"/>
<path d="M 10,40 Q 40,30 70,40 Q 40,50 10,40" fill="none" stroke="black" stroke-width="1.5"/>
<!-- Center shaft -->
<circle cx="40" cy="40" r="3" fill="black"/>
<!-- Suction and discharge indicators -->
<path d="M 0,40 L 10,40" stroke="black" stroke-width="3"/>
<path d="M 40,0 L 40,10" stroke="black" stroke-width="3"/>
<!-- Rotation arrow -->
<path d="M 55,25 A 20,20 0 0,1 60,40" fill="none" stroke="black" stroke-width="1" marker-end="url(#arrowhead)"/>
</symbol>’’’,

```
'pump_positive_displacement': '''<symbol id="pump_positive_displacement" viewBox="0 0 80 80">
    <rect x="15" y="15" width="50" height="50" rx="5" fill="white" stroke="black" stroke-width="2"/>
    <!-- Piston representation -->
    <rect x="30" y="25" width="20" height="30" fill="white" stroke="black" stroke-width="1.5"/>
    <line x1="40" y1="25" x2="40" y2="55" stroke="black" stroke-width="1"/>
    <!-- Ports -->
    <path d="M 0,30 L 15,30" stroke="black" stroke-width="3"/>
    <path d="M 65,50 L 80,50" stroke="black" stroke-width="3"/>
    <!-- Check valves -->
    <path d="M 15,30 L 20,25 L 20,35 Z" fill="black"/>
    <path d="M 60,50 L 65,45 L 65,55 Z" fill="black"/>
</symbol>''',

# Detailed Valve Symbols
'valve_gate_detailed': '''<symbol id="valve_gate_detailed" viewBox="0 0 60 80">
    <!-- Valve body -->
    <path d="M 10,40 L 10,60 L 50,60 L 50,40 Z" fill="white" stroke="black" stroke-width="2"/>
    <!-- Gate -->
    <rect x="25" y="35" width="10" height="30" fill="white" stroke="black" stroke-width="1.5"/>
    <!-- Stem -->
    <line x1="30" y1="35" x2="30" y2="10" stroke="black" stroke-width="2"/>
    <!-- Handwheel -->
    <circle cx="30" cy="10" r="8" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 22,10 L 38,10 M 30,2 L 30,18" stroke="black" stroke-width="1.5"/>
    <!-- Flanges -->
    <rect x="0" y="45" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="50" y="45" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <!-- Flange bolts -->
    <circle cx="5" cy="48" r="1" fill="black"/>
    <circle cx="5" cy="52" r="1" fill="black"/>
    <circle cx="55" cy="48" r="1" fill="black"/>
    <circle cx="55" cy="52" r="1" fill="black"/>
</symbol>''',

'valve_globe_detailed': '''<symbol id="valve_globe_detailed" viewBox="0 0 60 80">
    <!-- Valve body -->
    <circle cx="30" cy="50" r="20" fill="white" stroke="black" stroke-width="2"/>
    <!-- Internal disk and seat -->
    <path d="M 15,50 L 45,50" stroke="black" stroke-width="1.5"/>
    <circle cx="30" cy="50" r="5" fill="white" stroke="black" stroke-width="1.5"/>
    <!-- Stem -->
    <line x1="30" y1="45" x2="30" y2="10" stroke="black" stroke-width="2"/>
    <!-- Handwheel -->
    <circle cx="30" cy="10" r="8" fill="white" stroke="black" stroke-width="1.5"/>
    <path d="M 22,10 L 38,10 M 30,2 L 30,18" stroke="black" stroke-width="1.5"/>
    <!-- Ports -->
    <path d="M 0,50 L 10,50" stroke="black" stroke-width="3"/>
    <path d="M 50,50 L 60,50" stroke="black" stroke-width="3"/>
    <!-- Flow direction indicator -->
    <path d="M 15,55 L 20,50 L 15,45" fill="none" stroke="black" stroke-width="1" opacity="0.5"/>
</symbol>''',

'valve_control_detailed': '''<symbol id="valve_control_detailed" viewBox="0 0 60 100">
    <!-- Valve body -->
    <path d="M 10,60 L 10,80 L 50,80 L 50,60 Z" fill="white" stroke="black" stroke-width="2"/>
    <!-- Actuator -->
    <rect x="15" y="20" width="30" height="40" rx="5" fill="white" stroke="black" stroke-width="2"/>
    <!-- Diaphragm -->
    <ellipse cx="30" cy="40" rx="12" ry="3" fill="black"/>
    <!-- Spring -->
    <path d="M 25,25 L 35,30 L 25,35 L 35,40" fill="none" stroke="black" stroke-width="1.5"/>
    <!-- Signal connection -->
    <line x1="30" y1="20" x2="30" y2="5" stroke="black" stroke-width="1.5"/>
    <circle cx="30" cy="5" r="2" fill="black"/>
    <!-- Ports -->
    <path d="M 0,70 L 10,70" stroke="black" stroke-width="3"/>
    <path d="M 50,70 L 60,70" stroke="black" stroke-width="3"/>
</symbol>''',

# Detailed Vessel Symbols
'vessel_vertical_detailed': '''<symbol id="vessel_vertical_detailed" viewBox="0 0 100 180">
    <!-- Top head -->
    <ellipse cx="50" cy="30" rx="40" ry="20" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Shell -->
    <rect x="10" y="30" width="80" height="120" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Bottom head -->
    <ellipse cx="50" cy="150" rx="40" ry="20" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Weld lines -->
    <line x1="10" y1="30" x2="10" y2="150" stroke="black" stroke-width="2.5"/>
    <line x1="90" y1="30" x2="90" y2="150" stroke="black" stroke-width="2.5"/>
    <!-- Support legs -->
    <line x1="25" y1="170" x2="20" y2="190" stroke="black" stroke-width="2"/>
    <line x1="75" y1="170" x2="80" y2="190" stroke="black" stroke-width="2"/>
    <!-- Nozzles -->
    <circle cx="50" cy="10" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="90" cy="60" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="90" cy="120" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="50" cy="170" r="3" fill="white" stroke="black" stroke-width="2"/>
    <!-- Level indicator -->
    <rect x="0" y="80" width="10" height="40" fill="white" stroke="black" stroke-width="1.5"/>
    <line x1="5" y1="100" x2="5" y2="100" stroke="black" stroke-width="3"/>
</symbol>''',

'vessel_horizontal_detailed': '''<symbol id="vessel_horizontal_detailed" viewBox="0 0 180 100">
    <!-- Left head -->
    <ellipse cx="30" cy="50" rx="20" ry="40" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Shell -->
    <rect x="30" y="10" width="120" height="80" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Right head -->
    <ellipse cx="150" cy="50" rx="20" ry="40" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Weld lines -->
    <line x1="30" y1="10" x2="150" y2="10" stroke="black" stroke-width="2.5"/>
    <line x1="30" y1="90" x2="150" y2="90" stroke="black" stroke-width="2.5"/>
    <!-- Saddle supports -->
    <path d="M 50,90 Q 50,100 60,100 L 70,100 Q 80,100 80,90" fill="none" stroke="black" stroke-width="2"/>
    <path d="M 100,90 Q 100,100 110,100 L 120,100 Q 130,100 130,90" fill="none" stroke="black" stroke-width="2"/>
    <!-- Nozzles -->
    <circle cx="90" cy="10" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="170" cy="50" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="90" cy="90" r="3" fill="white" stroke="black" stroke-width="2"/>
</symbol>''',

# Filter with Details
'filter_detailed': '''<symbol id="filter_detailed" viewBox="0 0 60 100">
    <!-- Housing -->
    <path d="M 10,20 L 50,20 L 45,60 L 40,80 L 20,80 L 15,60 Z" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Filter element -->
    <rect x="15" y="30" width="30" height="5" fill="gray" opacity="0.3"/>
    <rect x="15" y="38" width="30" height="5" fill="gray" opacity="0.3"/>
    <rect x="15" y="46" width="30" height="5" fill="gray" opacity="0.3"/>
    <!-- Top flange -->
    <rect x="5" y="10" width="50" height="10" fill="white" stroke="black" stroke-width="2"/>
    <!-- Bottom flange -->
    <rect x="15" y="80" width="30" height="10" fill="white" stroke="black" stroke-width="2"/>
    <!-- Bolts -->
    <circle cx="10" cy="15" r="1.5" fill="black"/>
    <circle cx="50" cy="15" r="1.5" fill="black"/>
    <circle cx="20" cy="85" r="1.5" fill="black"/>
    <circle cx="40" cy="85" r="1.5" fill="black"/>
    <!-- Drain -->
    <line x1="30" y1="80" x2="30" y2="90" stroke="black" stroke-width="1.5"/>
    <path d="M 25,90 L 35,90" stroke="black" stroke-width="1.5"/>
</symbol>''',

# Heat Exchanger with Tubes
'heat_exchanger_detailed': '''<symbol id="heat_exchanger_detailed" viewBox="0 0 140 80">
    <!-- Shell -->
    <circle cx="40" cy="40" r="35" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Tube bundle -->
    <rect x="40" y="5" width="80" height="70" fill="white" stroke="black" stroke-width="2.5"/>
    <!-- Tubes -->
    <line x1="50" y1="15" x2="110" y2="15" stroke="black" stroke-width="1"/>
    <line x1="50" y1="25" x2="110" y2="25" stroke="black" stroke-width="1"/>
    <line x1="50" y1="35" x2="110" y2="35" stroke="black" stroke-width="1"/>
    <line x1="50" y1="45" x2="110" y2="45" stroke="black" stroke-width="1"/>
    <line x1="50" y1="55" x2="110" y2="55" stroke="black" stroke-width="1"/>
    <line x1="50" y1="65" x2="110" y2="65" stroke="black" stroke-width="1"/>
    <!-- Baffles -->
    <line x1="70" y1="5" x2="70" y2="35" stroke="black" stroke-width="2"/>
    <line x1="90" y1="45" x2="90" y2="75" stroke="black" stroke-width="2"/>
    <!-- Shell side nozzles -->
    <circle cx="40" cy="5" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="40" cy="75" r="3" fill="white" stroke="black" stroke-width="2"/>
    <!-- Tube side nozzles -->
    <circle cx="120" cy="20" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="120" cy="60" r="3" fill="white" stroke="black" stroke-width="2"/>
</symbol>''',

# Control Panel Representation
'control_panel': '''<symbol id="control_panel" viewBox="0 0 200 150">
    <!-- Panel outline -->
    <rect x="5" y="5" width="190" height="140" fill="#f0f0f0" stroke="black" stroke-width="2.5"/>
    <!-- Panel door -->
    <rect x="10" y="10" width="180" height="130" fill="white" stroke="black" stroke-width="2"/>
    <!-- Title area -->
    <rect x="10" y="10" width="180" height="25" fill="#e0e0e0" stroke="black" stroke-width="1"/>
    <text x="100" y="27" text-anchor="middle" font-size="12" font-weight="bold">CONTROL PANEL</text>
    <!-- Indicator lights -->
    <circle cx="30" cy="55" r="8" fill="#00ff00" stroke="black" stroke-width="1"/>
    <circle cx="55" cy="55" r="8" fill="#ffff00" stroke="black" stroke-width="1"/>
    <circle cx="80" cy="55" r="8" fill="#ff0000" stroke="black" stroke-width="1"/>
    <!-- Switches -->
    <rect x="20" y="80" width="15" height="25" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="45" y="80" width="15" height="25" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="70" y="80" width="15" height="25" fill="white" stroke="black" stroke-width="1.5"/>
    <!-- Display -->
    <rect x="110" y="50" width="70" height="40" fill="black" stroke="gray" stroke-width="2"/>
    <text x="145" y="75" text-anchor="middle" font-size="16" fill="#00ff00" font-family="monospace">RUN</text>
    <!-- Emergency stop -->
    <circle cx="145" cy="115" r="15" fill="#ff0000" stroke="black" stroke-width="2"/>
    <text x="145" y="120" text-anchor="middle" font-size="8" fill="white" font-weight="bold">E-STOP</text>
</symbol>''',

# Piping Components
'pipe_reducer': '''<symbol id="pipe_reducer" viewBox="0 0 60 40">
    <path d="M 0,10 L 20,10 L 40,15 L 60,15 L 60,25 L 40,25 L 20,30 L 0,30 Z" 
          fill="white" stroke="black" stroke-width="2"/>
</symbol>''',

'pipe_tee': '''<symbol id="pipe_tee" viewBox="0 0 60 60">
    <path d="M 0,25 L 60,25 L 60,35 L 35,35 L 35,60 L 25,60 L 25,35 L 0,35 Z" 
          fill="white" stroke="black" stroke-width="2"/>
</symbol>''',

'pipe_elbow': '''<symbol id="pipe_elbow" viewBox="0 0 40 40">
    <path d="M 0,20 L 20,20 Q 40,20 40,40 L 40,40 L 30,40 Q 10,40 10,20 L 0,20 Z" 
          fill="white" stroke="black" stroke-width="2"/>
</symbol>''',

# Instrumentation Details
'orifice_plate': '''<symbol id="orifice_plate" viewBox="0 0 60 30">
    <line x1="0" y1="15" x2="25" y2="15" stroke="black" stroke-width="3"/>
    <line x1="35" y1="15" x2="60" y2="15" stroke="black" stroke-width="3"/>
    <circle cx="30" cy="15" r="8" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="30" cy="15" r="3" fill="white" stroke="black" stroke-width="1.5"/>
</symbol>''',

'flow_nozzle': '''<symbol id="flow_nozzle" viewBox="0 0 80 40">
    <path d="M 0,20 L 20,20 L 30,15 Q 40,15 50,15 Q 60,15 60,20 L 80,20" 
          fill="none" stroke="black" stroke-width="2"/>
    <path d="M 0,20 L 20,20 L 30,25 Q 40,25 50,25 Q 60,25 60,20 L 80,20" 
          fill="none" stroke="black" stroke-width="2"/>
</symbol>''',
```

}

# Detailed Piping Specifications

PIPING_SPECS = {
‘CS150’: {  # Carbon Steel 150#
‘material’: ‘Carbon Steel’,
‘rating’: ‘150#’,
‘schedule’: ‘Sch 40’,
‘color’: ‘#000000’,
‘line_weight’: 2.0
},
‘CS300’: {  # Carbon Steel 300#
‘material’: ‘Carbon Steel’,
‘rating’: ‘300#’,
‘schedule’: ‘Sch 80’,
‘color’: ‘#000000’,
‘line_weight’: 2.5
},
‘SS150’: {  # Stainless Steel 150#
‘material’: ‘Stainless Steel’,
‘rating’: ‘150#’,
‘schedule’: ‘Sch 10S’,
‘color’: ‘#0066cc’,
‘line_weight’: 2.0
},
‘PVC’: {
‘material’: ‘PVC’,
‘rating’: ‘Sch 80’,
‘schedule’: ‘Sch 80’,
‘color’: ‘#666666’,
‘line_weight’: 1.5
}
}

# Equipment specification table format

def create_equipment_table_svg(equipment_list, x, y):
“”“Creates an equipment list table in SVG format”””
svg = f’<g transform="translate({x},{y})">’

```
# Table header
svg += '<rect x="0" y="0" width="400" height="25" fill="#cccccc" stroke="black" stroke-width="1"/>'
svg += '<text x="10" y="17" font-size="10" font-weight="bold">TAG</text>'
svg += '<text x="60" y="17" font-size="10" font-weight="bold">DESCRIPTION</text>'
svg += '<text x="200" y="17" font-size="10" font-weight="bold">SIZE/CAPACITY</text>'
svg += '<text x="300" y="17" font-size="10" font-weight="bold">MATERIAL</text>'

# Table rows
row_y = 25
for equip in equipment_list:
    svg += f'<rect x="0" y="{row_y}" width="400" height="20" fill="white" stroke="black" stroke-width="0.5"/>'
    svg += f'<text x="10" y="{row_y + 14}" font-size="9">{equip["tag"]}</text>'
    svg += f'<text x="60" y="{row_y + 14}" font-size="9">{equip["description"]}</text>'
    svg += f'<text x="200" y="{row_y + 14}" font-size="9">{equip["size"]}</text>'
    svg += f'<text x="300" y="{row_y + 14}" font-size="9">{equip["material"]}</text>'
    row_y += 20

svg += '</g>'
return svg
```

# Line list table format

def create_line_list_svg(line_list, x, y):
“”“Creates a line list table in SVG format”””
svg = f’<g transform="translate({x},{y})">’

```
# Table header
svg += '<rect x="0" y="0" width="500" height="25" fill="#cccccc" stroke="black" stroke-width="1"/>'
svg += '<text x="10" y="17" font-size="10" font-weight="bold">LINE NO.</text>'
svg += '<text x="100" y="17" font-size="10" font-weight="bold">FROM</text>'
svg += '<text x="200" y="17" font-size="10" font-weight="bold">TO</text>'
svg += '<text x="300" y="17" font-size="10" font-weight="bold">SIZE</text>'
svg += '<text x="350" y="17" font-size="10" font-weight="bold">SPEC</text>'
svg += '<text x="400" y="17" font-size="10" font-weight="bold">INSULATION</text>'

# Table rows
row_y = 25
for line in line_list:
    svg += f'<rect x="0" y="{row_y}" width="500" height="20" fill="white" stroke="black" stroke-width="0.5"/>'
    svg += f'<text x="10" y="{row_y + 14}" font-size="9">{line["number"]}</text>'
    svg += f'<text x="100" y="{row_y + 14}" font-size="9">{line["from"]}</text>'
    svg += f'<text x="200" y="{row_y + 14}" font-size="9">{line["to"]}</text>'
    svg += f'<text x="300" y="{row_y + 14}" font-size="9">{line["size"]}</text>'
    svg += f'<text x="350" y="{row_y + 14}" font-size="9">{line["spec"]}</text>'
    svg += f'<text x="400" y="{row_y + 14}" font-size="9">{line["insulation"]}</text>'
    row_y += 20

svg += '</g>'
return svg
```

# Annotation and dimension line functions

def create_dimension_line(x1, y1, x2, y2, text, offset=20):
“”“Creates a dimension line with text”””
# Calculate perpendicular offset
dx = x2 - x1
dy = y2 - y1
length = (dx**2 + dy**2)**0.5

```
if length == 0:
    return ""

# Normalize and rotate 90 degrees
nx = -dy / length * offset
ny = dx / length * offset

# Offset points
ox1, oy1 = x1 + nx, y1 + ny
ox2, oy2 = x2 + nx, y2 + ny

svg = f'<g class="dimension">'
# Extension lines
svg += f'<line x1="{x1}" y1="{y1}" x2="{ox1}" y2="{oy1}" stroke="black" stroke-width="0.5"/>'
svg += f'<line x1="{x2}" y1="{y2}" x2="{ox2}" y2="{oy2}" stroke="black" stroke-width="0.5"/>'
# Dimension line
svg += f'<line x1="{ox1}" y1="{oy1}" x2="{ox2}" y2="{oy2}" stroke="black" stroke-width="0.5"/>'
# Arrows
svg += f'<path d="M {ox1},{oy1} L {ox1+5},{oy1-3} L {ox1+5},{oy1+3} Z" fill="black"/>'
svg += f'<path d="M {ox2},{oy2} L {ox2-5},{oy2-3} L {ox2-5},{oy2+3} Z" fill="black"/>'
# Text
mid_x, mid_y = (ox1 + ox2) / 2, (oy1 + oy2) / 2
svg += f'<text x="{mid_x}" y="{mid_y - 3}" text-anchor="middle" font-size="10">{text}</text>'
svg += '</g>'

return svg
```

def create_equipment_tag_callout(x, y, tag, description):
“”“Creates a callout bubble for equipment tags”””
svg = f’<g class="callout">’
# Leader line
svg += f’<line x1="{x}" y1="{y}" x2="{x+30}" y2="{y-30}" stroke="black" stroke-width="0.5"/>’
# Callout box
box_width = max(100, len(description) * 6 + 20)
svg += f’<rect x="{x+30}" y="{y-45}" width="{box_width}" height="30" fill="white" stroke="black" stroke-width="1" rx="3"/>’
# Text
svg += f’<text x="{x+35}" y="{y-30}" font-size="10" font-weight="bold">{tag}</text>’
svg += f’<text x="{x+35}" y="{y-18}" font-size="8">{description}</text>’
svg += ‘</g>’

```
return svg
```
