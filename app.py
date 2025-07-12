import streamlit as st
import pandas as pd
import os
import json
import datetime
import re
import openai # Keep this import
import psycopg2
from psycopg2 import sql # Import sql from psycopg2 for safe queries
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
# Ensure these are set in your environment or .streamlit/secrets.toml
# --- IMPORTANT FIX: Initialize OpenAI client for new API ---
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

# --- HELPERS ---
def normalize(s):
    """Normalizes a string for use as a subtype identifier (e.g., for SVG filenames)."""
    if not isinstance(s, str):
        return ""
    # Use lowercase and replace spaces/hyphens for file names
    return s.lower().strip().replace(" ", "_").replace("-", "_")

def clean_component_id(s):
    """Normalizes a string for use as a component ID for lookup. Strips whitespace."""
    if not isinstance(s, str):
        return ""
    return s.strip()

def clean_svg_string(svg: str):
    """Removes XML declaration and DOCTYPE from an SVG string."""
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg, flags=re.MULTILINE).strip()
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg, flags=re.MULTILINE).strip()
    return svg

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}. Please ensure DATABASE_URL is set correctly and the database is accessible.")
        return None

def load_symbol_data_from_db(subtype):
    """Loads SVG data and metadata for a given subtype from the PostgreSQL database."""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Ensure column names match database exactly (lowercase often)
            cur.execute(sql.SQL("SELECT svg_data, metadata FROM generated_symbols WHERE subtype = %s"), (subtype,))
            row = cur.fetchone()
            cur.close()
            # --- SAFER JSON HANDLING FIX ---
            if row:
                svg_data = row[0]
                metadata_raw = row[1]
                # Only load JSON if it's a string or bytes
                if isinstance(metadata_raw, (str, bytes, bytearray)):
                    try:
                        metadata = json.loads(metadata_raw)
                    except Exception as e:
                        st.warning(f"Could not parse metadata JSON for {subtype}: {e}")
                        metadata = {}
                elif isinstance(metadata_raw, dict):  # Already a dict (e.g., from psycopg2 and JSONB)
                    metadata = metadata_raw
                else:
                    metadata = {}
                return svg_data, metadata
            else:
                return None, {}
        except Exception as e:
            st.warning(f"DB Load Error for '{subtype}': {e}. This might mean the column doesn't exist or data is malformed.")
            return None, {}
        finally:
            conn.close()
    return None, {}

def save_symbol_data_to_db(subtype, svg, metadata):
    """Saves SVG data and metadata for a given subtype to the PostgreSQL database."""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(sql.SQL("""
                INSERT INTO generated_symbols (subtype, svg_data, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (subtype) DO UPDATE SET svg_data = EXCLUDED.svg_data, metadata = EXCLUDED.metadata
            """), (subtype, svg, json.dumps(metadata))) # json.dumps for JSONB type
            conn.commit()
            cur.close()
        except Exception as e:
            st.error(f"DB Save Error for '{subtype}': {e}")
        finally:
            conn.close()

def generate_svg_openai(subtype):
    """Generates an SVG symbol using OpenAI's GPT-4 model."""
    prompt = f"Generate an SVG symbol in ISA P&ID style for a {subtype.replace('_', ' ')}. Transparent background. Use black lines only. Include standard port locations (e.g., 'inlet', 'outlet') as a JSON object within an SVG <metadata> tag, specifying 'dx' and 'dy' offsets from the symbol's viewBox origin (0,0). Provide ONLY the SVG code, no extra text or markdown."
    try:
        with st.spinner(f"Generating '{subtype.replace('_', ' ').title()}' symbol with AI..."):
            # --- IMPORTANT FIX: Use new OpenAI API syntax ---
            res = openai_client.chat.completions.create(
                model="gpt-3.5-turbo", # Using gpt-3.5-turbo as per previous successful attempts
                messages=[
                    {"role": "system", "content": "You are a process engineer who outputs SVG drawings using ISA symbols. Always include a <metadata> tag with port information (dx, dy) in JSON format. Do not include any XML declaration, DOCTYPE, or external text outside the main <svg> tag."},
                    {"role": "user", "content": prompt}
                ]
            )
        raw_content = res.choices[0].message.content.strip() # Accessing content for new API
        
        # Regex to find the SVG block (this is more robust for AI outputs)
        svg_match = re.search(r'<svg.*?</svg>', raw_content, re.DOTALL | re.IGNORECASE)
        
        if svg_match:
            svg_string = svg_match.group(0)
            
            # Extract metadata if available
            metadata = {}
            metadata_match = re.search(r'<metadata>\s*(\{.*\})\s*</metadata>', svg_string, re.DOTALL)
            if metadata_match:
                try:
                    metadata = json.loads(metadata_match.group(1))
                except json.JSONDecodeError:
                    st.warning(f"Could not parse metadata JSON for {subtype}.")
            
            # Remove metadata tag from the final SVG
            svg_string = re.sub(r'<metadata>.*?</metadata>', '', svg_string, flags=re.DOTALL)
            
            cleaned_svg = clean_svg_string(svg_string) # Final cleaning
            if "<svg" in cleaned_svg:
                return cleaned_svg, metadata
            else:
                st.warning(f"Generated content for {subtype} was not a valid SVG format after cleaning.")
                return None, {}
        else:
            st.warning(f"OpenAI did not return a valid SVG block for '{subtype}'. Raw response snippet: {raw_content[:200]}...")
            return None, {}

    except openai.APIError as e: # Catch new API error type
        st.error(f"OpenAI API Error for '{subtype}': {e}. Please check your OpenAI API key and ensure it has access.")
        return None, {}
    except Exception as e:
        st.error(f"An unexpected error occurred during OpenAI SVG generation for '{subtype}': {e}")
        return None, {}

