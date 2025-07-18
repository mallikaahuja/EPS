# advanced_rendering.py

from professional_symbols import get_component_symbol

def draw_svg_symbol(component_id, width=80, height=80):
    """
    Clean SVG for any component.
    """
    return get_component_symbol(component_id, width=width, height=height)

def render_line_with_gradient(points, pipe_style="process", arrow=True):
    """
    Industrial pipeline with ISA-compliant style.
    """
    if pipe_style == "process":
        color = "#000"
        width = 9
        dash_attr = ""
    elif pipe_style == "utility":
        color = "#666"
        width = 5
        dash_attr = ""
    elif pipe_style == "instrument":
        color = "#000"
        width = 2
        dash_attr = ' stroke-dasharray="6,5"'
    else:
        color = "#333"
        width = 7
        dash_attr = ""

    pts_str = " ".join([f"{int(x)},{int(y)}" for (x, y) in points])
    marker = ' marker-end="url(#arrowhead)"' if arrow and pipe_style != "instrument" else ""
    return f'<polyline points="{pts_str}" stroke="{color}" stroke-width="{width}" fill="none"{dash_attr}{marker}/>'


def render_signal_line(points):
    """
    Dashed signal line (for control/instrumentation).
    """
    pts_str = " ".join([f"{int(x)},{int(y)}" for (x, y) in points])
    return f'<polyline points="{pts_str}" stroke="#000" stroke-width="2" fill="none" stroke-dasharray="6,6" marker-end="url(#arrowhead)" />'

def render_tag_bubble(x, y, tag, font_size=13, tag_type="circle"):
    """
    Draw ISA-style tag bubble (circle or rectangle) at (x, y) with label.
    """
    if tag_type == "circle":
        r = 16
        svg = f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="#111" stroke-width="2"/>'
        svg += f'<text x="{x}" y="{y+5}" font-size="{font_size}" font-family="Arial" font-weight="bold" text-anchor="middle">{tag}</text>'
    else:
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
    svg = f'''
    <g id="titleblock">
      <rect x="{x0}" y="{y0}" width="400" height="90" fill="#fff" stroke="#111" stroke-width="2"/>
      <text x="{x0+20}" y="{y0+30}" font-size="19" font-family="Arial" font-weight="bold">{title}</text>
      <text x="{x0+20}" y="{y0+52}" font-size="14" font-family="Arial">Project: {project}</text>
      <text x="{x0+20}" y="{y0+70}" font-size="14" font-family="Arial">Rev: {rev}   Scale: {scale}   Date: {date}</text>
      <text x="{x0+260}" y="{y0+52}" font-size="12" font-family="Arial" text-anchor="end">{company}</text>
      <text x="{x0+380}" y="{y0+82}" font-size="11" font-family="Arial" text-anchor="end">Sheet: {sheet}</text>
    </g>
    '''
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
        desc = str(getattr(row, "Description", ""))[:65]  # truncate for fit
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
        desc = str(getattr(row, "Description", ""))[:55]
        svg += f'<text x="{x0+25}" y="{y+idx*row_h}" font-size="13">{tag}</text>'
        svg += f'<text x="{x0+155}" y="{y+idx*row_h}" font-size="13">{desc}</text>'
    svg += '</g>'
    return svg

# USAGE (in your drawing_engine.py's render_svg function):
# svg = (
#     '<svg width="2000" height="1100" viewBox="0 0 2000 1100" xmlns="http://www.w3.org/2000/svg">'
#     + render_grid()
#     + render_border()
#     + render_title_block(...)
#     + render_bom_block(equipment_df)
#     + render_legend_block(equipment_df)
#     + ... # other SVG layers: pipes, equipment, tags, etc.
#     + '</svg>'
# )
