# advanced_rendering.py

from professional_symbols import get_component_symbol

def draw_svg_symbol(component_id, width=80, height=80):
    """
    Returns a clean SVG string for the given component_id.
    Use get_component_symbol for industrial/ISA-style symbol.
    """
    return get_component_symbol(component_id, width=width, height=height)

def render_line_with_gradient(points, pipe_style="process", arrow=True):
    """
    Returns an SVG polyline string for a pipeline.
    pipe_style: 'process', 'utility', 'instrument'
    arrow: include arrow marker (for main process lines)
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
    Dashed line for instrument/control signals.
    """
    pts_str = " ".join([f"{int(x)},{int(y)}" for (x, y) in points])
    return f'<polyline points="{pts_str}" stroke="#000" stroke-width="2" fill="none" stroke-dasharray="6,6" marker-end="url(#arrowhead)" />'

def render_tag_bubble(x, y, tag, font_size=13, tag_type="circle"):
    """
    ISA-style tag bubbles: circle for instruments/valves, rectangle for controllers.
    """
    if tag_type == "circle":
        r = 16
        svg = f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="#111" stroke-width="2"/>'
        svg += f'<text x="{x}" y="{y+5}" font-size="{font_size}" font-family="Arial" font-weight="bold" text-anchor="middle">{tag}</text>'
    else:  # rectangle or square
        w, h = 36, 24
        svg = f'<rect x="{x-w//2}" y="{y-h//2}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="#111" stroke-width="2"/>'
        svg += f'<text x="{x}" y="{y+7}" font-size="{font_size}" font-family="Arial" font-weight="bold" text-anchor="middle">{tag}</text>'
    return svg

def render_grid(width=2000, height=1100, spacing=100):
    """
    Optional: Render faint grid lines (engineering paper look).
    """
    lines = ""
    for x in range(0, width+1, spacing):
        lines += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#eee" stroke-width="1"/>'
    for y in range(0, height+1, spacing):
        lines += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#eee" stroke-width="1"/>'
    return f'<g id="grid">{lines}</g>'

def render_border(width=2000, height=1100):
    """
    Render a thick border, like the reference P&ID.
    """
    return f'<rect x="6" y="6" width="{width-12}" height="{height-12}" fill="none" stroke="#222" stroke-width="3"/>'

def render_title_block(title="P&ID DRAWING", project="EPS", rev="00", scale="1:1", date=""):
    """
    Render a simple title block in the lower right (like your reference).
    Add more fields as needed.
    """
    x0, y0 = 1580, 990
    svg = f'''
    <g id="titleblock">
      <rect x="{x0}" y="{y0}" width="400" height="90" fill="#fff" stroke="#111" stroke-width="2"/>
      <text x="{x0+20}" y="{y0+30}" font-size="20" font-family="Arial" font-weight="bold">{title}</text>
      <text x="{x0+20}" y="{y0+55}" font-size="14" font-family="Arial">Project: {project}</text>
      <text x="{x0+20}" y="{y0+75}" font-size="14" font-family="Arial">Rev: {rev}   Scale: {scale}   Date: {date}</text>
    </g>
    '''
    return svg

# Example usage in your drawing_engine.py (combine these layers in render_svg):

# svg = (
#     '<svg width="2000" height="1100" viewBox="0 0 2000 1100" xmlns="http://www.w3.org/2000/svg">'
#     + render_grid()
#     + render_border()
#     + render_title_block()
#     + ... # your other layers: equipment, pipes, tags, etc.
#     + '</svg>'
# )

# You can easily modify the render_title_block() to fit your company's title block and add more metadata if needed.
