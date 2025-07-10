import streamlit as st
import pandas as pd
import os
import json
import datetime
import re
import openai
import psycopg2
from io import BytesIO
import ezdxf
from cairosvg import svg2png

# --- CONFIGURATION ---
st.set_page_config(layout="wide")
st.sidebar.title("EPS Interactive P&ID Generator")

# Sliders for visual controls
st.sidebar.markdown("### Layout & Visual Controls")
GRID_SPACING = st.sidebar.slider("Grid Spacing", 60, 200, 120, 5, key="grid_spacing")
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.5, 1.0, 0.1, key="symbol_scale")
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 5, 2, key="pipe_width")
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12, key="tag_font_size")
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 18, 10, key="pipe_label_font_size")
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10, key="legend_font_size")

# Global constants
PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 100
TITLE_BLOCK_WIDTH = 400
TITLE_BLOCK_CLIENT = "EPS Pvt. Ltd."

# Directory paths
LAYOUT_DATA_DIR = "layout_data"
SYMBOLS_DIR = "symbols"

# API keys and DB URL from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- HELPERS ---
def normalize(s):
    """Normalizes a string for use as a subtype identifier."""
    if not isinstance(s, str):
        return ""
    return s.lower().strip().replace(" ", "_").replace("-", "_")

def clean_svg_string(svg: str):
    """Removes XML declaration and DOCTYPE from an SVG string."""
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg, flags=re.MULTILINE).strip()
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg, flags=re.MULTILINE).strip()
    return svg

def load_svg_from_db(subtype):
    """Loads SVG data for a given subtype from the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT svg_data FROM generated_symbols WHERE subtype = %s", (subtype,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else None
    except Exception as e:
        st.error(f"DB Load Error for '{subtype}': {e}")
        return None

def save_svg_to_db(subtype, svg):
    """Saves SVG data for a given subtype to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO generated_symbols (subtype, svg_data)
            VALUES (%s, %s)
            ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data
        """, (subtype, svg))
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        st.error(f"DB Save Error for '{subtype}': {e}")

def generate_svg_openai(subtype):
    """Generates an SVG symbol using OpenAI's GPT-4 model."""
    prompt = f"Generate an SVG symbol in ISA P&ID style for a {subtype.replace('_', ' ')}. Transparent background. Use black lines only. Provide ONLY the SVG code, no extra text or markdown."
    try:
        with st.spinner(f"Generating '{subtype.replace('_', ' ').title()}' symbol with AI..."):
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a process engineer who outputs SVG drawings using ISA symbols."},
                    {"role": "user", "content": prompt}
                ]
            )
        raw_svg = res["choices"][0]["message"]["content"]
        # Clean before checking for <svg> to remove any markdown wrappers or conversational text
        cleaned_svg = clean_svg_string(raw_svg)
        if "<svg" in cleaned_svg:
            return cleaned_svg
        else:
            st.warning(f"OpenAI did not return a valid SVG for '{subtype}'. Raw (cleaned) response snippet: {cleaned_svg[:200]}...")
            return None
    except Exception as e:
        st.error(f"OpenAI Fallback Error for '{subtype}': {e}")
        return None

