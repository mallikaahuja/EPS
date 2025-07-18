from advanced_rendering import (
    draw_svg_symbol,
    render_line_with_gradient,
    render_signal_line,
    render_tag_bubble,
    render_grid,
    render_border,
    render_title_block,
    render_bom_block,
    render_legend_block,
)
import cairosvg
from io import BytesIO

def render_svg(equipment_df, pipeline_df, inline_df, positions, pipelines, inlines,
               width=2000, height=1100, show_grid=True, show_legend=True, show_title=True):
    # Use provided dimensions

    # --- Draw grid and border (background) ---
    svg_layers = []
    if show_grid:
        svg_layers.append(render_grid(width, height, spacing=100))
    svg_layers.append(render_border(width, height))

    # --- Title Block, BOM, Legend (footer blocks) ---
    if show_title:
        svg_layers.append(render_title_block(
            title="TENTATIVE P&amp;ID DRAWING FOR SUCTION FILTER + KDP-330",
            project="EPSPL_V2526-TP",
            rev="00",
            scale="1:50",
            date="2025-07-18",
            company="Economy Process Solutions Pvt. Ltd.",
            sheet="1 of 1"
        ))

    if show_legend:
        svg_layers.append(render_bom_block(equipment_df))
        svg_layers.append(render_legend_block(equipment_df))

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
            label_width = len(str(line_number)) * 7 + 10
            svg_layers.append(f'<rect x="{mid_x - label_width/2}" y="{mid_y - 9}" width="{label_width}" height="18" fill="white" stroke="black" stroke-width="0.5"/>')
            svg_layers.append(f'<text x="{mid_x}" y="{mid_y + 4}" font-size="10" text-anchor="middle" font-family="Arial">{line_number}</text>')

    # --- Equipment symbols & tag bubbles ---
    for _, row in equipment_df.iterrows():
        comp_id = row["ID"]
        x, y = positions[comp_id]
        svg_layers.append(
            f'<g id="{comp_id}"><g transform="translate({x},{y})">{draw_svg_symbol(comp_id, width=80, height=80)}</g></g>'
        )
        # Tag bubble under each equipment
        svg_layers.append(render_tag_bubble(x+40, y+110, tag=comp_id, font_size=13, tag_type="circle"))

    # --- Inline components (valves, meters) & tag bubbles ---
    for inline in inlines:
        comp_id = inline["ID"]
        x, y = inline["pos"]
        inline_type = inline.get("type", "valve")
        description = inline.get("description", comp_id)

        # Draw the inline component symbol
        svg_layers.append(
            f'<g transform="translate({x-24},{y-24})">{draw_svg_symbol(comp_id, width=48, height=48)}</g>'
        )

        # Tag bubble for inline component
        # For valves and similar, use smaller bubble below
        if "valve" in inline_type:
            svg_layers.append(render_tag_bubble(x, y+35, tag=comp_id, font_size=9, tag_type="circle"))
        else:
            # For instruments, use standard bubble to the side
            svg_layers.append(render_tag_bubble(x+30, y, tag=comp_id, font_size=11, tag_type="circle"))

    # --- Draw signal/instrument lines ---
    # Filter for instrument signal lines
    for pipe in pipelines:
        if pipe.get("line_type", "") in ["instrument", "instrument_signal", "signal"]:
            pts = pipe["points"]
            svg_layers.append(render_signal_line(pts, sig_type="instrument"))

    # --- Compose SVG ---
    svg_header = (
        '<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<marker id="arrowhead" markerWidth="14" markerHeight="12" refX="14" refY="6" orient="auto" markerUnits="strokeWidth">'
        '<polygon points="2,2 14,6 2,10" fill="#222" />'
        '</marker>'
        '<marker id="signal-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#0a85ff" stroke="#0a85ff"/>'
        '</marker>'
        '</defs>'
    ).format(w=width, h=height)

    svg = svg_header + "".join(svg_layers) + "</svg>"
    return svg

def svg_to_png(svg_string, scale=1.5):
    # Changed to standard straight quotes
    return cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)

def export_dxf(positions, pipelines):
    import ezdxf
    from io import StringIO
    import tempfile

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Add equipment blocks as circles with text (since blockref needs defined blocks)
    for eq_id, (x, y) in positions.items():
        # Add a circle to represent equipment
        msp.add_circle((x, y), radius=30, dxfattribs={'layer': 'EQUIPMENT', 'color': 2})
        # Add text label
        msp.add_text(eq_id, dxfattribs={'layer': 'TEXT', 'height': 10}).set_placement((x, y-40))

    # Add pipelines
    for pipe in pipelines:
        if "points" in pipe and len(pipe["points"]) >= 2:
            # Convert points to 2D tuples (DXF expects 2D or 3D points)
            points_2d = [(p[0], p[1]) for p in pipe["points"]]
            msp.add_lwpolyline(points_2d, dxfattribs={'layer': 'PIPING', 'color': 7, 'lineweight': 40})

    # Write to temporary file then read back
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dxf', delete=False) as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    with open(tmp_path, 'rb') as f:
        dxf_content = f.read()

    # Clean up temp file
    import os
    os.unlink(tmp_path)

    return dxf_content
