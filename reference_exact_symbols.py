"""
Exact ISA Symbols matching the reference P&ID
Including all specific components shown
"""

REFERENCE_EXACT_SYMBOLS = {
    # --- FILTER (Exact match to reference) ---
    'filter_suction': '''<symbol id="filter_suction" viewBox="0 0 100 150">
    <path d="M 20,40 L 80,40 L 70,100 L 65,120 L 35,120 L 30,100 Z" 
    fill="white" stroke="black" stroke-width="3"/>
    <line x1="25" y1="50" x2="75" y2="50" stroke="black" stroke-width="2"/>
    <line x1="27" y1="55" x2="73" y2="55" stroke="black" stroke-width="2"/>
    <line x1="29" y1="60" x2="71" y2="60" stroke="black" stroke-width="2"/>
    <line x1="31" y1="65" x2="69" y2="65" stroke="black" stroke-width="2"/>
    <line x1="33" y1="70" x2="67" y2="70" stroke="black" stroke-width="2"/>
    <path d="M 30,50 L 40,60 M 35,50 L 45,60 M 40,50 L 50,60 M 45,50 L 55,60 M 50,50 L 60,60 M 55,50 L 65,60 M 60,50 L 70,60" 
    stroke="black" stroke-width="0.5"/>
    <rect x="35" y="20" width="30" height="20" fill="white" stroke="black" stroke-width="3"/>
    <rect x="30" y="15" width="40" height="8" fill="white" stroke="black" stroke-width="3"/>
    <circle cx="35" cy="19" r="2" fill="black"/>
    <circle cx="65" cy="19" r="2" fill="black"/>
    <circle cx="35" cy="27" r="2" fill="black"/>
    <circle cx="65" cy="27" r="2" fill="black"/>
    <rect x="35" y="120" width="30" height="20" fill="white" stroke="black" stroke-width="3"/>
    <rect x="30" y="135" width="40" height="8" fill="white" stroke="black" stroke-width="3"/>
    <rect x="25" y="110" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <rect x="60" y="45" width="15" height="10" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="20" cy="60" r="3" fill="white" stroke="black" stroke-width="2"/>
    <circle cx="20" cy="80" r="3" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    # --- STRAINER (As shown in reference) ---
    'strainer_y': '''<symbol id="strainer_y" viewBox="0 0 80 100">
        <path d="M 40,20 L 40,50 L 60,70 L 60,80 L 50,80 L 30,60 L 30,50 L 30,20" 
              fill="white" stroke="black" stroke-width="3"/>
        <path d="M 25,20 L 55,20" stroke="black" stroke-width="3"/>
        <path d="M 35,55 L 55,75" stroke="black" stroke-width="1.5"/>
        <path d="M 35,60 L 50,75" stroke="black" stroke-width="1.5"/>
        <path d="M 35,65 L 45,75" stroke="black" stroke-width="1.5"/>
        <rect x="30" y="10" width="20" height="10" fill="white" stroke="black" stroke-width="3"/>
        <rect x="45" y="75" width="20" height="10" fill="white" stroke="black" stroke-width="3"/>
        <circle cx="55" cy="80" r="5" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    # --- PUMP (KDP-330 style from reference) ---
    'pump_kdp330': '''<symbol id="pump_kdp330" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="45" fill="white" stroke="black" stroke-width="4"/>
        <path d="M 60,15 Q 90,30 90,60 Q 90,90 60,105 Q 30,90 30,60 Q 30,30 60,15" 
              fill="none" stroke="black" stroke-width="3"/>
        <circle cx="60" cy="60" r="8" fill="black"/>
        <rect x="0" y="50" width="20" height="20" fill="white" stroke="black" stroke-width="3"/>
        <rect x="-5" y="48" width="10" height="24" fill="white" stroke="black" stroke-width="3"/>
        <rect x="50" y="0" width="20" height="20" fill="white" stroke="black" stroke-width="3"/>
        <rect x="48" y="-5" width="24" height="10" fill="white" stroke="black" stroke-width="3"/>
        <rect x="100" y="45" width="20" height="30" rx="5" fill="white" stroke="black" stroke-width="2" stroke-dasharray="3,2"/>
        <line x1="15" y1="105" x2="105" y2="105" stroke="black" stroke-width="3"/>
        <line x1="15" y1="105" x2="15" y2="110" stroke="black" stroke-width="3"/>
        <line x1="105" y1="105" x2="105" y2="110" stroke="black" stroke-width="3"/>
    </symbol>''',

    # --- EXPANSION BELLOWS ---
    'expansion_bellows': '''<symbol id="expansion_bellows" viewBox="0 0 100 40">
        <path d="M 20,10 Q 25,5 30,10 Q 35,15 40,10 Q 45,5 50,10 Q 55,15 60,10 Q 65,5 70,10 Q 75,15 80,10" 
              fill="none" stroke="black" stroke-width="2.5"/>
        <path d="M 20,30 Q 25,35 30,30 Q 35,25 40,30 Q 45,35 50,30 Q 55,25 60,30 Q 65,35 70,30 Q 75,25 80,30" 
              fill="none" stroke="black" stroke-width="2.5"/>
        <line x1="20" y1="10" x2="20" y2="30" stroke="black" stroke-width="2.5"/>
        <line x1="80" y1="10" x2="80" y2="30" stroke="black" stroke-width="2.5"/>
        <rect x="5" y="15" width="15" height="10" fill="white" stroke="black" stroke-width="3"/>
        <rect x="80" y="15" width="15" height="10" fill="white" stroke="black" stroke-width="3"/>
    </symbol>''',

    # --- PRESSURE REGULATOR ---
    'pressure_regulator': '''<symbol id="pressure_regulator" viewBox="0 0 100 100">
        <rect x="25" y="35" width="50" height="30" rx="5" fill="white" stroke="black" stroke-width="3"/>
        <rect x="35" y="10" width="30" height="25" fill="white" stroke="black" stroke-width="3"/>
        <path d="M 45,15 Q 50,20 45,25 Q 55,20 50,25 Q 45,30 50,35" stroke="black" stroke-width="2" fill="none"/>
        <rect x="48" y="5" width="4" height="10" fill="black"/>
        <circle cx="50" cy="5" r="5" fill="none" stroke="black" stroke-width="2"/>
        <line x1="35" y1="35" x2="65" y2="35" stroke="black" stroke-width="2"/>
        <rect x="5" y="45" width="20" height="10" fill="white" stroke="black" stroke-width="3"/>
        <rect x="75" y="45" width="20" height="10" fill="white" stroke="black" stroke-width="3"/>
        <circle cx="50" cy="65" r="3" fill="black"/>
        <line x1="50" y1="65" x2="50" y2="75" stroke="black" stroke-width="1.5"/>
    </symbol>''',

    # --- CATCH POT ---
    'catch_pot': '''<symbol id="catch_pot" viewBox="0 0 80 100">
        <rect x="20" y="30" width="40" height="50" rx="5" fill="white" stroke="black" stroke-width="3"/>
        <ellipse cx="40" cy="30" rx="20" ry="10" fill="white" stroke="black" stroke-width="3"/>
        <ellipse cx="40" cy="80" rx="20" ry="10" fill="white" stroke="black" stroke-width="3"/>
        <line x1="25" y1="55" x2="55" y2="55" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
        <rect x="35" y="15" width="10" height="15" fill="white" stroke="black" stroke-width="2.5"/>
        <rect x="60" y="50" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
        <rect x="35" y="80" width="10" height="15" fill="white" stroke="black" stroke-width="2.5"/>
    </symbol>''',

    # --- SOLENOID VALVE ---
    'solenoid_valve': '''<symbol id="solenoid_valve" viewBox="0 0 80 80">
        <rect x="20" y="35" width="40" height="20" fill="white" stroke="black" stroke-width="3"/>
        <rect x="30" y="15" width="20" height="20" rx="3" fill="white" stroke="black" stroke-width="2.5"/>
        <line x1="35" y1="20" x2="45" y2="20" stroke="black" stroke-width="1"/>
        <line x1="35" y1="25" x2="45" y2="25" stroke="black" stroke-width="1"/>
        <line x1="35" y1="30" x2="45" y2="30" stroke="black" stroke-width="1"/>
        <circle cx="40" cy="10" r="3" fill="black"/>
        <line x1="40" y1="10" x2="40" y2="15" stroke="black" stroke-width="2"/>
        <path d="M 30,45 L 40,40 L 50,45" fill="none" stroke="black" stroke-width="2"/>
        <rect x="5" y="40" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
        <rect x="60" y="40" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    </symbol>''',

    # --- CONTROL PANEL (Detailed) ---
    'control_panel_detailed': '''<symbol id="control_panel_detailed" viewBox="0 0 200 250">
        <rect x="10" y="10" width="180" height="230" rx="5" fill="white" stroke="black" stroke-width="4"/>
        <rect x="20" y="20" width="160" height="210" fill="none" stroke="black" stroke-width="2"/>
        <rect x="30" y="30" width="140" height="30" fill="white" stroke="black" stroke-width="1.5"/>
        <text x="100" y="50" text-anchor="middle" font-size="14" font-weight="bold">CONTROL PANEL</text>
        
        <rect x="40" y="70" width="60" height="45" fill="#e0e0e0" stroke="black" stroke-width="2"/>
        <text x="70" y="95" text-anchor="middle" font-size="10">HMI</text>
        
        <rect x="110" y="70" width="60" height="45" fill="#e0e0e0" stroke="black" stroke-width="2"/>
        <text x="140" y="95" text-anchor="middle" font-size="10">VFD</text>
        
        <circle cx="50" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
        <circle cx="75" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
        <circle cx="100" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
        <circle cx="125" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
        <circle cx="150" cy="130" r="8" fill="none" stroke="black" stroke-width="2"/>
        
        <rect x="40" y="150" width="25" height="25" rx="3" fill="white" stroke="black" stroke-width="2"/>
        <rect x="77" y="150" width="25" height="25" rx="3" fill="white" stroke="black" stroke-width="2"/>
        <rect x="114" y="150" width="25" height="25" rx="3" fill="white" stroke="black" stroke-width="2"/>
        <rect x="151" y="150" width="25" height="25" rx="3" fill="white" stroke="black" stroke-width="2"/>
        
        <rect x="30" y="190" width="140" height="30" fill="none" stroke="black" stroke-width="1.5"/>
        <text x="100" y="180" text-anchor="middle" font-size="8">TERMINAL STRIP</text>
        <line x1="30" y1="205" x2="170" y2="205" stroke="black" stroke-width="1"/>
        <line x1="40" y1="190" x2="40" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="55" y1="190" x2="55" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="70" y1="190" x2="70" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="85" y1="190" x2="85" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="100" y1="190" x2="100" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="115" y1="190" x2="115" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="130" y1="190" x2="130" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="145" y1="190" x2="145" y2="220" stroke="black" stroke-width="0.5"/>
        <line x1="160" y1="190" x2="160" y2="220" stroke="black" stroke-width="0.5"/>
    </symbol>''',

    # --- DRAIN VALVE (Small) ---
    'valve_drain': '''<symbol id="valve_drain" viewBox="0 0 40 40">
        <rect x="10" y="15" width="20" height="10" fill="white" stroke="black" stroke-width="2"/>
        <line x1="20" y1="15" x2="20" y2="5" stroke="black" stroke-width="2"/>
        <circle cx="20" cy="5" r="3" fill="none" stroke="black" stroke-width="1.5"/>
        <rect x="18" y="25" width="4" height="10" fill="white" stroke="black" stroke-width="2"/>
    </symbol>''',

    # --- FLAME ARRESTOR ---
    'flame_arrestor': '''<symbol id="flame_arrestor" viewBox="0 0 60 40">
        <rect x="15" y="10" width="30" height="20" fill="white" stroke="black" stroke-width="3"/>
        <line x1="25" y1="10" x2="25" y2="30" stroke="black" stroke-width="1.5"/>
        <line x1="30" y1="10" x2="30" y2="30" stroke="black" stroke-width="1.5"/>
        <line x1="35" y1="10" x2="35" y2="30" stroke="black" stroke-width="1.5"/>
        <rect x="0" y="15" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
        <rect x="45" y="15" width="15" height="10" fill="white" stroke="black" stroke-width="2.5"/>
    </symbol>''',
}

