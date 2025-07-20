import re
import os
from io import BytesIO

# Assuming advanced_rendering and professional_isa_symbols are in the same directory
# Or adjust imports based on your project structure
from advanced_rendering import ( # Assuming all modules are in the same directory or on PYTHONPATH

    draw_svg_symbol,
    render_line_with_gradient,
    render_signal_line,
    render_tag_bubble,
    render_grid,
    render_border,
    render_title_block,
    render_bom_block,
    render_legend_block,
    render_scope_boundary,
)
# Make sure cairosvg is installed (pip install cairosvg)
import cairosvg 

def render_svg(equipment_df, pipeline_df, inline_df, positions, pipelines, inlines,
               width=2000, height=1100, show_grid=True, show_legend=True, show_title=True):
    """
    Renders a complete P&ID SVG string based on provided dataframes and layout.
    
    Args:
        equipment_df (pd.DataFrame): DataFrame with equipment data (ID, Description, type).
        pipeline_df (pd.DataFrame): DataFrame with pipeline data. Not directly used here for lines,
                                    but could be for additional data.
        inline_df (pd.DataFrame): DataFrame with inline component data. Not directly used here for inlines,
                                  but could be for additional data.
        positions (dict): Dictionary mapping equipment ID to (x, y) coordinates.
        pipelines (list): List of dictionaries, each containing 'points', 'line_type', 'line_number'.
        inlines (list): List of dictionaries, each containing 'ID', 'pos' (x,y), 'type', 'description'.
        width (int): Width of the SVG canvas.
        height (int): Height of the SVG canvas.
        show_grid (bool): Whether to display a background grid.
        show_legend (bool): Whether to display the BOM and Legend blocks.
        show_title (bool): Whether to display the Title Block.

    Returns:
        str: The complete SVG string.
    """
    # --- Draw grid and border (background) ---
    svg_layers = []
    if show_grid:
        svg_layers.append(render_grid(width, height, spacing=100))
    svg_layers.append(render_border(width, height))

    # --- Title Block, BOM, Legend (footer blocks) ---
    if show_title:
        svg_layers.append(render_title_block(
            title="TENTATIVE P&ID DRAWING FOR SUCTION FILTER + KDP 330",
            project="EPSPL_V2526-TP_01",
            rev="00",
            scale="1:50",
            date="2025-07-18",
            company="Economy Process Solutions Pvt. Ltd.",
            sheet="1 of 1"
        ))

    if show_legend:
        # Assuming equipment_df contains the necessary data for BOM/Legend
        svg_layers.append(render_bom_block(equipment_df))
        svg_layers.append(render_legend_block(equipment_df))

    # --- Add scope boundaries ---
    # Customer scope (left side equipment)
    svg_layers.append(render_scope_boundary(250, 180, 600, 450, "CUSTOMER SCOPE"))
    # EPS scope (main equipment)
    svg_layers.append(render_scope_boundary(870, 80, 850, 700, "EPSPL SCOPE"))

    # --- Draw pipelines (with type detection) ---
    for pipe in pipelines:
        pts = pipe["points"]
        pipe_type = pipe.get("line_type", "process")  # Default to process
        
        # Render the line with appropriate style
        svg_layers.append(render_line_with_gradient(pts, pipe_type=pipe_type, arrow=True))
        
        # Add line number label if present
        line_number = pipe.get("line_number", "")
        if line_number and len(pts) >= 2:
            # Place label at midpoint of first segment
            mid_x = (pts[0][0] + pts[1][0]) / 2
            mid_y = (pts[0][1] + pts[1][1]) / 2
            
            # Create label background and text
            label_width = len(line_number) * 7 + 10
            svg_layers.append(f'<rect x="{mid_x - label_width/2}" y="{mid_y - 9}" width="{label_width}" height="18" fill="white" stroke="black" stroke-width="0.5"/>')
            svg_layers.append(f'<text x="{mid_x}" y="{mid_y + 4}" font-size="10" text-anchor="middle" font-family="Arial">{line_number}</text>')

    # --- Equipment symbols & tag bubbles ---
    for _, row in equipment_df.iterrows():
        comp_id = row["ID"]
        # Ensure 'positions' dictionary has the key
        if comp_id in positions:
            x, y = positions[comp_id]
            # Use draw_svg_symbol from advanced_rendering, which should call professional_isa_symbols
            svg_layers.append(
                f'<g id="{comp_id}"><g transform="translate({x},{y})">{draw_svg_symbol(comp_id, width=80, height=80)}</g></g>'
            )
            # Tag bubble under each equipment
            svg_layers.append(render_tag_bubble(x + 40, y + 110, tag=comp_id, font_size=13, tag_type="circle"))
        else:
            print(f"Warning: Position not found for equipment ID: {comp_id}")

    # --- Inline components (valves, meters) & tag bubbles ---
    for inline in inlines:
        comp_id = inline["ID"]
        # Ensure 'pos' key exists for inline components
        if "pos" in inline:
            x, y = inline["pos"]
            inline_type = inline.get("type", "valve")
            description = inline.get("description", comp_id) # Not used directly in SVG, but good to have.
            
            # Draw the inline component symbol
            # Assuming draw_svg_symbol can handle inline component IDs/types
            svg_layers.append(
                f'<g transform="translate({x-24},{y-24})">{draw_svg_symbol(comp_id, width=48, height=48)}</g>'
            )
            
            # Tag bubble for inline component
            # For valves and similar, use smaller bubble below
            if "valve" in inline_type.lower() or "flow_transmitter" in inline_type.lower() or "rotameter" in inline_type.lower(): # Added other inline types
                svg_layers.append(render_tag_bubble(x, y + 35, tag=comp_id, font_size=9, tag_type="circle"))
            else:
                # For instruments, use standard bubble to the side
                svg_layers.append(render_tag_bubble(x + 30, y, tag=comp_id, font_size=11, tag_type="circle"))
        else:
            print(f"Warning: Position not found for inline component ID: {comp_id}")

    # --- Draw signal/instrument lines ---
    # Filter for instrument signal lines explicitly
    for pipe in pipelines:
        # Check for both 'instrument' and 'instrument_signal' or 'signal' for robustness
        if pipe.get("line_type", "") in ["instrument", "instrument_signal", "signal"]:
            pts = pipe["points"]
            # Ensure render_signal_line is correctly implemented to handle 'instrument' type
            svg_layers.append(render_signal_line(pts, sig_type="instrument"))

    # --- Compose SVG ---
    # Moved defs block outside to contain both marker definitions
    svg_header = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        # Marker for general flow lines
        f'<marker id="arrowhead" markerWidth="14" markerHeight="12" refX="14" refY="6" orient="auto" markerUnits="strokeWidth">'
        f'<polygon points="2,2 14,6 2,10" fill="#222" />'
        f'</marker>'
        # Marker for instrument signal lines (more distinct)
        f'<marker id="signal-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="#0a85ff" stroke="#0a85ff"/>'
        f'</marker>'
        f'</defs>'
    )

    svg = svg_header + "".join(svg_layers) + "</svg>"
    return svg