@st.cache_resource
def load_symbol_and_meta_data(initial_eq_df, initial_mapping):
    """
    Loads all SVG symbols and populates metadata (viewBox, ports).
    Cached using st.cache_resource as this is expensive and static per session.
    """
    st.info("Loading initial P&ID data and symbols (this may take a moment)...")

    # Get all unique subtypes from the initial equipment data
    all_subtypes_from_data = sorted({normalize(row.get("block", "")) for _, row in initial_eq_df.iterrows() if normalize(row.get("block", ""))})

    svg_defs_dict = {}
    svg_meta_dict = {}

    for subtype in all_subtypes_from_data:
        svg_path = os.path.join(SYMBOLS_DIR, f"{subtype}.svg")
        svg_data = None

        # 1. Try to load from local file system
        if os.path.exists(svg_path):
            with open(svg_path, 'r') as f:
                svg_data = f.read()
            svg_data = clean_svg_string(svg_data) # Clean loaded SVG

        # 2. If not found, try loading from database
        if not svg_data or "<svg" not in svg_data:
            svg_data = load_svg_from_db(subtype)
            if svg_data: # If loaded from DB, ensure it's clean
                svg_data = clean_svg_string(svg_data)

        # 3. If still not found, generate using OpenAI and save
        if not svg_data or "<svg" not in svg_data:
            svg_data = generate_svg_openai(subtype)
            if svg_data:
                # Save to local file system
                os.makedirs(SYMBOLS_DIR, exist_ok=True)
                with open(svg_path, "w") as f:
                    f.write(svg_data)
                # Save to database
                save_svg_to_db(subtype, svg_data)
        
        # Process the loaded/generated SVG
        if svg_data and "<svg" in svg_data:
            viewbox_match = re.search(r'viewBox="([^"]+)"', svg_data)
            viewbox = viewbox_match.group(1) if viewbox_match else "0 0 100 100"
            # Wrap SVG in <symbol> for efficient use in main SVG
            symbol = re.sub(r"<svg[^>]*>", f'<symbol id="{subtype}" viewBox="{viewbox}">', svg_data)
            symbol = symbol.replace("</svg>", "</symbol>")
            svg_defs_dict[subtype] = symbol
            svg_meta_dict[subtype] = {"viewBox": viewbox, "ports": {}}
        else:
            # Fallback for symbols that couldn't be loaded/generated
            st.warning(f"Could not load or generate a valid SVG for subtype: '{subtype}'. Using a placeholder.")
            svg_defs_dict[subtype] = None # No symbol def for this one
            svg_meta_dict[subtype] = {"viewBox": "0 0 100 100", "ports": {}} # Still provide meta with default viewbox

    # Populate ports from component_mapping.json for all subtypes
    for entry in initial_mapping:
        subtype = normalize(entry.get("Component", ""))
        if subtype: # Ensure subtype is not empty
            port_name = entry.get("Port Name", "default")
            dx, dy = float(entry.get("dx", 0)), float(entry.get("dy", 0))
            if subtype not in svg_meta_dict: # Add entry if it doesn't exist from SVG loading
                 svg_meta_dict[subtype] = {"viewBox": "0 0 100 100", "ports": {}}
            svg_meta_dict[subtype]["ports"][port_name] = {"dx": dx, "dy": dy}
    st.success("P&ID data and symbols loaded!")
    return svg_defs_dict, svg_meta_dict, all_subtypes

# --- SESSION STATE INITIALIZATION ---
if 'eq_df' not in st.session_state:
    @st.cache_data
    def initial_load_layout_data():
        """Loads initial layout data from CSV/JSON. Cached separately for first load."""
        eq_df_path = os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv")
        pipe_df_path = os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv")
        mapping_path = os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")

        if not os.path.exists(eq_df_path):
            st.error(f"Error: {eq_df_path} not found. Please ensure it exists.")
            st.stop()
        if not os.path.exists(pipe_df_path):
            st.error(f"Error: {pipe_df_path} not found. Please ensure it exists.")
            st.stop()

        eq_df = pd.read_csv(eq_df_path)
        pipe_df = pd.read_csv(pipe_df_path)
        try:
            with open(mapping_path) as f:
                mapping = json.load(f)
        except FileNotFoundError:
            st.warning(f"Warning: {mapping_path} not found. Component port mapping will be limited.")
            mapping = []
        except json.JSONDecodeError as e:
            st.error(f"Error decoding {mapping_path}: {e}. Please check JSON format.")
            mapping = []
        return eq_df, pipe_df, mapping

    st.session_state.eq_df, st.session_state.pipe_df, st.session_state.mapping = initial_load_layout_data()

# Load symbols and metadata using cache_resource (runs once per app session or input change)
svg_defs, svg_meta, all_subtypes = load_symbol_and_meta_data(st.session_state.eq_df, st.session_state.mapping)

# Get current dataframes from session state for rendering/modification
eq_df_current = st.session_state.eq_df
pipe_df_current = st.session_state.pipe_df