@st.cache_resource
def load_symbol_and_meta_data(initial_eq_df, initial_mapping):
    """
    Loads all SVG symbols and populates metadata (viewBox, ports).
    Cached using st.cache_resource as this is expensive and static per session.
    """
    st.info("Loading initial P&ID data and symbols (this may take a moment)...")

    # Ensure all_subtypes is generated only from actual component names
    all_subtypes_from_data = sorted(
        {normalize(row.get("Component")) for _, row in initial_eq_df.iterrows() 
         if row.get("Component") is not None and isinstance(row.get("Component"), str)}
    )

    svg_defs_dict = {}
    svg_meta_dict = {}

    for subtype in all_subtypes_from_data:
        svg_data = None
        metadata = {}

        # 1. Try to load from local file system
        svg_path = os.path.join(SYMBOLS_DIR, f"{subtype}.svg")
        meta_path = os.path.join(SYMBOLS_DIR, f"{subtype}.json") # For local metadata if any
        if os.path.exists(svg_path):
            with open(svg_path, 'r') as f:
                svg_data = f.read()
            svg_data = clean_svg_string(svg_data)
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                except json.JSONDecodeError:
                    st.warning(f"Could not load metadata from {meta_path} for {subtype}.")

        # 2. If not found or incomplete, try loading from database
        if not svg_data or "<svg" not in svg_data or not metadata:
            db_svg, db_meta = load_symbol_data_from_db(subtype)
            if db_svg and "<svg" in db_svg:
                svg_data = clean_svg_string(db_svg)
                metadata = db_meta # Prioritize DB metadata if found
        
        # 3. If still not found or incomplete, generate using OpenAI and save
        if not svg_data or "<svg" not in svg_data or not metadata:
            generated_svg, generated_meta = generate_svg_openai(subtype)
            if generated_svg and "<svg" in generated_svg:
                svg_data = generated_svg
                metadata = generated_meta
                # Save to local file system
                os.makedirs(SYMBOLS_DIR, exist_ok=True)
                with open(svg_path, "w") as f:
                    f.write(svg_data)
                with open(meta_path, "w") as f:
                    json.dump(metadata, f)
                # Save to database
                save_symbol_data_to_db(subtype, svg_data, metadata)
        
        # Process the loaded/generated SVG and metadata
        if svg_data and "<svg" in svg_data:
            viewbox_match = re.search(r'viewBox="([^"]+)"', svg_data)
            viewbox = viewbox_match.group(1) if viewbox_match else "0 0 100 100"
            
            # Wrap SVG in <symbol> for efficient use in main SVG
            # Ensure viewBox is applied to the <symbol>
            symbol = re.sub(r"<svg[^>]*?>", f'<symbol id="{subtype}" viewBox="{viewbox}">', svg_data)
            symbol = symbol.replace("</svg>", "</symbol>") # Replace closing tag
            svg_defs_dict[subtype] = symbol
            
            # Ensure metadata structure has 'ports'
            if 'ports' not in metadata:
                metadata['ports'] = {}
            metadata['viewBox'] = viewbox # Add viewBox to metadata
            svg_meta_dict[subtype] = metadata
        else:
            # Fallback for symbols that couldn't be loaded/generated
            st.warning(f"Could not load or generate a valid SVG for subtype: '{subtype}'. Using a placeholder.")
            svg_defs_dict[subtype] = None # No symbol def for this one
            svg_meta_dict[subtype] = {"viewBox": "0 0 100 100", "ports": {}} # Still provide meta with default viewbox

    # Populate ports from component_mapping.json (if any) as a fallback/initial source
    # This might override AI-generated ports if the mapping is considered more authoritative.
    for entry in initial_mapping:
        subtype = normalize(entry.get("Component", "")) # Normalize component name from JSON mapping
        if subtype:
            port_name = entry.get("Port Name", "default")
            dx, dy = float(entry.get("dx", 0)), float(entry.get("dy", 0))
            if subtype not in svg_meta_dict:
                 svg_meta_dict[subtype] = {"viewBox": "0 0 100 100", "ports": {}}
            svg_meta_dict[subtype]["ports"][port_name] = {"dx": dx, "dy": dy}
    
    st.success("P&ID data and symbols loaded!")
    return svg_defs_dict, svg_meta_dict, all_subtypes_from_data 

