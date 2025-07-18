"""
Professional ISA Symbol Library
Detailed, industry-standard P&ID symbols matching real engineering drawings
"""

# Professional ISA Symbols with accurate details
# All symbols are designed to fit conceptually within a 80x80 unit space.
# The viewBox "0 0 80 80" will be applied for scaling.
#
# Note: Some new symbols may be designed on a 100x100 viewBox implicitly.
# The get_component_symbol function is designed to scale these correctly
# by applying a "0 0 80 80" viewBox to the outer <svg> tag.
# If symbols consistently use a different internal viewBox,
# the default_viewbox variable in get_component_symbol might need adjustment
# or a per-symbol viewBox definition could be added to the dictionary.

import re

PROFESSIONAL_ISA_SYMBOLS = {
    # --- Existing symbols from your previous file ---
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
    "interconnecting_piping": '''
        <rect x="24" y="38" width="32" height="8" fill="white" stroke="black" stroke-dasharray="3,2"/>
        <text x="40" y="56" font-size="7" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Interconnect</text>
    ''',
    "electrical_panel_box": '''
        <rect x="24" y="24" width="32" height="32" rx="6" fill="white" stroke="black"/>
        <text x="40" y="38" font-size="9" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">FLP/NFLP</text>
        <rect x="32" y="24" width="16" height="6" fill="white" stroke="black"/>
    ''',
    "discharge_silencer": '''
        <ellipse cx="40" cy="40" rx="18" ry="9" stroke="black" fill="white"/>
        <path d="M22,40 Q40,30 58,40" stroke="black" fill="none"/>
        <text x="40" y="54" font-size="8" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">Silencer</text>
        <polyline points="22,40 10,40" stroke="black"/>
        <polyline points="58,40 70,40" stroke="black"/>
        <text x="40" y="18" font-size="8" text-anchor="middle" dominant-baseline="middle" fill="#aaa" font-family="Arial, sans-serif">~</text>
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
    # --- NEW / UPDATED SYMBOLS from your provided list ---
    "vertical_vessel": '''
      <ellipse cx="50" cy="15" rx="15" ry="8" fill="white" stroke="black" stroke-width="2"/>
      <rect x="35" y="15" width="30" height="60" fill="#f8fafc" stroke="black" stroke-width="2"/>
      <ellipse cx="50" cy="75" rx="15" ry="8" fill="white" stroke="black" stroke-width="2"/>
      <text x="50" y="43" font-size="10" text-anchor="middle" font-family="Arial" fill="#212121">V-101</text>
      <text x="50" y="88" font-size="8" text-anchor="middle" font-family="Arial" fill="#333">COLUMN</text>
      <line x1="50" y1="5" x2="50" y2="15" stroke="black" stroke-width="2"/>
      <circle cx="50" cy="10" r="2" fill="none" stroke="black" stroke-width="1"/>
    ''',
    "gate_valve": '''
      <line x1="50" y1="20" x2="50" y2="45" stroke="black" stroke-width="2"/>
      <line x1="46" y1="20" x2="54" y2="20" stroke="black" stroke-width="2"/>
      <rect x="40" y="45" width="20" height="10" fill="#e0e7ef" stroke="#212121" stroke-width="2"/>
      <text x="70" y="53" font-size="10" font-family="Arial" fill="#383838">GV-101</text>
    ''',
    "centrifugal_pump": '''
      <circle cx="50" cy="60" r="15" fill="#eef6fb" stroke="black" stroke-width="2"/>
      <rect x="35" y="40" width="30" height="18" fill="white" stroke="#223155" stroke-width="2"/>
      <line x1="65" y1="50" x2="85" y2="50" stroke="black" stroke-width="2"/>
      <line x1="35" y1="50" x2="15" y2="50" stroke="black" stroke-width="2"/>
      <text x="50" y="80" font-size="10" font-family="Arial" text-anchor="middle" fill="#2b2b2b">PUMP P-101</text>
    ''',
    "control_panel": '''
      <rect x="10" y="10" width="80" height="80" fill="#f6f4ed" stroke="black" stroke-width="2"/>
      <rect x="15" y="25" width="20" height="50" fill="#e5ebfa" stroke="black" stroke-width="1"/>
      <text x="25" y="82" font-size="9" text-anchor="middle" font-family="Arial">HMI</text>
      <rect x="39" y="25" width="20" height="50" fill="#e5faf1" stroke="black" stroke-width="1"/>
      <text x="49" y="82" font-size="9" text-anchor="middle" font-family="Arial">VFD</text>
      <rect x="62" y="25" width="12" height="24" fill="#fbeee5" stroke="black" stroke-width="1"/>
      <text x="68" y="58" font-size="8" text-anchor="middle" font-family="Arial">FLP</text>
      <rect x="62" y="54" width="12" height="21" fill="#e5faf8" stroke="black" stroke-width="1"/>
      <text x="68" y="80" font-size="8" text-anchor="middle" font-family="Arial">NFLP</text>
      <text x="50" y="105" font-size="10" text-anchor="middle" font-family="Arial" fill="#3e3e3e">CONTROL PANEL</text>
    ''',
    "pressure_gauge": '''
      <circle cx="50" cy="45" r="18" fill="#fff" stroke="black" stroke-width="2"/>
      <path d="M50,45 L62,33" stroke="#c23a1a" stroke-width="2"/>
      <text x="50" y="69" font-size="10" text-anchor="middle" font-weight="bold" font-family="Arial" fill="#184bd7">PI</text>
      <rect x="48" y="63" width="4" height="8" fill="#404040"/>
      <text x="75" y="50" font-size="10" font-family="Arial">PG-101</text>
    ''',
    "flow_transmitter": '''
      <circle cx="50" cy="50" r="14" fill="#f8f8ff" stroke="#222" stroke-width="2"/>
      <text x="50" y="56" font-size="11" text-anchor="middle" font-family="Arial" fill="#4878c0" font-weight="bold">FT</text>
      <rect x="47" y="60" width="6" height="10" fill="#385" stroke="#212121" stroke-width="1"/>
      <text x="77" y="54" font-size="9" font-family="Arial" fill="#212121">FT-101</text>
    ''',
    "globe_valve": '''
      <circle cx="50" cy="50" r="10" fill="#fff" stroke="#333" stroke-width="2"/>
      <rect x="45" y="20" width="10" height="20" fill="#fed" stroke="black" stroke-width="1"/>
      <line x1="10" y1="50" x2="40" y2="50" stroke="black" stroke-width="2"/>
      <line x1="60" y1="50" x2="90" y2="50" stroke="black" stroke-width="2"/>
      <text x="82" y="63" font-size="10" font-family="Arial" fill="#212121">GV-102</text>
    ''',
    "flange": '''
      <circle cx="50" cy="50" r="20" fill="#e6f7fc" stroke="#222" stroke-width="2"/>
      <circle cx="50" cy="50" r="14" fill="#fff" stroke="#222" stroke-width="2"/>
      <text x="50" y="50" font-size="10" text-anchor="middle" font-family="Arial" fill="#075">FLG</text>
    ''',
    "expansion_bellow": '''
      <rect x="37" y="44" width="26" height="12" rx="3" fill="#f6e9e1" stroke="#a67c52" stroke-width="2"/>
      <path d="M37,44 Q50,55 63,44" fill="none" stroke="#a67c52" stroke-width="2"/>
      <text x="50" y="65" font-size="9" text-anchor="middle" font-family="Arial" fill="#555">EXPN. BELLOWS</text>
    ''',
    "catch_pot": '''
      <ellipse cx="50" cy="80" rx="15" ry="5" fill="#f9f9fa" stroke="#111" stroke-width="2"/>
      <rect x="35" y="45" width="30" height="35" fill="#fff" stroke="#222" stroke-width="2"/>
      <ellipse cx="50" cy="45" rx="15" ry="5" fill="#f9f9fa" stroke="#222" stroke-width="2"/>
      <text x="50" y="36" font-size="10" text-anchor="middle" font-family="Arial" fill="#553">CATCH POT</text>
    ''',
}

# Define standard arrowhead for pipes, to be used in the main SVG <defs>
ARROWHEAD_MARKER = '''
    <marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="black" stroke="black"/>
    </marker>
'''

def get_component_symbol(component_id, target_width=None, target_height=None):
    """
    Returns a valid SVG string for the requested ISA symbol.
    The symbols in PROFESSIONAL_ISA_SYMBOLS are generally designed for a base unit space (e.g., 80x80 or 100x100).
    This function scales them to the target_width and target_height by
    wrapping them in an <svg> tag with the appropriate viewBox.
    If a symbol is not found, it returns a "NO SYMBOL" placeholder.
    """
    svg_inner = PROFESSIONAL_ISA_SYMBOLS.get(component_id)
    
    # Default viewBox for the internal symbol definitions
    # Assuming most symbols are drawn on an 80x80 canvas,
    # but some new ones might implicitly use 100x100.
    # The outer SVG's viewBox will handle the scaling to the final dimensions.
    default_viewbox = "0 0 80 80" 

    if svg_inner is None:
        # Fallback "NO SYMBOL" representation, also designed for 80x80
        svg_inner = (
            '<rect x="10" y="10" width="60" height="60" fill="white" stroke="#f00" stroke-width="3"/>'
            '<text x="40" y="40" font-size="10" text-anchor="middle" dominant-baseline="middle" fill="#f00" font-family="Arial, sans-serif">NO</text>'
            '<text x="40" y="55" font-size="10" text-anchor="middle" dominant-baseline="middle" fill="#f00" font-family="Arial, sans-serif">SYMBOL</text>'
        )

    # Use target_width and target_height if provided, otherwise default to 80x80 for standalone SVG
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
        # --- Mappings for new symbols ---
        'vertical_vessel': 'vertical_vessel',
        'gate_valve': 'gate_valve',
        'centrifugal_pump': 'centrifugal_pump',
        'pressure_gauge': 'pressure_gauge',
        'flow_transmitter': 'flow_transmitter',
        'globe_valve': 'globe_valve',
        'flange': 'flange',
        'catch_pot': 'catch_pot',
    }

    normalized_type = component_type.lower().replace('-', '_').replace(' ', '_')
    mapped_type = type_mapping.get(normalized_type, normalized_type)

    # This function should ideally return the raw SVG for embedding,
    # without the wrapping <svg> tag, as it's meant for internal use
    # within a larger SVG generation.
    # The get_component_symbol function is for standalone symbol generation.
    return PROFESSIONAL_ISA_SYMBOLS.get(mapped_type, '')


def create_professional_instrument_bubble(tag: str, x: float, y: float, size: float = 25) -> str:
    """
    Creates a professional instrument bubble with proper ISA formatting.
    This function should be called by advanced_rendering.py's render_tag_bubble.
    It's moved here for symbol-specific logic.
    """
    import re

    # Parse instrument tag
    match = re.match(r'^([A-Z]+)[-]?(\d+)([A-Z]?)$', tag)
    
    # Default to a simple circle if tag doesn't match expected format
    if not match:
        return f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    letters = match.group(1)
    number = match.group(2)
    suffix = match.group(3) # Not currently used in display, but kept for parsing

    # Determine if local panel (L prefix) or field mounted
    is_local_mounted = letters.startswith('L')
    if is_local_mounted:
        letters = letters[1:]  # Remove L prefix for display purposes in the bubble

    # ISA Standard for mounting:
    # Field Mounted: Circle with horizontal line through center
    # Local Panel Mounted (within operator reach): Circle with single horizontal line above center
    # Main Control Panel (shared display/control): Circle with a dashed horizontal line through center
    # Auxiliary Control Panel (behind panel): Circle with a solid line above and below center (double line)
    
    # For simplicity, let's implement Field Mounted (line through center) and Local (no line)
    # based on the `is_local_mounted` flag.
    # If you need Shared/Auxiliary, you'd add more logic to distinguish them.

    # Create SVG group for the instrument
    svg = f'<g class="instrument-{tag}">'

    # Main circle
    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    # Add horizontal line for field-mounted instruments
    if not is_local_mounted: # Assuming not 'local panel' means it's field mounted for now
        svg += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" stroke="black" stroke-width="2.5"/>'

    # Text positioning based on the 2-line format
    text_size_letters = size * 0.5
    text_size_number = size * 0.4
    
    # Calculate Y positions for the two lines of text
    # The overall height of the two lines of text will be approx (text_size_letters + text_size_number)
    # We want to center this block of text vertically in the circle.
    total_text_height = text_size_letters + text_size_number
    
    # Adjust base Y to move the combined text block's center to the circle's center
    base_y_offset = (total_text_height / 2) - text_size_letters 

    # Tag letters (function) - Top part
    svg += f'<text x="{x}" y="{y + base_y_offset + (text_size_letters * 0.75) / 2}" text-anchor="middle" '
    svg += f'font-size="{text_size_letters}" font-weight="bold" font-family="Arial, sans-serif">{letters}</text>'

    # Tag number - Bottom part
    svg += f'<text x="{x}" y="{y + base_y_offset + text_size_letters + (text_size_number * 0.75) / 2}" text-anchor="middle" '
    svg += f'font-size="{text_size_number}" font-family="Arial, sans-serif">{number}</text>'

    svg += '</g>'
    return svg


def create_pipe_with_spec(points: list, pipe_spec: str, line_type: str = 'process') -> str:
    """
    Creates a pipe with specification label.
    Example spec: "2"-PG-101-CS" means 2 inch, Process Gas, Line 101, Carbon Steel
    """
    if len(points) < 2:
        return ''

    # Line styles based on type (replicated from advanced_rendering for self-containment if needed elsewhere)
    # However, this function might be redundant if advanced_rendering.render_line_with_gradient
    # handles all line drawing. The 'pipe_spec' part is unique here.
    line_styles = {
        'process': {'width': 2, 'color': 'black', 'dash': ''},
        'utility': {'width': 5, 'color': '#666', 'dash': ''}, # From your original advanced_rendering
        'instrument': {'width': 1, 'color': '#0a85ff', 'dash': '5,4'}, # From new advanced_rendering
        'pneumatic': {'width': 1, 'color': '#33aa00', 'dash': '2,4'},
        'electric': {'width': 1, 'color': '#ebbc33', 'dash': '1,4'},
        'hydraulic': {'width': 1, 'color': '#b23d2a', 'dash': '8,2,2,2'},
        'scope_break': {'width': 1, 'color': '#a6a6a6', 'dash': '3,3'},
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
        # For long pipes, you might want to place the label near a bend or a specific point.
        # This currently places it at the midpoint of the first segment.
        mid_x = (points[0][0] + points[1][0]) / 2
        mid_y = (points[0][1] + points[1][1]) / 2

        # Label background
        # Estimate text width; this is a simplification and may not be accurate for all fonts/sizes
        estimated_char_width = 6 # pixels per char for font-size 10 Arial
        text_width_estimate = len(pipe_spec) * estimated_char_width + 10 # Add some padding
        text_height = 18 # Fixed height for background rectangle, slightly smaller

        svg += f'<rect x="{mid_x - text_width_estimate/2}" y="{mid_y - text_height/2}" '
        svg += f'width="{text_width_estimate}" height="{text_height}" fill="white" stroke="black" stroke-width="0.5"/>' # Added thin border for clarity

        # Label text
        svg += f'<text x="{mid_x}" y="{mid_y + 3}" text-anchor="middle" dominant-baseline="middle" ' # Adjust y slightly
        svg += f'font-size="10" font-family="Arial, sans-serif" fill="black">{pipe_spec}</text>'

    svg += '</g>'
    return svg