# --- P&ID CLASSES ---
class PnidComponent:
    """Represents a P&ID component."""
    def __init__(self, row):
        self.id = row['id']
        self.tag = row.get('tag', self.id)
        self.subtype = normalize(row.get('block', ''))
        self.x = row['x']
        self.y = row['y']
        # Use default width/height if not provided, scale by SYMBOL_SCALE
        self.width = row.get('Width', 60) * SYMBOL_SCALE
        self.height = row.get('Height', 60) * SYMBOL_SCALE
        # Get port info from global svg_meta
        self.ports = svg_meta.get(self.subtype, {}).get('ports', {})

    def get_port_coords(self, port_name):
        """Calculates absolute coordinates for a given port."""
        port = self.ports.get(port_name)
        if port:
            return (self.x + port["dx"] * SYMBOL_SCALE, self.y + port["dy"] * SYMBOL_SCALE)
        # Fallback to center if port not found or default is requested
        st.warning(f"Port '{port_name}' not defined for component '{self.tag}' (subtype: {self.subtype}). Using center coordinates.")
        return (self.x + self.width / 2, self.y + self.height / 2)

class PnidPipe:
    """Represents a P&ID pipe connection."""
    def __init__(self, row, component_map):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        self.points = []
        from_comp_id = row['From Component']
        to_comp_id = row['To Component']
        from_comp = component_map.get(from_comp_id)
        to_comp = component_map.get(to_comp_id)

        # Log warnings for missing components
        if not from_comp:
            st.warning(f"Pipe '{self.id}': 'From Component' ID '{from_comp_id}' not found. Pipe may be incomplete.")
        if not to_comp:
            st.warning(f"Pipe '{self.id}': 'To Component' ID '{to_comp_id}' not found. Pipe may be incomplete.")

        # Prioritize Polyline Points from CSV if present
        if 'Polyline Points (x, y)' in row and isinstance(row['Polyline Points (x, y)'], str) and row['Polyline Points (x, y)'].strip():
            pts = re.findall(r"\(([\d.\-]+),\s*([\d.\-]+)\)", row['Polyline Points (x, y)'])
            self.points = [(float(x), float(y)) for x, y in pts]
            # Snap endpoints to port positions if components exist
            if self.points:
                if from_comp: self.points[0] = from_comp.get_port_coords(row.get("From Port", "default"))
                if to_comp: self.points[-1] = to_comp.get_port_coords(row.get("To Port", "default"))
        else:
            # Default to direct line between components if no polyline points
            if from_comp and to_comp:
                self.points = [
                    from_comp.get_port_coords(row.get("From Port", "default")),
                    to_comp.get_port_coords(row.get("To Port", "default"))
                ]
            # Handle cases where only one component is found (draw a stub)
            elif from_comp:
                self.points = [from_comp.get_port_coords(row.get("From Port", "default")), (from_comp.x + from_comp.width / 2 + 50, from_comp.y + from_comp.height / 2)] # Draw a stub 50 units right
            elif to_comp:
                self.points = [(to_comp.x + to_comp.width / 2 - 50, to_comp.y + to_comp.height / 2), to_comp.get_port_coords(row.get("To Port", "default"))] # Draw a stub 50 units left


# --- Initialize PnidComponent and PnidPipe objects from current dataframes ---
# This block MUST come BEFORE any UI elements that try to use 'components' or 'pipes'
components = {row['id']: PnidComponent(row) for _, row in eq_df_current.iterrows()}
pipes = [PnidPipe(row, components) for _, row in pipe_df_current.iterrows()]

# --- SVG RENDERING FUNCTIONS (Modularized) ---

def _render_svg_defs_section():
    """Renders the <defs> section of the SVG with arrowhead marker and all component symbols."""
    defs = ["<defs>"]
    defs.append('<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black"/></marker>')
    for symbol_id, symbol_content in svg_defs.items():
        if symbol_content: # Only add if symbol content exists
            defs.append(symbol_content)
    defs.append("</defs>")
    return "".join(defs)

def _render_grid_lines(max_x, max_y, grid_spacing):
    """Renders grid lines for the P&ID diagram."""
    grid_lines = []
    for i in range(0, int(max_x), grid_spacing):
        grid_lines.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{max_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, int(max_y), grid_spacing):
        grid_lines.append(f'<line x1="0" y1="{i}" x2="{max_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')
    return "".join(grid_lines)

