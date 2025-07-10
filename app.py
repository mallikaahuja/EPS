import streamlit as st
import pandas as pd
import base64
import os
from io import BytesIO
import ezdxf
import psycopg2
from psycopg2 import sql
import openai
import json
import re

# Set Streamlit page configuration (MUST be the first Streamlit command)
st.set_page_config(layout="wide")

# --- Database Connection Management ---
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}. Please ensure DATABASE_URL is set correctly and the database is accessible.")
        return None

# --- Custom Classes ---
class PnidComponent:
    def __init__(self, data):
        self.component = data['Component']
        self.id = data['id']
        self.tag = data['tag']
        self.x = data['x']
        self.y = data['y']
        self.width = data['Width']
        self.height = data['Height']
        self.description = data['Description']
        self.svg = "" # Will be populated later

class PnidPipe:
    def __init__(self, data, components_map):
        self.pipe_no = data['Pipe No.']
        
        # Look up components by their ID (e.g., TK-001, SF-001)
        self.from_component_id = data['From Component']
        self.to_component_id = data['To Component']

        self.from_component = components_map.get(self.from_component_id)
        self.to_component = components_map.get(self.to_component_id)

        if not self.from_component:
            st.warning(f"Pipe '{self.pipe_no}': 'From Component' ID '{self.from_component_id}' not found. Pipe may be incomplete.")
        if not self.to_component:
            st.warning(f"Pipe '{self.pipe_no}': 'To Component' ID '{self.to_component_id}' not found. Pipe may be incomplete.")

        self.from_port = data['From Port']
        self.to_port = data['To Port']
        # IMPORTANT: Ensure polyline_str is always a string before parsing
        self.polyline_str = str(data['Polyline Points (x, y)'])
        self.label = data['Label']
        self.pipe_type = data['pipe_type']
        
        self.points = self._parse_polyline(self.polyline_str)
        
    def _parse_polyline(self, polyline_str):
        points = []
        # Check if polyline_str is empty or NaN after conversion
        if not polyline_str or polyline_str.lower() == 'nan':
            return [] # Return empty list if no valid polyline string

        # Handle different separators if necessary, assume '-->' for now
        coords_pairs = polyline_str.split('-->')
        for pair in coords_pairs:
            try:
                # Remove parentheses and split by comma
                x_str, y_str = pair.strip().replace('(', '').replace(')', '').split(',')
                points.append((float(x_str.strip()), float(y_str.strip())))
            except ValueError:
                st.warning(f"Could not parse polyline point '{pair}' for Pipe {self.pipe_no}.")
                continue
        return points

