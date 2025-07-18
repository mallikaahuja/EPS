import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
import io
import base64
from professional_symbols import PROFESSIONAL_ISA_SYMBOLS, ARROW_MARKERS
from reference_exact_symbols import REFERENCE_EXACT_SYMBOLS
from advanced_rendering import ProfessionalRenderer # This class seems unused in the provided snippet
from control_systems import ControlSystemAnalyzer, PipeRouter, PnIDValidator # PipeRouter might be a duplicate/different one
import re
import math
import ast # Added for safe evaluation of waypoints from CSV

# --- CONFIG ---

st.set_page_config(page_title="EPS P&ID Suite", layout="wide", initial_sidebar_state="expanded")

# Initialize session state

if 'components' not in st.session_state:
    st.session_state.components = {}
if 'pipes' not in st.session_state:
    st.session_state.pipes = []
if 'selected_component' not in st.session_state:
    st.session_state.selected_component = None
if 'drawing_mode' not in st.session_state:
    st.session_state.drawing_mode = 'select'

# --- LOAD DATA ---

@st.cache_data
def load_equipment_data():
    return pd.read_csv("equipment_list.csv")

@st.cache_data
def load_pipeline_data():
    return pd.read_csv("pipeline_list.csv")

@st.cache_data
def load_inline_data():
    return pd.read_csv("inline_component_list.csv")

@st.cache_data
def load_component_layout():
    return pd.read_csv("enhanced_equipment_layout.csv")

