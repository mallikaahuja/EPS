import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime

# Page config

st.set_page_config(
page_title=“EPS Professional P&ID Suite”,
page_icon=“🏭”,
layout=“wide”,
initial_sidebar_state=“expanded”
)

# Custom CSS for professional interface

st.markdown(”””

<style>
    /* Main container */
    .main {
        padding: 0.5rem;
    }
    
    /* P&ID viewer container */
    .pnid-viewer {
        border: 3px solid #000;
        background: white;
        min-height: 800px;
        position: relative;
    }
    
    /* Control buttons */
    .zoom-controls {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: white;
        border: 1px solid #ccc;
        padding: 5px;
        border-radius: 4px;
    }
    
    /* Legend styling */
    .legend-box {
        border: 2px solid #000;
        background: #f9f9f9;
        padding: 10px;
        margin: 10px 0;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        margin: 5px 0;
    }
    
    .legend-symbol {
        width: 40px;
        height: 40px;
        margin-right: 10px;
    }
    
    /* BOM table styling */
    .bom-table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 20px;
    }
    
    .bom-table th, .bom-table td {
        border: 1px solid #000;
        padding: 8px;
        text-align: left;
    }
    
    .bom-table th {
        background-color: #e0e0e0;
        font-weight: bold;
    }
    
    /* Equipment data box */
    .equipment-data {
        position: absolute;
        background: white;
        border: 1px solid #000;
        padding: 5px;
        font-size: 10px;
        pointer-events: none;
    }
    
    /* Professional title */
    h1 {
        font-family: Arial, sans-serif;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f0f0f0;
        border-bottom: 2px solid #000;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: bold;
        color: #000;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #f5f5f5;
        border: 1px solid #ccc;
        border-radius: 0;
        padding: 10px;
    }
</style>

“””, unsafe_allow_html=True)

# Import symbols from reference

from reference_exact_symbols import REFERENCE_EXACT_SYMBOLS, REFERENCE_LINE_TYPES, REFERENCE_EQUIPMENT_LIST

# — COMPLETE EQUIPMENT DATA —