# --- Symbol Data Management (PostgreSQL & OpenAI) ---
@st.cache_data(show_spinner="Loading initial P&ID data and symbols...")
def load_symbol_and_meta_data(eq_df):
    conn = get_db_connection()
    svg_defs = {}
    svg_meta = {}
    all_subtypes = []

    if eq_df is not None and not eq_df.empty:
        all_subtypes = eq_df['Component'].unique().tolist()
    
    if conn:
        try:
            cursor = conn.cursor()
            for subtype in all_subtypes:
                # Try to load from DB first
                cursor.execute(sql.SQL("SELECT svg_data, metadata FROM generated_symbols WHERE subtype = %s"), (subtype,))
                result = cursor.fetchone()

                if result:
                    svg_data, metadata_json = result
                    svg_defs[subtype] = svg_data
                    if metadata_json:
                        svg_meta[subtype] = json.loads(metadata_json)
                    else:
                        svg_meta[subtype] = {} # Ensure it's a dict even if empty
                else:
                    # If not in DB, generate with OpenAI and store
                    st.info(f"Generating SVG for '{subtype}' using OpenAI...")
                    # Generate with OpenAI
                    generated_svg, generated_meta = generate_svg_openai(subtype)
                    if generated_svg:
                        svg_defs[subtype] = generated_svg
                        svg_meta[subtype] = generated_meta
                        # Save to DB
                        cursor.execute(
                            sql.SQL("INSERT INTO generated_symbols (subtype, svg_data, metadata) VALUES (%s, %s, %s) ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data, metadata = EXCLUDED.metadata"),
                            (subtype, generated_svg, json.dumps(generated_meta))
                        )
                        conn.commit()
                    else:
                        st.warning(f"Could not load or generate a valid SVG for subtype: '{subtype}'. Using a placeholder.")
                        # Placeholder SVG for missing symbols
                        svg_defs[subtype] = f'<svg width="100" height="100" viewBox="0 0 100 100"><rect x="0" y="0" width="100" height="100" fill="none" stroke="red" stroke-width="2"/><text x="50" y="50" font-size="12" fill="red" text-anchor="middle" alignment-baseline="middle">?</text></svg>'
                        svg_meta[subtype] = {'ports': {}} # No specific ports for placeholder
            cursor.close()
        except Exception as e:
            st.error(f"DB Load Error: {e}. HINT: Perhaps you meant to reference the column 'generated_symbols.svg_data'.")
        finally:
            if conn: # Ensure conn exists before closing
                conn.close()
    else:
        # Fallback if no DB connection
        st.warning("No database connection. Symbols will not be loaded or cached. Attempting to generate with OpenAI directly (if API key set).")
        for subtype in all_subtypes:
            st.info(f"Generating SVG for '{subtype}' using OpenAI (no DB caching)...")
            generated_svg, generated_meta = generate_svg_openai(subtype)
            if generated_svg:
                svg_defs[subtype] = generated_svg
                svg_meta[subtype] = generated_meta
            else:
                st.warning(f"Could not load or generate a valid SVG for subtype: '{subtype}'. Using a placeholder.")
                svg_defs[subtype] = f'<svg width="100" height="100" viewBox="0 0 100 100"><rect x="0" y="0" width="100" height="100" fill="none" stroke="red" stroke-width="2"/><text x="50" y="50" font-size="12" fill="red" text-anchor="middle" alignment-baseline="middle">?</text></svg>'
                svg_meta[subtype] = {'ports': {}}


    return svg_defs, svg_meta, all_subtypes

@st.cache_data(show_spinner=False)
def generate_svg_openai(component_type):
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None, {}

    try:
        # Use the older OpenAI API syntax (compatible with openai<1.0.0)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a P&ID symbol generator. Given a component type, generate a simple, clean, and typical SVG representation of that component. Include a viewBox, and ensure all paths/shapes are relative to a 0,0 origin within that viewBox. Do NOT include any XML declaration, DOCTYPE, or other tags outside the main <svg> tag. If the component has standard inlet/outlet ports, define them as a JSON object within a <metadata> tag inside the SVG, specifying dx and dy offsets from the symbol's origin."},
                {"role": "user", "content": f"Generate a simple P&ID SVG symbol for a {component_type}. Also, include common ports like inlet/outlet, suction/discharge etc. in a metadata JSON."}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract content from the response
        content = response.choices[0].message.content.strip()

        # Regex to find the SVG block
        svg_match = re.search(r'<svg.*?</svg>', content, re.DOTALL | re.IGNORECASE)
        
        if svg_match:
            svg_string = svg_match.group(0)
            
            # Extract metadata if available
            metadata = {}
            metadata_match = re.search(r'<metadata>\s*(\{.*\})\s*</metadata>', svg_string, re.DOTALL)
            if metadata_match:
                try:
                    metadata = json.loads(metadata_match.group(1))
                except json.JSONDecodeError:
                    st.warning(f"Could not parse metadata JSON for {component_type}.")
            
            # Remove metadata tag from the final SVG if it was present
            svg_string = re.sub(r'<metadata>.*?</metadata>', '', svg_string, flags=re.DOTALL)
            
            # Clean up potential extra newlines or spaces around SVG content
            svg_string = svg_string.strip()
            
            # Basic validation: ensure it starts and ends with svg tags
            if svg_string.startswith('<svg') and svg_string.endswith('</svg>'):
                return svg_string, metadata
            else:
                st.warning(f"Generated content for {component_type} was not a valid SVG format.")
                return None, {}
        else:
            st.warning(f"OpenAI Fallback Error for '{component_type}': No SVG content found in response.")
            return None, {}

    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API Error for '{component_type}': {e}. You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 - see the README at https://github.com/openai/openai-python or alternatively, you can pin your installation to the old version, e.g. pip install openai==0.28")
        return None, {}
    except Exception as e:
        st.error(f"An unexpected error occurred during OpenAI SVG generation for '{component_type}': {e}")
        return None, {}


