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

def render_svg(equipment_df, pipeline_df, inline_df, positions, pipelines, inlines):
    width, height = 2000, 1100

    # --- Draw grid and border (background) ---
    svg_layers = [
        render_grid(width, height, spacing=100),
        render_border(width, height)
    ]

    # --- Title Block, BOM, Legend (footer blocks) ---
    svg_layers.append(render_title_block(
        title="TENTATIVE P&ID DRAWING FOR SUCTION FILTER + KDP-330",
        project="EPSPL_V2526-TP",
        rev="00",
        scale="1:50",
        date="2025-07-18",
        company="Economy Process Solutions Pvt. Ltd.",
        sheet="1 of 1"
    ))
    svg_layers.append(render_bom_block(equipment_df))
    svg_layers.append(render_legend_block(equipment_df))

    # --- Draw pipelines (with type detection) ---
    for pipe in pipelines:
        pts = pipe["points"]
        style = "process"
        src = pipe.get("src", "").lower()
        dst = pipe.get("dst", "").lower()
        # Detect by src/dst or a 'Type' key in your pipe dict
        if "utility" in src or "utility" in dst:
            style = "utility"
        if "instrument" in src or "instrument" in dst:
            style = "instrument"
        svg_layers.append(render_line_with_gradient(pts, pipe_style=style, arrow=True))

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
        svg_layers.append(
            f'<g transform="translate({x},{y})">{draw_svg_symbol(comp_id, width=48, height=48)}</g>'
        )
        # Inline tag bubble (slightly offset below)
        svg_layers.append(render_tag_bubble(x+24, y+60, tag=comp_id, font_size=11, tag_type="circle"))

    # --- Optionally draw signal/instrument lines (if you have them in your process data) ---
    # Example (if you build a 'signals' list in your control/logic engine):
    # for sig in signals:
    #     svg_layers.append(render_signal_line(sig["points"]))

    # --- Compose SVG ---
    svg_header = (
        '<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<marker id="arrowhead" markerWidth="14" markerHeight="12" refX="14" refY="6" orient="auto" markerUnits="strokeWidth">'
        '<polygon points="2,2 14,6 2,10" fill="#222" />'
        '</marker>'
        '</defs>'
    ).format(w=width, h=height)

    svg = svg_header + "".join(svg_layers) + "</svg>"
    return svg

def svg_to_png(svg_string, scale=1.5):
    return cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)

def export_dxf(positions, pipelines):
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for eq_id, (x, y) in positions.items():
        msp.add_blockref(eq_id, (x, y, 0))
    for pipe in pipelines:
        msp.add_lwpolyline(pipe["points"], dxfattribs={'layer': 'PIPING', 'color': 7, 'lineweight': 40})
    out = BytesIO()
    doc.write(out)
    return out.getvalue()
