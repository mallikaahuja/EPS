"""
Professional ISA Symbol Library - Complete Working Version
All symbols properly defined for the vacuum system P&ID
"""

import re
import os # Added for path handling

# Ensure 'symbols' directory exists for generated symbols
symbols_dir = "symbols"
os.makedirs(symbols_dir, exist_ok=True)

# Symbol mapping by ID and type
SYMBOL_ID_MAPPING = {
    'EB-001': 'expansion_bellows',
    'EPB-001': 'electrical_panel_box',
    'FA-001': 'flame_arrestor',
    'C-001': 'vapor_condenser',
    'ACG-001': 'acg_filter',
    'SF-001': 'suction_filter',
    'P-001': 'kdp_pump',
    'SIL-001': 'silencer',
    'C-002': 'condenser_discharge',
    'SCR-001': 'scrubber',
    'CP-001': 'control_panel',
    'WP-001': 'water_pump',
    'CT-001': 'cooling_tower',
    'MV-001': 'motor',
    'DP-001': 'drain_point',
    'V-001': 'gate_valve',
    'V-002': 'gate_valve',
    'V-003': 'gate_valve',
    'V-004': 'gate_valve',
    'NRV-001': 'check_valve',
    'SV-001': 'solenoid_valve',
    'PT-001': 'pressure_transmitter',
    'TT-001': 'temperature_transmitter',
    'FT-001': 'flow_transmitter',
    'LS-001': 'level_switch',
    'PG-001': 'pressure_gauge',
    'PG-002': 'pressure_gauge',
    'TG-001': 'temperature_gauge',
    'PSV-001': 'pressure_relief_valve',
    'PR-001': 'pressure_regulator',
    'RM-001': 'rotameter'
}

