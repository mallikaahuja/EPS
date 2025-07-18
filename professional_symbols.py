"""
Professional ISA Symbol Library
Detailed, industry-standard P&ID symbols matching real engineering drawings
"""

# Professional ISA Symbols with accurate details

PROFESSIONAL_ISA_SYMBOLS = {
    "kdp_330_pump": '''
        <rect x="20" y="20" width="40" height="30" rx="8" stroke="black" stroke-width="2" fill="none"/>
        <text x="40" y="38" font-size="14" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">KDP</text>
        <circle cx="22" cy="35" r="4" stroke="black" fill="white"/>
        <circle cx="58" cy="35" r="4" stroke="black" fill="white"/>
        <rect x="12" y="31" width="8" height="8" rx="2" stroke="black" fill="white"/>
        <rect x="60" y="31" width="8" height="8" rx="2" stroke="black" fill="white"/>
    ''',

    "motor_10hp_2pole_b5": '''
        <rect x="25" y="25" width="30" height="20" stroke="black" stroke-width="2" fill="none"/>
        <rect x="25" y="20" width="30" height="5" stroke="black" fill="white"/>
        <text x="40" y="38" font-size="10" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">10HP</text>
        <line x1="25" y1="45" x2="55" y2="45" stroke="black" stroke-width="2"/>
    ''',

    "vfd": '''
        <rect x="28" y="20" width="24" height="40" stroke="black" stroke-width="2" fill="none"/>
        <rect x="30" y="22" width="20" height="8" fill="white" stroke="black"/>
        <circle cx="40" cy="42" r="3" stroke="black" fill="white"/>
        <text x="40" y="54" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">VFD</text>
    ''',

    "epo_valve": '''
        <circle cx="40" cy="40" r="13" stroke="black" stroke-width="2" fill="none"/>
        <text x="40" y="45" font-size="11" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">EPO</text>
        <line x1="40" y1="53" x2="60" y2="53" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
        <rect x="60" y="50" width="8" height="6" stroke="black" fill="white"/>
    ''',

    "n2_purge_assembly": '''
        <ellipse cx="30" cy="40" rx="12" ry="7" stroke="black" fill="white"/>
        <text x="30" y="44" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">N2</text>
        <rect x="42" y="36" width="10" height="8" rx="3" stroke="black" fill="white"/>
        <polygon points="52,40 62,38 62,42" fill="white" stroke="black"/>
    ''',

    "liquid_flushing_assembly": '''
        <polygon points="30,40 35,30 40,40" fill="white" stroke="black"/>
        <rect x="42" y="34" width="8" height="12" stroke="black" fill="white"/>
        <polygon points="55,40 65,38 65,42" fill="white" stroke="black"/>
    ''',

    "suction_condenser": '''
        <rect x="34" y="22" width="12" height="36" stroke="black" fill="white"/>
        <polyline points="36,26 44,30 36,34 44,38 36,42 44,46" stroke="black" fill="none"/>
        <text x="40" y="40" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Condenser</text>
    ''',

    "catch_pot_manual_drain": '''
        <ellipse cx="40" cy="28" rx="13" ry="7" stroke="black" fill="white"/>
        <rect x="27" y="28" width="26" height="30" stroke="black" fill="none"/>
        <polygon points="40,58 37,65 43,65" fill="white" stroke="black"/>
        <rect x="36" y="65" width="8" height="7" stroke="black" fill="white"/>
        <line x1="40" y1="58" x2="40" y2="72" stroke="black"/>
    ''',
    "catch_pot_auto_drain": '''
        <ellipse cx="40" cy="28" rx="13" ry="7" stroke="black" fill="white"/>
        <rect x="27" y="28" width="26" height="30" stroke="black" fill="none"/>
        <polygon points="40,58 37,65 43,65" fill="white" stroke="black"/>
        <circle cx="40" cy="71" r="5" stroke="black" fill="white"/>
        <line x1="40" y1="58" x2="40" y2="76" stroke="black"/>
    ''',

    "suction_filter": '''
        <rect x="24" y="24" width="32" height="32" stroke="black" fill="white"/>
        <line x1="26" y1="26" x2="54" y2="54" stroke="black" stroke-width="1"/>
        <line x1="54" y1="26" x2="26" y2="54" stroke="black" stroke-width="1"/>
        <text x="40" y="48" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Suction Filter</text>
    ''',

    "scrubber": '''
        <rect x="32" y="15" width="16" height="50" rx="8" stroke="black" fill="white"/>
        <line x1="32" y1="28" x2="48" y2="28" stroke="black"/>
        <line x1="32" y1="38" x2="48" y2="38" stroke="black"/>
        <line x1="32" y1="48" x2="48" y2="48" stroke="black"/>
        <text x="40" y="70" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Scrubber</text>
    ''',

    "flame_arrestor_suction": '''
        <rect x="30" y="32" width="20" height="16" stroke="black" fill="white"/>
        <polygon points="38,36 40,42 42,36 44,42 46,36" fill="none" stroke="black"/>
        <polyline points="30,40 20,40" stroke="black"/>
        <polyline points="50,40 60,40" stroke="black"/>
        <text x="40" y="60" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Flame</text>
        <polygon points="62,37 65,40 62,43" fill="black"/>
    ''',

    "flame_arrestor_discharge": '''
        <rect x="30" y="32" width="20" height="16" stroke="black" fill="white"/>
        <polygon points="38,36 40,42 42,36 44,42 46,36" fill="none" stroke="black"/>
        <polyline points="30,40 20,40" stroke="black"/>
        <polyline points="50,40 60,40" stroke="black"/>
        <text x="40" y="60" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Flame</text>
        <polygon points="18,37 15,40 18,43" fill="black"/>
    ''',

    "flex_conn_suction": '''
        <path d="M20,40 Q30,35 40,45 Q50,55 60,40" stroke="black" fill="none"/>
        <text x="40" y="60" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Flex Conn (Suction)</text>
    ''',

    "flex_conn_discharge": '''
        <path d="M20,40 Q30,45 40,35 Q50,25 60,40" stroke="black" fill="none"/>
        <text x="40" y="60" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Flex Conn (Discharge)</text>
    ''',

    "pressure_transmitter_discharge": '''
        <circle cx="40" cy="40" r="12" stroke="black" stroke-width="2" fill="white"/>
        <text x="40" y="44" font-size="10" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">PT</text>
        <line x1="40" y1="52" x2="60" y2="60" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
        <rect x="60" y="57" width="10" height="6" stroke="black" fill="white"/>
    ''',

    "discharge_condenser": '''
        <rect x="20" y="34" width="40" height="12" stroke="black" fill="white"/>
        <polyline points="22,36 38,44 54,36" stroke="black" fill="none"/>
        <text x="40" y="56" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Condenser</text>
    ''',

    "catch_pot_discharge_manual": '''
        <ellipse cx="40" cy="28" rx="13" ry="7" stroke="black" fill="white"/>
        <rect x="27" y="28" width="26" height="30" stroke="black" fill="none"/>
        <polygon points="40,58 37,65 43,65" fill="white" stroke="black"/>
        <rect x="36" y="65" width="8" height="7" stroke="black" fill="white"/>
        <line x1="40" y1="58" x2="40" y2="72" stroke="black"/>
        <text x="40" y="76" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Manual Drain</text>
    ''',

    "catch_pot_discharge_auto": '''
        <ellipse cx="40" cy="28" rx="13" ry="7" stroke="black" fill="white"/>
        <rect x="27" y="28" width="26" height="30" stroke="black" fill="none"/>
        <polygon points="40,58 37,65 43,65" fill="white" stroke="black"/>
        <circle cx="40" cy="71" r="5" stroke="black" fill="white"/>
        <line x1="40" y1="58" x2="40" y2="76" stroke="black"/>
        <text x="40" y="78" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Auto Drain</text>
    ''',

    "discharge_silencer": '''
        <ellipse cx="40" cy="40" rx="18" ry="9" stroke="black" fill="white"/>
        <path d="M22,40 Q40,30 58,40" stroke="black" fill="none"/>
        <text x="40" y="54" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Silencer</text>
        <polyline points="22,40 10,40" stroke="black"/>
        <polyline points="58,40 70,40" stroke="black"/>
        <text x="40" y="18" font-size="8" text-anchor="middle" dominant-baseline="middle" fill="#aaa" font-family="Arial, sans-serif">~</text>
    ''',

    "temp_transmitter_suction": '''
        <circle cx="40" cy="40" r="12" stroke="black" stroke-width="2" fill="white"/>
        <text x="40" y="44" font-size="10" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">TT</text>
        <line x1="40" y1="52" x2="60" y2="60" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
        <rect x="60" y="57" width="10" height="6" stroke="black" fill="white"/>
    ''',

    "temp_transmitter_discharge": '''
        <circle cx="40" cy="40" r="12" stroke="black" stroke-width="2" fill="white"/>
        <text x="40" y="44" font-size="10" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">TT</text>
        <line x1="40" y1="52" x2="60" y2="60" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
        <rect x="60" y="57" width="10" height="6" stroke="black" fill="white"/>
    ''',

    "temp_gauge_suction": '''
        <circle cx="40" cy="40" r="11" stroke="black" fill="white"/>
        <rect x="37" y="30" width="6" height="12" fill="white" stroke="black"/>
        <text x="40" y="44" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">&#8451;</text>
    ''',

    "temp_gauge_discharge": '''
        <circle cx="40" cy="40" r="11" stroke="black" fill="white"/>
        <rect x="37" y="30" width="6" height="12" fill="white" stroke="black"/>
        <text x="40" y="44" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">&#8451;</text>
    ''',

    "acg_filter_suction": '''
        <ellipse cx="40" cy="40" rx="10" ry="20" stroke="black" fill="white"/>
        <line x1="40" y1="20" x2="40" y2="60" stroke="black"/>
        <line x1="35" y1="30" x2="45" y2="50" stroke="black"/>
        <line x1="45" y1="30" x2="35" y2="50" stroke="black"/>
        <text x="40" y="64" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">ACG Filter</text>
    ''',

    "tc": '''
        <rect x="30" y="30" width="20" height="20" fill="white" stroke="black"/>
        <text x="40" y="44" font-size="10" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">TC</text>
    ''',

    "solenoid_valve": '''
        <rect x="30" y="30" width="20" height="20" stroke="black" fill="white"/>
        <rect x="35" y="18" width="10" height="10" stroke="black" fill="white"/>
        <line x1="40" y1="40" x2="40" y2="18" stroke="black" stroke-width="2" stroke-dasharray="3,2"/>
    ''',

    "pressure_regulator": '''
        <ellipse cx="40" cy="40" rx="16" ry="8" stroke="black" fill="white"/>
        <path d="M32,40 Q40,30 48,40" stroke="black" fill="none"/>
        <polygon points="40,32 38,36 42,36" fill="black"/>
    ''',

    "rotameter": '''
        <rect x="35" y="22" width="10" height="36" stroke="black" fill="white"/>
        <ellipse cx="40" cy="38" rx="5" ry="8" stroke="black" fill="none"/>
        <text x="40" y="60" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Rotameter</text>
    ''',

    "level_switch": '''
        <rect x="32" y="36" width="16" height="16" fill="white" stroke="black"/>
        <text x="40" y="46" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">LS</text>
        <line x1="40" y1="52" x2="60" y2="54" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
    ''',

    "temperature_control_valve": '''
        <rect x="32" y="36" width="16" height="16" stroke="black" fill="white"/>
        <text x="40" y="46" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">TCV</text>
        <circle cx="40" cy="60" r="6" stroke="black" fill="white"/>
        <text x="40" y="64" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">CV</text>
    ''',

    "drain_point": '''
        <polygon points="40,64 46,76 34,76" fill="white" stroke="black"/>
        <line x1="40" y1="64" x2="40" y2="54" stroke="black"/>
        <text x="40" y="80" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Drain</text>
    ''',

    "expansion_bellow": '''
        <rect x="32" y="36" width="16" height="16" fill="white" stroke="black"/>
        <path d="M36,38 Q40,44 44,38" stroke="black" fill="none"/>
        <path d="M36,46 Q40,52 44,46" stroke="black" fill="none"/>
        <text x="40" y="58" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Bellow</text>
    ''',

    "interconnecting_piping": '''
        <rect x="24" y="38" width="32" height="8" fill="white" stroke="black" stroke-dasharray="3,2"/>
        <text x="40" y="56" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Interconnect</text>
    ''',

    "electrical_panel_box": '''
        <rect x="24" y="24" width="32" height="32" rx="6" fill="white" stroke="black"/>
        <text x="40" y="38" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">FLP/NFLP</text>
        <rect x="32" y="24" width="16" height="6" fill="white" stroke="black"/>
    ''',

    "control_panel": '''
        <rect x="20" y="20" width="40" height="40" rx="10" fill="white" stroke="black"/>
        <rect x="24" y="24" width="32" height="10" fill="white" stroke="black"/>
        <rect x="24" y="34" width="32" height="18" fill="white" stroke="black"/>
        <text x="40" y="28" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">VFD</text>
        <text x="40" y="48" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">HMI</text>
    '''
}

