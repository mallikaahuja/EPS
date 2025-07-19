I can definitely help you with that! It looks like you have a mix of smart quotes (“”, ’’) and some indentation issues, especially with the multi-line SVG strings. Python requires standard straight double quotes (") or single quotes (') for string literals, and """ or ''' for multiline strings (docstrings and other multi-line content).
Here's the corrected code with all quotes standardized to " or ''' and consistent indentation.
"""
Professional ISA Symbol Library - Fixed Version
Includes all symbols for the vacuum system P&ID
"""

import re

PROFESSIONAL_ISA_SYMBOLS = {
    # --- EXPANSION BELLOWS ---
    "EB-001": '''
<rect x="10" y="35" width="60" height="10" fill="white" stroke="black" stroke-width="2"/>
<path d="M 15,30 Q 20,25 25,30 Q 30,35 35,30 Q 40,25 45,30 Q 50,35 55,30 Q 60,25 65,30" 
fill="none" stroke="black" stroke-width="2.5"/>
<path d="M 15,50 Q 20,55 25,50 Q 30,45 35,50 Q 40,55 45,50 Q 50,45 55,50 Q 60,55 65,50" 
fill="none" stroke="black" stroke-width="2.5"/>
<line x1="15" y1="30" x2="15" y2="50" stroke="black" stroke-width="2.5"/>
<line x1="65" y1="30" x2="65" y2="50" stroke="black" stroke-width="2.5"/>
''',

    # --- ELECTRICALLY HEATED PANEL BOX ---
    "EPB-001": '''
    <rect x="10" y="10" width="60" height="60" rx="5" fill="white" stroke="black" stroke-width="3"/>
    <rect x="15" y="15" width="50" height="50" fill="none" stroke="black" stroke-width="1.5"/>
    <text x="40" y="30" font-size="8" text-anchor="middle" font-family="Arial" font-weight="bold">FLP</text>
    <text x="40" y="45" font-size="8" text-anchor="middle" font-family="Arial" font-weight="bold">NFLP</text>
    <circle cx="25" cy="55" r="3" fill="none" stroke="black" stroke-width="1"/>
    <circle cx="40" cy="55" r="3" fill="none" stroke="black" stroke-width="1"/>
    <circle cx="55" cy="55" r="3" fill="none" stroke="black" stroke-width="1"/>
    <path d="M 20,60 Q 25,58 30,60 Q 35,62 40,60 Q 45,58 50,60 Q 55,62 60,60" stroke="red" stroke-width="1.5" fill="none"/>
''',

    # --- FLAME ARRESTOR ---
    "FA-001": '''
    <rect x="15" y="30" width="50" height="20" fill="white" stroke="black" stroke-width="3"/>
    <line x1="25" y1="30" x2="25" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="30" y1="30" x2="30" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="35" y1="30" x2="35" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="40" y1="30" x2="40" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="45" y1="30" x2="45" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="50" y1="30" x2="50" y2="50" stroke="black" stroke-width="1.5"/>
    <line x1="55" y1="30" x2="55" y2="50" stroke="black" stroke-width="1.5"/>
    <polygon points="38,25 40,20 42,25" fill="orange" stroke="black" stroke-width="1"/>
''',

    # --- VAPOR CONDENSER WITH INTEGRATED CATCHPOT ---
    "C-001": '''
    <rect x="20" y="10" width="40" height="50" stroke="black" stroke-width="2" fill="white"/>
    <polyline points="25,15 35,25 25,35 35,45 25,55" stroke="black" stroke-width="2" fill="none"/>
    <polyline points="55,15 45,25 55,35 45,45 55,55" stroke="black" stroke-width="2" fill="none"/>
    <ellipse cx="40" cy="65" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
    <rect x="20" y="65" width="40" height="10" stroke="black" stroke-width="2" fill="white"/>
    <ellipse cx="40" cy="75" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
    <line x1="30" y1="70" x2="50" y2="70" stroke="black" stroke-width="1" stroke-dasharray="2,2"/>
''',

    # --- ACG (ACTIVATED CARBON) FILTER ---
    "ACG-001": '''
    <rect x="25" y="10" width="30" height="60" rx="15" stroke="black" stroke-width="2.5" fill="white"/>
    <circle cx="40" cy="25" r="2" fill="black"/>
    <circle cx="35" cy="30" r="2" fill="black"/>
    <circle cx="45" cy="30" r="2" fill="black"/>
    <circle cx="40" cy="35" r="2" fill="black"/>
    <circle cx="35" cy="40" r="2" fill="black"/>
    <circle cx="45" cy="40" r="2" fill="black"/>
    <circle cx="40" cy="45" r="2" fill="black"/>
    <circle cx="35" cy="50" r="2" fill="black"/>
    <circle cx="45" cy="50" r="2" fill="black"/>
    <circle cx="40" cy="55" r="2" fill="black"/>
    <text x="40" y="5" font-size="8" text-anchor="middle" font-family="Arial">ACG</text>
''',

    # --- SUCTION FILTER ---
    "SF-001": '''
    <path d="M 25,20 L 55,20 L 50,50 L 48,65 L 32,65 L 30,50 Z" 
          fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="28" y1="25" x2="52" y2="25" stroke="black" stroke-width="1.5"/>
    <line x1="29" y1="30" x2="51" y2="30" stroke="black" stroke-width="1.5"/>
    <line x1="30" y1="35" x2="50" y2="35" stroke="black" stroke-width="1.5"/>
    <line x1="31" y1="40" x2="49" y2="40" stroke="black" stroke-width="1.5"/>
    <line x1="32" y1="45" x2="48" y2="45" stroke="black" stroke-width="1.5"/>
    <path d="M 30,25 L 40,35 M 35,25 L 45,35 M 40,25 L 50,35 M 45,25 L 52,32" 
          stroke="black" stroke-width="0.5"/>
    <rect x="35" y="10" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="35" y="65" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

    # --- KDP-330 DRY SCREW VACUUM PUMP ---
    "P-001": '''
    <circle cx="40" cy="40" r="30" fill="white" stroke="black" stroke-width="3"/>
    <path d="M 40,10 Q 55,20 60,40 Q 55,60 40,70 Q 25,60 20,40 Q 25,20 40,10" 
          fill="none" stroke="black" stroke-width="2.5"/>
    <circle cx="40" cy="40" r="5" fill="black"/>
    <rect x="10" y="35" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="55" y="35" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <text x="40" y="40" font-size="8" text-anchor="middle" font-family="Arial" fill="white">KDP</text>
    <line x1="20" y1="65" x2="60" y2="65" stroke="black" stroke-width="2"/>
    <line x1="20" y1="65" x2="20" y2="70" stroke="black" stroke-width="2"/>
    <line x1="60" y1="65" x2="60" y2="70" stroke="black" stroke-width="2"/>
''',

    # --- DISCHARGE SILENCER ---
    "SIL-001": '''
    <ellipse cx="40" cy="40" rx="25" ry="12" stroke="black" stroke-width="2.5" fill="white"/>
    <path d="M15,40 Q40,25 65,40" stroke="black" stroke-width="2" fill="none"/>
    <path d="M20,35 Q20,30 25,30 M25,30 Q30,30 30,35" stroke="black" stroke-width="1" fill="none"/>
    <path d="M50,35 Q50,30 55,30 M55,30 Q60,30 60,35" stroke="black" stroke-width="1" fill="none"/>
    <rect x="10" y="35" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="60" y="35" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

    # --- POST-PUMP CONDENSER WITH CATCHPOT ---
    "C-002": '''
    <rect x="20" y="10" width="40" height="50" stroke="black" stroke-width="2" fill="white"/>
    <polyline points="25,15 35,25 25,35 35,45 25,55" stroke="black" stroke-width="2" fill="none"/>
    <polyline points="55,15 45,25 55,35 45,45 55,55" stroke="black" stroke-width="2" fill="none"/>
    <ellipse cx="40" cy="65" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
    <rect x="20" y="65" width="40" height="10" stroke="black" stroke-width="2" fill="white"/>
    <ellipse cx="40" cy="75" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
    <line x1="30" y1="70" x2="50" y2="70" stroke="black" stroke-width="1" stroke-dasharray="2,2"/>
''',

    # --- DISCHARGE SCRUBBER ---
    "SCR-001": '''
    <rect x="25" y="10" width="30" height="60" rx="15" stroke="black" stroke-width="2.5" fill="white"/>
    <line x1="25" y1="25" x2="55" y2="25" stroke="black" stroke-width="1.5"/>
    <line x1="25" y1="35" x2="55" y2="35" stroke="black" stroke-width="1.5"/>
    <line x1="25" y1="45" x2="55" y2="45" stroke="black" stroke-width="1.5"/>
    <line x1="25" y1="55" x2="55" y2="55" stroke="black" stroke-width="1.5"/>
    <circle cx="30" cy="30" r="2" fill="black"/>
    <circle cx="50" cy="30" r="2" fill="black"/>
    <circle cx="35" cy="40" r="2" fill="black"/>
    <circle cx="45" cy="40" r="2" fill="black"/>
    <circle cx="30" cy="50" r="2" fill="black"/>
    <circle cx="50" cy="50" r="2" fill="black"/>
''',

    # --- CONTROL PANEL ---
    "CP-001": '''
    <rect x="5" y="5" width="70" height="70" rx="5" fill="white" stroke="black" stroke-width="3"/>
    <rect x="10" y="10" width="60" height="60" fill="none" stroke="black" stroke-width="2"/>
    <rect x="15" y="15" width="25" height="20" fill="#e0e0e0" stroke="black" stroke-width="1.5"/>
    <text x="27" y="28" text-anchor="middle" font-size="8" font-family="Arial">HMI</text>
    <rect x="45" y="15" width="20" height="20" fill="#e0e0e0" stroke="black" stroke-width="1.5"/>
    <text x="55" y="28" text-anchor="middle" font-size="8" font-family="Arial">VFD</text>
    <circle cx="20" cy="45" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="30" cy="45" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="40" cy="45" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="50" cy="45" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <circle cx="60" cy="45" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <rect x="15" y="55" width="10" height="10" rx="2" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="30" y="55" width="10" height="10" rx="2" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="45" y="55" width="10" height="10" rx="2" fill="white" stroke="black" stroke-width="1.5"/>
    <rect x="60" y="55" width="5" height="10" rx="2" fill="white" stroke="black" stroke-width="1.5"/>
''',

    # --- COOLING TOWER ---
    "CT-001": '''
    <rect x="15" y="20" width="50" height="40" stroke="black" stroke-width="2.5" fill="white"/>
    <path d="M 15,20 L 25,10 L 55,10 L 65,20" stroke="black" stroke-width="2.5" fill="none"/>
    <circle cx="40" cy="15" r="8" stroke="black" stroke-width="2" fill="white"/>
    <path d="M 35,12 L 40,15 L 35,18 M 40,12 L 45,15 L 40,18 M 45,12 L 50,15 L 45,18" stroke="black" stroke-width="1" fill="none"/>
    <line x1="20" y1="30" x2="60" y2="30" stroke="black" stroke-width="1"/>
    <line x1="20" y1="40" x2="60" y2="40" stroke="black" stroke-width="1"/>
    <line x1="20" y1="50" x2="60" y2="50" stroke="black" stroke-width="1"/>
    <path d="M 25,35 L 25,55 M 35,35 L 35,55 M 45,35 L 45,55 M 55,35 L 55,55" stroke="blue" stroke-width="1" stroke-dasharray="2,2"/>
''',

    # --- CENTRIFUGAL PUMP (WATER) ---
    "WP-001": '''
    <circle cx="40" cy="40" r="20" fill="white" stroke="black" stroke-width="2.5"/>
    <path d="M 40,20 Q 50,30 50,40 Q 50,50 40,60 Q 30,50 30,40 Q 30,30 40,20" 
          fill="none" stroke="black" stroke-width="2"/>
    <rect x="15" y="35" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="55" y="35" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

    # --- VALVES ---
    "gate_valve": '''
    <rect x="25" y="35" width="30" height="10" fill="white" stroke="black" stroke-width="2"/>
    <line x1="40" y1="35" x2="40" y2="20" stroke="black" stroke-width="2"/>
    <circle cx="40" cy="18" r="4" fill="none" stroke="black" stroke-width="1.5"/>
    <line x1="20" y1="40" x2="25" y2="40" stroke="black" stroke-width="2"/>
    <line x1="55" y1="40" x2="60" y2="40" stroke="black" stroke-width="2"/>
''',

    "check_valve": '''
    <circle cx="40" cy="40" r="15" fill="white" stroke="black" stroke-width="2"/>
    <line x1="40" y1="25" x2="40" y2="55" stroke="black" stroke-width="2"/>
    <polygon points="35,35 45,40 35,45" fill="black"/>
''',

    "solenoid_valve": '''
    <rect x="25" y="35" width="30" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="35" y="20" width="10" height="15" rx="2" fill="white" stroke="black" stroke-width="2"/>
    <line x1="37" y1="25" x2="43" y2="25" stroke="black" stroke-width="1"/>
    <line x1="37" y1="28" x2="43" y2="28" stroke="black" stroke-width="1"/>
    <line x1="37" y1="31" x2="43" y2="31" stroke="black" stroke-width="1"/>
    <circle cx="40" cy="15" r="2" fill="black"/>
    <line x1="40" y1="17" x2="40" y2="20" stroke="black" stroke-width="1.5"/>
''',

    # --- INSTRUMENTS ---
    "pressure_transmitter": '''
    <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
    <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">PT</text>
    <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
    <rect x="38" y="58" width="4" height="10" fill="black"/>
''',

    "temperature_transmitter": '''
    <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
    <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">TT</text>
    <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
    <rect x="38" y="58" width="4" height="10" fill="black"/>
''',

    "flow_transmitter": '''
    <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
    <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">FT</text>
    <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
    <rect x="38" y="58" width="4" height="10" fill="black"/>
''',

    "level_switch": '''
    <rect x="25" y="25" width="30" height="30" fill="white" stroke="black" stroke-width="2.5"/>
    <text x="40" y="35" font-size="11" text-anchor="middle" font-weight="bold" font-family="Arial">LS</text>
    <text x="40" y="47" font-size="9" text-anchor="middle" font-family="Arial">001</text>
''',

    # --- DRAIN POINT ---
    "DP-001": '''
    <polygon points="40,20 55,50 25,50" fill="white" stroke="black" stroke-width="2.5"/>
    <line x1="40" y1="50" x2="40" y2="60" stroke="black" stroke-width="2"/>
    <line x1="35" y1="60" x2="45" y2="60" stroke="black" stroke-width="2"/>
    <line x1="37" y1="63" x2="43" y2="63" stroke="black" stroke-width="1.5"/>
    <line x1="39" y1="66" x2="41" y2="66" stroke="black" stroke-width="1"/>
''',

    # --- MOTOR ---
    "MV-001": '''
    <circle cx="40" cy="40" r="25" fill="white" stroke="black" stroke-width="3"/>
    <text x="40" y="40" font-size="14" text-anchor="middle" font-weight="bold" font-family="Arial">M</text>
    <rect x="35" y="65" width="10" height="10" fill="white" stroke="black" stroke-width="2"/>
''',

    # --- DEFAULT/FALLBACK SYMBOLS ---
    "default": '''
    <rect x="20" y="20" width="40" height="40" rx="5" fill="white" stroke="black" stroke-width="2"/>
    <text x="40" y="45" font-size="10" text-anchor="middle" font-family="Arial">?</text>
'''
}

# Standard arrowhead marker for pipes
ARROWHEAD_MARKER = '''
<marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
<path d="M 0 0 L 10 5 L 0 10 z" fill="black" stroke="black"/>
</marker>
'''

def get_component_symbol(component_id, target_width=None, target_height=None):
    """
    Returns a valid SVG string for the requested ISA symbol.
    Falls back to component type-based lookup if specific ID not found.
    """
    # Default viewBox for internal symbol definitions
    default_viewbox = "0 0 80 80"

    # Try to get symbol by specific ID first
    svg_inner = PROFESSIONAL_ISA_SYMBOLS.get(component_id)

    # If not found by ID, try by type
    if svg_inner is None:
        # Extract base type from ID (e.g., "PT-001" -> "pressure_transmitter")
        component_type = None
        
        if '-' in component_id:
            prefix = component_id.split('-')[0].upper()
            type_mapping = {
                'PT': 'pressure_transmitter',
                'TT': 'temperature_transmitter',
                'FT': 'flow_transmitter',
                'LS': 'level_switch',
                'V': 'gate_valve',
                'SV': 'solenoid_valve',
                'NRV': 'check_valve',
                'DP': 'DP-001',
                'CP': 'CP-001',
                'SCR': 'SCR-001',
                'SIL': 'SIL-001',
                'C': 'C-001',  # Condenser
                'P': 'P-001',   # Pump
                'SF': 'SF-001', # Suction Filter
                'ACG': 'ACG-001',
                'FA': 'FA-001',
                'EB': 'EB-001',
                'EPB': 'EPB-001',
                'WP': 'WP-001',
                'CT': 'CT-001',
                'MV': 'MV-001'
            }
            component_type = type_mapping.get(prefix)
            
        if component_type:
            svg_inner = PROFESSIONAL_ISA_SYMBOLS.get(component_type)

    # Final fallback to default symbol
    if svg_inner is None:
        svg_inner = PROFESSIONAL_ISA_SYMBOLS['default']

    # Use target dimensions if provided
    final_width = target_width if target_width is not None else 80
    final_height = target_height if target_height is not None else 80

    svg = (
        f'<svg width="{final_width}" height="{final_height}" viewBox="{default_viewbox}" '
        f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'{svg_inner}'
        f'</svg>'
    )
    return svg

def get_component_symbol_from_type(component_type: str) -> str:
    """
    Returns the raw SVG content for a component type.
    """
    # Normalize type name
    normalized_type = component_type.lower().replace('-', '_').replace(' ', '_')

    # Try direct lookup
    if normalized_type in PROFESSIONAL_ISA_SYMBOLS:
        return PROFESSIONAL_ISA_SYMBOLS[normalized_type]

    # Try to find a matching symbol
    for key in PROFESSIONAL_ISA_SYMBOLS:
        if normalized_type in key.lower() or key.lower() in normalized_type:
            return PROFESSIONAL_ISA_SYMBOLS[key]

    # Return default if not found
    return PROFESSIONAL_ISA_SYMBOLS['default']

def create_professional_instrument_bubble(tag: str, x: float, y: float, size: float = 25) -> str:
    """
    Creates a professional instrument bubble with ISA formatting.
    """
    # Parse instrument tag
    match = re.match(r'^([A-Z]+)[-]?(\d+)([A-Z]?)$', tag)

    if not match:
        # Simple circle for non-standard tags
        return f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    letters = match.group(1)
    number = match.group(2)
    suffix = match.group(3)

    # Determine mounting type
    is_local_mounted = letters.startswith('L')
    if is_local_mounted:
        letters = letters[1:]

    # Create SVG group
    svg = f'<g class="instrument-{tag}">'

    # Main circle
    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    # Add horizontal line for field-mounted instruments
    if not is_local_mounted:
        svg += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" stroke="black" stroke-width="2.5"/>'

    # Text positioning
    text_size_letters = size * 0.5
    text_size_number = size * 0.4

    # Tag letters (top)
    svg += f'<text x="{x}" y="{y - size * 0.2}" text-anchor="middle" '
    svg += f'font-size="{text_size_letters}" font-weight="bold" font-family="Arial, sans-serif">{letters}</text>'

    # Tag number (bottom)
    svg += f'<text x="{x}" y="{y + size * 0.3}" text-anchor="middle" '
    svg += f'font-size="{text_size_number}" font-family="Arial, sans-serif">{number}</text>'

    svg += '</g>'
    return svg