PROFESSIONAL_ISA_SYMBOLS = {
    # EXPANSION BELLOWS - Wavy flexible connector
    'expansion_bellows': '''
        <rect x="10" y="35" width="60" height="10" fill="none" stroke="black" stroke-width="2"/>
        <path d="M 15,30 Q 20,25 25,30 Q 30,35 35,30 Q 40,25 45,30 Q 50,35 55,30 Q 60,25 65,30" 
        fill="none" stroke="black" stroke-width="2"/>
        <path d="M 15,50 Q 20,55 25,50 Q 30,45 35,50 Q 40,55 45,50 Q 50,45 55,50 Q 60,55 65,50" 
        fill="none" stroke="black" stroke-width="2"/>
        <line x1="15" y1="30" x2="15" y2="50" stroke="black" stroke-width="2"/>
        <line x1="65" y1="30" x2="65" y2="50" stroke="black" stroke-width="2"/>
    ''',

    # ELECTRICAL PANEL BOX - Box with FLP/NFLP marking
    'electrical_panel_box': '''
        <rect x="10" y="10" width="60" height="60" rx="3" fill="white" stroke="black" stroke-width="2.5"/>
        <rect x="15" y="15" width="50" height="50" fill="none" stroke="black" stroke-width="1"/>
        <text x="40" y="28" font-size="10" text-anchor="middle" font-family="Arial" font-weight="bold">FLP</text>
        <line x1="15" y1="35" x2="65" y2="35" stroke="black" stroke-width="1"/>
        <text x="40" y="48" font-size="10" text-anchor="middle" font-family="Arial" font-weight="bold">NFLP</text>
        <circle cx="25" cy="58" r="2" fill="black"/>
        <circle cx="40" cy="58" r="2" fill="black"/>
        <circle cx="55" cy="58" r="2" fill="black"/>
    ''',

    # FLAME ARRESTOR - Grid pattern in box
    'flame_arrestor': '''
        <rect x="20" y="30" width="40" height="20" fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="30" y1="30" x2="30" y2="50" stroke="black" stroke-width="1.5"/>
        <line x1="35" y1="30" x2="35" y2="50" stroke="black" stroke-width="1.5"/>
        <line x1="40" y1="30" x2="40" y2="50" stroke="black" stroke-width="1.5"/>
        <line x1="45" y1="30" x2="45" y2="50" stroke="black" stroke-width="1.5"/>
        <line x1="50" y1="30" x2="50" y2="50" stroke="black" stroke-width="1.5"/>
        <line x1="10" y1="40" x2="20" y2="40" stroke="black" stroke-width="2"/>
        <line x1="60" y1="40" x2="70" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # VAPOR CONDENSER WITH INTEGRATED CATCHPOT
    'vapor_condenser': '''
        <rect x="20" y="15" width="40" height="35" stroke="black" stroke-width="2" fill="white"/>
        <path d="M 25,20 L 35,30 L 25,40" stroke="black" stroke-width="2" fill="none"/>
        <path d="M 55,20 L 45,30 L 55,40" stroke="black" stroke-width="2" fill="none"/>
        <ellipse cx="40" cy="55" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
        <rect x="20" y="55" width="40" height="15" stroke="black" stroke-width="2" fill="white"/>
        <ellipse cx="40" cy="70" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
        <line x1="10" y1="30" x2="20" y2="30" stroke="black" stroke-width="2"/>
        <line x1="60" y1="30" x2="70" y2="30" stroke="black" stroke-width="2"/>
        <line x1="40" y1="70" x2="40" y2="75" stroke="black" stroke-width="2"/>
    ''',

    # ACG (ACTIVATED CARBON) FILTER
    'acg_filter': '''
        <rect x="25" y="10" width="30" height="60" rx="15" stroke="black" stroke-width="2.5" fill="white"/>
        <circle cx="40" cy="25" r="1.5" fill="black"/>
        <circle cx="35" cy="30" r="1.5" fill="black"/>
        <circle cx="45" cy="30" r="1.5" fill="black"/>
        <circle cx="40" cy="35" r="1.5" fill="black"/>
        <circle cx="35" cy="40" r="1.5" fill="black"/>
        <circle cx="45" cy="40" r="1.5" fill="black"/>
        <circle cx="40" cy="45" r="1.5" fill="black"/>
        <circle cx="35" cy="50" r="1.5" fill="black"/>
        <circle cx="45" cy="50" r="1.5" fill="black"/>
        <circle cx="40" cy="55" r="1.5" fill="black"/>
        <line x1="40" y1="0" x2="40" y2="10" stroke="black" stroke-width="2"/>
        <line x1="40" y1="70" x2="40" y2="80" stroke="black" stroke-width="2"/>
    ''',

    # SUCTION FILTER - Conical with mesh
    'suction_filter': '''
        <path d="M 25,15 L 55,15 L 50,50 L 48,65 L 32,65 L 30,50 Z" 
              fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="28" y1="20" x2="52" y2="20" stroke="black" stroke-width="1.5"/>
        <line x1="29" y1="25" x2="51" y2="25" stroke="black" stroke-width="1.5"/>
        <line x1="30" y1="30" x2="50" y2="30" stroke="black" stroke-width="1.5"/>
        <line x1="31" y1="35" x2="49" y2="35" stroke="black" stroke-width="1.5"/>
        <line x1="32" y1="40" x2="48" y2="40" stroke="black" stroke-width="1.5"/>
        <path d="M 30,20 L 35,25 M 35,20 L 40,25 M 40,20 L 45,25 M 45,20 L 50,25" 
              stroke="black" stroke-width="0.5"/>
        <line x1="40" y1="5" x2="40" y2="15" stroke="black" stroke-width="2"/>
        <line x1="40" y1="65" x2="40" y2="75" stroke="black" stroke-width="2"/>
    ''',

    # KDP-330 DRY SCREW VACUUM PUMP
    'kdp_pump': '''
        <circle cx="40" cy="40" r="30" fill="white" stroke="black" stroke-width="3"/>
        <path d="M 40,10 Q 60,25 60,40 Q 60,55 40,70 Q 20,55 20,40 Q 20,25 40,10" 
              fill="none" stroke="black" stroke-width="2.5"/>
        <circle cx="40" cy="40" r="5" fill="black"/>
        <text x="40" y="45" font-size="10" text-anchor="middle" font-family="Arial" fill="white">KDP</text>
        <line x1="5" y1="40" x2="10" y2="40" stroke="black" stroke-width="3"/>
        <line x1="70" y1="40" x2="75" y2="40" stroke="black" stroke-width="3"/>
        <line x1="20" y1="70" x2="60" y2="70" stroke="black" stroke-width="2"/>
    ''',

    # SILENCER - Muffler shape
    'silencer': '''
        <ellipse cx="40" cy="40" rx="30" ry="15" stroke="black" stroke-width="2.5" fill="white"/>
        <path d="M10,40 Q40,20 70,40" stroke="black" stroke-width="2" fill="none"/>
        <circle cx="25" cy="35" r="3" fill="white" stroke="black" stroke-width="1"/>
        <circle cx="40" cy="30" r="3" fill="white" stroke="black" stroke-width="1"/>
        <circle cx="55" cy="35" r="3" fill="white" stroke="black" stroke-width="1"/>
        <line x1="5" y1="40" x2="10" y2="40" stroke="black" stroke-width="2"/>
        <line x1="70" y1="40" x2="75" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # POST-PUMP CONDENSER (Similar to Vapor Condenser but conceptually different)
    'condenser_discharge': '''
        <rect x="20" y="15" width="40" height="35" stroke="black" stroke-width="2" fill="white"/>
        <path d="M 25,20 L 35,30 L 25,40" stroke="black" stroke-width="2" fill="none"/>
        <path d="M 55,20 L 45,30 L 55,40" stroke="black" stroke-width="2" fill="none"/>
        <ellipse cx="40" cy="55" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
        <rect x="20" y="55" width="40" height="15" stroke="black" stroke-width="2" fill="white"/>
        <ellipse cx="40" cy="70" rx="20" ry="5" stroke="black" stroke-width="2" fill="white"/>
        <line x1="10" y1="30" x2="20" y2="30" stroke="black" stroke-width="2"/>
        <line x1="60" y1="30" x2="70" y2="30" stroke="black" stroke-width="2"/>
        <line x1="40" y1="70" x2="40" y2="75" stroke="black" stroke-width="2"/>
    ''',

    # SCRUBBER - Vertical vessel with trays
    'scrubber': '''
        <rect x="25" y="10" width="30" height="60" rx="15" stroke="black" stroke-width="2.5" fill="white"/>
        <line x1="25" y1="25" x2="55" y2="25" stroke="black" stroke-width="1.5"/>
        <line x1="25" y1="35" x2="55" y2="35" stroke="black" stroke-width="1.5"/>
        <line x1="25" y1="45" x2="55" y2="45" stroke="black" stroke-width="1.5"/>
        <line x1="25" y1="55" x2="55" y2="55" stroke="black" stroke-width="1.5"/>
        <line x1="40" y1="0" x2="40" y2="10" stroke="black" stroke-width="2"/>
        <line x1="40" y1="70" x2="40" y2="80" stroke="black" stroke-width="2"/>
        <line x1="15" y1="30" x2="25" y2="30" stroke="black" stroke-width="2"/>
        <line x1="55" y1="60" x2="65" y2="60" stroke="black" stroke-width="2"/>
    ''',

    # CONTROL PANEL - Detailed panel
    'control_panel': '''
        <rect x="5" y="5" width="70" height="70" rx="3" fill="white" stroke="black" stroke-width="3"/>
        <rect x="10" y="10" width="60" height="60" fill="none" stroke="black" stroke-width="1.5"/>
        <rect x="15" y="15" width="25" height="20" fill="#ddd" stroke="black" stroke-width="1"/>
        <text x="27" y="28" text-anchor="middle" font-size="9" font-family="Arial">HMI</text>
        <rect x="45" y="15" width="20" height="20" fill="#ddd" stroke="black" stroke-width="1"/>
        <text x="55" y="28" text-anchor="middle" font-size="9" font-family="Arial">VFD</text>
        <circle cx="20" cy="45" r="3" fill="green"/>
        <circle cx="30" cy="45" r="3" fill="yellow"/>
        <circle cx="40" cy="45" r="3" fill="red"/>
        <circle cx="50" cy="45" r="3" fill="green"/>
        <circle cx="60" cy="45" r="3" fill="green"/>
        <rect x="15" y="55" width="50" height="10" fill="none" stroke="black" stroke-width="1"/>
        <text x="40" y="62" text-anchor="middle" font-size="7" font-family="Arial">CONTROL PANEL</text>
    ''',

    # COOLING TOWER
    'cooling_tower': '''
        <rect x="15" y="25" width="50" height="35" stroke="black" stroke-width="2.5" fill="white"/>
        <path d="M 15,25 L 25,15 L 55,15 L 65,25" stroke="black" stroke-width="2.5" fill="white"/>
        <circle cx="40" cy="20" r="10" stroke="black" stroke-width="2" fill="white"/>
        <path d="M 33,18 L 40,20 L 33,22 M 40,18 L 47,20 L 40,22" stroke="black" stroke-width="1.5" fill="none"/>
        <line x1="20" y1="35" x2="60" y2="35" stroke="black" stroke-width="1"/>
        <line x1="20" y1="45" x2="60" y2="45" stroke="black" stroke-width="1"/>
        <path d="M 25,40 L 25,55 M 35,40 L 35,55 M 45,40 L 45,55 M 55,40 L 55,55" stroke="blue" stroke-width="1.5" stroke-dasharray="2,2"/>
        <line x1="40" y1="60" x2="40" y2="70" stroke="black" stroke-width="2"/>
    ''',

    # WATER PUMP
    'water_pump': '''
        <circle cx="40" cy="40" r="20" fill="white" stroke="black" stroke-width="2.5"/>
        <path d="M 40,20 Q 50,30 50,40 Q 50,50 40,60 Q 30,50 30,40 Q 30,30 40,20" 
              fill="none" stroke="black" stroke-width="2"/>
        <line x1="15" y1="40" x2="20" y2="40" stroke="black" stroke-width="2"/>
        <line x1="60" y1="40" x2="65" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # MOTOR
    'motor': '''
        <circle cx="40" cy="40" r="25" fill="white" stroke="black" stroke-width="3"/>
        <text x="40" y="45" font-size="16" text-anchor="middle" font-weight="bold" font-family="Arial">M</text>
        <line x1="40" y1="65" x2="40" y2="75" stroke="black" stroke-width="2"/>
    ''',

    # GATE VALVE
    'gate_valve': '''
        <polygon points="30,30 50,30 50,50 30,50" fill="white" stroke="black" stroke-width="2"/>
        <polygon points="30,30 40,40 50,30" fill="white" stroke="black" stroke-width="2"/>
        <polygon points="30,50 40,40 50,50" fill="white" stroke="black" stroke-width="2"/>
        <line x1="40" y1="30" x2="40" y2="20" stroke="black" stroke-width="2"/>
        <circle cx="40" cy="18" r="3" fill="none" stroke="black" stroke-width="1.5"/>
        <line x1="10" y1="40" x2="30" y2="40" stroke="black" stroke-width="2"/>
        <line x1="50" y1="40" x2="70" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # CHECK VALVE (NON-RETURN VALVE)
    'check_valve': '''
        <circle cx="40" cy="40" r="15" fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="40" y1="25" x2="40" y2="55" stroke="black" stroke-width="2.5"/>
        <polygon points="32,35 48,40 32,45" fill="black"/>
        <line x1="20" y1="40" x2="25" y2="40" stroke="black" stroke-width="2"/>
        <line x1="55" y1="40" x2="60" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # SOLENOID VALVE
    'solenoid_valve': '''
        <polygon points="30,30 50,30 50,50 30,50" fill="white" stroke="black" stroke-width="2"/>
        <polygon points="30,30 40,40 50,30" fill="white" stroke="black" stroke-width="2"/>
        <polygon points="30,50 40,40 50,50" fill="white" stroke="black" stroke-width="2"/>
        <rect x="35" y="15" width="10" height="15" rx="2" fill="white" stroke="black" stroke-width="2"/>
        <line x1="37" y1="20" x2="43" y2="20" stroke="black" stroke-width="1"/>
        <line x1="37" y1="23" x2="43" y2="23" stroke="black" stroke-width="1"/>
        <line x1="37" y1="26" x2="43" y2="26" stroke="black" stroke-width="1"/>
        <line x1="40" y1="10" x2="40" y2="15" stroke="black" stroke-width="2"/>
        <line x1="10" y1="40" x2="30" y2="40" stroke="black" stroke-width="2"/>
        <line x1="50" y1="40" x2="70" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # PRESSURE TRANSMITTER
    'pressure_transmitter': '''
        <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
        <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">PT</text>
        <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
        <rect x="38" y="58" width="4" height="12" fill="black"/>
        <line x1="38" y1="58" x2="42" y2="58" stroke="black" stroke-width="2.5"/>
    ''',

    # TEMPERATURE TRANSMITTER
    'temperature_transmitter': '''
        <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
        <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">TT</text>
        <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
        <rect x="38" y="58" width="4" height="12" fill="black"/>
        <line x1="38" y1="58" x2="42" y2="58" stroke="black" stroke-width="2.5"/>
    ''',

    # FLOW TRANSMITTER
    'flow_transmitter': '''
        <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
        <text x="40" y="38" font-size="12" text-anchor="middle" font-weight="bold" font-family="Arial">FT</text>
        <text x="40" y="50" font-size="9" text-anchor="middle" font-family="Arial">001</text>
        <rect x="38" y="58" width="4" height="12" fill="black"/>
        <line x1="38" y1="58" x2="42" y2="58" stroke="black" stroke-width="2.5"/>
    ''',

    # LEVEL SWITCH
    'level_switch': '''
        <rect x="25" y="25" width="30" height="30" fill="white" stroke="black" stroke-width="2.5"/>
        <text x="40" y="36" font-size="11" text-anchor="middle" font-weight="bold" font-family="Arial">LS</text>
        <text x="40" y="48" font-size="9" text-anchor="middle" font-family="Arial">001</text>
        <line x1="40" y1="55" x2="40" y2="65" stroke="black" stroke-width="2" stroke-dasharray="3,2"/>
    ''',

    # PRESSURE GAUGE
    'pressure_gauge': '''
        <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
        <circle cx="40" cy="40" r="15" stroke="black" stroke-width="1" fill="none"/>
        <line x1="40" y1="40" x2="50" y2="30" stroke="black" stroke-width="2"/>
        <circle cx="40" cy="40" r="2" fill="black"/>
        <text x="40" y="65" font-size="8" text-anchor="middle" font-family="Arial">PG</text>
        <line x1="40" y1="58" x2="40" y2="65" stroke="black" stroke-width="2"/>
    ''',

    # TEMPERATURE GAUGE
    'temperature_gauge': '''
        <circle cx="40" cy="40" r="18" stroke="black" stroke-width="2.5" fill="white"/>
        <rect x="37" y="30" width="6" height="15" fill="none" stroke="black" stroke-width="1.5"/>
        <circle cx="40" cy="48" r="4" fill="black"/>
        <text x="40" y="65" font-size="8" text-anchor="middle" font-family="Arial">°C</text>
        <line x1="40" y1="58" x2="40" y2="65" stroke="black" stroke-width="2"/>
    ''',

    # PRESSURE RELIEF VALVE
    'pressure_relief_valve': '''
        <polygon points="30,50 50,50 40,30" fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="40" y1="50" x2="40" y2="60" stroke="black" stroke-width="2.5"/>
        <path d="M 35,25 Q 40,20 45,25" stroke="black" stroke-width="2" fill="none"/>
        <line x1="40" y1="20" x2="40" y2="10" stroke="black" stroke-width="2" stroke-dasharray="3,2"/>
    ''',

    # PRESSURE REGULATOR
    'pressure_regulator': '''
        <ellipse cx="40" cy="40" rx="20" ry="10" stroke="black" stroke-width="2.5" fill="white"/>
        <path d="M 30,40 Q 40,30 50,40" stroke="black" stroke-width="2" fill="none"/>
        <polygon points="40,32 38,36 42,36" fill="black"/>
        <circle cx="40" cy="20" r="5" fill="none" stroke="black" stroke-width="2"/>
        <line x1="40" y1="25" x2="40" y2="30" stroke="black" stroke-width="2"/>
        <line x1="10" y1="40" x2="20" y2="40" stroke="black" stroke-width="2"/>
        <line x1="60" y1="40" x2="70" y2="40" stroke="black" stroke-width="2"/>
    ''',

    # ROTAMETER (FLOW INDICATOR)
    'rotameter': '''
        <rect x="35" y="20" width="10" height="40" stroke="black" stroke-width="2.5" fill="white"/>
        <path d="M 35,20 L 30,15 L 50,15 L 45,20" stroke="black" stroke-width="2" fill="white"/>
        <path d="M 35,60 L 30,65 L 50,65 L 45,60" stroke="black" stroke-width="2" fill="white"/>
        <ellipse cx="40" cy="40" rx="4" ry="8" stroke="black" stroke-width="1.5" fill="black"/>
        <line x1="40" y1="65" x2="40" y2="75" stroke="black" stroke-width="2"/>
        <line x1="40" y1="5" x2="40" y2="15" stroke="black" stroke-width="2"/>
    ''',

    # DRAIN POINT
    'drain_point': '''
        <polygon points="40,20 55,50 25,50" fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="40" y1="50" x2="40" y2="60" stroke="black" stroke-width="2.5"/>
        <line x1="35" y1="60" x2="45" y2="60" stroke="black" stroke-width="2.5"/>
        <line x1="37" y1="63" x2="43" y2="63" stroke="black" stroke-width="2"/>
        <line x1="39" y1="66" x2="41" y2="66" stroke="black" stroke-width="1.5"/>
    ''',

    # DEFAULT/FALLBACK SYMBOL
    'default': '''
        <rect x="20" y="20" width="40" height="40" rx="5" fill="white" stroke="red" stroke-width="2"/>
        <text x="40" y="45" font-size="10" text-anchor="middle" font-family="Arial" fill="red">?</text>
    '''
}