def _render_legend_section(components_map, max_x, max_y, legend_x, legend_y):
    """Renders the legend box and entries."""
    legend_svg = []
    # Adjust legend box height based on diagram height, but with a max
    legend_box_height = min(650, max_y - (legend_y - 30) - 60) # Ensure it doesn't go off screen
    legend_svg.append(f'<rect x="{legend_x-10}" y="{legend_y-30}" width="{LEGEND_WIDTH-40}" height="{legend_box_height}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    legend_svg.append(f'<text x="{legend_x+80}" y="{legend_y-10}" font-size="{LEGEND_FONT_SIZE+4}" font-weight="bold">Legend</text>')

    legend_entries = {}
    for c in components_map.values(): # Use components_map here
        if c.subtype: # Ensure subtype is not empty
            key = (c.tag, c.subtype)
            if key not in legend_entries:
                legend_entries[key] = c.subtype.replace("_", " ").title()

    legend_y_pos = legend_y + 20
    for i, ((tag, subtype), name) in enumerate(legend_entries.items()):
        sym_pos_y = legend_y_pos + i * 28 - 10 # Adjusted for vertical spacing
        
        # Calculate icon size based on viewBox
        width, height = 20, 20 # Default small size if no viewBox or symbol found
        if subtype in svg_meta and svg_meta[subtype] and 'viewBox' in svg_meta[subtype]:
            try:
                viewBox = svg_meta[subtype]["viewBox"].split(" ")
                vb_w = float(viewBox[2])
                vb_h = float(viewBox[3])
                scale_factor = min(25 / vb_w, 25 / vb_h) # Max 25px in any dimension
                width = vb_w * scale_factor
                height = vb_h * scale_factor
            except (ValueError, IndexError):
                pass # Use default if viewBox parsing fails

        if subtype in svg_defs and svg_defs[subtype]:
            legend_svg.append(f'<use href="#{subtype}" x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" />')
        else:
            # Fallback for missing symbol in legend
            legend_svg.append(f'<rect x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" fill="#eee" stroke="red"/>')
        
        legend_svg.append(f'<text x="{legend_x+32}" y="{sym_pos_y+16}" font-size="{LEGEND_FONT_SIZE}">{tag} — {name}</text>')
    return "".join(legend_svg)

def _render_title_block(max_y):
    """Renders the title block with client name and generation date."""
    title_block_svg = []
    title_block_svg.append(f'<rect x="10" y="{max_y-TITLE_BLOCK_HEIGHT}" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT-10}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    title_block_svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+30}" font-size="14" font-weight="bold">{TITLE_BLOCK_CLIENT}</text>')
    title_block_svg.append(f'<text x="30" y="{max_y-TITLE_BLOCK_HEIGHT+55}" font-size="12">Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</text>')
    return "".join(title_block_svg)

def _render_components(components_map): # Use components_map as argument
    """Renders all P&ID components."""
    components_svg = []
    for c in components_map.values():
        if c.subtype in svg_defs and svg_defs[c.subtype]:
            components_svg.append(f'<use href="#{c.subtype}" x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" />')
            components_svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 14}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
        else:
            # Fallback for missing component symbol
            components_svg.append(f'<rect x="{c.x}" y="{c.y}" width="{c.width}" height="{c.height}" fill="lightgray" stroke="red"/>')
            components_svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height/2}" font-size="{TAG_FONT_SIZE}" text-anchor="middle" fill="black">?</text>')
            components_svg.append(f'<text x="{c.x + c.width/2}" y="{c.y + c.height + 14}" font-size="{TAG_FONT_SIZE}" text-anchor="middle">{c.tag}</text>')
    return "".join(components_svg)

def _render_pipes(pipes_list): # Use pipes_list as argument
    """Renders all P&ID pipes."""
    pipes_svg = []
    for p in pipes_list:
        if len(p.points) >= 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            pipes_svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#arrowhead)"/>')
            # Calculate midpoint for label
            mx = sum(x for x, _ in p.points) / len(p.points)
            my = sum(y for _, y in p.points) / len(p.points)
            pipes_svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')
    return "".join(pipes_svg)

