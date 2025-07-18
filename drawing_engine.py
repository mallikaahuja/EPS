from professional_symbols import get_component_symbol
from advanced_rendering import draw_svg_symbol, render_line_with_gradient
from control_systems import render_pid_loops, render_signal_lines, render_instrument_bubbles
import cairosvg
from io import BytesIO

def render_svg(equipment_df, pipeline_df, inline_df, positions, pipelines, inlines):
    symbol_size = 80
    # --- Equipment ---
    svg_equip = ""
    for _, row in equipment_df.iterrows():
        comp_id = row["ID"]
        x, y = positions[comp_id]
        # Use advanced rendering for SVG symbol
        symbol_svg = draw_svg_symbol(comp_id, width=symbol_size, height=symbol_size)
        svg_equip += f'<g id="{comp_id}"><g transform="translate({x},{y})">{symbol_svg}</g>'
        svg_equip += f'<text x="{x + symbol_size/2 - 15}" y="{y + symbol_size + 20}" font-size="13">{comp_id}</text></g>'

    # --- Pipes ---
    svg_pipes = ""
    for pipe in pipelines:
        pts = pipe["points"]
        # Use advanced rendering for lines (can use gradient/lineweight)
        svg_pipes += render_line_with_gradient(pts, pipe_style="process" if "process" in pipe["src"].lower() else "utility")

    # --- Inline components (valves/meters) ---
    svg_inline = ""
    for inline in inlines:
        comp_id = inline["ID"]
        x, y = inline["pos"]
        symbol_svg = draw_svg_symbol(comp_id, width=48, height=48)
        svg_inline += f'<g transform="translate({x},{y})">{symbol_svg}</g>'

    # --- Control systems & signals ---
    svg_controls = render_pid_loops(equipment_df, positions)
    svg_signals = render_signal_lines(equipment_df, positions)
    svg_instruments = render_instrument_bubbles(equipment_df, positions)

    # --- Equipment List / Legend ---
    svg_legend = render_equipment_list_svg(equipment_df)

    svg_header = """
    <svg width="2000" height="1100" viewBox="0 0 2000 1100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrowhead" markerWidth="14" markerHeight="12" refX="14" refY="6" orient="auto" markerUnits="strokeWidth">
          <polygon points="2,2 14,6 2,10" fill="#222" />
        </marker>
      </defs>
    """
    return svg_header + svg_legend + svg_pipes + svg_equip + svg_inline + svg_controls + svg_signals + svg_instruments + "</svg>"

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

def render_equipment_list_svg(equipment_df):
    # Add legend block (could add symbol previews if wanted)
    header = ["Tag", "Description", "Spec"]
    x0, y0, row_h, col_w = 30, 40, 22, [60, 170, 120]
    svg = f'<g id="equipment-list"><text x="{x0}" y="{y0}" font-size="18" font-weight="bold">EQUIPMENT LIST</text>'
    y = y0 + 24
    svg += f'<rect x="{x0-8}" y="{y0+5}" width="{sum(col_w)}" height="{row_h}" fill="#eee" stroke="#222"/>'
    for c, head in enumerate(header):
        svg += f'<text x="{x0 + sum(col_w[:c]) + 5}" y="{y}" font-size="12" font-weight="bold">{head}</text>'
    y += row_h
    for _, row in equipment_df.iterrows():
        svg += f'<rect x="{x0-8}" y="{y-row_h+5}" width="{sum(col_w)}" height="{row_h}" fill="#fff" stroke="#bbb"/>'
        for c, key in enumerate(["ID", "Description", "Specs"]):
            val = str(row[key]) if key in row else ""
            svg += f'<text x="{x0 + sum(col_w[:c]) + 5}" y="{y}" font-size="12">{val}</text>'
        y += row_h
    svg += '</g>'
    return svg
