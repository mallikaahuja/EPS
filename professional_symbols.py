"""
Professional ISA Symbol Library
Detailed, industry-standard P&ID symbols matching real engineering drawings
"""

# Professional ISA Symbols with accurate details

PROFESSIONAL_ISA_SYMBOLS = {
    # --- PUMPS ---
    'pump_centrifugal': '''<symbol id="pump_centrifugal" viewBox="0 0 80 80" preserveAspectRatio="xMidYMid meet">
    <circle cx="40" cy="40" r="35" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 40,15 Q 55,25 55,40 Q 55,55 40,65 Q 25,55 25,40 Q 25,25 40,15 Z" 
    fill="none" stroke="black" stroke-width="2"/>
    <circle cx="40" cy="40" r="4" fill="black"/>
    <rect x="0" y="35" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="35" y="0" width="10" height="15" fill="white" stroke="black" stroke-width="2"/>
    <path d="M 25,40 L 40,25" stroke="black" stroke-width="1.5" marker-end="url(#arrowhead)"/>
    </symbol>''',

    # --- VALVES ---
    'valve_gate': '''<symbol id="valve_gate" viewBox="0 0 60 80" preserveAspectRatio="xMidYMid meet">
    <rect x="10" y="30" width="40" height="30" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="25" y="35" width="10" height="20" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="28" y="10" width="4" height="25" fill="black"/>
    <circle cx="30" cy="10" r="8" fill="none" stroke="black" stroke-width="2"/>
    <path d="M 22,10 L 38,10 M 30,2 L 30,18" stroke="black" stroke-width="2"/>
    <rect x="0" y="40" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="50" y="40" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="5" cy="42" r="1" fill="black"/>
    <circle cx="5" cy="48" r="1" fill="black"/>
    <circle cx="55" cy="42" r="1" fill="black"/>
    <circle cx="55" cy="48" r="1" fill="black"/>
    </symbol>''',

    'valve_globe': '''<symbol id="valve_globe" viewBox="0 0 60 80" preserveAspectRatio="xMidYMid meet">
    <path d="M 10,45 Q 10,30 30,30 Q 50,30 50,45 Q 50,60 30,60 Q 10,60 10,45 Z" 
          fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="20" y1="40" x2="40" y2="50" stroke="black" stroke-width="2"/>
    <line x1="40" y1="40" x2="20" y2="50" stroke="black" stroke-width="2"/>
    <rect x="28" y="10" width="4" height="25" fill="black"/>
    <circle cx="30" cy="10" r="8" fill="none" stroke="black" stroke-width="2"/>
    <path d="M 22,10 L 38,10 M 30,2 L 30,18" stroke="black" stroke-width="2"/>
    <rect x="0" y="40" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="50" y="40" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    'valve_ball': '''<symbol id="valve_ball" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
    <rect x="10" y="20" width="40" height="20" fill="white" stroke="black" stroke-width="2.5"/>
    <circle cx="30" cy="30" r="8" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="30" cy="30" r="3" fill="black"/>
    <rect x="28" y="5" width="4" height="20" fill="black"/>
    <rect x="20" y="5" width="20" height="4" rx="2" fill="black"/>
    <rect x="0" y="25" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="50" y="25" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    'control_valve': '''<symbol id="control_valve" viewBox="0 0 60 100" preserveAspectRatio="xMidYMid meet">
    <path d="M 10,60 Q 10,45 30,45 Q 50,45 50,60 Q 50,75 30,75 Q 10,75 10,60 Z" 
          fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 20,55 L 30,65 L 40,55" fill="none" stroke="black" stroke-width="2"/>
    <rect x="15" y="15" width="30" height="30" rx="5" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 15,30 Q 30,25 45,30" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="28" y="30" width="4" height="20" fill="black"/>
    <circle cx="30" cy="10" r="3" fill="black"/>
    <line x1="30" y1="10" x2="30" y2="15" stroke="black" stroke-width="2"/>
    <rect x="0" y="55" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="50" y="55" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    # --- VESSELS ---
    'vessel_vertical': '''<symbol id="vessel_vertical" viewBox="0 0 100 160" preserveAspectRatio="xMidYMid meet">
    <path d="M 20,40 Q 20,20 50,20 Q 80,20 80,40" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="20" y="40" width="60" height="80" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 20,120 Q 20,140 50,140 Q 80,140 80,120" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 25,140 L 25,155 L 75,155 L 75,140" fill="none" stroke="black" stroke-width="2"/>
    <rect x="45" y="5" width="10" height="15" fill="white" stroke="black" stroke-width="2"/>
    <rect x="80" y="60" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="80" y="90" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="45" y="140" width="10" height="15" fill="white" stroke="black" stroke-width="2"/>
    <line x1="25" y1="80" x2="75" y2="80" stroke="black" stroke-width="1" stroke-dasharray="4,2" opacity="0.5"/>
    </symbol>''',

    'filter': '''<symbol id="filter" viewBox="0 0 80 120" preserveAspectRatio="xMidYMid meet">
    <path d="M 15,30 L 65,30 L 55,80 L 50,90 L 30,90 L 25,80 Z" 
          fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="20" y1="40" x2="60" y2="40" stroke="black" stroke-width="1.5"/>
    <line x1="22" y1="45" x2="58" y2="45" stroke="black" stroke-width="1.5"/>
    <line x1="24" y1="50" x2="56" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="26" y1="55" x2="54" y2="55" stroke="black" stroke-width="1.5"/>
    <line x1="28" y1="60" x2="52" y2="60" stroke="black" stroke-width="1.5"/>
    <line x1="30" y1="65" x2="50" y2="65" stroke="black" stroke-width="1.5"/>
    <path d="M 25,40 L 35,50 M 30,40 L 40,50 M 35,40 L 45,50 M 40,40 L 50,50 M 45,40 L 55,50" 
          stroke="black" stroke-width="0.5" opacity="0.5"/>
    <rect x="35" y="10" width="10" height="20" fill="white" stroke="black" stroke-width="2"/>
    <rect x="30" y="10" width="20" height="5" fill="white" stroke="black" stroke-width="2"/>
    <rect x="35" y="90" width="10" height="20" fill="white" stroke="black" stroke-width="2"/>
    <rect x="30" y="105" width="20" height="5" fill="white" stroke="black" stroke-width="2"/>
    <rect x="25" y="85" width="8" height="8" fill="white" stroke="black" stroke-width="1.5"/>
    </symbol>''',

    # --- INSTRUMENTS (Enhanced) ---
    'pressure_gauge': '''<symbol id="pressure_gauge" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
    <circle cx="30" cy="30" r="25" fill="white" stroke="black" stroke-width="2.5"/>
    <circle cx="30" cy="30" r="20" fill="white" stroke="black" stroke-width="1"/>
    <line x1="30" y1="30" x2="30" y2="15" stroke="black" stroke-width="2" transform="rotate(45 30 30)"/>
    <circle cx="30" cy="30" r="3" fill="black"/>
    <rect x="27" y="50" width="6" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    'temperature_gauge': '''<symbol id="temperature_gauge" viewBox="0 0 60 80" preserveAspectRatio="xMidYMid meet">
    <circle cx="30" cy="60" r="10" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="25" y="20" width="10" height="40" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 25,20 Q 30,15 35,20" fill="white" stroke="black" stroke-width="2.5"/>
    <circle cx="30" cy="60" r="6" fill="gray"/>
    <rect x="27" y="35" width="6" height="25" fill="gray"/>
    <line x1="20" y1="30" x2="25" y2="30" stroke="black" stroke-width="1"/>
    <line x1="20" y1="40" x2="25" y2="40" stroke="black" stroke-width="1"/>
    <line x1="20" y1="50" x2="25" y2="50" stroke="black" stroke-width="1"/>
    </symbol>''',

    # --- ELECTRICAL ---
    'motor': '''<symbol id="motor" viewBox="0 0 80 80" preserveAspectRatio="xMidYMid meet">
    <circle cx="40" cy="40" r="30" fill="white" stroke="black" stroke-width="2.5"/>
    <text x="40" y="48" text-anchor="middle" font-size="24" font-weight="bold" font-family="Arial">M</text>
    <rect x="35" y="5" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="20" y="65" width="40" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    'control_panel': '''<symbol id="control_panel" viewBox="0 0 120 160" preserveAspectRatio="xMidYMid meet">
    <rect x="10" y="10" width="100" height="140" rx="5" fill="white" stroke="black" stroke-width="3"/>
    <rect x="20" y="20" width="80" height="120" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="25" y="25" width="70" height="20" fill="none" stroke="black" stroke-width="1"/>
    <text x="60" y="38" text-anchor="middle" font-size="10" font-family="Arial">CONTROL PANEL</text>
    <circle cx="35" cy="60" r="5" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="50" cy="60" r="5" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="65" cy="60" r="5" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="80" cy="60" r="5" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="30" y="80" width="15" height="20" rx="2" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="50" y="80" width="15" height="20" rx="2" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="70" y="80" width="15" height="20" rx="2" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="25" y="110" width="70" height="25" fill="none" stroke="black" stroke-width="1"/>
    <line x1="25" y1="120" x2="95" y2="120" stroke="black" stroke-width="0.5"/>
    <line x1="35" y1="110" x2="35" y2="135" stroke="black" stroke-width="0.5"/>
    <line x1="45" y1="110" x2="45" y2="135" stroke="black" stroke-width="0.5"/>
    <line x1="55" y1="110" x2="55" y2="135" stroke="black" stroke-width="0.5"/>
    <line x1="65" y1="110" x2="65" y2="135" stroke="black" stroke-width="0.5"/>
    <line x1="75" y1="110" x2="75" y2="135" stroke="black" stroke-width="0.5"/>
    <line x1="85" y1="110" x2="85" y2="135" stroke="black" stroke-width="0.5"/>
    </symbol>''',

    # --- PIPING COMPONENTS ---
    'flange': '''<symbol id="flange" viewBox="0 0 30 20" preserveAspectRatio="xMidYMid meet">
    <rect x="0" y="5" width="30" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    <circle cx="5" cy="7" r="1" fill="black"/>
    <circle cx="5" cy="13" r="1" fill="black"/>
    <circle cx="25" cy="7" r="1" fill="black"/>
    <circle cx="25" cy="13" r="1" fill="black"/>
    </symbol>''',

    'reducer': '''<symbol id="reducer" viewBox="0 0 60 40" preserveAspectRatio="xMidYMid meet">
    <path d="M 0,5 L 20,5 L 40,15 L 60,15 L 60,25 L 40,25 L 20,35 L 0,35 Z" 
          fill="white" stroke="black" stroke-width="2.5"/>
    </symbol>''',

    'pipe_tee': '''<symbol id="pipe_tee" viewBox="0 0 60 60" preserveAspectRatio="xMidYMid meet">
    <rect x="0" y="20" width="60" height="20" fill="white" stroke="black" stroke-width="2.5"/>
    <rect x="20" y="0" width="20" height="40" fill="white" stroke="black" stroke-width="2.5"/>
    </symbol>''',

    'pipe_elbow': '''<symbol id="pipe_elbow" viewBox="0 0 40 40" preserveAspectRatio="xMidYMid meet">
    <path d="M 0,15 L 15,15 Q 25,15 25,25 L 25,40" 
          fill="none" stroke="black" stroke-width="10" stroke-linejoin="round"/>
    <path d="M 0,15 L 15,15 Q 25,15 25,25 L 25,40" 
          fill="none" stroke="white" stroke-width="7" stroke-linejoin="round"/>
    </symbol>''',
}

# Arrow marker definitions for flow direction

ARROW_MARKERS = '''
<defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
    <polygon points="0,0 10,5 0,10" fill="black"/>
    </marker>

    <marker id="arrowhead-large" markerWidth="15" markerHeight="15" refX="14" refY="7.5" orient="auto">
        <polygon points="0,0 15,7.5 0,15" fill="black"/>
    </marker>
    
    <marker id="arrowhead-signal" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
        <polygon points="0,0 10,5 0,10" fill="none" stroke="black" stroke-width="1"/>
    </marker>
</defs>
'''

def get_component_symbol(component_type: str) -> str:
    """
    Returns the appropriate symbol SVG for a component type
    """
    # Map common variations to standard symbols
    type_mapping = {
        'centrifugal_pump': 'pump_centrifugal',
        'pump': 'pump_centrifugal',
        'gate_valve': 'valve_gate',
        'globe_valve': 'valve_globe',
        'ball_valve': 'valve_ball',
        'control_valve': 'control_valve',
        'vessel': 'vessel_vertical',
        'column': 'vessel_vertical',
        'tank': 'vessel_vertical',
        'filter': 'filter',
        'strainer': 'filter',
        'motor': 'motor',
        'control_panel': 'control_panel',
        'panel': 'control_panel',
    }

    normalized_type = component_type.lower().replace('-', '_').replace(' ', '_')
    mapped_type = type_mapping.get(normalized_type, normalized_type)

    return PROFESSIONAL_ISA_SYMBOLS.get(mapped_type, '')


def create_professional_instrument_bubble(tag: str, x: float, y: float, size: float = 25) -> str:
    """
    Creates a professional instrument bubble with proper ISA formatting
    """
    import re

    # Parse instrument tag
    match = re.match(r'^([A-Z]+)[-]?(\d+)([A-Z]?)$', tag)
    if not match:
        return f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2"/>'

    letters = match.group(1)
    number = match.group(2)
    suffix = match.group(3)

    # Determine if local panel (L prefix) or field mounted
    is_local = letters.startswith('L')
    if is_local:
        letters = letters[1:]  # Remove L prefix

    # Create SVG
    svg = f'<g class="instrument-{tag}">'

    # Main circle
    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    # Add horizontal line for field-mounted instruments
    if not is_local:
        svg += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" stroke="black" stroke-width="2.5"/>'

    # Add box for panel-mounted instruments
    if 'C' in letters or 'I' in letters:  # Controller or Indicator
        box_size = size * 0.7
        svg += f'<rect x="{x-box_size}" y="{y-box_size}" width="{box_size*2}" height="{box_size*2}" '
        svg += f'fill="none" stroke="black" stroke-width="1.5" stroke-dasharray="3,3"/>'

    # Text positioning
    text_size = size * 0.5
    y_offset = size * 0.15

    # Tag letters (function)
    svg += f'<text x="{x}" y="{y-y_offset}" text-anchor="middle" '
    svg += f'font-size="{text_size}" font-weight="bold" font-family="Arial, sans-serif">{letters}</text>'

    # Tag number
    svg += f'<text x="{x}" y="{y+text_size*0.7}" text-anchor="middle" '
    svg += f'font-size="{text_size*0.8}" font-family="Arial, sans-serif">{number}{suffix}</text>'

    svg += '</g>'
    return svg


def create_pipe_with_spec(points: list, pipe_spec: str, line_type: str = 'process') -> str:
    """
    Creates a pipe with specification label
    Example spec: "2"-PG-101-CS" means 2 inch, Process Gas, Line 101, Carbon Steel
    """
    if len(points) < 2:
        return ''

    # Line styles based on type
    line_styles = {
        'process': {'width': 3, 'color': 'black', 'dash': ''},
        'utility': {'width': 2.5, 'color': 'black', 'dash': ''},
        'instrument': {'width': 1, 'color': 'black', 'dash': '5,3'},
        'electrical': {'width': 1, 'color': 'black', 'dash': '2,2'},
    }

    style = line_styles.get(line_type, line_styles['process'])

    # Create path
    path_d = f"M {points[0][0]},{points[0][1]}"
    for point in points[1:]:
        path_d += f" L {point[0]},{point[1]}"

    svg = '<g class="pipe">'

    # Main pipe line
    svg += f'<path d="{path_d}" fill="none" stroke="{style["color"]}" '
    svg += f'stroke-width="{style["width"]}"'
    if style['dash']:
        svg += f' stroke-dasharray="{style["dash"]}"'
    svg += '/>'

    # Add specification label if provided
    if pipe_spec and len(points) >= 2:
        # Calculate midpoint
        mid_idx = len(points) // 2
        mid_x = (points[mid_idx-1][0] + points[mid_idx][0]) / 2
        mid_y = (points[mid_idx-1][1] + points[mid_idx][1]) / 2
        
        # Label background
        text_width = len(pipe_spec) * 8
        svg += f'<rect x="{mid_x - text_width/2}" y="{mid_y - 12}" '
        svg += f'width="{text_width}" height="20" fill="white" stroke="none"/>'
        
        # Label text
        svg += f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" '
        svg += f'font-size="10" font-family="Arial, sans-serif">{pipe_spec}</text>'

    svg += '</g>'
    return svg