@st.cache_data
def load_pipe_connections():
    """
    Loads pipe connections from a CSV file.
    Includes the fix for parsing 'waypoints' column.
    """
    try:
        connections_df = pd.read_csv("pipes_connections.csv")
        # Convert 'with_arrow' column to boolean
        connections_df['with_arrow'] = connections_df['with_arrow'].astype(bool)
        # Convert 'waypoints' column from string representation of list to actual list
        connections_df['waypoints'] = connections_df['waypoints'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        return connections_df
    except FileNotFoundError:
        st.error("Error: 'pipes_connections.csv' was not found. Please ensure it's in the same directory.")
        return pd.DataFrame()
    except pd.errors.ParserError as e:
        st.error(f"Error parsing 'pipes_connections.csv': {e}")
        st.error("Please check your 'pipes_connections.csv' file for malformed lines, especially regarding quotes around `[]` in the 'waypoints' column.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred while loading 'pipes_connections.csv': {e}")
        return pd.DataFrame()


# Professional component class

class ProfessionalPnidComponent:
    def __init__(self, comp_id, tag, component_type, x, y, width, height, description=""):
        self.id = comp_id
        self.tag = tag
        self.component_type = component_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.description = description
        self.is_instrument = any(inst in tag for inst in ['PT', 'TT', 'FT', 'LT', 'FIC', 'PIC', 'TIC', 'LIC'])
        self.ports = self._define_ports()

    def _define_ports(self):
        """Define connection ports based on component type"""
        ports = {}
        # Default center port for instrument signals
        if self.is_instrument:
            ports['center'] = (self.x + self.width/2, self.y + self.height/2)

        # Specific ports based on component type
        if 'pump' in self.component_type:
            ports.update({
                'suction': (self.x, self.y + self.height/2),
                'discharge': (self.x + self.width, self.y + self.height/2)
            })
        elif 'valve' in self.component_type or 'control_valve' in self.component_type:
            ports.update({
                'inlet': (self.x, self.y + self.height/2),
                'outlet': (self.x + self.width, self.y + self.height/2)
            })
        elif 'vessel' in self.component_type:
            ports.update({
                'top': (self.x + self.width/2, self.y),
                'bottom': (self.x + self.width/2, self.y + self.height),
                'side_top': (self.x + self.width, self.y + self.height/3),
                'side_bottom': (self.x + self.width, self.y + 2*self.height/3)
            })
        elif 'heat_exchanger' in self.component_type:
            ports.update({
                'inlet': (self.x, self.y + self.height/3),
                'outlet': (self.x + self.width, self.y + 2*self.height/3),
                'cooling_in': (self.x + self.width/3, self.y),
                'cooling_out': (self.x + 2*self.width/3, self.y + self.height)
            })
        elif 'filter' in self.component_type:
             ports.update({
                'inlet': (self.x, self.y + self.height/2),
                'outlet': (self.x + self.width, self.y + self.height/2)
            })
        # Add other component types and their ports as needed
        return ports

    def get_svg(self):
        """Get SVG representation using professional symbols"""
        # Try reference exact symbols first
        if self.component_type in REFERENCE_EXACT_SYMBOLS:
            symbol_svg = REFERENCE_EXACT_SYMBOLS[self.component_type]
        elif self.component_type in PROFESSIONAL_ISA_SYMBOLS:
            symbol_svg = PROFESSIONAL_ISA_SYMBOLS[self.component_type]
        else:
            # Fallback to basic rectangle
            symbol_svg = f'''<rect x="0" y="0" width="{self.width}" height="{self.height}"
                           fill="white" stroke="black" stroke-width="2.5"/>
                           <text x="{self.width/2}" y="{self.height/2}" text-anchor="middle"
                           font-size="10">{self.tag}</text>'''

        # Wrap in group with transform
        return f'''<g transform="translate({self.x},{self.y})">
                    {symbol_svg}
                    <text x="{self.width/2}" y="{self.height + 15}" text-anchor="middle"
                    font-size="12" font-weight="bold">{self.tag}</text>
                   </g>'''

# --- START ImprovedPipeRouter CLASS (Copied from your previous input) ---
class ImprovedPipeRouter:
    """Professional pipe routing for P&ID diagrams"""

    def __init__(self, grid_size=10):
        self.grid_size = grid_size
        self.occupied_paths = [] # This could be used for advanced collision avoidance

    def route_pipe(self, start_point, end_point, components, existing_pipes=[]):
        """
        Route a pipe between two points avoiding components and minimizing crossings
        """
        # Convert points to grid coordinates
        start_grid = (int(start_point[0] / self.grid_size), int(start_point[1] / self.grid_size))
        end_grid = (int(end_point[0] / self.grid_size), int(end_point[1] / self.grid_size))

        path = []

        # Get component bounds for collision detection
        obstacles = self._get_obstacle_grid(components)

        # Simple strategies for now; can be expanded with A* for complex avoidance
        # Try horizontal-then-vertical
        path1 = [
            start_point,
            (end_point[0], start_point[1]),  # Horizontal segment
            end_point                        # Vertical segment
        ]

        # Try vertical-then-horizontal
        path2 = [
            start_point,
            (start_point[0], end_point[1]),  # Vertical segment
            end_point                        # Horizontal segment
        ]

        # Try with intermediate points for complex routing
        # This will make an "S" or "Z" shape for more natural routing
        mid_x = (start_point[0] + end_point[0]) / 2
        mid_y = (start_point[1] + end_point[1]) / 2

        path3 = [
            start_point,
            (start_point[0], mid_y),    # Vertical to midpoint Y
            (end_point[0], mid_y),      # Horizontal across to end X
            end_point                    # Vertical to end
        ]

        path4 = [
            start_point,
            (mid_x, start_point[1]),    # Horizontal to midpoint X
            (mid_x, end_point[1]),      # Vertical across to end Y
            end_point                    # Horizontal to end
        ]

        # Choose the first path that is clear. In a real system, you'd use A*
        # or a cost function to pick the "best" path (shortest, fewest turns, etc.)
        for current_path in [path1, path2, path3, path4]:
            if self._is_path_clear(current_path, obstacles):
                return current_path

        # If no clear path found by simple strategies, default to one
        # This should ideally be replaced by a proper pathfinding algorithm
        # that guarantees a path if one exists.
        return path3

    def _get_obstacle_grid(self, components):
        """Convert components to grid obstacles (in grid coordinates)"""
        obstacles = set()
        for comp in components.values():
            # Add padding around components for routing clearance
            padding = 20 # pixels
            # Convert component bounds to grid coordinates
            x1_grid = int((comp.x - padding) / self.grid_size)
            y1_grid = int((comp.y - padding) / self.grid_size)
            x2_grid = int((comp.x + comp.width + padding) / self.grid_size)
            y2_grid = int((comp.y + comp.height + padding) / self.grid_size)

            # Mark all grid cells covered by the padded component as obstacles
            for x in range(x1_grid, x2_grid + 1):
                for y in range(y1_grid, y2_grid + 1):
                    obstacles.add((x, y))
        return obstacles

    def _is_path_clear(self, path, obstacles):
        """
        Check if path avoids obstacles.
        Simplified check: just checks path endpoints and midpoints of segments.
        A more robust check would involve Bresenham's line algorithm or similar
        to check all grid cells along each segment.
        """
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i + 1]

            # Check start and end points of segment in grid coordinates
            grid_p1 = (int(p1[0] / self.grid_size), int(p1[1] / self.grid_size))
            grid_p2 = (int(p2[0] / self.grid_size), int(p2[1] / self.grid_size))

            if grid_p1 in obstacles or grid_p2 in obstacles:
                return False

            # For orthogonal segments, also check points in between
            # This is a very basic check. For full collision, iterate through all cells.
            if p1[0] == p2[0]: # Vertical segment
                for y_coord in range(min(grid_p1[1], grid_p2[1]), max(grid_p1[1], grid_p2[1]) + 1):
                    if (grid_p1[0], y_coord) in obstacles:
                        return False
            elif p1[1] == p2[1]: # Horizontal segment
                for x_coord in range(min(grid_p1[0], grid_p2[0]), max(grid_p1[0], grid_p2[0]) + 1):
                    if (x_coord, grid_p1[1]) in obstacles:
                        return False
        return True