# Additional line type definitions for reference accuracy

REFERENCE_LINE_TYPES = {
    'process_heavy': {'width': 4, 'color': 'black', 'dash': None},
    'process_medium': {'width': 3, 'color': 'black', 'dash': None},
    'process_light': {'width': 2, 'color': 'black', 'dash': None},
    'instrument_signal': {'width': 0.8, 'color': 'black', 'dash': '4,2'},
    'electrical_power': {'width': 1.5, 'color': 'black', 'dash': '2,2'},
    'electrical_signal': {'width': 0.8, 'color': 'black', 'dash': '2,2'},
}

# Component data matching reference

REFERENCE_EQUIPMENT_LIST = [
    {'tag': 'F-001', 'description': 'SUCTION FILTER', 'type': 'filter_suction', 'size': '10”', 'rating': '150#'},
    {'tag': 'P-001', 'description': 'CENTRIFUGAL PUMP', 'type': 'pump_kdp330', 'model': 'KDP-330'},
    {'tag': 'Y-001', 'description': 'Y-STRAINER', 'type': 'strainer_y', 'size': '10”', 'rating': '150#'},
    {'tag': 'PSV-001', 'description': 'PRESSURE SAFETY VALVE', 'type': 'psv', 'set_pressure': '10 kg/cm²'},
    {'tag': 'PR-001', 'description': 'PRESSURE REGULATOR', 'type': 'pressure_regulator'},
    {'tag': 'CP-001', 'description': 'CONTROL PANEL', 'type': 'control_panel_detailed'},
    {'tag': 'EB-001', 'description': 'EXPANSION BELLOWS', 'type': 'expansion_bellows'},
    {'tag': 'CT-001', 'description': 'CATCH POT', 'type': 'catch_pot'},
]
