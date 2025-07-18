# advanced_rendering.py

# Keep this import as per your existing structure
from professional_symbols import get_component_symbol

def draw_svg_symbol(component_id, width=80, height=80):
    """
    Retrieves SVG for component. This function will now simply pass
    the target width and height to get_component_symbol, which will
    handle the scaling and fallback.
    """
    # Renamed parameters to target_width, target_height for clarity
    # to match the drawing_engine.py calls.
    return get_component_symbol(component_id, target_width=width, target_height=height)

def render_line_with_gradient(points, pipe_type="process", arrow=True): # Renamed pipe_style to pipe_type for consistency
    """
    Industrial pipeline with ISA-compliant style based on its type.
    Incorporates detailed styling guidance.
    """
    stroke_color = "black"
    stroke_width = 2 # Default for process pipes (changed from 9)
    dash_array = ""
    marker_end = ' marker-end="url(#arrowhead)"' if arrow else ""

    if pipe_type == "instrument" or pipe_type == "instrument_signal":
        stroke_color = "#0a85ff" # Blue
        stroke_width = 1
        dash_array = ' stroke-dasharray="5,4"' # Dashed
        marker_end = ' marker-end="url(#signal-arrow)"' if arrow else ""
    elif pipe_type == "pneumatic":
        stroke_color = "#33aa00" # Green
        stroke_width = 1
        dash_array = ' stroke-dasharray="2,4"' # Dot-dash
    elif pipe_type == "electric":
        stroke_color = "#ebbc33" # Yellow
        stroke_width = 1
        dash_array = ' stroke-dasharray="1,4"' # Dotted
    elif pipe_type == "hydraulic":
        stroke_color = "#b23d2a" # Red
        stroke_width = 1
        dash_array = ' stroke-dasharray="8,2,2,2"' # Dash-long-dash
    elif pipe_type == "scope_break":
        stroke_color = "#a6a6a6" # Gray
        stroke_width = 1
        dash_array = ' stroke-dasharray="3,3"' # Short dashed
    elif pipe_type == "utility": # Retained from original if still needed
        stroke_color = "#666"
        stroke_width = 5
        dash_array = ""
    # "process" is the default (black, width 2, solid)

    pts_str = " ".join([f"{p[0]},{p[1]}" for p in points])
    # Using <path> for robustness, starting with M for "move to" and then L for "line to"
    path_d = f"M {pts_str.replace(' ', ' L ')}"
    return f'<path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}"{dash_array}{marker_end}/>'

def render_signal_line(points, sig_type="signal"): # Added sig_type for potential future differentiation
    """
    Dashed signal line (for control/instrumentation).
    Note: Much of this functionality might be covered by render_line_with_gradient.
    Consider consolidating if this is redundant.
    """
    stroke_color = "#000" # Default
    dash_array = ' stroke-dasharray="6,6"'
    marker = ' marker-end="url(#signal-arrow)"'

    if sig_type == "instrument": # If you need a specific signal_line style
        stroke_color = "#0a85ff"
        dash_array = ' stroke-dasharray="5,4"'

    pts_str = " ".join([f"{int(x)},{int(y)}" for (x, y) in points])
    return f'<polyline points="{pts_str}" stroke="{stroke_color}" stroke-width="2" fill="none"{dash_array}{marker} />'

def render_tag_bubble(x, y, tag, font_size=11, tag_type="circle"): # Adjusted default font_size to 11
    """
    Draw ISA-style tag bubble (circle or rectangle) at (x, y) with label.
    Splits tags like "PI-101" into primary ("PI") and secondary ("101").
    """
    parts = tag.split('-')
    main_tag_content = parts[0]
    secondary_tag_content = parts[1] if len(parts) > 1 else ""

    bubble_radius = font_size * 1.5 # Base radius, will be adjusted for two lines

    if tag_type == "circle":
        # Adjust radius if secondary tag exists to give more space
        if secondary_tag_content:
            bubble_radius = font_size * 2 # Increase radius for better two-line fit

        svg = f'<circle cx="{x}" cy="{y}" r="{bubble_radius}" fill="white" stroke="black" stroke-width="2"/>'

        # Position for main tag (e.g., PI)
        # Shift up slightly if there's a secondary tag, otherwise center
        main_text_y_offset = (font_size * 0.3) - (font_size * 0.5 if secondary_tag_content else 0)

        svg += (f'<text x="{x}" y="{y + main_text_y_offset}" font-size="{font_size}" '
                f'font-family="Arial" font-weight="bold" text-anchor="middle" fill="#333">{main_tag_content}</text>')

        # Position for secondary tag (e.g., 101)
        if secondary_tag_content:
            secondary_font_size = font_size * 0.7 # Smaller font for number
            secondary_text_y_offset = (font_size * 0.3) + (font_size * 0.7) # Position below main tag
            svg += (f'<text x="{x}" y="{y + secondary_text_y_offset}" font-size="{secondary_font_size}" '
                    f'font-family="Arial" text-anchor="middle" fill="#318">{secondary_tag_content}</text>')
    else: # Original rectangle logic for other tag_types
        w, h = 36, 24
        svg = f'<rect x="{x-w//2}" y="{y-h//2}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="#111" stroke-width="2"/>'
        svg += f'<text x="{x}" y="{y+7}" font-size="{font_size}" font-family="Arial" font-weight="bold" text-anchor="middle">{tag}</text>'
    return svg