def render_svg_diagram(components_map, pipes_list):
    """Main function to render the complete P&ID SVG."""
    # Determine overall SVG dimensions (zoom-to-fit)
    # Get max_x and max_y from components
    max_x_comp = max((c.x + c.width for c in components_map.values()), default=0)
    max_y_comp = max((c.y + c.height for c in components_map.values()), default=0)

    # Get max_x and max_y from pipe points
    pipe_max_x = max((x for p in pipes_list for x, _ in p.points), default=0)
    pipe_max_y = max((y for p in pipes_list for _, y in p.points), default=0)

    # Combine and add padding, legend width, title block height
    total_max_x = max(max_x_comp, pipe_max_x) + PADDING + LEGEND_WIDTH
    total_max_y = max(max_y_comp, pipe_max_y) + PADDING + TITLE_BLOCK_HEIGHT

    svg_parts = []
    svg_parts.append(f'<svg width="{total_max_x}" height="{total_max_y}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">')

    svg_parts.append(_render_svg_defs_section())
    svg_parts.append(_render_grid_lines(total_max_x, total_max_y, GRID_SPACING))
    svg_parts.append(_render_legend_section(components_map, total_max_x, total_max_y, total_max_x - LEGEND_WIDTH + 30, 50))
    svg_parts.append(_render_title_block(total_max_y))
    svg_parts.append(_render_components(components_map))
    svg_parts.append(_render_pipes(pipes_list))

    svg_parts.append('</svg>')
    return "".join(svg_parts)


# --- ISA LOGIC BLOCK ---
def generate_isa_control_logic_box(components_map):
    """Generates a text block describing ISA instrumentation control logic based on component tags."""
    logic_lines = []
    logic_lines.append("INSTRUMENTATION CONTROL LOGIC")
    logic_lines.append("──────────────────────────────")
    loop_counter = 1
    # Identify common ISA tag prefixes for instruments that might be part of control loops
    instrument_tags = sorted([
        comp.tag for comp in components_map.values()
        if any(re.match(r'^(P|T|F|L|C|D|V|Z)I', comp.tag) or # P-Pressure, T-Temp, F-Flow, L-Level, C-Control, D-Density, V-Valve, Z-Position, I-Indicator
               re.match(r'^(P|T|F|L|C)T', comp.tag) # T-Transmitter
               for code in ['PT', 'TT', 'FT', 'LT', 'CT', 'ZT'] if code in comp.tag.upper()
              )
    ])

    for tag in instrument_tags:
        # Example logic: if it's a transmitter, assume it feeds into a PID loop and a control valve
        if 'T' in tag and len(tag) > 2 and tag[1] in 'TPFL': # e.g., PT, TT, FT, LT
             # Extract base variable (P, T, F, L)
            variable_type = tag[0]
            # Try to find a related control valve (CV) or general valve (V)
            related_valve = f"CV-{loop_counter:03d}" # Placeholder or try to match
            logic_lines.append(f"{tag} (Measured {variable_type}) → PID Controller → {related_valve} (LOOP-{loop_counter:03d})")
            loop_counter += 1
        elif 'V' in tag or 'Z' in tag: # e.g., FV, LV, ZV (Flow Valve, Level Valve, Position Valve)
            # Already handled by above, but can add specific logic if needed
            pass
        else: # Catch-all for other instruments
             logic_lines.append(f"{tag} (Instrument)")


    return "\n".join(logic_lines)

# --- STREAMLIT APP LAYOUT ---