# --- SESSION STATE INITIALIZATION ---
if 'eq_df' not in st.session_state:
    # Use st.cache_data for initial load of CSVs/JSON as they are static data files
    @st.cache_data(show_spinner="Loading layout data...")
    def initial_load_layout_data():
        """Loads initial layout data from CSV/JSON. Cached separately for first load."""
        eq_file_path = os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv")
        pipe_file_path = os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv")
        mapping_path = os.path.join(LAYOUT_DATA_DIR, "component_mapping.json")

        if not os.path.exists(eq_file_path):
            st.error(f"Error: {eq_file_path} not found. Please ensure it exists.")
            st.stop()
        if not os.path.exists(pipe_file_path):
            st.error(f"Error: {pipe_file_path} not found. Please ensure it exists.")
            st.stop()

        eq_df = pd.read_csv(eq_file_path)
        # --- IMPORTANT FIX: Explicitly set dtype for polyline points ---
        pipe_df = pd.read_csv(pipe_file_path, dtype={'Polyline Points (x, y)': str})
        
        # --- IMPORTANT FIXES FOR COMPONENT ID MATCHING: Apply stripping to all relevant columns immediately after loading ---
        if 'id' in eq_df.columns:
            eq_df['id'] = eq_df['id'].apply(clean_component_id)
        
        if 'From Component' in pipe_df.columns:
            pipe_df['From Component'] = pipe_df['From Component'].apply(clean_component_id)
        if 'To Component' in pipe_df.columns:
            pipe_df['To Component'] = pipe_df['To Component'].apply(clean_component_id)
        # --- END IMPORTANT FIXES ---

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
# This will be re-run if eq_df changes due to manual additions/uploads
svg_defs, svg_meta, all_subtypes = load_symbol_and_meta_data(st.session_state.eq_df, st.session_state.mapping)

# ... rest of your file unchanged ...
# (The remainder of your app.py after symbol/meta loading does not need fixing for this issue.)

# --- P&ID CLASSES ---
class PnidComponent:
    """Represents a P&ID component."""
    def __init__(self, row):
        self.id = clean_component_id(row['id'])
        self.tag = row.get('tag', self.id)
        self.subtype = normalize(row.get('Component', '')) 
        self.x = row['x']
        self.y = row['y']
        
        # Get dimensions from metadata or use defaults
        meta = svg_meta.get(self.subtype)
        if meta and 'viewBox' in meta and isinstance(meta['viewBox'], str):
            viewbox_str = meta['viewBox']
        else:
            viewbox_str = '0 0 100 100' # Default fallback
        
        try:
            _, _, vb_width, vb_height = map(float, viewbox_str.split())
        except ValueError:
            vb_width, vb_height = 100, 100

        self.width = row.get('Width', vb_width) * SYMBOL_SCALE
        self.height = row.get('Height', vb_height) * SYMBOL_SCALE
        
        # Get port info from global svg_meta
        self.ports = meta.get('ports', {}) if meta else {}

    def get_port_coords(self, port_name):
        """Calculates absolute coordinates for a given port relative to the component's SVG origin."""
        port = self.ports.get(port_name)
        if port:
            meta = svg_meta.get(self.subtype)
            if meta and 'viewBox' in meta and isinstance(meta['viewBox'], str):
                viewbox_str = meta['viewBox']
            else:
                viewbox_str = '0 0 100 100'

            try:
                _, _, vb_w, vb_h = map(float, viewbox_str.split())
            except ValueError:
                vb_w, vb_h = 100, 100

            scale_x = self.width / vb_w if vb_w > 0 else 1
            scale_y = self.height / vb_h if vb_h > 0 else 1

            return (self.x + port["dx"] * scale_x, self.y + port["dy"] * scale_y)
        return (self.x + self.width / 2, self.y + self.height / 2)

class PnidPipe:
    """Represents a P&ID pipe connection."""
    def __init__(self, row, component_map):
        self.id = row['Pipe No.']
        self.label = row.get('Label', f"Pipe {self.id}")
        self.points = []
        self.pipe_type = row.get('pipe_type', 'process_line')
        
        from_comp_id = clean_component_id(row['From Component'])
        to_comp_id = clean_component_id(row['To Component'])

        from_comp = component_map.get(from_comp_id)
        to_comp = component_map.get(to_comp_id)

        if not from_comp:
            st.warning(f"Pipe '{self.id}': 'From Component' ID '{from_comp_id}' not found. Pipe may be incomplete or component data is missing.")
        if not to_comp:
            st.warning(f"Pipe '{self.id}': 'To Component' ID '{to_comp_id}' not found. Pipe may be incomplete or component data is missing.")

        polyline_str_raw = str(row.get('Polyline Points (x, y)', '')).strip()
        if polyline_str_raw and polyline_str_raw.lower() != 'nan':
            clean_polyline_str = polyline_str_raw.strip('[]')
            pts = re.findall(r"\(([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\)", clean_polyline_str)
            if pts:
                self.points = [(float(x), float(y)) for x, y in pts]
            else:
                st.warning(f"Pipe '{self.id}': Could not parse polyline points from '{polyline_str_raw}'. Drawing straight line if components exist.")
        if not self.points:
            if from_comp and to_comp:
                self.points = [
                    from_comp.get_port_coords(row.get("From Port", "default")),
                    to_comp.get_port_coords(row.get("To Port", "default"))
                ]
            elif from_comp:
                from_x, from_y = from_comp.get_port_coords(row.get("From Port", "default"))
                self.points = [from_x, (from_x + 50, from_y)]
            elif to_comp:
                to_x, to_y = to_comp.get_port_coords(row.get("To Port", "default"))
                self.points = [(to_x - 50, to_y), to_x, to_y]