import re

def get_component_symbol(component_id, width=None, height=None):
    """
    Returns a valid SVG string for the requested ISA symbol.
    If width and height are given, wraps in an <svg> root tag for scaling.
    All output is valid XML for SVG or PNG rendering.
    """
    svg_inner = PROFESSIONAL_ISA_SYMBOLS.get(component_id)
    if svg_inner is None:
        svg_inner = (
            '<rect x="10" y="10" width="60" height="60" fill="#fff" stroke="#f00" stroke-width="3"/>'
            '<text x="40" y="54" font-size="13" text-anchor="middle" fill="#f00" font-family="Arial, sans-serif">NO SYMBOL</text>'
        )

    # Attempt to derive a viewBox from the first element's attributes if available.
    # Otherwise, use a sensible default.
    # This is a heuristic and might need manual adjustment if symbols are oddly sized.
    viewbox = "0 0 80 80" # Default viewBox

    # A more robust way to get a viewBox would be to calculate the bounding box
    # of all elements within the SVG string, but that's complex without an XML parser.
    # For now, we'll assume symbols are designed within an 80x80 or similar canvas.

    if width is not None and height is not None:
        svg = (
            f'<svg width="{width}" height="{height}" viewBox="{viewbox}" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
            f'{svg_inner}'
            f'</svg>'
        )
    else:
        # If no explicit width/height, assume a default size for the standalone SVG
        svg = (
            f'<svg width="80" height="80" viewBox="{viewbox}" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
            f'{svg_inner}'
            f'</svg>'
        )
    return svg