# --- END ImprovedPipeRouter CLASS ---


class ProfessionalPipe:
    def __init__(self, from_comp, from_port, to_comp, to_port, label="", line_type="process"):
        self.from_comp = from_comp
        self.from_port = from_port
        self.to_comp = to_comp
        self.to_port = to_port
        self.label = label
        self.line_type = line_type
        # self.waypoints will be set by the router
        self.waypoints = []

    def get_svg(self, router_instance, all_components, all_pipes_list_for_router): # Added router_instance, all_components, all_pipes_list_for_router
        """Get SVG representation of pipe with proper routing"""
        if not self.from_comp or not self.to_comp:
            return ""

        # Get actual port positions
        from_pos = self.from_comp.ports.get(self.from_port, (self.from_comp.x + self.from_comp.width/2, self.from_comp.y + self.from_comp.height/2))
        to_pos = self.to_comp.ports.get(self.to_port, (self.to_comp.x + self.to_comp.width/2, self.to_comp.y + self.to_comp.height/2))

        # --- USE ImprovedPipeRouter FOR PATH CREATION ---
        self.waypoints = router_instance.route_pipe(from_pos, to_pos, all_components, all_pipes_list_for_router)
        path_points = self.waypoints
        # --- END ImprovedPipeRouter USAGE ---

        # Build SVG path
        path_d = f"M {path_points[0][0]},{path_points[0][1]}"
        for point in path_points[1:]:
            path_d += f" L {point[0]},{point[1]}"

        # Line style based on type
        if self.line_type == "instrument_signal":
            stroke_width = "1"
            stroke_dasharray = 'stroke-dasharray="5,3"'
        else:
            stroke_width = "3"
            stroke_dasharray = ""

        svg = f'<path d="{path_d}" fill="none" stroke="black" stroke-width="{stroke_width}" {stroke_dasharray}/>'

        # Add flow arrows (now called via the helper function)
        svg = add_flow_arrows(svg, path_points)

        # Add label
        if self.label and len(path_points) >= 2:
            # Find a suitable position for the label (e.g., midpoint of the longest segment)
            longest_segment_index = -1
            max_length = 0
            for i in range(len(path_points) - 1):
                length = self._distance(path_points[i], path_points[i+1])
                if length > max_length:
                    max_length = length
                    longest_segment_index = i

            if longest_segment_index != -1:
                p1_label = path_points[longest_segment_index]
                p2_label = path_points[longest_segment_index + 1]
                label_x = (p1_label[0] + p2_label[0]) / 2
                label_y = (p1_label[1] + p2_label[1]) / 2

                # Adjust label position for horizontal/vertical lines
                if p1_label[0] == p2_label[0]: # Vertical
                    label_x += 10 # Offset to the right
                else: # Horizontal or diagonal
                    label_y -= 10 # Offset above

                svg += f'''<rect x="{label_x - 40}" y="{label_y - 10}" width="80" height="20"
                          fill="white" stroke="none"/>
                          <text x="{label_x}" y="{label_y + 3}" text-anchor="middle"
                          font-size="10" font-family="Arial">{self.label}</text>'''

        return svg

    def _distance(self, p1, p2):
        """Calculate distance between two points"""
        return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5

    # Removed _create_orthogonal_path as it's replaced by ImprovedPipeRouter