# Get current dataframes from session state for rendering/modification
# Ensure components and pipes are re-initialized AFTER session_state.eq_df and pipe_df are loaded/updated
# This block is correctly placed AFTER class definitions and BEFORE sidebar forms
# --- IMPORTANT FIX: Re-initialize components and pipes when dataframes change ---
# This ensures that additions/uploads update the diagram immediately
if 'eq_df' in st.session_state and 'pipe_df' in st.session_state:
    components = {c.id: c for c in [PnidComponent(row) for _, row in st.session_state.eq_df.iterrows()]}
    pipes = [PnidPipe(row, components) for _, row in st.session_state.pipe_df.iterrows()]
else:
    components = {}
    pipes = []


# --- SVG RENDERING FUNCTIONS (Modularized) ---

def _render_svg_defs_section():
    """Renders the <defs> section of the SVG with arrowhead marker and all component symbols."""
    defs = ["<defs>"]
    # Define common arrowheads based on pipe types
    defs.append(f'<marker id="arrowhead-process" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="black"/></marker>')
    defs.append(f'<marker id="arrowhead-instrumentation" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polyline points="0 0, 10 3.5, 0 7" fill="none" stroke="blue" stroke-width="1"/></marker>') # Example for instrument
    defs.append(f'<marker id="arrowhead-electrical" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><circle cx="5" cy="3.5" r="3" fill="red"/></marker>') # Example for electrical
    
    for symbol_id, symbol_content in svg_defs.items():
        if symbol_content: # Only add if symbol content exists
            defs.append(symbol_content)
    defs.append("</defs>")
    return "".join(defs)

def _render_grid_lines(max_x, max_y, grid_spacing):
    """Renders grid lines for the P&ID diagram."""
    grid_lines = []
    # Add a buffer for the grid so it extends slightly beyond content
    end_x = int(max_x + PADDING)
    end_y = int(max_y + PADDING)

    for i in range(0, end_x, grid_spacing):
        grid_lines.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{end_y}" stroke="#eee" stroke-width="0.5"/>')
    for i in range(0, end_y, grid_spacing):
        grid_lines.append(f'<line x1="0" y1="{i}" x2="{end_x}" y2="{i}" stroke="#eee" stroke-width="0.5"/>')
    return "".join(grid_lines)