# Removed ARROW_MARKERS as it's not used by the current get_component_symbol implementation.
# If you integrate these into a larger SVG with <defs> and <use>, you'd place this in that <defs> section.


def get_component_symbol_from_type(component_type: str) -> str:
    """
    Returns the appropriate symbol SVG fragment for a component type.
    This function returns the raw SVG content (e.g., <rect>...</rect>),
    not a wrapped <svg> or <symbol> tag.
    It's intended to be used when building a larger SVG's content directly.
    """
    # Map common variations to standard symbols
    type_mapping = {
        'kdp_330_pump': 'kdp_330_pump',
        'motor': 'motor_10hp_2pole_b5', # Assuming this is the default motor
        'vfd': 'vfd',
        'epo_valve': 'epo_valve',
        'n2_purge_assembly': 'n2_purge_assembly',
        'liquid_flushing_assembly': 'liquid_flushing_assembly',
        'suction_condenser': 'suction_condenser',
        'catch_pot_manual_drain': 'catch_pot_manual_drain',
        'catch_pot_auto_drain': 'catch_pot_auto_drain',
        'suction_filter': 'suction_filter',
        'scrubber': 'scrubber',
        'flame_arrestor_suction': 'flame_arrestor_suction',
        'flame_arrestor_discharge': 'flame_arrestor_discharge',
        'flex_conn_suction': 'flex_conn_suction',
        'flex_conn_discharge': 'flex_conn_discharge',
        'pressure_transmitter_discharge': 'pressure_transmitter_discharge',
        'discharge_condenser': 'discharge_condenser',
        'catch_pot_discharge_manual': 'catch_pot_discharge_manual',
        'catch_pot_discharge_auto': 'catch_pot_discharge_auto',
        'discharge_silencer': 'discharge_silencer',
        'temp_transmitter_suction': 'temp_transmitter_suction',
        'temp_transmitter_discharge': 'temp_transmitter_discharge',
        'temp_gauge_suction': 'temp_gauge_suction',
        'temp_gauge_discharge': 'temp_gauge_discharge',
        'acg_filter_suction': 'acg_filter_suction',
        'tc': 'tc',
        'solenoid_valve': 'solenoid_valve',
        'pressure_regulator': 'pressure_regulator',
        'rotameter': 'rotameter',
        'level_switch': 'level_switch',
        'temperature_control_valve': 'temperature_control_valve',
        'drain_point': 'drain_point',
        'expansion_bellow': 'expansion_bellow',
        'interconnecting_piping': 'interconnecting_piping',
        'electrical_panel_box': 'electrical_panel_box',
        'control_panel': 'control_panel',
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
        # Fallback for malformed tags
        return f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2"/>'

    letters = match.group(1)
    number = match.group(2)
    suffix = match.group(3)

    # Determine if local panel (L prefix) or field mounted
    is_local = letters.startswith('L')
    if is_local:
        letters = letters[1:]  # Remove L prefix for display purposes

    # Create SVG group for the instrument
    svg = f'<g class="instrument-{tag}">'

    # Main circle
    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    # Add horizontal line for field-mounted instruments
    if not is_local:
        # Ensure line is drawn within the circle's bounds or slightly beyond for clarity
        svg += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" stroke="black" stroke-width="2.5"/>'

    # Add box for panel-mounted instruments (dash-dotted line usually)
    # Note: ISA standard for panel-mounted (mounted on main control panel) is often a solid line circle
    # and a dashed line for aux panel. A box inside a circle is more for a 'shared display/control'.
    # I'll keep your existing logic for the box, but know that strict ISA might differ.
    if 'C' in letters or 'I' in letters:  # Controller or Indicator (often implies panel mounting context)
        box_padding = 5 # Padding from circle edge
        box_width = (size * 2) - (box_padding * 2)
        box_height = box_width # Keep it square
        svg += f'<rect x="{x - box_width/2}" y="{y - box_height/2}" width="{box_width}" height="{box_height}" '
        svg += f'fill="none" stroke="black" stroke-width="1.5" stroke-dasharray="5,3"/>' # Common for shared/auxiliary

    # Text positioning
    text_size_letters = size * 0.5
    text_size_number = size * 0.4
    y_offset_letters = size * 0.15 # For top text
    y_offset_number = size * 0.25 # For bottom text relative to center

    # Tag letters (function) - Top part
    svg += f'<text x="{x}" y="{y - y_offset_letters}" text-anchor="middle" '
    svg += f'font-size="{text_size_letters}" font-weight="bold" font-family="Arial, sans-serif">{letters}</text>'

    # Tag number - Bottom part
    svg += f'<text x="{x}" y="{y + y_offset_number + text_size_number/2}" text-anchor="middle" '
    svg += f'font-size="{text_size_number}" font-family="Arial, sans-serif">{number}{suffix}</text>'

    svg += '</g>'
    return svg


def create_pipe_with_spec(points: list, pipe_spec: str, line_type: str = 'process') -> str:
    """
    Creates a pipe with specification label.
    Example spec: "2"-PG-101-CS" means 2 inch, Process Gas, Line 101, Carbon Steel
    """
    if len(points) < 2:
        return ''

    # Line styles based on type
    line_styles = {
        'process': {'width': 3, 'color': 'black', 'dash': ''},
        'utility': {'width': 2.5, 'color': 'black', 'dash': ''},
        'instrument': {'width': 1.5, 'color': 'black', 'dash': '5,3'}, # Increased width for visibility
        'electrical': {'width': 1.5, 'color': 'black', 'dash': '2,2'}, # Increased width for visibility
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
        # Calculate midpoint of the first segment for simplicity, or the entire path
        mid_x = (points[0][0] + points[1][0]) / 2
        mid_y = (points[0][1] + points[1][1]) / 2

        # Label background
        # Estimate text width; this is a simplification and may not be accurate for all fonts/sizes
        estimated_char_width = 7 # pixels per char for font-size 10 Arial
        text_width_estimate = len(pipe_spec) * estimated_char_width + 10 # Add some padding
        text_height = 20 # Fixed height for background rectangle

        svg += f'<rect x="{mid_x - text_width_estimate/2}" y="{mid_y - text_height/2}" '
        svg += f'width="{text_width_estimate}" height="{text_height}" fill="white" stroke="black" stroke-width="0.5"/>' # Added thin border for clarity

        # Label text
        svg += f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" dominant-baseline="middle" '
        svg += f'font-size="10" font-family="Arial, sans-serif" fill="black">{pipe_spec}</text>'

    svg += '</g>'
    return svg