def create_professional_pnid():
    """Create a professional P&ID from loaded data"""
    # Load layout and connections
    layout_df = load_component_layout()
    connections_df = load_pipe_connections()

    components = {}
    pipes = []

    # Create components from layout
    for _, row in layout_df.iterrows():
        comp = ProfessionalPnidComponent(
            comp_id=row['id'],
            tag=row['tag'],
            component_type=row['Component'],
            x=float(row['x']),
            y=float(row['y']),
            width=float(row['Width']),
            height=float(row['Height']),
            description=row.get('description', '')
        )
        components[comp.id] = comp

    # Instantiate the router
    router = ImprovedPipeRouter(grid_size=st.session_state.get('grid_spacing', 10)) # Use grid_spacing from UI if available

    # Create pipes from connections
    for _, row in connections_df.iterrows():
        if row['from_component'] in components and row['to_component'] in components:
            pipe = ProfessionalPipe(
                from_comp=components[row['from_component']],
                from_port=row['from_port'],
                to_comp=components[row['to_component']],
                to_port=row['to_port'],
                label=row.get('line_number', ''),
                line_type=row.get('line_type', 'process')
            )
            # pipes are collected here, but the actual routing and waypoint setting
            # happens when pipe.get_svg() is called because it needs the router.
            # We'll pass the router and components to get_svg.
            pipes.append(pipe)
        else:
            st.warning(f"Warning: Component '{row['from_component']}' or '{row['to_component']}' not found for connection '{row.get('line_number', '')}'. Skipping.")

    return components, pipes, router # Return router instance

def render_professional_svg(components, pipes, router_instance, width=1600, height=1200): # Added router_instance
    """Render complete P&ID as SVG"""
    svg_parts = []

    # SVG header with professional styling
    svg_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" version="1.1"
     style="font-family: Arial, sans-serif; background-color: white">''')

    # Add arrow markers (assuming ARROW_MARKERS is defined in professional_symbols.py)
    svg_parts.append(ARROW_MARKERS)

    # Draw border and title block
    svg_parts.append(f'''
<g id="drawing-frame">
    <rect x="10" y="10" width="{width-20}" height="{height-20}"
          fill="none" stroke="black" stroke-width="2"/>
    <rect x="10" y="{height-100}" width="{width-20}" height="90"
          fill="none" stroke="black" stroke-width="2"/>
    <text x="30" y="{height-70}" font-size="16" font-weight="bold">
        TENTATIVE P&ID DRAWING FOR SUCTION FILTER + KDP-330
    </text>
    <text x="30" y="{height-50}" font-size="12">EPS Process Solutions Pvt. Ltd.</text>
    <text x="30" y="{height-30}" font-size="10">Drawing No: EPSPL/V2526-TP/01</text>
    <text x="{width-200}" y="{height-30}" font-size="10">Rev: 00</text>