def _render_legend_section(components_map, max_x, max_y, legend_x, legend_y):
    """Renders the legend box and entries."""
    legend_svg = []
    
    # Calculate effective diagram height for legend positioning
    effective_diagram_height = max_y + PADDING + TITLE_BLOCK_HEIGHT # Use total height
    
    legend_box_height = min(650, effective_diagram_height - (legend_y - 30) - 60) # Ensure it fits vertically
    legend_svg.append(f'<rect x="{legend_x-10}" y="{legend_y-30}" width="{LEGEND_WIDTH-40}" height="{legend_box_height}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    legend_svg.append(f'<text x="{legend_x+80}" y="{legend_y-10}" font-size="{LEGEND_FONT_SIZE+4}" font-weight="bold" text-anchor="middle">Legend</text>')

    legend_entries = {}
    for c in components_map.values():
        if c.subtype:
            key = (c.tag, c.subtype)
            if key not in legend_entries:
                legend_entries[key] = c.subtype.replace("_", " ").title()

    legend_y_pos = legend_y + 20
    for i, ((tag, subtype), name) in enumerate(legend_entries.items()):
        sym_pos_y = legend_y_pos + i * 28 - 10 
        
        width, height = 20, 20
        # Scale legend icons to fit 25x25 box
        # --- IMPORTANT FIX: Check if svg_meta[subtype] exists before accessing its keys ---
        if subtype in svg_meta and svg_meta[subtype] and 'viewBox' in svg_meta[subtype] and isinstance(svg_meta[subtype]['viewBox'], str):
            try:
                viewBox = svg_meta[subtype]["viewBox"].split(" ")
                vb_w = float(viewBox[2])
                vb_h = float(viewBox[3])
                scale_factor = min(25 / vb_w, 25 / vb_h) if vb_w > 0 and vb_h > 0 else 1 # Avoid division by zero
                width = vb_w * scale_factor
                height = vb_h * scale_factor
            except (ValueError, IndexError):
                pass 

        if subtype in svg_defs and svg_defs[subtype]:
            # Use 'use' element for legend items
            legend_svg.append(f'<use href="#{subtype}" x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" />')
        else:
            # Fallback for missing symbol in legend
            legend_svg.append(f'<rect x="{legend_x}" y="{sym_pos_y}" width="{width}" height="{height}" fill="#eee" stroke="red"/>')
        
        legend_svg.append(f'<text x="{legend_x+32}" y="{sym_pos_y+16}" font-size="{LEGEND_FONT_SIZE}">{tag} - {name}</text>')
    return "".join(legend_svg)

def _render_title_block(max_x, max_y): # Pass max_x directly
    """Renders the title block with client name and generation date."""
    title_block_svg = []
    # Position relative to bottom right
    x_pos = max_x - TITLE_BLOCK_WIDTH + PADDING # Adjusted to float with max_x
    y_pos = max_y - TITLE_BLOCK_HEIGHT + PADDING + (TITLE_BLOCK_HEIGHT / 2) # Adjusted to float with max_y

    title_block_svg.append(f'<rect x="{x_pos}" y="{y_pos}" width="{TITLE_BLOCK_WIDTH}" height="{TITLE_BLOCK_HEIGHT-10}" fill="#fcfcfc" stroke="black" stroke-width="1"/>')
    title_block_svg.append(f'<text x="{x_pos + 20}" y="{y_pos + 30}" font-size="14" font-weight="bold">{TITLE_BLOCK_CLIENT}</text>')
    title_block_svg.append(f'<text x="{x_pos + 20}" y="{y_pos + 55}" font-size="12">Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</text>')
    return "".join(title_block_svg)

def _render_components(components_map):
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

def _render_pipes(pipes_list):
    """Renders all P&ID pipes with appropriate arrowheads."""
    pipes_svg = []
    for p in pipes_list:
        if len(p.points) >= 2:
            pts = " ".join(f"{x},{y}" for x, y in p.points)
            
            marker_id = "arrowhead-process" # Default
            if p.pipe_type == 'instrumentation':
                marker_id = "arrowhead-instrumentation"
            elif p.pipe_type == 'electrical':
                marker_id = "arrowhead-electrical"
            # Add more types as needed

            pipes_svg.append(f'<polyline points="{pts}" stroke="black" stroke-width="{PIPE_WIDTH}" fill="none" marker-end="url(#{marker_id})"/>')
            
            # Calculate midpoint for label
            # Ensure points are valid before calculating midpoint
            if p.points:
                mx = sum(x for x, _ in p.points) / len(p.points)
                my = sum(y for _, y in p.points) / len(p.points)
                pipes_svg.append(f'<text x="{mx}" y="{my - 5}" font-size="{PIPE_LABEL_FONT_SIZE}" text-anchor="middle">{p.label}</text>')
    return "".join(pipes_svg)

# Global variables for calculated diagram dimensions
max_x_calc = 0
max_y_calc = 0

def render_svg_diagram(components_map, pipes_list):
    """Main function to render the complete P&ID SVG."""
    global max_x_calc, max_y_calc # Declare globals

    # Determine overall SVG dimensions (zoom-to-fit)
    max_x_comp = max((c.x + c.width for c in components_map.values()), default=0)
    max_y_comp = max((c.y + c.height for c in components_map.values()), default=0)

    pipe_max_x = max((x for p in pipes_list for x, _ in p.points), default=0)
    pipe_max_y = max((y for p in pipes_list for _, y in p.points), default=0)

    # Calculate overall dimensions including padding, legend, and title block
    # Ensure LEGEND_WIDTH is considered in final width
    max_x_calc = max(max_x_comp, pipe_max_x) + PADDING * 2 + LEGEND_WIDTH # Add padding on both sides
    max_y_calc = max(max_y_comp, pipe_max_y) + PADDING * 2 + TITLE_BLOCK_HEIGHT # Add padding top/bottom

    svg_parts = []
    svg_parts.append(f'<svg width="{max_x_calc}" height="{max_y_calc}" viewBox="0 0 {max_x_calc} {max_y_calc}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">')

    svg_parts.append(_render_svg_defs_section())
    svg_parts.append(_render_grid_lines(max_x_calc, max_y_calc, GRID_SPACING))
    # Legend position needs to be relative to the full SVG width
    svg_parts.append(_render_legend_section(components_map, max_x_calc, max_y_calc, max_x_calc - LEGEND_WIDTH + 30, PADDING)) # Place legend at top right with padding
    svg_parts.append(_render_title_block(max_x_calc, max_y_calc - TITLE_BLOCK_HEIGHT)) # Pass max_x and adjust max_y for title block bottom
    svg_parts.append(_render_components(components_map))
    svg_parts.append(_render_pipes(pipes_list))

    svg_parts.append('</svg>')
    return "".join(svg_parts)


# --- ISA LOGIC BLOCK ---
def generate_isa_control_logic_box(components_map):
    """Generates a text block describing ISA instrumentation control logic based on component tags."""
    logic_lines = []
    logic_lines.append("INSTRUMENTATION CONTROL LOGIC")
    logic_lines.append("=" * 30)
    loop_counter = 1
    
    # Mapping for ISA first letters to physical variables
    isa_variable_map = {
        'P': 'Pressure', 'T': 'Temperature', 'F': 'Flow', 'L': 'Level',
        'C': 'Conductivity', 'D': 'Density', 'V': 'Vibration', 'Z': 'Position'
    }

    instrument_tags = sorted([
        comp.tag for comp in components_map.values()
        if re.match(r'^[A-Z]{1,2}\d{3}$', comp.tag) or re.match(r'^[A-Z]{1,2}-[0-9]+$', comp.tag) # Basic check for instrument-like tags
    ])

    for tag in instrument_tags:
        # Simple rule-based logic for demonstration
        if 'T' in tag and (tag.startswith('P') or tag.startswith('T') or tag.startswith('F') or tag.startswith('L')): # e.g., PT-101, TT-201, FT-301
            variable = isa_variable_map.get(tag[0], 'Unknown')
            logic_lines.append(f"{tag} ({variable} Transmitter) -> PLC Input -> Control Logic Decision")
        elif 'V' in tag and (tag.startswith('F') or tag.startswith('L') or tag.startswith('P')): # e.g., FV-401, LV-501
            variable = isa_variable_map.get(tag[0], 'Unknown')
            logic_lines.append(f"{tag} ({variable} Control Valve) -> PLC Output -> Control Logic Decision")
        elif 'I' in tag and (tag.startswith('P') or tag.startswith('T') or tag.startswith('F') or tag.startswith('L')): # e.g., PI-101, LI-201
            variable = isa_variable_map.get(tag[0], 'Unknown')
            logic_lines.append(f"{tag} ({variable} Indicator) -> Operator Display")
        else:
             logic_lines.append(f"{tag} (General Instrument)")

    if not instrument_tags:
        logic_lines.append("No specific instrumentation tags found to generate detailed logic.")
    return "\n".join(logic_lines)


# --- STREAMLIT APP LAYOUT ---

# Manual Component Addition Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### â Add New Component")
with st.sidebar.form("add_component_form"):
    new_comp_subtype = st.selectbox("Component Type", options=all_subtypes if all_subtypes else ["No types loaded"], key="new_comp_type_select")
    new_comp_id_raw = st.text_input("Component ID (unique)", key="new_comp_id_input")
    new_comp_id = clean_component_id(new_comp_id_raw) # Clean the new ID here
    new_comp_tag = st.text_input("Component Tag (optional)", value="", key="new_comp_tag_input")
    new_comp_x = st.number_input("X Position", value=100, step=10, key="new_comp_x_input")
    new_comp_y = st.sidebar.number_input("Y Position", value=100, step=10, key="new_comp_y_input")

    add_comp_submitted = st.form_submit_button("Add Component to Diagram")

    if add_comp_submitted:
        if not new_comp_id:
            st.error("Component ID cannot be empty or just whitespace.")
        elif new_comp_id in st.session_state.eq_df['id'].values:
            st.error(f"Component ID '{new_comp_id}' already exists. Please choose a unique ID.")
        elif new_comp_subtype == "No types loaded" and all_subtypes: # Ensure all_subtypes is not empty before flagging
             st.error("Cannot add component: No component types are loaded or selected. Check data files or OpenAI key.")
        else:
            new_row = {
                'id': new_comp_id, # Use the cleaned ID
                'tag': new_comp_tag if new_comp_tag else new_comp_id,
                'Component': new_comp_subtype, 
                'x': new_comp_x,
                'y': new_comp_y,
                'Width': 60,  # Default values, will be scaled by SYMBOL_SCALE in PnidComponent
                'Height': 60
            }
            st.session_state.eq_df = pd.concat([st.session_state.eq_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Added component '{new_comp_id}' of type '{new_comp_subtype}'.")
            st.rerun() # Rerun to update diagram

# Manual Pipe Addition Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### â Add New Pipe")
current_comp_ids_for_dropdown = sorted(list(components.keys()))
if not current_comp_ids_for_dropdown:
    current_comp_ids_for_dropdown = ["No components available"]

with st.sidebar.form("add_pipe_form"):
    new_pipe_id = st.text_input("Pipe ID (unique)", key="new_pipe_id_input")
    new_pipe_label = st.text_input("Pipe Label (optional)", key="new_pipe_label_input")
    
    from_comp_select = st.selectbox("From Component", options=current_comp_ids_for_dropdown, key="from_comp_select")
    from_comp_obj = components.get(from_comp_select)
    from_port_options = sorted(list(from_comp_obj.ports.keys())) if from_comp_obj and from_comp_obj.ports else ["default"]
    new_pipe_from_port = st.selectbox("From Port", options=from_port_options, key="new_pipe_from_port")

    to_comp_select = st.selectbox("To Component", options=current_comp_ids_for_dropdown, key="to_comp_select")
    to_comp_obj = components.get(to_comp_select)
    to_port_options = sorted(list(to_comp_obj.ports.keys())) if to_comp_obj and to_comp_obj.ports else ["default"]
    new_pipe_to_port = st.selectbox("To Port", options=to_port_options, key="new_pipe_to_port")

    pipe_type_options = ['process_line', 'instrumentation', 'electrical'] # Define common pipe types
    new_pipe_type = st.selectbox("Pipe Type", options=pipe_type_options, key="new_pipe_type")

    add_pipe_submitted = st.form_submit_button("Add Pipe to Diagram")

    if add_pipe_submitted:
        if not new_pipe_id:
            st.error("Pipe ID cannot be empty.")
        elif new_pipe_id in st.session_state.pipe_df['Pipe No.'].values:
            st.error(f"Pipe ID '{new_pipe_id}' already exists. Please choose a unique ID.")
        elif from_comp_select == "No components available" or to_comp_select == "No components available":
            st.error("Please add components first before adding pipes.")
        else:
            new_pipe_row = {
                'Pipe No.': new_pipe_id,
                'Label': new_pipe_label if new_pipe_label else f"Pipe {new_pipe_id}",
                'From Component': from_comp_select,
                'From Port': new_pipe_from_port,
                'To Component': to_comp_select,
                'To Port': new_pipe_to_port,
                'Polyline Points (x, y)': '', # Initially auto-calculated
                'pipe_type': new_pipe_type # Include pipe type
            }
            st.session_state.pipe_df = pd.concat([st.session_state.pipe_df, pd.DataFrame([new_pipe_row])], ignore_index=True)
            st.success(f"Added pipe '{new_pipe_id}'.")
            st.rerun()

# --- Main Content Area - Renders the P&ID ---
st.markdown("## Preview: Auto-Generated P&ID")

svg_output = render_svg_diagram(components, pipes)
st.components.v1.html(svg_output, height=800, scrolling=True)


# ISA Control Logic Section
st.markdown("---")
st.markdown("### ð§ Instrumentation Control Logic")
logic_block = generate_isa_control_logic_box(components)
st.text_area("ISA Instrumentation Control Logic", value=logic_block, height=200, key="isa_logic_output")


# --- EXPORT OPTIONS ---
st.markdown("---")
st.markdown("### â¬ï¸ Download Options")
col1, col2, col3 = st.columns(3)

# PNG Export
def export_png(svg_data):
    output = BytesIO()
    try:
        # Convert SVG string (bytes-like object) to PNG
        svg2png(bytestring=svg_data.encode('utf-8'), write_to=output)
        return output.getvalue()
    except Exception as e:
        st.error(f"Error converting SVG to PNG: {e}. Ensure your SVG is valid and `cairosvg` is installed correctly. This might be due to malformed SVG output from AI.")
        return None

# DXF Export (Revised for add_rect and robust saving)
def export_dxf(components_map, pipes_list):
    doc = ezdxf.new('R2010') # Specify DXF version for compatibility
    msp = doc.modelspace()
    
    # Add components as basic rectangles/text for DXF (no complex SVG symbols in DXF)
    for c in components_map.values():
        # --- IMPORTANT FIX: Use add_lwpolyline for rectangle outlines ---
        p1 = (c.x, c.y)
        p2 = (c.x + c.width, c.y)
        p3 = (c.x + c.width, c.y + c.height)
        p4 = (c.x, c.y + c.height)
        rect_points = [p1, p2, p3, p4, p1] # 5 points to close the rectangle
        msp.add_lwpolyline(rect_points, dxfattribs={'color': 1}) # Red outline for component (ACI color 1 is red)
        
        # Add text for tag
        # Adjust text height for DXF to be reasonable, 2.5 units is common
        msp.add_text(c.tag, dxfattribs={'height': TAG_FONT_SIZE * 0.1, 'insert': (c.x + c.width/2, c.y + c.height + 5)}) 
        
    for p in pipes_list:
        if len(p.points) >= 2:
            # --- IMPORTANT FIX: Ensure points are tuples/lists of (x,y) ---
            # add_lwpolyline expects a list of 2D points (tuples or lists)
            msp.add_lwpolyline(p.points, dxfattribs={'color': 7}) # White/Black pipe (ACI color 7 is white/black depending on background)
            
            # Add pipe labels as text
            if p.points: # Ensure there are points before calculating midpoint
                mx = sum(x for x, _ in p.points) / len(p.points)
                my = sum(y for _, y in p.points) / len(p.points)
                # Adjust text height for DXF, 1.5 units is common
                msp.add_text(p.label, dxfattribs={'height': PIPE_LABEL_FONT_SIZE * 0.1, 'insert': (mx, my - 2)})

    from io import StringIO
    import tempfile
    
    try:
        # Use a temporary file for reliable DXF export
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as temp_file:
            doc.saveas(temp_file.name)
            temp_file.seek(0)
            with open(temp_file.name, 'rb') as f:
                return f.read()
    except Exception as e:
        st.error(f"Error during DXF export: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            import os
            os.unlink(temp_file.name)
        except:
            pass

with col1:
    st.download_button("ð¥ Download SVG", svg_output, "pnid.svg", "image/svg+xml", key="download_svg")
with col2:
    png_data = export_png(svg_output)
    if png_data:
        st.download_button("ð¥ Download PNG", png_data, "pnid.png", "image/png", key="download_png")
    else:
        st.warning("PNG export failed. Check console for errors.")
with col3:
    dxf_data = export_dxf(components, pipes)
    if dxf_data:
        st.download_button("ð¥ Download DXF", dxf_data, "pnid.dxf", "application/dxf", key="download_dxf")
    else:
        st.warning("DXF export failed or data not available.")

# --- DATA MANAGEMENT ---
st.markdown("---")
st.markdown("### ðï¸ Data Management")

# Display current dataframes
with st.expander("View Current Components Data"):
    st.dataframe(st.session_state.eq_df, use_container_width=True)

with st.expander("View Current Pipes Data"):
    st.dataframe(st.session_state.pipe_df, use_container_width=True)

# Save current state to files
if st.button("ð¾ Save Current Diagram Data to Files"):
    try:
        os.makedirs(LAYOUT_DATA_DIR, exist_ok=True)
        st.session_state.eq_df.to_csv(os.path.join(LAYOUT_DATA_DIR, "enhanced_equipment_layout.csv"), index=False)
        st.session_state.pipe_df.to_csv(os.path.join(LAYOUT_DATA_DIR, "pipe_connections_layout.csv"), index=False)
        st.success(f"Diagram data saved to '{LAYOUT_DATA_DIR}' folder.")
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Clear diagram button
# --- IMPORTANT FIX: Simplified clear button logic ---
if st.button("ðï¸ Clear Diagram (Reset to Empty)", key="clear_diagram_btn"):
    # Use session state to manage confirmation without nested buttons
    st.session_state.confirm_clear = True

if st.session_state.get('confirm_clear', False):
    st.warning("Are you sure you want to clear the diagram? This cannot be undone.", icon="â ï¸")
    col_clear_yes, col_clear_no = st.columns(2)
    with col_clear_yes:
        if st.button("Yes, Clear Diagram Permanently", key="confirm_clear_yes"):
            st.session_state.eq_df = pd.DataFrame(columns=['id', 'tag', 'Component', 'x', 'y', 'Width', 'Height'])
            st.session_state.pipe_df = pd.DataFrame(columns=['Pipe No.', 'Label', 'From Component', 'From Port', 'To Component', 'To Port', 'Polyline Points (x, y)', 'pipe_type'])
            st.session_state.confirm_clear = False # Reset confirmation
            st.success("Diagram cleared!")
            st.rerun()
    with col_clear_no:
        if st.button("No, Keep Diagram", key="confirm_clear_no"):
            st.session_state.confirm_clear = False # Reset confirmation
            st.info("Diagram not cleared.")
            st.rerun() # Rerun to remove confirmation prompt

# Upload new dataframes
st.markdown("#### Upload New Diagram Data")
uploaded_eq_file = st.file_uploader("Upload Equipment Layout CSV", type=["csv"], key="upload_eq_file")
uploaded_pipe_file = st.file_uploader("Upload Pipe Connections CSV", type=["csv"], key="upload_pipe_file")

if uploaded_eq_file or uploaded_pipe_file:
    if st.button("Load Uploaded Data", key="load_uploaded_data_btn"):
        try:
            if uploaded_eq_file:
                df = pd.read_csv(uploaded_eq_file)
                if 'id' in df.columns:
                    df['id'] = df['id'].apply(clean_component_id)
                if 'Component' not in df.columns:
                    st.error("Uploaded Equipment Layout CSV must contain a 'Component' column for subtypes.")
                    st.stop()
                st.session_state.eq_df = df
                st.success("Equipment data loaded from uploaded file.")
            if uploaded_pipe_file:
                # --- IMPORTANT FIX: Explicitly set dtype for polyline points on upload ---
                df = pd.read_csv(uploaded_pipe_file, dtype={'Polyline Points (x, y)': str})
                if 'From Component' in df.columns:
                    df['From Component'] = df['From Component'].apply(clean_component_id)
                if 'To Component' in df.columns:
                    df['To Component'] = df['To Component'].apply(clean_component_id)
                st.session_state.pipe_df = df
                st.success("Pipe data loaded from uploaded file.")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading uploaded files: {e}")

# --- OPTIONAL DEBUG INFO ---
with st.expander("ð Debug Info"):
    st.write("Current `eq_df` head (after cleaning):")
    st.dataframe(st.session_state.eq_df.head())
    st.write("Current `pipe_df` head (after cleaning):")
    st.dataframe(st.session_state.pipe_df.head())
    st.write("All Subtypes:", all_subtypes)
    st.write("Component IDs in `components` dictionary (first 5):", list(components.keys())[:5])
    st.write("SVG Meta (sample for first 3 subtypes):", {k: {key: val for key, val in v.items() if key != 'ports'} for k,v in list(svg_meta.items())[:3]})
    st.write("First few SVG Defs (keys):", list(svg_defs.keys())[:5])
    st.write("`DATABASE_URL` is set:", bool(DATABASE_URL))
    st.write("`OPENAI_API_KEY` is set:", bool(openai_client.api_key)) # Use openai_client here