def get_component_symbol(component_id, target_width=None, target_height=None):
    """
    Returns a valid SVG string for the requested ISA symbol.
    """
    # First try to get the symbol type from the ID mapping
    symbol_type = SYMBOL_ID_MAPPING.get(component_id)

    # If not found in mapping, try to determine type from ID pattern
    if not symbol_type:
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
                'PG': 'pressure_gauge',
                'TG': 'temperature_gauge',
                'PSV': 'pressure_relief_valve',
                'PR': 'pressure_regulator',
                'RM': 'rotameter',
                'C': 'vapor_condenser', # Added C for condenser from mapping
                'P': 'kdp_pump',       # Added P for pump from mapping
                'EB': 'expansion_bellows', # Added EB
                'EPB': 'electrical_panel_box', # Added EPB
                'FA': 'flame_arrestor', # Added FA
                'ACG': 'acg_filter',   # Added ACG
                'SF': 'suction_filter', # Added SF
                'SIL': 'silencer',     # Added SIL
                'SCR': 'scrubber',     # Added SCR
                'CP': 'control_panel', # Added CP
                'WP': 'water_pump',    # Added WP
                'CT': 'cooling_tower', # Added CT
                'MV': 'motor',         # Added MV
                'DP': 'drain_point'    # Added DP
            }
            symbol_type = type_mapping.get(prefix, 'default')
        else:
            symbol_type = 'default'

    # Get the SVG content
    svg_inner = PROFESSIONAL_ISA_SYMBOLS.get(symbol_type, PROFESSIONAL_ISA_SYMBOLS['default'])

    # Default dimensions
    final_width = target_width if target_width is not None else 80
    final_height = target_height if target_height is not None else 80

    # Return complete SVG
    svg = f'''<svg width="{final_width}" height="{final_height}" viewBox="0 0 80 80" 
              xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
              {svg_inner}
              </svg>'''

    return svg