</g>''')

    # Draw grid (optional)
    if st.session_state.get('show_grid', False):
        svg_parts.append('<g id="grid" opacity="0.3">')
        for x_grid in range(0, width, st.session_state.get('grid_spacing', 50)): # Use grid_spacing for grid lines
            svg_parts.append(f'<line x1="{x_grid}" y1="0" x2="{x_grid}" y2="{height}" stroke="gray" stroke-width="0.5"/>')
        for y_grid in range(0, height, st.session_state.get('grid_spacing', 50)): # Use grid_spacing for grid lines
            svg_parts.append(f'<line x1="0" y1="{y_grid}" x2="{width}" y2="{y_grid}" stroke="gray" stroke-width="0.5"/>')
        svg_parts.append('</g>')

    # Draw pipes first (behind components)
    svg_parts.append('<g id="pipes">')
    # Pass the router instance and all_components to pipe.get_svg()
    for pipe in pipes:
        svg_parts.append(pipe.get_svg(router_instance, components, pipes)) # Passing 'pipes' list for future advanced routing
    svg_parts.append('</g>')

    # Draw components
    svg_parts.append('<g id="components">')
    for comp in components.values():
        svg_parts.append(comp.get_svg())
    svg_parts.append('</g>')

    # Add legend
    if st.session_state.get('show_legend', True):
        svg_parts.append(render_legend(width - 300, 50))

    # Add BOM table
    if st.session_state.get('show_bom', True):
        svg_parts.append(render_bom_table(components, width - 500, height - 400))

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

def render_legend(x, y):
    """Render symbol legend"""
    legend_svg = f'''<g id="legend" transform="translate({x},{y})">
<rect x="0" y="0" width="280" height="400" fill="white" stroke="black" stroke-width="1"/>
<text x="140" y="20" text-anchor="middle" font-size="14" font-weight="bold">SYMBOL LEGEND</text>'''

    # Add common symbols
    symbols = [
        ("pump_centrifugal", "CENTRIFUGAL PUMP", 40),
        ("valve_gate", "GATE VALVE", 100),
        ("filter", "FILTER", 160),
        ("vessel_vertical", "VESSEL", 220),
        ("control_valve", "CONTROL VALVE", 280),
    ]

    for symbol_type, description, y_pos in symbols:
        # Ensure the symbol_type exists in one of your symbol dictionaries
        symbol_source = None
        if symbol_type in REFERENCE_EXACT_SYMBOLS:
            symbol_source = REFERENCE_EXACT_SYMBOLS
        elif symbol_type in PROFESSIONAL_ISA_SYMBOLS:
            symbol_source = PROFESSIONAL_ISA_SYMBOLS

        if symbol_source:
            legend_svg += f'''<g transform="translate(30,{y_pos}) scale(0.5)">
                {symbol_source[symbol_type]}
                </g>
                <text x="100" y="{y_pos + 20}" font-size="10">{description}</text>'''

    legend_svg += '</g>'
    return legend_svg

def render_bom_table(components, x, y):
    """Render Bill of Materials table"""
    bom_svg = f'''<g id="bom" transform="translate({x},{y})">