def svg_to_png(svg_string, scale=1.5):
    """
    Converts an SVG string to a PNG image (bytes).
    Requires cairosvg to be installed.
    
    Args:
        svg_string (str): The SVG content as a string.
        scale (float): Scaling factor for the output PNG resolution.

    Returns:
        bytes: PNG image data.
    """
    try:
        # cairosvg expects bytes for bytestring argument
        png_data = cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)
        return png_data
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        # Return an empty BytesIO object or raise the exception, depending on desired error handling
        return BytesIO()


def export_dxf(positions, pipelines, equipment_df, inline_df): # Added equipment_df, inline_df for more detail
    """
    Exports P&ID data to a DXF file.
    
    Args:
        positions (dict): Dictionary mapping equipment ID to (x, y) coordinates.
        pipelines (list): List of dictionaries, each containing 'points', 'line_type', 'line_number'.
        equipment_df (pd.DataFrame): DataFrame with equipment data (ID, Description, type).
        inline_df (pd.DataFrame): DataFrame with inline component data (ID, type, pos).

    Returns:
        bytes: DXF file content as bytes.
    """
    # Ensure ezdxf is installed (pip install ezdxf)
    import ezdxf
    from io import StringIO # Not strictly needed if using NamedTemporaryFile
    import tempfile

    doc = ezdxf.new("R2010") # Use a robust DXF version
    msp = doc.modelspace()

    # Define layers for better organization in DXF
    doc.layers.add("EQUIPMENT", color=2) # Green
    doc.layers.add("PIPING", color=7)    # White
    doc.layers.add("INSTRUMENTATION", color=4) # Cyan
    doc.layers.add("TEXT", color=0)      # Black (or white depending on background)
    doc.layers.add("VALVES", color=1)    # Red

    # Add equipment blocks as circles with text (since blockref needs defined blocks)
    for eq_id, (x, y) in positions.items():
        # Get equipment details from dataframe for more info in DXF if needed
        eq_row = equipment_df[equipment_df['ID'] == eq_id]
        eq_type = eq_row['type'].iloc[0] if not eq_row.empty else "EQUIPMENT"
        eq_desc = eq_row['Description'].iloc[0] if not eq_row.empty else ""

        # Add a circle to represent equipment
        msp.add_circle((x, y), radius=30, dxfattribs={'layer': 'EQUIPMENT', 'color': 2})
        # Add text label for ID
        msp.add_text(eq_id, dxfattribs={'layer': 'TEXT', 'height': 10}).set_placement((x, y - 40))
        # Add equipment type/description (optional)
        if eq_desc:
            msp.add_text(eq_desc, dxfattribs={'layer': 'TEXT', 'height': 7}).set_placement((x, y - 55))


    # Add pipelines
    for pipe in pipelines:
        if "points" in pipe and len(pipe["points"]) >= 2:
            # Convert points to 2D tuples (DXF expects 2D or 3D points)
            points_2d = [(p[0], p[1]) for p in pipe["points"]]
            
            # Determine layer and linetype based on pipe_type
            pipe_type = pipe.get("line_type", "process").lower()
            dxf_layer = "PIPING"
            dxf_color = 7 # White
            
            # Add specific linetypes if defined in your DXF template or ezdxf
            # For simplicity, we'll just use solid lines and different colors for now
            if "instrument" in pipe_type or "signal" in pipe_type:
                dxf_layer = "INSTRUMENTATION"
                dxf_color = 4 # Cyan
                # You might define custom linetypes for instrument lines
                # e.g., doc.linetypes.add("DASH_DOT", [0.5, -0.25, 0, -0.25])
                # msp.add_lwpolyline(points_2d, dxfattribs={'layer': dxf_layer, 'color': dxf_color, 'linetype': 'DASH_DOT'})

            msp.add_lwpolyline(points_2d, dxfattribs={'layer': dxf_layer, 'color': dxf_color, 'lineweight': 40})
            
            # Add line number text if available
            line_number = pipe.get("line_number", "")
            if line_number and len(points_2d) >= 2:
                # Place label near the start of the line for DXF
                text_x = (points_2d[0][0] + points_2d[1][0]) / 2
                text_y = (points_2d[0][1] + points_2d[1][1]) / 2
                msp.add_text(line_number, dxfattribs={'layer': 'TEXT', 'height': 8}).set_placement((text_x, text_y + 10))

    # Add inline components
    for inline in inlines:
        comp_id = inline["ID"]
        x, y = inline.get("pos", (0,0)) # Get position, default to (0,0) if not found
        inline_type = inline.get("type", "UNKNOWN").lower()

        if x == 0 and y == 0:
            print(f"Warning: Inline component {comp_id} has no position, skipping DXF export.")
            continue

        # Represent inline components based on their type
        if "valve" in inline_type:
            # Draw a cross for a valve
            msp.add_line((x-10, y-10), (x+10, y+10), dxfattribs={'layer': 'VALVES', 'color': 1})
            msp.add_line((x-10, y+10), (x+10, y-10), dxfattribs={'layer': 'VALVES', 'color': 1})
            msp.add_text(comp_id, dxfattribs={'layer': 'TEXT', 'height': 6}).set_placement((x, y+15))
        elif "transmitter" in inline_type or "gauge" in inline_type or "switch" in inline_type or "meter" in inline_type:
            # Draw a circle for an instrument
            msp.add_circle((x, y), radius=10, dxfattribs={'layer': 'INSTRUMENTATION', 'color': 4})
            msp.add_text(comp_id, dxfattribs={'layer': 'TEXT', 'height': 6}).set_placement((x, y+15))
        else:
            # Generic representation for other inlines
            msp.add_circle((x, y), radius=15, dxfattribs={'layer': 'INSTRUMENTATION', 'color': 8}) # Grey
            msp.add_text(comp_id, dxfattribs={'layer': 'TEXT', 'height': 6}).set_placement((x, y+20))


    # Write to temporary file then read back
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.dxf', delete=False) as tmp: # 'wb' for binary write
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    with open(tmp_path, 'rb') as f: # 'rb' for binary read
        dxf_content = f.read()

    # Clean up temp file
    os.unlink(tmp_path)

    return dxf_content