def get_component_symbol_from_type(component_type):
    """
    Returns the raw SVG content for a component type.
    This function is intended for fetching symbols based on a generic type name
    rather than a specific ID (like 'pump' instead of 'P-001').
    """
    # Normalize type name by replacing spaces and hyphens with underscores, and making lowercase
    normalized_type = component_type.lower().replace('-', '_').replace(' ', '_')

    # Check if exact normalized type exists
    if normalized_type in PROFESSIONAL_ISA_SYMBOLS:
        return PROFESSIONAL_ISA_SYMBOLS[normalized_type]

    # Try to find a partial match (e.g., 'dry_screw_vacuum_pump' might match 'kdp_pump')
    for key, svg_content in PROFESSIONAL_ISA_SYMBOLS.items():
        if normalized_type in key or key in normalized_type:
            return svg_content

    # Return default if not found
    return PROFESSIONAL_ISA_SYMBOLS['default']

def create_professional_instrument_bubble(tag, x, y, size=25):
    """
    Creates a professional ISA instrument bubble with standard formatting.
    Supports field-mounted (circle with line) and locally mounted (simple circle).
    """
    # Parse instrument tag using regex
    # Expected format: [Optional Location Letter][Function Letters][-][Loop Number][Optional Suffix Letter]
    # Example: PT-001, LIC-102A, TE-301
    match = re.match(r'^([A-Z]*)([A-Z]+)[-]?(\d+)([A-Z]?)$', tag)

    if not match:
        # Fallback for non-standard tags: simple circle with full tag in middle
        return f'''
            <g class="instrument-{tag}">
                <circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>
                <text x="{x}" y="{y + size * 0.15}" text-anchor="middle" 
                      font-size="{size * 0.5}" font-weight="bold" font-family="Arial, sans-serif">{tag}</text>
            </g>
        '''

    location_or_modifier = match.group(1) # e.g., 'L' for local, 'I' for indication etc. (less common as leading)
    function_letters = match.group(2)     # e.g., 'P', 'T', 'F', 'L', 'I', 'C'
    loop_number = match.group(3)          # e.g., '001', '102'
    suffix_letter = match.group(4)        # e.g., 'A', 'B'

    # Determine mounting type based on common ISA conventions
    # Field-mounted (no line) vs. Board/Panel mounted (solid line) vs. Local (no line, usually 'L' prefix in tag)
    # Streamlit typically focuses on displaying the symbol, not differentiating mounting from tag itself for visual style
    # For now, let's assume if it's a "valve" type it won't have the line, otherwise it's a standard instrument circle.
    
    # Check if it's a valve or a generic equipment with ID that might not have a line
    is_valve_like = any(f.lower() in function_letters.lower() for f in ['V', 'SV', 'NRV', 'RV', 'FCV'])
    
    # Consider "local" if the first letter of the *original* tag (before parsing) implies it
    # This might need refinement based on strict ISA interpretation for your project.
    # For now, let's simplify: if it's not a valve-like, it's a standard instrument circle.
    # We'll omit the internal line for now unless specifically requested.

    svg = f'<g class="instrument-{tag}">'

    # Main circle
    svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" stroke="black" stroke-width="2.5"/>'

    # Text positioning for two-line format
    text_size_letters = size * 0.6
    text_size_number = size * 0.4

    # Tag letters (top)
    # Combine location/modifier and function letters if both exist
    full_letters = function_letters
    if location_or_modifier: # If there was a leading letter, like 'L' for local
        full_letters = location_or_modifier + function_letters

    svg += f'<text x="{x}" y="{y - size * 0.15}" text-anchor="middle" '
    svg += f'font-size="{text_size_letters}" font-weight="bold" font-family="Arial, sans-serif">{full_letters}</text>'

    # Tag number (bottom)
    display_number = loop_number
    if suffix_letter:
        display_number += suffix_letter

    svg += f'<text x="{x}" y="{y + size * 0.35}" text-anchor="middle" '
    svg += f'font-size="{text_size_number}" font-family="Arial, sans-serif">{display_number}</text>'

    svg += '</g>'
    return svg