<rect x="0" y="0" width="480" height="300" fill="white" stroke="black" stroke-width="1"/>
<text x="240" y="20" text-anchor="middle" font-weight="bold">BILL OF MATERIALS</text>
<line x1="0" y1="30" x2="480" y2="30" stroke="black"/>'''

    # Table headers
    headers = ["SR NO.", "TAG", "DESCRIPTION", "SIZE", "QTY"]
    col_widths = [50, 80, 200, 80, 70]
    x_pos = 0
    for i, header in enumerate(headers):
        bom_svg += f'<text x="{x_pos + col_widths[i]/2}" y="45" text-anchor="middle" font-size="10" font-weight="bold">{header}</text>'
        x_pos += col_widths[i]

    bom_svg += '<line x1="0" y1="50" x2="480" y2="50" stroke="black"/>'

    # Table rows
    y_pos = 65
    for i, (comp_id, comp) in enumerate(components.items()):
        if i < 10:  # Limit to first 10 items for display
            x_pos = 0
            row_data = [str(i+1), comp.tag, comp.description[:30], "-", "1"] # Description truncated
            for j, data in enumerate(row_data):
                bom_svg += f'<text x="{x_pos + col_widths[j]/2}" y="{y_pos}" text-anchor="middle" font-size="9">{data}</text>'
                x_pos += col_widths[j]
            y_pos += 15

    bom_svg += '</g>'
    return bom_svg

# --- STREAMLIT UI ---

st.title("🏭 EPS P&ID Suite")

# Sidebar controls
with st.sidebar:
    st.header("📐 Drawing Standards")
    drawing_standard = st.selectbox("Standard", ["ISA", "ISO", "DIN", "JIS"])
    drawing_size = st.selectbox("Size", ["A3", "A2", "A1", "A0"])

    st.header("🎨 Visual Controls")
    st.session_state.show_grid = st.checkbox("Show Grid", value=False)
    st.session_state.show_legend = st.checkbox("Show Legend", value=True)
    st.session_state.show_bom = st.checkbox("Show BOM", value=True)

    # Store grid_spacing in session_state so it can be accessed by the router
    st.session_state.grid_spacing = st.slider("Grid Spacing (pixels)", 10, 50, 25)
    symbol_scale = st.slider("Symbol Scale", 0.5, 2.0, 1.0, 0.1)

# Main drawing area
col1, col2 = st.columns([3, 1])

with col1:
    # Create P&ID (now returns components, pipes, and router)
    components, pipes, router = create_professional_pnid()

    # Render SVG (pass the router instance)
    svg_content = render_professional_svg(components, pipes, router)

    # Display SVG
    st.markdown("### P&ID Drawing")
    st.components.v1.html(f'''
        <div style="background: white; border: 2px solid #333; overflow: auto; height: 800px;">
            {svg_content}
        </div>
    ''', height=820)

with col2:
    st.markdown("### Component Library")
    # Component categories
    category = st.selectbox("Category", ["Pumps", "Valves", "Vessels", "Instruments", "Piping"])

    # Show component thumbnails (these are just text for now)
    if category == "Pumps":
        st.write("🔄 Centrifugal Pump")
        st.write("🔄 Vacuum Pump")
        st.write("🔄 Positive Displacement")
    elif category == "Valves":
        st.write("🔧 Gate Valve")
        st.write("🔧 Globe Valve")
        st.write("🔧 Control Valve")
    # You would typically have actual SVG representations or images here for selection

    # Component properties
    if st.session_state.selected_component:
        st.markdown("### Properties")
        comp = components.get(st.session_state.selected_component)
        if comp:
            st.text_input("Tag", comp.tag)
            st.text_area("Description", comp.description)
            st.number_input("X Position", value=comp.x)
            st.number_input("Y Position", value=comp.y)

# Bottom toolbar
col3, col4, col5, col6 = st.columns(4)

with col3:
    if st.button("🔍 Validate P&ID"):
        validator = PnIDValidator(components, pipes) # Make sure PnIDValidator can accept 'pipes' as is
        results = validator.validate_all()

        if results['is_valid']:
            st.success("✅ P&ID validation passed!")
        else:
            st.error(f"❌ Found {len(results['errors'])} errors")
            for error in results['errors'][:5]: # Show top 5 errors
                st.error(error)

        if results['warnings']:
            st.warning(f"⚠️ {len(results['warnings'])} warnings")
            for warning in results['warnings'][:3]: # Show top 3 warnings
                st.warning(warning)

with col4:
    if st.button("🤖 Analyze Control Loops"):
        analyzer = ControlSystemAnalyzer(components, pipes)
        st.info(f"Found {len(analyzer.control_loops)} control loops")
        for loop in analyzer.control_loops:
            st.write(f"- {loop.loop_type.value}: {loop.loop_id}")

with col5:
    if st.button("💾 Export SVG"):
        # Create download link
        b64 = base66.b64encode(svg_content.encode()).decode()
        href = f'<a href="data:image/svg+xml;base64,{b64}" download="pnid_drawing.svg">Download SVG File</a>'
        st.markdown(href, unsafe_allow_html=True)

with col6:
    if st.button("🖨️ Export PDF"):
        st.info("PDF export requires additional libraries (cairosvg)")

# Footer
st.markdown("---")
st.markdown("EPS Process Solutions Pvt. Ltd. - P&ID Automation Platform v2.0")

# Helper functions (outside of main Streamlit flow, but called within)

def add_scope_boundaries(svg_content, scope_areas):
    """Add dashed scope boundary boxes"""
    scope_svg = '<g id="scope-boundaries">'

    for scope in scope_areas:
        scope_svg += f'''
    <rect x="{scope['x']}" y="{scope['y']}"
          width="{scope['width']}" height="{scope['height']}"
          fill="none" stroke="black" stroke-width="1.5"
          stroke-dasharray="10,5" rx="5"/>
    <text x="{scope['x'] + 10}" y="{scope['y'] - 5}"
          font-size="12" font-weight="bold">{scope['label']}</text>
    '''

    scope_svg += '</g>'
    return svg_content.replace('</svg>', scope_svg + '</svg>')

def add_nozzle_indicators(component):
    """Add nozzle markers to vessels"""
    nozzle_svg = ''
    if 'vessel' in component.component_type:
        nozzles = [
            {'x': component.width/2, 'y': 0, 'tag': 'N1'},  # Top
            {'x': component.width, 'y': component.height/3, 'tag': 'N2'},  # Side
            {'x': component.width/2, 'y': component.height, 'tag': 'N3'},  # Bottom
        ]

        for nozzle in nozzles:
            nozzle_svg += f'''
        <circle cx="{nozzle['x']}" cy="{nozzle['y']}" r="5"
                fill="white" stroke="black" stroke-width="2"/>
        <text x="{nozzle['x'] + 10}" y="{nozzle['y'] + 3}"
              font-size="8">{nozzle['tag']}</text>
        '''
    return nozzle_svg

def create_instrument_bubble(tag, x, y):
    """Create proper ISA instrument bubble"""
    match = re.match(r'^([A-Z]+)-(\d+)$', tag)
    if not match:
        return ''

    letters = match.group(1)
    number = match.group(2)

    is_controller = 'C' in letters

    bubble_svg = f'<g transform="translate({x},{y})">'
    bubble_svg += '<circle cx="0" cy="0" r="22" fill="white" stroke="black" stroke-width="2"/>'

    if is_controller:
        bubble_svg += '<rect x="-22" y="-22" width="44" height="44" fill="none" stroke="black" stroke-width="1.5"/>'

    if not is_controller:
        bubble_svg += '<line x1="-22" y1="0" x2="22" y2="0" stroke="black" stroke-width="2"/>'

    bubble_svg += f'''