# --- SVG Rendering Functions ---

# Function to escape SVG for data URL
def svg_to_data_url(svg_content):
    if svg_content:
        encoded = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"
    return ""

def get_svg_viewbox(svg_string):
    match = re.search(r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg_string)
    if match:
        x, y, width, height = map(float, match.groups())
        return x, y, width, height
    return 0, 0, 100, 100 # Default if no viewBox

def render_svg_diagram(components_map, pipes_list, svg_defs, svg_meta, symbol_scale, pipe_width, tag_font_size, pipe_label_size, grid_spacing):
    # Calculate overall diagram size based on components and pipes
    max_x = 0
    max_y = 0

    if components_map:
        for c in components_map.values():
            max_x = max(max_x, c.x + c.width * symbol_scale)
            max_y = max(max_y, c.y + c.height * symbol_scale)
    
    if pipes_list:
        for p in pipes_list:
            for px, py in p.points:
                max_x = max(max_x, px)
                max_y = max(max_y, py)

    # Add some padding
    width = max_x + 200
    height = max_y + 200

    svg_elements = []

    # Draw pipes
    for p in pipes_list:
        if len(p.points) >= 2:
            polyline_points = " ".join([f"{x},{y}" for x, y in p.points])
            svg_elements.append(f'<polyline points="{polyline_points}" fill="none" stroke="black" stroke-width="{pipe_width}"/>')
            
            # Add arrows for process lines (simplified)
            if p.pipe_type == 'process_line' and len(p.points) >= 2:
                # Get the last two points for arrow direction
                x1, y1 = p.points[-2]
                x2, y2 = p.points[-1]
                
                # Calculate angle for the arrow
                # Avoid division by zero
                dx = x2 - x1
                dy = y2 - y1
                angle_rad = 0
                if dx != 0 or dy != 0:
                    angle_rad = - ( (dy) / ( (dx)**2 + (dy)**2 )**0.5) if ( (dx)**2 + (dy)**2 )**0.5 != 0 else 0 # Corrected calculation for angle
                    angle_deg = angle_rad * 180 / 3.14159
                else:
                    angle_deg = 0 # No movement, no angle


                # Arrowhead (simple triangle)
                arrow_size = pipe_width * 3
                svg_elements.append(f'''
                    <g transform="translate({x2} {y2}) rotate({angle_deg})">
                        <polygon points="0,0 {arrow_size},{-arrow_size/2} {arrow_size},{arrow_size/2}" fill="black"/>
                    </g>
                ''')

            # Add pipe label
            if p.label:
                # Find midpoint of the first segment or overall centroid
                if len(p.points) > 1:
                    mid_x = (p.points[0][0] + p.points[1][0]) / 2
                    mid_y = (p.points[0][1] + p.points[1][1]) / 2
                else: # Fallback for single point, though pipes need at least two
                    mid_x, mid_y = p.points[0]
                
                # Basic text background for visibility
                # Add a white background rectangle behind the text for better visibility
                # (This is a simplified approach, real implementation would calculate text bounds)
                text_bg_width = len(p.label) * pipe_label_size * 0.6
                text_bg_height = pipe_label_size * 1.2
                svg_elements.append(f'''
                    <rect x="{mid_x - text_bg_width/2}" y="{mid_y - text_bg_height/2}" 
                          width="{text_bg_width}" height="{text_bg_height}" fill="white" stroke="none"/>
                    <text x="{mid_x}" y="{mid_y + pipe_label_size*0.3}" font-size="{pipe_label_size}" 
                          text-anchor="middle" dominant-baseline="middle" fill="black">{p.label}</text>
                ''')


    # Draw components
    for c in components_map.values():
        symbol_svg = svg_defs.get(c.component, '')
        viewbox_x, viewbox_y, viewbox_w, viewbox_h = get_svg_viewbox(symbol_svg)

        # Calculate scale factor for the symbol relative to its intrinsic viewBox
        # Use component's width/height from CSV, apply symbol_scale, then scale symbol SVG
        scale_x = (c.width * symbol_scale) / viewbox_w if viewbox_w > 0 else 1
        scale_y = (c.height * symbol_scale) / viewbox_h if viewbox_h > 0 else 1
        
        # Place the symbol's top-left corner at c.x, c.y
        # Translate it so its top-left viewBox corner aligns with c.x, c.y after scaling
        # (viewbox_x, viewbox_y) is the top-left of the symbol's content within its coordinate system
        transform_str = f"translate({c.x - viewbox_x * scale_x}, {c.y - viewbox_y * scale_y}) scale({scale_x} {scale_y})"
        
        # Replace the original <svg> tag with a <g> tag that includes the transform
        # and embed the original SVG's inner content directly
        inner_svg_content = re.sub(r'<svg[^>]*?>|</svg>', '', symbol_svg, flags=re.DOTALL)
        svg_elements.append(f'<g transform="{transform_str}">{inner_svg_content}</g>')

        # Add tag label
        svg_elements.append(f'<text x="{c.x + (c.width * symbol_scale / 2)}" y="{c.y + (c.height * symbol_scale) + 15}" font-size="{tag_font_size}" text-anchor="middle" fill="black">{c.tag}</text>')

    # Final SVG assembly
    full_svg = f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
            {"".join(svg_elements)}
        </svg>
    '''
    return full_svg

# --- Export Functions ---
def export_dxf(components_map, pipes_list, legend_data, grid_spacing):
    doc = ezdxf.new('R2010') # Specify DXF version for compatibility
    msp = doc.modelspace()
    
    # Add components as basic rectangles/text for DXF (no complex SVG symbols in DXF)
    for c in components_map.values():
        p1 = (c.x, c.y)
        p2 = (c.x + c.width, c.y)
        p3 = (c.x + c.width, c.y + c.height)
        p4 = (c.x, c.y + c.height)
        rect_points = [p1, p2, p3, p4, p1] # 5 points to close the rectangle
        msp.add_lwpolyline(rect_points, dxfattribs={'color': 1}) # Red outline for component
        
        # Adjust text position based on component bounding box
        msp.add_text(c.tag, dxfattribs={'height': 5, 'insert': (c.x + c.width / 2, c.y - 10), 'halign': ezdxf.enums.TextHAlign.CENTER})
        
    for p in pipes_list:
        if len(p.points) >= 2:
            msp.add_lwpolyline(p.points, dxfattribs={'color': 7}) # White/Black pipe
            # Add pipe labels as text
            # Calculate midpoint for label
            mx = sum(x for x, _ in p.points) / len(p.points)
            my = sum(y for _, y in p.points) / len(p.points)
            msp.add_text(p.label, dxfattribs={'height': 3, 'insert': (mx, my - 5), 'halign': ezdxf.enums.TextHAlign.CENTER})

    # Add legend
    if legend_data:
        legend_start_x = max([c.x + c.width for c in components_map.values()]) + 50 if components_map else 50
        legend_start_y = 50
        msp.add_text("Legend", dxfattribs={'height': 10, 'insert': (legend_start_x, legend_start_y), 'halign': ezdxf.enums.TextHAlign.LEFT})
        
        current_y = legend_start_y - 20 # Move down for items
        for tag, component_name in legend_data.items():
            current_y -= 15 # Line spacing
            msp.add_text(f"{tag}: {component_name}", dxfattribs={'height': 4, 'insert': (legend_start_x, current_y), 'halign': ezdxf.enums.TextHAlign.LEFT})


    output = BytesIO()
    try:
        doc.saveas(output)
        output.seek(0)
        return output.read()
    except Exception as e:
        st.error(f"Error during DXF export: {e}")
        return None

def export_png(svg_string):
    try:
        # cairosvg.svg2png expects bytes
        png_bytes = BytesIO(cairosvg.svg2png(bytestring=svg_string.encode('utf-8')))
        return png_bytes.getvalue()
    except Exception as e:
        st.error(f"Error converting SVG to PNG: {e}. This often happens with malformed SVG or invalid transformations. Review your SVG symbols.")
        return None

# --- Data Loading and Initialization ---
# Initialize session state for dataframes if not already present
if 'eq_df' not in st.session_state:
    st.session_state.eq_df = pd.DataFrame()
if 'pipe_df' not in st.session_state:
    st.session_state.pipe_df = pd.DataFrame()
if 'components' not in st.session_state:
    st.session_state.components = {}
if 'pipes' not in st.session_state:
    st.session_state.pipes = []
if 'svg_defs' not in st.session_state:
    st.session_state.svg_defs = {}
if 'svg_meta' not in st.session_state:
    st.session_state.svg_meta = {}
if 'all_subtypes' not in st.session_state:
    st.session_state.all_subtypes = []


def load_initial_data(folder="layout_data"):
    # Clear existing dataframes before loading new
    st.session_state.eq_df = pd.DataFrame()
    st.session_state.pipe_df = pd.DataFrame()

    eq_file_path = os.path.join(folder, "enhanced_equipment_layout.csv")
    pipe_file_path = os.path.join(folder, "pipe_connections_layout.csv")

    if os.path.exists(eq_file_path):
        st.session_state.eq_df = pd.read_csv(eq_file_path)
    # Explicitly define dtype for 'Polyline Points (x, y)' to be string
    if os.path.exists(pipe_file_path):
        st.session_state.pipe_df = pd.read_csv(pipe_file_path, dtype={'Polyline Points (x, y)': str})

    # Re-initialize components and pipes after loading new dataframes
    initialize_pnid_objects()
    # Re-load symbols based on new eq_df
    st.session_state.svg_defs, st.session_state.svg_meta, st.session_state.all_subtypes = load_symbol_and_meta_data(st.session_state.eq_df)

def initialize_pnid_objects():
    # Ensure this runs AFTER eq_df and pipe_df are potentially updated
    st.session_state.components = {c.id: c for c in [PnidComponent(row) for _, row in st.session_state.eq_df.iterrows()]}
    st.session_state.pipes = [PnidPipe(row, st.session_state.components) for _, row in st.session_state.pipe_df.iterrows()]

# --- Streamlit UI Layout ---

st.sidebar.title("EPS Interactive P&ID Generator")

# Load initial data (only once at start or when explicitly triggered)
if 'initial_load_done' not in st.session_state:
    load_initial_data()
    st.session_state.initial_load_done = True
    st.success("P&ID data and symbols loaded!")

# Layout and Visual Controls
st.sidebar.header("Layout & Visual Controls")
grid_spacing = st.sidebar.slider("Grid Spacing", 60, 200, 120)
symbol_scale = st.sidebar.slider("Symbol Scale", 0.50, 2.50, 1.00, 0.05)
pipe_width = st.sidebar.slider("Pipe Width", 1, 5, 2)
tag_font_size = st.sidebar.slider("Tag Font Size", 8, 24, 12)
pipe_label_size = st.sidebar.slider("Pipe Label Size", 6, 18, 10)
legend_font_size = st.sidebar.slider("Legend Font Size", 8, 20, 10)


# Add New Component
st.sidebar.header("➕ Add New Component")
selected_component_type = st.sidebar.selectbox(
    "Component Type", 
    options=st.session_state.all_subtypes, 
    index=0 if st.session_state.all_subtypes else None, 
    format_func=lambda x: x.replace('_', ' ').title() # Make it look nice
)
new_component_id = st.sidebar.text_input("Component ID (unique)")
new_component_tag = st.sidebar.text_input("Component Tag (optional)", value=new_component_id)
new_x = st.sidebar.number_input("X Position", value=100, step=10)
new_y = st.sidebar.number_input("Y Position", value=100, step=10)

if st.sidebar.button("Add Component to Diagram"):
    if new_component_id and selected_component_type:
        # Get default width/height from metadata if available, otherwise use a default
        default_width = st.session_state.svg_meta.get(selected_component_type, {}).get('width', 100)
        default_height = st.session_state.svg_meta.get(selected_component_type, {}).get('height', 100)

        new_component_data = {
            'Component': selected_component_type,
            'id': new_component_id,
            'tag': new_component_tag if new_component_tag else new_component_id,
            'x': new_x,
            'y': new_y,
            'Width': default_width,
            'Height': default_height,
            'Description': "" # Default description
        }
        # Check if ID already exists
        if new_component_id in st.session_state.components:
            st.sidebar.warning(f"Component ID '{new_component_id}' already exists. Please choose a unique ID.")
        else:
            new_eq_df = pd.DataFrame([new_component_data])
            st.session_state.eq_df = pd.concat([st.session_state.eq_df, new_eq_df], ignore_index=True)
            initialize_pnid_objects() # Re-initialize all PnidComponent objects
            st.sidebar.success(f"Component '{new_component_id}' added.")
            st.rerun() # Rerun to update diagram

# Main content area
st.header("Preview: Auto-Generated P&ID")

# Generate and display SVG
svg_output = render_svg_diagram(
    st.session_state.components, 
    st.session_state.pipes, 
    st.session_state.svg_defs, 
    st.session_state.svg_meta, 
    symbol_scale, 
    pipe_width, 
    tag_font_size, 
    pipe_label_size, 
    grid_spacing
)

st.components.v1.html(svg_output, height=800, scrolling=True)

# Instrumentation Control Logic (Simplified Display)
st.subheader("Instrumentation Control Logic")
# Extract control logic from pipe_df if available
instrumentation_pipes = st.session_state.pipe_df[st.session_state.pipe_df['pipe_type'] == 'signal']
if not instrumentation_pipes.empty:
    for _, row in instrumentation_pipes.iterrows():
        from_comp_id = row['From Component']
        to_comp_id = row['To Component']
        label = row['Label']
        st.write(f"{from_comp_id} → {to_comp_id} ({label})")
else:
    st.info("No instrumentation control logic defined in pipe data.")


# Legend
st.subheader("Legend")
# Create legend data from components
legend_data = {c.tag: c.component.replace('_', ' ').title() for c in st.session_state.components.values()}
if legend_data:
    cols = st.columns(3) # Display in columns for better readability
    for i, (tag, comp_name) in enumerate(legend_data.items()):
        cols[i % 3].markdown(f"<span style='font-size:{legend_font_size}px;'>**{tag}**: {comp_name}</span>", unsafe_allow_html=True)
else:
    st.info("No components to display in legend.")


# Download Options
st.subheader("Download Options")
col1, col2, col3 = st.columns(3)

with col1:
    st.download_button(
        label="Download SVG",
        data=svg_output.encode('utf-8'),
        file_name="pnid.svg",
        mime="image/svg+xml"
    )

# The PNG export relies on cairosvg, which can be problematic if symbols are malformed.
# Only attempt if cairosvg is importable and no Cairo error (though that's runtime)
try:
    import cairosvg
    with col2:
        if st.button("Generate & Download PNG"):
            with st.spinner("Generating PNG..."):
                png_output = export_png(svg_output)
                if png_output:
                    st.download_button(
                        label="Download PNG",
                        data=png_output,
                        file_name="pnid.png",
                        mime="image/png"
                    )
                else:
                    st.error("Failed to generate PNG. Check for console errors related to SVG rendering.")
except ImportError:
    st.warning("`cairosvg` library not found. PNG export is disabled. Install with `pip install cairosvg`.")

with col3:
    # Prepare legend for DXF export
    dxf_legend_data = {c.tag: c.description if c.description else c.component.replace('_', ' ').title() for c in st.session_state.components.values()}
    dxf_data = export_dxf(st.session_state.components, st.session_state.pipes, dxf_legend_data, grid_spacing)
    if dxf_data:
        st.download_button(
            label="Download DXF",
            data=dxf_data,
            file_name="pnid.dxf",
            mime="application/dxf"
        )
    else:
        st.warning("DXF export failed or data not available.")


# Data Management Section
st.subheader("Data Management")

# Debug Info (Show current dataframes)
with st.expander("Debug Info"):
    st.write("Current `eq_df` (head after cleaning):")
    st.dataframe(st.session_state.eq_df.head())
    st.write("Current `pipe_df` (head after cleaning):")
    st.dataframe(st.session_state.pipe_df.head())
    st.write("All Subtypes:")
    st.write(st.session_state.all_subtypes)


uploaded_eq_file = st.file_uploader("Upload Equipment Layout CSV", type="csv")
if uploaded_eq_file is not None:
    st.session_state.eq_df = pd.read_csv(uploaded_eq_file)
    initialize_pnid_objects()
    st.session_state.svg_defs, st.session_state.svg_meta, st.session_state.all_subtypes = load_symbol_and_meta_data(st.session_state.eq_df)
    st.success("Equipment layout CSV uploaded and loaded!")
    st.rerun()

uploaded_pipe_file = st.file_uploader("Upload Pipe Connections CSV", type="csv")
if uploaded_pipe_file is not None:
    # Explicitly define dtype for 'Polyline Points (x, y)' to be string
    st.session_state.pipe_df = pd.read_csv(uploaded_pipe_file, dtype={'Polyline Points (x, y)': str})
    initialize_pnid_objects() # Re-initialize pipes with updated pipe_df and existing components
    st.success("Pipe connections CSV uploaded and loaded!")
    st.rerun()

if st.button("Clear Diagram (Reset to Empty)"):
    st.session_state.eq_df = pd.DataFrame()
    st.session_state.pipe_df = pd.DataFrame()
    st.session_state.components = {}
    st.session_state.pipes = []
    st.session_state.svg_defs = {}
    st.session_state.svg_meta = {}
    st.session_state.all_subtypes = []
    st.success("Diagram data cleared.")
    st.rerun()

# Save current diagram data to files
if st.button("Save Current Diagram Data to Files"):
    try:
        # Ensure the directory exists
        save_dir = "layout_data"
        os.makedirs(save_dir, exist_ok=True)

        st.session_state.eq_df.to_csv(os.path.join(save_dir, "enhanced_equipment_layout.csv"), index=False)
        # Ensure 'Polyline Points (x, y)' is written as string (though it should be after dtype fix)
        st.session_state.pipe_df.to_csv(os.path.join(save_dir, "pipe_connections_layout.csv"), index=False)
        st.success(f"Current diagram data saved to '{save_dir}' folder.")
    except Exception as e:
        st.error(f"Error saving data: {e}")