def render_grid(width=2000, height=1100, spacing=100):
    """
    Faint engineering grid.
    """
    lines = ""
    for x in range(0, width+1, spacing):
        lines += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#eee" stroke-width="1"/>'
    for y in range(0, height+1, spacing):
        lines += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#eee" stroke-width="1"/>'
    return f'<g id="grid">{lines}</g>'

def render_border(width=2000, height=1100):
    """
    Thick border, just like your reference.
    """
    return f'<rect x="6" y="6" width="{width-12}" height="{height-12}" fill="none" stroke="#222" stroke-width="3"/>'

def render_title_block(
    title="TENTATIVE P&ID DRAWING FOR SUCTION FILTER + KDP-330",
    project="EPSPL_V2526-TP",
    rev="00",
    scale="1:50",
    date="2025-07-18",
    company="Economy Process Solutions Pvt. Ltd.",
    sheet="1 of 1"
):
    """
    Bottom-right title block, like a real P&ID.
    """
    x0, y0 = 1580, 990
    svg = f"""
<g id="titleblock">
<rect x="{x0}" y="{y0}" width="400" height="90" fill="#fff" stroke="#111" stroke-width="2"/>
<text x="{x0+20}" y="{y0+30}" font-size="19" font-family="Arial" font-weight="bold">{title}</text>
<text x="{x0+20}" y="{y0+52}" font-size="14" font-family="Arial">Project: {project}</text>
<text x="{x0+20}" y="{y0+70}" font-size="14" font-family="Arial">Rev: {rev}   Scale: {scale}   Date: {date}</text>
<text x="{x0+260}" y="{y0+52}" font-size="12" font-family="Arial" text-anchor="end">{company}</text>
<text x="{x0+380}" y="{y0+82}" font-size="11" font-family="Arial" text-anchor="end">Sheet: {sheet}</text>
</g>
"""
    return svg

def render_bom_block(equipment_df, x0=40, y0=930, width=700, row_h=28):
    """
    Lower-left Bill of Materials block, matching your reference.
    """
    # Header
    svg = f'<g id="bomblock">'
    svg += f'<rect x="{x0}" y="{y0}" width="{width}" height="{row_h}" fill="#eee" stroke="#111" stroke-width="2"/>'
    svg += f'<text x="{x0+15}" y="{y0+20}" font-size="15" font-family="Arial" font-weight="bold">BILL OF MATERIAL</text>'
    # Columns
    cols = ["SR NO", "DESCRIPTION"]
    col_widths = [70, width-70]
    for i, col in enumerate(cols):
        svg += f'<text x="{x0+sum(col_widths[:i])+12}" y="{y0+45}" font-size="13" font-weight="bold">{col}</text>'
    # Rows
    y = y0 + row_h + 20
    for idx, row in enumerate(equipment_df.itertuples(), 1):
        # Truncate description more aggressively if it overflows
        desc = str(getattr(row, "Description", ""))
        if len(desc) > 60: # Adjusted truncation length
            desc = desc[:57] + "..."
        svg += f'<text x="{x0+25}" y="{y+idx*row_h}" font-size="13">{idx}</text>'
        svg += f'<text x="{x0+90}" y="{y+idx*row_h}" font-size="13">{desc}</text>'
    svg += '</g>'
    return svg

def render_legend_block(equipment_df, x0=750, y0=930, width=750, row_h=28):
    """
    Lower-center legend block with all tags/descriptions.
    """
    svg = f'<g id="legendblock">'
    svg += f'<rect x="{x0}" y="{y0}" width="{width}" height="{row_h}" fill="#eee" stroke="#111" stroke-width="2"/>'
    svg += f'<text x="{x0+15}" y="{y0+20}" font-size="15" font-family="Arial" font-weight="bold">LEGEND</text>'
    cols = ["TAG", "DESCRIPTION"]
    col_widths = [120, width-120]
    for i, col in enumerate(cols):
        svg += f'<text x="{x0+sum(col_widths[:i])+12}" y="{y0+45}" font-size="13" font-weight="bold">{col}</text>'
    y = y0 + row_h + 20
    for idx, row in enumerate(equipment_df.itertuples()):
        tag = str(getattr(row, "ID", ""))[:16]
        desc = str(getattr(row, "Description", ""))
        if len(desc) > 50: # Adjusted truncation length
            desc = desc[:47] + "..."
        svg += f'<text x="{x0+25}" y="{y+idx*row_h}" font-size="13">{tag}</text>'
        svg += f'<text x="{x0+155}" y="{y+idx*row_h}" font-size="13">{desc}</text>'
    svg += '</g>'
    return svg