<text x="0" y="-5" text-anchor="middle" font-size="12" font-weight="bold">{letters}</text>
<text x="0" y="10" text-anchor="middle" font-size="10">{number}</text>
'''
    bubble_svg += '</g>'
    return bubble_svg

def add_flow_arrows(pipe_svg, path_points):
    """Add flow direction arrows to pipes"""
    if len(path_points) < 2:
        return pipe_svg

    # Calculate arrow positions (place at 1/3 and 2/3 of pipe length)
    positions = [0.33, 0.67]
    arrows_svg = ''

    total_length = 0
    segments = []

    for i in range(len(path_points) - 1):
        p1, p2 = path_points[i], path_points[i + 1]
        length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        segments.append((p1, p2, length))
        total_length += length

    for pos in positions:
        target_length = total_length * pos
        current_length = 0

        for p1, p2, length in segments:
            if length == 0: # Avoid division by zero for coincident points
                continue
            if current_length + length >= target_length:
                ratio = (target_length - current_length) / length
                arrow_x = p1[0] + ratio * (p2[0] - p1[0])
                arrow_y = p1[1] + ratio * (p2[1] - p1[1])

                angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

                arrows_svg += f'''
            <polygon points="-8,-4 0,0 -8,4" fill="black"
                     transform="translate({arrow_x},{arrow_y}) rotate({angle})"/>
            '''
                break
            current_length += length
    return pipe_svg + arrows_svg

# Example scope areas for the reference P&ID (not directly used in render_professional_svg yet)
REFERENCE_SCOPE_AREAS = [
    {
        'x': 100, 'y': 250, 'width': 600, 'height': 350,
        'label': 'EPSPL SCOPE'
    },
    {
        'x': 750, 'y': 250, 'width': 200, 'height': 200,
        'label': 'CUSTOMER SCOPE'
    },
    {
        'x': 980, 'y': 100, 'width': 250, 'height': 300,
        'label': 'CONTROL PANEL'
    }
]
