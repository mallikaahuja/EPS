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

# Import professional modules

from professional_symbols import PROFESSIONAL_ISA_SYMBOLS, get_component_symbol, create_professional_instrument_bubble, create_pipe_with_spec, ARROW_MARKERS
from advanced_rendering import ProfessionalRenderer, create_suction_filter_system
from control_systems import ControlSystemAnalyzer, PipeRouter, PnIDValidator

# — CONFIGURATION —

st.set_page_config(
    layout="wide",
    page_title="EPS Professional P&ID Generator",
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI

st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #0066cc;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0052a3;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #f0f2f5;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0px 20px;
        background-color: white;
        border-radius: 4px;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* P&ID Display Area */
    .pnid-container {
        background-color: white;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar configuration

st.sidebar.image("https://via.placeholder.com/300x100/0066cc/ffffff?text=EPS+P%26ID+Suite", use_column_width=True)
st.sidebar.markdown("---")
st.sidebar.title("⚙️ P&ID Configuration")

# Drawing Standards

st.sidebar.markdown("### 📐 Drawing Standards")
col1, col2 = st.sidebar.columns(2)
with col1:
    drawing_standard = st.selectbox(
        "Standard",
        ["ISA", "DIN", "ISO", "JIS"],
        help="Select the P&ID drawing standard"
    )
with col2:
    drawing_size = st.selectbox(
        "Size",
        ["A3", "A2", "A1", "A0"],
        help="Select drawing size"
    )

# Visual Controls with professional defaults

st.sidebar.markdown("### 🎨 Visual Controls")

# Use columns for compact layout

col1, col2 = st.sidebar.columns(2)
with col1:
    GRID_VISIBLE = st.checkbox("Show Grid", True)
    DIMENSIONS_VISIBLE = st.checkbox("Show Dimensions", False)
with col2:
    ANNOTATIONS_VISIBLE = st.checkbox("Show Annotations", True)
    FLOW_ARROWS = st.checkbox("Show Flow Arrows", True)

# Sliders for fine control

GRID_SPACING = st.sidebar.slider("Grid Spacing (mm)", 10, 50, 25, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.0, 1.0, 0.1)

# Line weights based on standard

st.sidebar.markdown("### 📏 Line Weights")
line_weight_options = {
    "Major Process": st.sidebar.slider("Major Process", 2.0, 5.0, 3.0, 0.5),
    "Minor Process": st.sidebar.slider("Minor Process", 1.5, 3.0, 2.0, 0.5),
    "Instrument Signal": st.sidebar.slider("Instrument Signal", 0.5, 1.5, 0.7, 0.1),
    "Electrical": st.sidebar.slider("Electrical", 0.5, 1.5, 0.7, 0.1),
}

# Advanced Features

st.sidebar.markdown("### 🚀 Advanced Features")
enable_smart_routing = st.sidebar.checkbox("Smart Pipe Routing", True)
enable_clash_detection = st.sidebar.checkbox("Clash Detection", True)
enable_auto_tag = st.sidebar.checkbox("Auto Tag Generation", True)
enable_3d_symbols = st.sidebar.checkbox("3D Effect on Symbols", True)

# Global constants

DRAWING_SIZES = {
    "A3": (420, 297),
    "A2": (594, 420),
    "A1": (841, 594),
    "A0": (1189, 841)
}

PADDING = 30
TITLE_BLOCK_HEIGHT = 180
TITLE_BLOCK_WIDTH = 594

# Initialize session state

if 'project_info' not in st.session_state:
    st.session_state.project_info = {
        'client': 'EPS Pvt. Ltd.',
        'project': 'SUCTION FILTER + KDP-330',
        'drawing_no': 'EPSPL-V2526-TP-01',
        'drawn_by': 'ABC',
        'checked_by': 'XYZ',
        'approved_by': 'PQR',
        'revision': '0',
        'date': datetime.datetime.now().strftime("%Y-%m-%d")
    }

# — ENHANCED P&ID CLASSES —

class ProfessionalPnidComponent:
    """Professional P&ID component with detailed rendering"""

    def __init__(self, row):
        self.id = str(row['id']).strip()
        self.tag = row.get('tag', self.id)
        self.component_type = str(row.get('Component', 'valve')).lower().replace(' ', '_')
        self.x = float(row.get('x', 0))
        self.y = float(row.get('y', 0))
        self.width = float(row.get('Width', 60)) * SYMBOL_SCALE
        self.height = float(row.get('Height', 60)) * SYMBOL_SCALE
        self.rotation = float(row.get('rotation', 0))
        
        # Check if instrument
        self.is_instrument = self._check_if_instrument()
        
        # Define connection ports based on type
        self.ports = self._define_professional_ports()
        
        # Additional properties for professional rendering
        self.material = row.get('material', 'CS')  # Carbon Steel default
        self.rating = row.get('rating', '150#')
        self.size = row.get('size', '')

    def _check_if_instrument(self):
        """Check if component is an instrument based on tag pattern"""
        if not self.tag:
            return False
        
        # ISA instrument tag pattern
        pattern = r'^[A-Z]{2,4}[-]?\d{3,4}[A-Z]?$'
        return bool(re.match(pattern, self.tag))

    def _define_professional_ports(self):
        """Define detailed connection ports for professional P&ID"""
        ports = {}
        
        if self.is_instrument:
            # Instrument standard ports
            ports = {
                'center': {'dx': self.width/2, 'dy': self.height/2},
                'top': {'dx': self.width/2, 'dy': 0},
                'bottom': {'dx': self.width/2, 'dy': self.height},
                'left': {'dx': 0, 'dy': self.height/2},
                'right': {'dx': self.width, 'dy': self.height/2},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        elif 'pump' in self.component_type:
            ports = {
                'suction': {'dx': 0, 'dy': self.height * 0.6},
                'discharge': {'dx': self.width * 0.5, 'dy': 0},
                'drain': {'dx': self.width * 0.2, 'dy': self.height},
                'vent': {'dx': self.width * 0.8, 'dy': 0},
                'seal_flush': {'dx': self.width, 'dy': self.height * 0.3},
                'default': {'dx': 0, 'dy': self.height * 0.6}
            }
        elif 'valve' in self.component_type:
            ports = {
                'inlet': {'dx': 0, 'dy': self.height/2},
                'outlet': {'dx': self.width, 'dy': self.height/2},
                'stem': {'dx': self.width/2, 'dy': 0},
                'body_drain': {'dx': self.width/2, 'dy': self.height},
                'default': {'dx': 0, 'dy': self.height/2}
            }
        elif 'vessel' in self.component_type or 'tank' in self.component_type:
            ports = {
                'top': {'dx': self.width/2, 'dy': 0},
                'bottom': {'dx': self.width/2, 'dy': self.height},
                'inlet': {'dx': 0, 'dy': self.height * 0.3},
                'outlet': {'dx': self.width, 'dy': self.height * 0.7},
                'drain': {'dx': self.width * 0.3, 'dy': self.height},
                'vent': {'dx': self.width * 0.7, 'dy': 0},
                'level_tap_high': {'dx': 0, 'dy': self.height * 0.2},
                'level_tap_low': {'dx': 0, 'dy': self.height * 0.8},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        elif 'filter' in self.component_type:
            ports = {
                'inlet': {'dx': self.width/2, 'dy': 0},
                'outlet': {'dx': self.width/2, 'dy': self.height},
                'drain': {'dx': self.width * 0.2, 'dy': self.height * 0.9},
                'vent': {'dx': self.width * 0.8, 'dy': self.height * 0.1},
                'dp_high': {'dx': 0, 'dy': self.height * 0.3},
                'dp_low': {'dx': 0, 'dy': self.height * 0.7},
                'default': {'dx': self.width/2, 'dy': 0}
            }
        else:
            # Generic ports
            ports = {
                'inlet': {'dx': 0, 'dy': self.height/2},
                'outlet': {'dx': self.width, 'dy': self.height/2},
                'top': {'dx': self.width/2, 'dy': 0},
                'bottom': {'dx': self.width/2, 'dy': self.height},
                'default': {'dx': self.width/2, 'dy': self.height/2}
            }
        
        return ports

    def get_port_coords(self, port_name):
        """Get absolute coordinates for a connection port"""
        port = self.ports.get(port_name) or self.ports.get('default')
        if port:
            # Apply rotation if needed
            if self.rotation != 0:
                # Rotate port position around component center
                cx, cy = self.width/2, self.height/2
                dx, dy = port['dx'] - cx, port['dy'] - cy
                
                angle = math.radians(self.rotation)
                new_dx = dx * math.cos(angle) - dy * math.sin(angle) + cx
                new_dy = dx * math.sin(angle) + dy * math.cos(angle) + cy
                
                return (self.x + new_dx, self.y + new_dy)
            else:
                return (self.x + port['dx'], self.y + port['dy'])
        
        return (self.x + self.width/2, self.y + self.height/2)


class ProfessionalPnidPipe:
    """Professional P&ID pipe with detailed specifications"""

    def __init__(self, row, component_map, router=None):
        self.id = row.get('Pipe No.', '')
        self.label = row.get('Label', '')
        self.line_type = row.get('pipe_type', 'process_line')
        
        # Parse pipe specification
        self._parse_pipe_spec()
        
        # Get components
        from_comp_id = str(row.get('From Component', '')).strip()
        to_comp_id = str(row.get('To Component', '')).strip()
        
        self.from_comp = component_map.get(from_comp_id)
        self.to_comp = component_map.get(to_comp_id)
        
        self.from_port = row.get('From Port', 'default')
        self.to_port = row.get('To Port', 'default')
        
        # Parse or calculate path
        polyline_str = str(row.get('Polyline Points (x, y)', '')).strip()
        
        if enable_smart_routing and router and not polyline_str and self.from_comp and self.to_comp:
            # Use smart routing
            start = self.from_comp.get_port_coords(self.from_port)
            end = self.to_comp.get_port_coords(self.to_port)
            self.points = router.find_path(start, end)
        else:
            # Use provided points or simple routing
            self.points = self._parse_polyline_points(polyline_str)
        
        # Determine flow direction
        self.with_arrow = self.line_type in ['process_line', 'process']
        
        # Additional properties
        self.insulation = row.get('insulation', False)
        self.heat_traced = row.get('heat_traced', False)

    def _parse_pipe_spec(self):
        """Parse pipe specification like 2"-PG-101-CS"""
        if self.label:
            match = re.match(r'^(\d+)"?-([A-Z]+)-(\d+)-([A-Z]+)$', self.label)
            if match:
                self.size = int(match.group(1))
                self.service = match.group(2)
                self.number = match.group(3)
                self.material = match.group(4)
            else:
                self.size = 2
                self.service = 'PG'
                self.number = '001'
                self.material = 'CS'
        else:
            self.size = 2
            self.service = 'PG'
            self.number = '001'
            self.material = 'CS'

    def _parse_polyline_points(self, polyline_str):
        """Parse polyline points from string"""
        points = []
        
        if polyline_str and polyline_str.lower() != 'nan':
            # Parse points like [(x1,y1), (x2,y2)]
            pts = re.findall(r'\(([-\d.]+),\s*([-\d.]+)\)', polyline_str)
            if pts:
                points = [(float(x), float(y)) for x, y in pts]
        
        # If no valid points but we have components, create simple path
        if not points and self.from_comp and self.to_comp:
            start = self.from_comp.get_port_coords(self.from_port)
            end = self.to_comp.get_port_coords(self.to_port)
            
            # Professional orthogonal routing
            points = self._create_orthogonal_path(start, end)
        
        return points

    def _create_orthogonal_path(self, start, end):
        """Create professional orthogonal path"""
        points = [start]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Determine routing strategy
        if abs(dx) > 50 and abs(dy) > 50:
            # Use intermediate points for cleaner routing
            if abs(dx) > abs(dy):
                # Horizontal preference
                mid_x = start[0] + dx * 0.7
                points.append((mid_x, start[1]))
                points.append((mid_x, end[1]))
            else:
                # Vertical preference
                mid_y = start[1] + dy * 0.7
                points.append((start[0], mid_y))
                points.append((end[0], mid_y))
        else:
            # Simple L-shape
            points.append((end[0], start[1]))
        
        points.append(end)
        return points

# — MAIN RENDERING FUNCTION —

def render_final_professional_pnid(components, pipes, project_info):
    """Render the final professional-quality P&ID"""

    # Initialize professional renderer
    renderer = ProfessionalRenderer()

    # Calculate drawing size
    width, height = DRAWING_SIZES[drawing_size]
    width *= 10  # Convert to pixels (assuming 10px/mm)
    height *= 10

    # Start SVG
    svg_parts = []
    svg_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
xmlns="http://www.w3.org/2000/svg" version="1.1"
style="font-family: Arial, Helvetica, sans-serif; background-color: white;">''')

    # Add professional definitions
    svg_parts.append(ARROW_MARKERS)
    svg_parts.append('<defs>')

    # Add all professional symbols
    for symbol_id, symbol_svg in PROFESSIONAL_ISA_SYMBOLS.items():
        svg_parts.append(symbol_svg)

    # Add custom patterns and filters
    svg_parts.append('''
    <pattern id="insulation" patternUnits="userSpaceOnUse" width="20" height="10">
        <path d="M 0,5 Q 5,0 10,5 T 20,5" stroke="black" stroke-width="0.5" fill="none"/>
    </pattern>
    
    <pattern id="heat-trace" patternUnits="userSpaceOnUse" width="20" height="20">
        <path d="M 0,10 L 20,10" stroke="red" stroke-width="1" stroke-dasharray="2,2"/>
    </pattern>
    
    <filter id="drop-shadow">
        <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
        <feOffset dx="2" dy="2" result="offsetblur"/>
        <feFlood flood-color="#000000" flood-opacity="0.3"/>
        <feComposite in2="offsetblur" operator="in"/>
        <feMerge>
            <feMergeNode/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>
</defs>''')

    # Layers
    svg_parts.append('')
    if GRID_VISIBLE:
        svg_parts.append(f'<g id="grid" opacity="0.3">')
        # Grid lines
        for x in range(0, int(width), GRID_SPACING * 4):
            svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#cccccc" stroke-width="0.5"/>')
        for y in range(0, int(height), GRID_SPACING * 4):
            svg_parts.append(f'<line x1="0" y1="{y}" x2="{x}" y2="{y}" stroke="#cccccc" stroke-width="0.5"/>') # Corrected x2 to x, not width
        svg_parts.append('</g>')

    # Drawing border
    svg_parts.append('')
    svg_parts.append(f'<rect x="{PADDING}" y="{PADDING}" width="{width-PADDING*2}" height="{height-PADDING*2}" '
                    f'fill="none" stroke="black" stroke-width="3"/>')
    svg_parts.append(f'<rect x="{PADDING+5}" y="{PADDING+5}" width="{width-PADDING*2-10}" height="{height-PADDING*2-10}" '
                    f'fill="none" stroke="black" stroke-width="1"/>')

    # Equipment layer
    svg_parts.append('')
    svg_parts.append('<g id="equipment">')

    for comp in components.values():
        if comp.is_instrument:
            # Render professional instrument bubble
            svg_parts.append(create_professional_instrument_bubble(
                comp.tag,
                comp.x + comp.width/2,
                comp.y + comp.height/2,
                min(comp.width, comp.height) / 2
            ))
        else:
            # Get professional symbol
            symbol = get_component_symbol(comp.component_type)
            if symbol:
                # Apply transformations
                transform = f'translate({comp.x},{comp.y})'
                if comp.rotation:
                    cx = comp.width / 2
                    cy = comp.height / 2
                    transform += f' rotate({comp.rotation},{cx},{cy})'
                
                # Add 3D effect for major equipment
                filter_attr = ''
                if enable_3d_symbols and comp.component_type in ['pump_centrifugal', 'vessel_vertical', 'filter']:
                    filter_attr = 'filter="url(#drop-shadow)"'
                
                svg_parts.append(f'<g transform="{transform}" {filter_attr}>')
                
                # Scale symbol to component size
                svg_parts.append(f'<g transform="scale({comp.width/80},{comp.height/80})">')
                svg_parts.append(symbol)
                svg_parts.append('</g>')
                
                # Add tag with professional styling
                if comp.tag:
                    tag_bg_width = len(comp.tag) * 8 + 6
                    tag_y = comp.height + 15
                    
                    # Tag background
                    svg_parts.append(f'<rect x="{comp.width/2 - tag_bg_width/2}" y="{tag_y - 12}" '
                                   f'width="{tag_bg_width}" height="16" '
                                   f'fill="white" stroke="black" stroke-width="0.5" rx="2"/>')
                    
                    # Tag text
                    svg_parts.append(f'<text x="{comp.width/2}" y="{tag_y}" '
                                   f'text-anchor="middle" font-size="11" font-weight="bold">{comp.tag}</text>')
                
                svg_parts.append('</g>')

    svg_parts.append('</g>')

    # Piping layer
    svg_parts.append('')
    svg_parts.append('<g id="piping">')

    for pipe in pipes:
        if len(pipe.points) >= 2:
            # Determine line weight based on size
            line_weight = line_weight_options.get("Major Process", 3.0) if pipe.size >= 4 else line_weight_options.get("Minor Process", 2.0)
            
            if pipe.line_type in ['instrumentation', 'instrument_signal']:
                line_weight = line_weight_options.get("Instrument Signal", 0.7)
            elif pipe.line_type == 'electrical':
                line_weight = line_weight_options.get("Electrical", 0.7)
            
            # Create professional pipe path
            svg_parts.append(create_pipe_with_spec(
                pipe.points,
                pipe.label,
                pipe.line_type
            ))
            
            # Add flow arrows if enabled
            if FLOW_ARROWS and pipe.with_arrow and len(pipe.points) >= 2:
                # Add arrow at 1/3 and 2/3 points
                for fraction in [0.33, 0.67]:
                    idx = int(len(pipe.points) * fraction)
                    if idx > 0 and idx < len(pipe.points):
                        p1 = pipe.points[idx-1]
                        p2 = pipe.points[idx]
                        
                        angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
                        mid_x = (p1[0] + p2[0]) / 2
                        mid_y = (p1[1] + p2[1]) / 2
                        
                        svg_parts.append(f'<g transform="translate({mid_x},{mid_y}) rotate({angle})">')
                        svg_parts.append(f'<polygon points="-8,-4 0,0 -8,4" fill="black"/>')
                        svg_parts.append('</g>')

    svg_parts.append('</g>')

    # Annotations layer
    if ANNOTATIONS_VISIBLE:
        svg_parts.append('')
        svg_parts.append('<g id="annotations">')
        
        # Add equipment callouts, dimensions, etc.
        # This would be expanded based on specific requirements
        
        svg_parts.append('</g>')

    # Title block
    svg_parts.append('')
    tb_x = width - TITLE_BLOCK_WIDTH - PADDING - 10
    tb_y = height - TITLE_BLOCK_HEIGHT - PADDING - 10

    svg_parts.append(f'<g transform="translate({tb_x},{tb_y})">')

    # Title block border
    svg_parts.append(f'<rect x="0" y="0" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT}" '
                    f'fill="white" stroke="black" stroke-width="2"/>')

    # Internal divisions
    divisions = [40, 80, 110, 140, 160]
    for y in divisions:
        svg_parts.append(f'<line x1="0" y1="{y}" x2="{TITLE_BLOCK_WIDTH}" y2="{y}" stroke="black" stroke-width="1"/>')

    # Vertical divisions
    svg_parts.append(f'<line x1="200" y1="0" x2="200" y2="140" stroke="black" stroke-width="1"/>')
    svg_parts.append(f'<line x1="400" y1="0" x2="400" y2="140" stroke="black" stroke-width="1"/>')

    # Content
    svg_parts.append(f'<text x="100" y="25" text-anchor="middle" font-size="18" font-weight="bold">{project_info["client"]}</text>')
    svg_parts.append(f'<text x="300" y="60" text-anchor="middle" font-size="14" font-weight="bold">PIPING AND INSTRUMENTATION DIAGRAM</text>')
    svg_parts.append(f'<text x="300" y="100" text-anchor="middle" font-size="12">{project_info["project"]}</text>')

    # Details
    details = [
        ("DRAWING NO:", project_info['drawing_no'], 10, 125),
        ("DATE:", project_info['date'], 210, 125),
        ("REV:", project_info['revision'], 410, 125),
        ("DRAWN:", project_info['drawn_by'], 10, 155),
        ("CHECKED:", project_info['checked_by'], 210, 155),
        ("APPROVED:", project_info['approved_by'], 410, 155),
    ]

    for label, value, x, y in details:
        svg_parts.append(f'<text x="{x}" y="{y}" font-size="10">{label}</text>')
        svg_parts.append(f'<text x="{x + 70}" y="{y}" font-size="10" font-weight="bold">{value}</text>')

    svg_parts.append('</g>')

    svg_parts.append('</svg>')

    return ''.join(svg_parts)


# — MAIN APPLICATION —

# Load data

@st.cache_data
def load_professional_data():
    """Load P&ID data or create sample"""

    # Check if layout data exists
    layout_dir = "layout_data"
    eq_file = os.path.join(layout_dir, "enhanced_equipment_layout.csv")
    pipe_file = os.path.join(layout_dir, "pipe_connections_layout.csv")

    if os.path.exists(eq_file) and os.path.exists(pipe_file):
        eq_df = pd.read_csv(eq_file)
        pipe_df = pd.read_csv(pipe_file, dtype={'Polyline Points (x, y)': str})
        
        # Clean IDs
        if 'id' in eq_df.columns:
            eq_df['id'] = eq_df['id'].astype(str).str.strip()
        for col in ['From Component', 'To Component']:
            if col in pipe_df.columns:
                pipe_df[col] = pipe_df[col].astype(str).str.strip()
                
        return eq_df, pipe_df
    else:
        # Create professional sample data matching reference
        components, pipes = create_suction_filter_system()
        eq_df = pd.DataFrame(components)
        pipe_df = pd.DataFrame(pipes)
        return eq_df, pipe_df


# Initialize data

if 'eq_df' not in st.session_state:
    st.session_state.eq_df, st.session_state.pipe_df = load_professional_data()

# Create components and pipes

components = {c.id: c for c in [ProfessionalPnidComponent(row) for _, row in st.session_state.eq_df.iterrows()]}

# Initialize router if smart routing enabled

router = None
if enable_smart_routing:
    router = PipeRouter(grid_size=10)
    for comp in components.values():
        router.add_component_obstacle(comp.x, comp.y, comp.width, comp.height, padding=20)

pipes = [ProfessionalPnidPipe(row, components, router) for _, row in st.session_state.pipe_df.iterrows()]

# Main display

st.title("🏭 EPS Professional P&ID Generator")

# Quick actions bar

col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

with col1:
    st.markdown(f"**Project:** {st.session_state.project_info['project']}")
    st.markdown(f"**Drawing:** {st.session_state.project_info['drawing_no']} Rev.{st.session_state.project_info['revision']}")

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with col3:
    if st.button("✅ Validate", use_container_width=True):
        validator = PnIDValidator(components, pipes)
        validation = validator.validate_all()
        if validation['is_valid']:
            st.success("P&ID validation passed!")
        else:
            st.error(f"Found {len(validation['errors'])} errors")

with col4:
    if st.button("📊 Analyze", use_container_width=True):
        analyzer = ControlSystemAnalyzer(components, pipes)
        st.info(f"Found {len(analyzer.control_loops)} control loops")

with col5:
    export_format = st.selectbox("Export", ["SVG", "PNG", "DXF", "PDF"], label_visibility="collapsed")

# Main P&ID display

st.markdown('<div class="pnid-container">', unsafe_allow_html=True)
svg_output = render_final_professional_pnid(components, pipes, st.session_state.project_info)
st.components.v1.html(svg_output, height=800, scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)

# Metrics row

st.markdown("---")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Equipment", len([c for c in components.values() if not c.is_instrument]))
with col2:
    st.metric("Instruments", len([c for c in components.values() if c.is_instrument]))
with col3:
    st.metric("Pipes", len(pipes))
with col4:
    st.metric("Valves", len([c for c in components.values() if 'valve' in c.component_type]))
with col5:
    analyzer = ControlSystemAnalyzer(components, pipes)
    st.metric("Control Loops", len(analyzer.control_loops))
with col6:
    st.metric("Line Numbers", len(set(p.label for p in pipes if p.label)))

# Tabs for different functions

tab1, tab2, tab3, tab4 = st.tabs(["📝 Edit", "🔧 Components", "📊 Analysis", "📁 Data"])

with tab1:
    # Component addition
    st.markdown("### Add Component")
    col1, col2, col3 = st.columns(3)

    with col1:
        new_id = st.text_input("ID", key="new_comp_id")
        new_tag = st.text_input("Tag", key="new_comp_tag")

    with col2:
        comp_types = list(PROFESSIONAL_ISA_SYMBOLS.keys()) + ['instrument']
        new_type = st.selectbox("Type", comp_types, key="new_comp_type")
        new_size = st.selectbox("Size", ["1/2\"", "3/4\"", "1\"", "1-1/2\"", "2\"", "3\"", "4\"", "6\"", "8\""])

    with col3:
        new_x = st.number_input("X Position", 0, 2000, 500, 25)
        new_y = st.number_input("Y Position", 0, 2000, 300, 25)

    if st.button("Add Component", type="primary"):
        if new_id and new_id not in st.session_state.eq_df['id'].values:
            new_row = {
                'id': new_id,
                'tag': new_tag or new_id,
                'Component': new_type,
                'x': new_x,
                'y': new_y,
                'Width': 60,
                'Height': 60,
                'rotation': 0,
                'size': new_size
            }
            st.session_state.eq_df = pd.concat([st.session_state.eq_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Added {new_type}: {new_tag}")
            st.rerun()

with tab2:
    # Component library browser
    st.markdown("### Component Library")

    # Group symbols by category
    categories = {
        'Pumps': ['pump_centrifugal', 'pump_positive_displacement'],
        'Valves': ['valve_gate', 'valve_globe', 'valve_ball', 'valve_check', 'control_valve'],
        'Vessels': ['vessel_vertical', 'vessel_horizontal', 'tank'],
        'Equipment': ['filter', 'heat_exchanger', 'compressor'],
        'Instruments': ['pressure_gauge', 'temperature_gauge', 'level_gauge'],
        'Electrical': ['motor', 'control_panel'],
        'Fittings': ['flange', 'reducer', 'pipe_tee', 'pipe_elbow']
    }

    selected_category = st.selectbox("Category", list(categories.keys()))

    # Display symbols in grid
    cols = st.columns(4)
    for i, symbol_type in enumerate(categories.get(selected_category, [])):
        with cols[i % 4]:
            if symbol_type in PROFESSIONAL_ISA_SYMBOLS:
                # Display symbol preview
                preview_svg = f'<svg width="100" height="100" viewBox="0 0 100 100">{PROFESSIONAL_ISA_SYMBOLS[symbol_type]}</svg>'
                st.markdown(preview_svg, unsafe_allow_html=True)
                st.caption(symbol_type.replace('_', ' ').title())

with tab3:
    # Analysis results
    st.markdown("### P&ID Analysis")

    # Control systems
    analyzer = ControlSystemAnalyzer(components, pipes)

    if analyzer.control_loops:
        st.markdown("#### Control Loops")
        for loop in analyzer.control_loops:
            st.write(f"- **{loop.loop_type.value}** ({loop.loop_id}): "
                    f"{loop.primary_element} → {loop.controller} → {loop.final_element}")

    # Validation
    validator = PnIDValidator(components, pipes)
    validation = validator.validate_all()

    if validation['errors']:
        st.markdown("#### ❌ Errors")
        for error in validation['errors']:
            st.error(error)

    if validation['warnings']:
        st.markdown("#### ⚠️ Warnings")
        for warning in validation['warnings']:
            st.warning(warning)

with tab4:
    # Data management
    st.markdown("### Data Management")

    # Export options
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            "📥 Download SVG",
            svg_output,
            "professional_pnid.svg",
            "image/svg+xml",
            use_container_width=True
        )

    with col2:
        if st.button("Generate PNG", use_container_width=True):
            try:
                png_data = svg2png(bytestring=svg_output.encode('utf-8'), output_width=3000)
                st.download_button(
                    "📥 Download PNG",
                    png_data,
                    "professional_pnid.png",
                    "image/png",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PNG generation error: {e}")

    # Data tables
    with st.expander("Equipment Data"):
        st.dataframe(st.session_state.eq_df, use_container_width=True)

    with st.expander("Pipe Data"):
        st.dataframe(st.session_state.pipe_df, use_container_width=True)

# Footer

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
    <p>EPS Professional P&ID Generator v2.0 | © 2024 EPS Pvt. Ltd. | ISO 15926 Compliant</p>
    </div>
    """,
    unsafe_allow_html=True
)