# Manual Component Addition Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### ➕ Add New Component")
with st.sidebar.form("add_component_form"):
    new_comp_subtype = st.selectbox("Component Type", options=all_subtypes, key="new_comp_type_select")
    new_comp_id = st.text_input("Component ID (unique)", key="new_comp_id_input")
    new_comp_tag = st.text_input("Component Tag (optional)", value="", key="new_comp_tag_input")
    new_comp_x = st.number_input("X Position", value=100, step=10, key="new_comp_x_input")
    new_comp_y = st.number_input("Y Position", value=100, step=10, key="new_comp_y_input")

    add_comp_submitted = st.form_submit_button("Add Component to Diagram")

    if add_comp_submitted:
        if not new_comp_id:
            st.error("Component ID cannot be empty.")
        elif new_comp_id in st.session_state.eq_df['id'].values:
            st.error(f"Component ID '{new_comp_id}' already exists. Please choose a unique ID.")
        else:
            new_row = {
                'id': new_comp_id,
                'tag': new_comp_tag if new_comp_tag else new_comp_id,
                'block': new_comp_subtype,
                'x': new_comp_x,
                'y': new_comp_y,
                'Width': 60,  # Default values
                'Height': 60
            }
            # Update the session state DataFrame directly
            st.session_state.eq_df = pd.concat([st.session_state.eq_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Added component '{new_comp_id}' of type '{new_comp_subtype}'.")
            st.rerun() # Rerun to update diagram and component lists

# Manual Pipe Addition Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### ➕ Add New Pipe")
# Get current component IDs for dropdowns
current_comp_ids = sorted(list(eq_df_current['id'].unique()))
if not current_comp_ids: # Add a placeholder if no components exist yet
    current_comp_ids = ["No components available"]

with st.sidebar.form("add_pipe_form"):
    new_pipe_id = st.text_input("Pipe ID (unique)", key="new_pipe_id_input")
    new_pipe_label = st.text_input("Pipe Label (optional)", key="new_pipe_label_input")
    from_comp_select = st.selectbox("From Component", options=current_comp_ids, key="from_comp_select")
    
    # Dynamically populate 'From Port' options based on selected 'From Component'
    # This now works because 'components' is defined earlier
    from_comp_obj = components.get(from_comp_select)
    from_port_options = sorted(list(from_comp_obj.ports.keys())) if from_comp_obj else ["default"]
    new_pipe_from_port = st.selectbox("From Port", options=from_port_options, key="new_pipe_from_port")

    to_comp_select = st.selectbox("To Component", options=current_comp_ids, key="to_comp_select")
    
    # Dynamically populate 'To Port' options
    to_comp_obj = components.get(to_comp_select)
    to_port_options = sorted(list(to_comp_obj.ports.keys())) if to_comp_obj else ["default"]
    new_pipe_to_port = st.selectbox("To Port", options=to_port_options, key="new_pipe_to_port")

    add_pipe_submitted = st.form_submit_button("Add Pipe to Diagram")

    if add_pipe_submitted:
        if not new_pipe_id:
            st.error("Pipe ID cannot be empty.")
        elif new_pipe_id in st.session_state.pipe_df['Pipe No.'].values:
            st.error(f"Pipe ID '{new_pipe_id}' already exists. Please choose a unique ID.")
        elif from_comp_select == "No components available" or to_comp_select == "No components available":
            st.error("Please add components first before adding pipes.")
        elif from_comp_select == to_comp_select:
            st.warning("Pipes connecting a component to itself are not typical. Proceeding anyway.")
        else:
            new_pipe_row = {
                'Pipe No.': new_pipe_id,
                'Label': new_pipe_label if new_pipe_label else f"Pipe {new_pipe_id}",
                'From Component': from_comp_select,
                'From Port': new_pipe_from_port,
                'To Component': to_comp_select,
                'To Port': new_pipe_to_port,
                'Polyline Points (x, y)': '' # Initially, let it be auto-calculated (straight line)
            }
            # Update the session state DataFrame directly
            st.session_state.pipe_df = pd.concat([st.session_state.pipe_df, pd.DataFrame([new_pipe_row])], ignore_index=True)
            st.success(f"Added pipe '{new_pipe_id}'.")
            st.rerun() # Rerun to update diagram

# --- Main Content Area - Renders the P&ID ---
st.markdown("## Preview: Auto-Generated P&ID")

# Render and display SVG
svg_output = render_svg_diagram(components, pipes)
st.markdown(svg_output, unsafe_allow_html=True)

# ISA Control Logic Section
st.markdown("---")
st.markdown("### 🔧 Instrumentation Control Logic")
logic_block = generate_isa_control_logic_box(components)
st.text_area("ISA Instrumentation Control Logic", value=logic_block, height=200, key="isa_logic_output")


# --- EXPORT OPTIONS ---
st.markdown("---")
st.markdown("### ⬇️ Download Options")
col1, col2, col3 = st.columns(3)

# PNG Export
def export_png(svg_data):
    output = BytesIO()
    svg2png(bytestring=svg_data.encode(), write_to=output)
    return output.getvalue()

# DXF Export
def export_dxf(components_map, pipes_list): # Use arguments for clarity
    doc = ezdxf.new()
    msp = doc.modelspace()
    for c in components_map.values():
        # Ensure text location is correctly set
        msp.add_text(c.tag, dxfattribs={'height': 2.5, 'insert': (c.x, c.y + c.height + 5)}) # Adjust text position slightly
    for p in pipes_list:
        if len(p.points) >= 2:
            msp.add_lwpolyline(p.points)
    output = BytesIO()
    doc.write(output)
    return output.getvalue()

with col1:
    st.download_button("📥 Download SVG", svg_output, "pnid.svg", "image/svg+xml", key="download_svg")
with col2:
    st.download_button("📥 Download PNG", export_png(svg_output), "pnid.png", "image/png", key="download_png")
with col3:
    st.download_button("📥 Download DXF", export_dxf(components, pipes), "pnid.dxf", "application/dxf", key="download_dxf")

# --- DATA MANAGEMENT ---
st.markdown("---")
st.markdown("### 🗃️ Data Management")

# Display current dataframes
with st.expander("View Current Components Data"):
    st.dataframe(eq_df_current, use_container_width=True)

with st.expander("View Current Pipes Data"):
    st.dataframe(pipe_df_current, use_container_width=True)

# Save current state to files
if st.button("💾 Save Current Diagram Data to Files"):
    try:
        os.makedirs(LAYOUT_DATA_DIR, exist_ok=True)
        st.session_state.eq_df.to_csv(os.path.join(LAYOUT_DATA_DIR, "current_equipment_layout.csv"), index=False)
        st.session_state.pipe_df.to_csv(os.path.join(LAYOUT_DATA_DIR, "current_pipe_connections_layout.csv"), index=False)
        st.success(f"Diagram data saved to '{LAYOUT_DATA_DIR}' folder.")
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Clear diagram button
if st.button("🗑️ Clear Diagram (Reset to Empty)"):
    if st.warning("Are you sure you want to clear the diagram? This cannot be undone.", icon="⚠️"):
        # Reset to empty DataFrames with original columns
        st.session_state.eq_df = pd.DataFrame(columns=['id', 'tag', 'block', 'x', 'y', 'Width', 'Height'])
        st.session_state.pipe_df = pd.DataFrame(columns=['Pipe No.', 'Label', 'From Component', 'From Port', 'To Component', 'To Port', 'Polyline Points (x, y)'])
        st.success("Diagram cleared!")
        st.rerun()

# Upload new dataframes
st.markdown("#### Upload New Diagram Data")
uploaded_eq_file = st.file_uploader("Upload Equipment Layout CSV", type=["csv"], key="upload_eq_file")
uploaded_pipe_file = st.file_uploader("Upload Pipe Connections CSV", type=["csv"], key="upload_pipe_file")

if uploaded_eq_file or uploaded_pipe_file:
    if st.button("Load Uploaded Data"):
        try:
            if uploaded_eq_file:
                st.session_state.eq_df = pd.read_csv(uploaded_eq_file)
                st.success("Equipment data loaded from uploaded file.")
            if uploaded_pipe_file:
                st.session_state.pipe_df = pd.read_csv(uploaded_pipe_file)
                st.success("Pipe data loaded from uploaded file.")
            st.rerun() # Rerun to apply new data
        except Exception as e:
            st.error(f"Error loading uploaded files: {e}")

# --- OPTIONAL DEBUG INFO ---
with st.expander("🔍 Debug Info"):
    st.write("Current `eq_df` head:")
    st.dataframe(eq_df_current.head())
    st.write("Current `pipe_df` head:")
    st.dataframe(pipe_df_current.head())
    st.write("All Subtypes:", all_subtypes)
    st.write("SVG Meta (sample):", {k: {key: val for key, val in v.items() if key != 'ports'} for k,v in list(svg_meta.items())[:3]}) # show sample without port details
    st.write("First few SVG Defs (sample):", list(svg_defs.keys())[:5])