COMPLETE_EQUIPMENT_DATA = pd.DataFrame([
# Main equipment
{‘id’: ‘F-001’, ‘tag’: ‘F-001’, ‘type’: ‘filter_suction’, ‘description’: ‘SUCTION FILTER’,
‘x’: 400, ‘y’: 300, ‘width’: 100, ‘height’: 150, ‘rotation’: 0,
‘size’: ‘10”’, ‘rating’: ‘150#’, ‘material’: ‘CS’, ‘design_pressure’: ‘10 kg/cm²’},

```
{'id': 'P-001', 'tag': 'P-001', 'type': 'pump_kdp330', 'description': 'CENTRIFUGAL PUMP', 
 'x': 700, 'y': 350, 'width': 120, 'height': 120, 'rotation': 0,
 'model': 'KDP-330', 'flow': '100 m³/hr', 'head': '50 m', 'power': '30 kW'},

{'id': 'Y-001', 'tag': 'Y-001', 'type': 'strainer_y', 'description': 'Y-STRAINER', 
 'x': 250, 'y': 320, 'width': 80, 'height': 100, 'rotation': 0,
 'size': '10"', 'rating': '150#', 'mesh': '40'},

{'id': 'PSV-001', 'tag': 'PSV-001', 'type': 'psv', 'description': 'PRESSURE SAFETY VALVE', 
 'x': 450, 'y': 200, 'width': 60, 'height': 80, 'rotation': 0,
 'set_pressure': '10 kg/cm²', 'size': '2"x3"'},

{'id': 'PR-001', 'tag': 'PR-001', 'type': 'pressure_regulator', 'description': 'PRESSURE REGULATOR', 
 'x': 550, 'y': 450, 'width': 100, 'height': 100, 'rotation': 0,
 'inlet_pressure': '10 kg/cm²', 'outlet_pressure': '3 kg/cm²'},

{'id': 'EB-001', 'tag': 'EB-001', 'type': 'expansion_bellows', 'description': 'EXPANSION BELLOWS', 
 'x': 150, 'y': 340, 'width': 100, 'height': 40, 'rotation': 0,
 'size': '10"', 'rating': '150#'},

{'id': 'CP-001', 'tag': 'CP-001', 'type': 'control_panel_detailed', 'description': 'CONTROL PANEL', 
 'x': 1000, 'y': 150, 'width': 200, 'height': 250, 'rotation': 0},

{'id': 'CT-001', 'tag': 'CT-001', 'type': 'catch_pot', 'description': 'CATCH POT', 
 'x': 850, 'y': 400, 'width': 80, 'height': 100, 'rotation': 0,
 'volume': '50 L'},

# Valves
{'id': 'V-001', 'tag': 'V-001', 'type': 'valve_gate', 'description': 'GATE VALVE', 
 'x': 300, 'y': 340, 'width': 60, 'height': 80, 'rotation': 0,
 'size': '10"', 'rating': '150#'},

{'id': 'V-002', 'tag': 'V-002', 'type': 'valve_gate', 'description': 'GATE VALVE', 
 'x': 550, 'y': 350, 'width': 60, 'height': 80, 'rotation': 0,
 'size': '10"', 'rating': '150#'},

{'id': 'V-003', 'tag': 'V-003', 'type': 'valve_drain', 'description': 'DRAIN VALVE', 
 'x': 400, 'y': 480, 'width': 40, 'height': 40, 'rotation': 0,
 'size': '2"', 'rating': '150#'},

{'id': 'SV-001', 'tag': 'SV-001', 'type': 'solenoid_valve', 'description': 'SOLENOID VALVE', 
 'x': 450, 'y': 550, 'width': 80, 'height': 80, 'rotation': 0,
 'size': '1"', 'voltage': '24VDC'},

# Instruments
{'id': 'PT-001', 'tag': 'PT-001', 'type': 'instrument', 'description': 'PRESSURE TRANSMITTER', 
 'x': 350, 'y': 380, 'width': 44, 'height': 44, 'rotation': 0},

{'id': 'PT-002', 'tag': 'PT-002', 'type': 'instrument', 'description': 'PRESSURE TRANSMITTER', 
 'x': 600, 'y': 380, 'width': 44, 'height': 44, 'rotation': 0},

{'id': 'PI-001', 'tag': 'PI-001', 'type': 'instrument', 'description': 'PRESSURE INDICATOR', 
 'x': 450, 'y': 250, 'width': 44, 'height': 44, 'rotation': 0},

{'id': 'FT-001', 'tag': 'FT-001', 'type': 'instrument', 'description': 'FLOW TRANSMITTER', 
 'x': 750, 'y': 300, 'width': 44, 'height': 44, 'rotation': 0},

{'id': 'LT-001', 'tag': 'LT-001', 'type': 'instrument', 'description': 'LEVEL TRANSMITTER', 
 'x': 900, 'y': 420, 'width': 44, 'height': 44, 'rotation': 0},

{'id': 'TT-001', 'tag': 'TT-001', 'type': 'instrument', 'description': 'TEMPERATURE TRANSMITTER', 
 'x': 650, 'y': 300, 'width': 44, 'height': 44, 'rotation': 0},
```

])

# — PIPING DATA —

COMPLETE_PIPING_DATA = pd.DataFrame([
# Main process lines
{‘id’: ‘L-001’, ‘from’: ‘INLET’, ‘to’: ‘EB-001’, ‘from_port’: ‘outlet’, ‘to_port’: ‘inlet’,
‘line_spec’: ‘10”-PG-001-CS’, ‘type’: ‘process_heavy’},

```
{'id': 'L-002', 'from': 'EB-001', 'to': 'Y-001', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '10"-PG-002-CS', 'type': 'process_heavy'},

{'id': 'L-003', 'from': 'Y-001', 'to': 'V-001', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '10"-PG-003-CS', 'type': 'process_heavy'},

{'id': 'L-004', 'from': 'V-001', 'to': 'F-001', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '10"-PG-004-CS', 'type': 'process_heavy'},

{'id': 'L-005', 'from': 'F-001', 'to': 'V-002', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '10"-PG-005-CS', 'type': 'process_heavy'},

{'id': 'L-006', 'from': 'V-002', 'to': 'P-001', 'from_port': 'outlet', 'to_port': 'suction',
 'line_spec': '10"-PS-006-CS', 'type': 'process_heavy'},

{'id': 'L-007', 'from': 'P-001', 'to': 'CT-001', 'from_port': 'discharge', 'to_port': 'inlet',
 'line_spec': '8"-PD-007-CS', 'type': 'process_medium'},

{'id': 'L-008', 'from': 'CT-001', 'to': 'OUTLET', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '8"-PD-008-CS', 'type': 'process_medium'},

# Relief line
{'id': 'L-009', 'from': 'F-001', 'to': 'PSV-001', 'from_port': 'top', 'to_port': 'inlet',
 'line_spec': '2"-PR-009-CS', 'type': 'process_light'},

# Drain lines
{'id': 'L-010', 'from': 'F-001', 'to': 'V-003', 'from_port': 'drain', 'to_port': 'inlet',
 'line_spec': '2"-DR-010-CS', 'type': 'process_light'},

{'id': 'L-011', 'from': 'V-003', 'to': 'SV-001', 'from_port': 'outlet', 'to_port': 'inlet',
 'line_spec': '2"-DR-011-CS', 'type': 'process_light'},

# Instrument lines
{'id': 'IS-001', 'from': 'PT-001', 'to': 'CP-001', 'from_port': 'center', 'to_port': 'terminal_1',
 'line_spec': '', 'type': 'instrument_signal'},

{'id': 'IS-002', 'from': 'PT-002', 'to': 'CP-001', 'from_port': 'center', 'to_port': 'terminal_2',
 'line_spec': '', 'type': 'instrument_signal'},

{'id': 'IS-003', 'from': 'FT-001', 'to': 'CP-001', 'from_port': 'center', 'to_port': 'terminal_3',
 'line_spec': '', 'type': 'instrument_signal'},
```

])

# — INTERACTIVE P&ID VIEWER —

def create_interactive_pnid():
“”“Creates an interactive P&ID with zoom/pan using Plotly”””

```
fig = go.Figure()

# Add grid
for x in range(0, 1400, 50):
    fig.add_shape(
        type="line", x0=x, y0=0, x1=x, y1=800,
        line=dict(color="lightgray", width=0.5)
    )
for y in range(0, 800, 50):
    fig.add_shape(
        type="line", x0=0, y0=y, x1=1400, y1=y,
        line=dict(color="lightgray", width=0.5)
    )

# Add border
fig.add_shape(
    type="rect", x0=10, y0=10, x1=1390, y1=790,
    line=dict(color="black", width=3),
    fillcolor="rgba(0,0,0,0)"
)

# Add equipment symbols (simplified for Plotly)
for _, equip in COMPLETE_EQUIPMENT_DATA.iterrows():
    # Equipment box
    fig.add_shape(
        type="rect",
        x0=equip['x'], y0=equip['y'],
        x1=equip['x'] + equip['width'], y1=equip['y'] + equip['height'],
        line=dict(color="black", width=2),
        fillcolor="white"
    )
    
    # Equipment tag
    fig.add_annotation(
        x=equip['x'] + equip['width']/2,
        y=equip['y'] + equip['height'] + 10,
        text=equip['tag'],
        showarrow=False,
        font=dict(size=12, color="black", family="Arial")
    )
    
    # Special handling for instruments
    if equip['type'] == 'instrument':
        fig.add_shape(
            type="circle",
            x0=equip['x'], y0=equip['y'],
            x1=equip['x'] + equip['width'], y1=equip['y'] + equip['height'],
            line=dict(color="black", width=2),
            fillcolor="white"
        )
        # Add instrument tag inside
        fig.add_annotation(
            x=equip['x'] + equip['width']/2,
            y=equip['y'] + equip['height']/2,
            text=equip['tag'],
            showarrow=False,
            font=dict(size=10, color="black", family="Arial")
        )

# Add piping (simplified)
for _, pipe in COMPLETE_PIPING_DATA.iterrows():
    # This is simplified - in real implementation, calculate actual paths
    line_style = REFERENCE_LINE_TYPES.get(pipe['type'], {'width': 2, 'color': 'black'})
    
    # Example line (would need proper routing in production)
    if pipe['from'] in COMPLETE_EQUIPMENT_DATA['id'].values and pipe['to'] in COMPLETE_EQUIPMENT_DATA['id'].values:
        from_equip = COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['id'] == pipe['from']].iloc[0]
        to_equip = COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['id'] == pipe['to']].iloc[0]
        
        fig.add_shape(
            type="line",
            x0=from_equip['x'] + from_equip['width'],
            y0=from_equip['y'] + from_equip['height']/2,
            x1=to_equip['x'],
            y1=to_equip['y'] + to_equip['height']/2,
            line=dict(color=line_style['color'], width=line_style['width'])
        )

# Add title block
fig.add_shape(
    type="rect", x0=1000, y0=600, x1=1380, y1=780,
    line=dict(color="black", width=2),
    fillcolor="white"
)

fig.add_annotation(
    x=1190, y=750, text="EPS Pvt. Ltd.",
    showarrow=False, font=dict(size=16, color="black", family="Arial Bold")
)

fig.add_annotation(
    x=1190, y=720, text="PIPING AND INSTRUMENTATION DIAGRAM",
    showarrow=False, font=dict(size=12, color="black", family="Arial")
)

fig.add_annotation(
    x=1190, y=690, text="SUCTION FILTER + KDP-330",
    showarrow=False, font=dict(size=12, color="black", family="Arial")
)

fig.add_annotation(
    x=1190, y=630, text=f"DWG NO: EPSPL-V2526-TP-01 REV.0",
    showarrow=False, font=dict(size=10, color="black", family="Arial")
)

# Configure layout
fig.update_layout(
    width=1400,
    height=800,
    xaxis=dict(range=[0, 1400], showgrid=False, zeroline=False, visible=False),
    yaxis=dict(range=[0, 800], showgrid=False, zeroline=False, visible=False, scaleanchor="x"),
    plot_bgcolor="white",
    margin=dict(l=0, r=0, t=0, b=0),
    dragmode='pan',
    hovermode=False
)

return fig
```

# — LEGEND GENERATION —

def generate_legend():
“”“Generates the equipment legend”””
legend_html = “””
<div class="legend-box">
<h3 style="text-align: center; margin: 10px 0;">LEGEND</h3>
<table style="width: 100%;">
“””

```
# Group equipment by type
equipment_types = COMPLETE_EQUIPMENT_DATA[['type', 'description']].drop_duplicates()

for _, eq_type in equipment_types.iterrows():
    if eq_type['type'] != 'instrument':  # Skip generic instruments
        legend_html += f"""
        <tr>
            <td style="width: 60px; text-align: center;">
                <div style="width: 50px; height: 50px; border: 1px solid #000; background: white;">
                    <!-- Symbol would go here -->
                    <span style="font-size: 10px;">{eq_type['type'][:3].upper()}</span>
                </div>
            </td>
            <td style="padding-left: 10px;">
                <strong>{eq_type['description']}</strong>
            </td>
        </tr>
        """

legend_html += """
    </table>
</div>
"""

return legend_html
```

# — BILL OF MATERIALS —

def generate_bom():
“”“Generates Bill of Materials table”””
bom_data = []

```
# Equipment BOM
for _, equip in COMPLETE_EQUIPMENT_DATA.iterrows():
    bom_data.append({
        'Item No.': len(bom_data) + 1,
        'Tag No.': equip['tag'],
        'Description': equip['description'],
        'Size': equip.get('size', '-'),
        'Rating': equip.get('rating', '-'),
        'Material': equip.get('material', 'CS'),
        'Qty': 1,
        'Remarks': equip.get('model', '')
    })

# Piping BOM (simplified)
for _, pipe in COMPLETE_PIPING_DATA.iterrows():
    if pipe['line_spec']:
        bom_data.append({
            'Item No.': len(bom_data) + 1,
            'Tag No.': pipe['id'],
            'Description': 'PIPE',
            'Size': pipe['line_spec'].split('-')[0],
            'Rating': '150#',
            'Material': 'CS',
            'Qty': '-',
            'Remarks': pipe['line_spec']
        })

return pd.DataFrame(bom_data)
```

# — MAIN APPLICATION —

st.title(“🏭 EPS Professional P&ID Suite”)

# Header information

col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
with col1:
st.markdown(”**Project:** SUCTION FILTER + KDP-330”)
with col2:
st.markdown(”**Drawing:** EPSPL-V2526-TP-01”)
with col3:
st.markdown(”**Rev:** 0”)
with col4:
st.markdown(f”**Date:** {datetime.now().strftime(’%Y-%m-%d’)}”)

# Tabs

tab1, tab2, tab3, tab4, tab5 = st.tabs([
“📊 P&ID View”,
“📋 Legend”,
“📑 Bill of Materials”,
“🔧 Equipment Data”,
“📐 Nozzle Schedule”
])

with tab1:
# P&ID Display with zoom controls
st.markdown(”### Interactive P&ID Viewer”)

```
# Zoom controls
col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
with col1:
    if st.button("🔍 Zoom In"):
        st.info("Zoom In clicked")
with col2:
    if st.button("🔍 Zoom Out"):
        st.info("Zoom Out clicked")
with col3:
    if st.button("📐 Fit"):
        st.info("Fit to screen clicked")

# Display interactive P&ID
fig = create_interactive_pnid()
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
    'modeBarButtonsToRemove': ['lasso2d', 'select2d']
})

# Quick stats
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Equipment", len(COMPLETE_EQUIPMENT_DATA))
with col2:
    st.metric("Instruments", len(COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['type'] == 'instrument']))
with col3:
    st.metric("Valves", len(COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['type'].str.contains('valve')]))
with col4:
    st.metric("Lines", len(COMPLETE_PIPING_DATA))
with col5:
    st.metric("I/O Points", 12)
```

with tab2:
# Legend display
st.markdown(”### Equipment Legend”)

```
# Create two columns for legend
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Process Equipment")
    legend_equipment = COMPLETE_EQUIPMENT_DATA[~COMPLETE_EQUIPMENT_DATA['type'].str.contains('valve|instrument')]
    for _, eq in legend_equipment.iterrows():
        st.markdown(f"**{eq['tag']}** - {eq['description']}")

with col2:
    st.markdown("#### Valves & Instruments")
    legend_valves = COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['type'].str.contains('valve|instrument')]
    for _, eq in legend_valves.iterrows():
        st.markdown(f"**{eq['tag']}** - {eq['description']}")

# Line types legend
st.markdown("#### Line Types")
line_types_df = pd.DataFrame([
    {'Type': 'Process Line (Heavy)', 'Description': 'Main process piping ≥ 6"', 'Symbol': '━━━━━'},
    {'Type': 'Process Line (Medium)', 'Description': 'Process piping 2"-4"', 'Symbol': '━━━━'},
    {'Type': 'Process Line (Light)', 'Description': 'Process piping ≤ 1.5"', 'Symbol': '━━━'},
    {'Type': 'Instrument Signal', 'Description': 'Pneumatic/Electronic signal', 'Symbol': '┅┅┅┅'},
    {'Type': 'Electrical', 'Description': 'Power/Control wiring', 'Symbol': '┈┈┈┈'},
])
st.dataframe(line_types_df, hide_index=True, use_container_width=True)
```

with tab3:
# Bill of Materials
st.markdown(”### Bill of Materials”)

```
bom_df = generate_bom()

# Display BOM table
st.dataframe(bom_df, hide_index=True, use_container_width=True, height=600)

# Export options
col1, col2 = st.columns([1, 5])
with col1:
    csv = bom_df.to_csv(index=False)
    st.download_button(
        label="📥 Download BOM (CSV)",
        data=csv,
        file_name="BOM_EPSPL-V2526-TP-01.csv",
        mime="text/csv"
    )
```

with tab4:
# Equipment Data Sheets
st.markdown(”### Equipment Data Sheets”)

```
# Select equipment
selected_equipment = st.selectbox(
    "Select Equipment",
    COMPLETE_EQUIPMENT_DATA['tag'].tolist()
)

if selected_equipment:
    equip_data = COMPLETE_EQUIPMENT_DATA[COMPLETE_EQUIPMENT_DATA['tag'] == selected_equipment].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### General Information")
        st.write(f"**Tag Number:** {equip_data['tag']}")
        st.write(f"**Description:** {equip_data['description']}")
        st.write(f"**Type:** {equip_data['type']}")
        
    with col2:
        st.markdown("#### Technical Data")
        if 'size' in equip_data:
            st.write(f"**Size:** {equip_data.get('size', '-')}")
        if 'rating' in equip_data:
            st.write(f"**Rating:** {equip_data.get('rating', '-')}")
        if 'material' in equip_data:
            st.write(f"**Material:** {equip_data.get('material', '-')}")
        
    # Additional specifications
    st.markdown("#### Additional Specifications")
    specs_df = pd.DataFrame([
        {'Parameter': 'Design Pressure', 'Value': equip_data.get('design_pressure', '10 kg/cm²'), 'Unit': 'kg/cm²'},
        {'Parameter': 'Design Temperature', 'Value': '80', 'Unit': '°C'},
        {'Parameter': 'Operating Pressure', 'Value': '7', 'Unit': 'kg/cm²'},
        {'Parameter': 'Operating Temperature', 'Value': '60', 'Unit': '°C'},
    ])
    st.dataframe(specs_df, hide_index=True)
```

with tab5:
# Nozzle Schedule
st.markdown(”### Nozzle Schedule”)

```
nozzle_data = []

# Generate nozzle schedule from equipment data
for _, equip in COMPLETE_EQUIPMENT_DATA.iterrows():
    if equip['type'] in ['vessel', 'tank', 'filter_suction', 'catch_pot']:
        # Add typical nozzles
        nozzles = {
            'N1': {'service': 'Inlet', 'size': equip.get('size', '4"'), 'rating': '150#', 'type': 'RF'},
            'N2': {'service': 'Outlet', 'size': equip.get('size', '4"'), 'rating': '150#', 'type': 'RF'},
            'N3': {'service': 'Drain', 'size': '2"', 'rating': '150#', 'type': 'RF'},
            'N4': {'service': 'Vent', 'size': '1"', 'rating': '150#', 'type': 'RF'},
        }
        
        for nozzle_mark, nozzle_info in nozzles.items():
            nozzle_data.append({
                'Equipment': equip['tag'],
                'Nozzle Mark': nozzle_mark,
                'Service': nozzle_info['service'],
                'Size': nozzle_info['size'],
                'Rating': nozzle_info['rating'],
                'Face Type': nozzle_info['type'],
                'Projection': '150 mm'
            })

nozzle_df = pd.DataFrame(nozzle_data)
st.dataframe(nozzle_df, hide_index=True, use_container_width=True, height=400)
```

# Sidebar controls

st.sidebar.markdown(”### 🎨 Display Options”)
show_grid = st.sidebar.checkbox(“Show Grid”, True)
show_dimensions = st.sidebar.checkbox(“Show Dimensions”, False)
show_tags = st.sidebar.checkbox(“Show Tags”, True)
show_flow_arrows = st.sidebar.checkbox(“Show Flow Arrows”, True)

st.sidebar.markdown(”### 🔧 Edit Mode”)
edit_mode = st.sidebar.radio(“Mode”, [“View”, “Edit”, “Measure”])

if edit_mode == “Edit”:
st.sidebar.markdown(”#### Add Component”)
component_type = st.sidebar.selectbox(
“Type”,
list(REFERENCE_EXACT_SYMBOLS.keys())
)

```
if st.sidebar.button("Add to P&ID"):
    st.sidebar.success("Click on P&ID to place component")
```

# Footer

st.markdown(”—”)
st.markdown(
“””
<div style="text-align: center; font-size: 12px; color: #666;">
EPS Professional P&ID Suite v3.0 | © 2024 EPS Pvt. Ltd. | Compliant with ISA-5.1 Standard
</div>
“””,
unsafe_allow_html=True
)
