# drawing_engine.py

import io
import ezdxf
import cairosvg
import networkx as nx
from symbols import SymbolRenderer
from typing import Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import base64

def render_svg(dsl_dict: Dict, renderer: SymbolRenderer, positions: Dict, show_grid=True, show_legend=True, zoom=1.0) -> Tuple[str, Dict]:
    """
    Renders a complete P&ID diagram in SVG format using port-aware symbol rendering
    and routing with NetworkX.

    Args:
        dsl_dict: The DSL dictionary containing components and connections.
        renderer: SymbolRenderer instance.
        positions: Dict mapping component IDs to (x, y) positions.
        show_grid: Whether to render a background grid.
        show_legend: Whether to include a symbol legend.
        zoom: Scaling factor.

    Returns:
        svg_string: SVG image as string.
        port_map: Dict of component_id → port positions.
    """
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_aspect('equal')
    ax.axis('off')

    if show_grid:
        ax.set_xlim(0, 2000)
        ax.set_ylim(0, 1500)
        ax.set_xticks(range(0, 2000, 100))
        ax.set_yticks(range(0, 1500, 100))
        ax.grid(True, which='both', linestyle='--', linewidth=0.3)

    port_map = {}
    image_cache = {}

    # Render equipment
    for comp in dsl_dict["components"]:
        comp_id = comp["id"]
        label = comp.get("label", comp_id)
        x, y = positions.get(comp_id, (0, 0))
        image_bytes, ports = renderer.render_symbol(comp_id.lower(), label, size=zoom)

        port_map[comp_id] = {k: (x*100 + dx*100, y*100 + dy*100) for k, (dx, dy) in ports.items()}

        # Draw the image
        image = plt.imread(io.BytesIO(image_bytes), format='png')
        ax.imshow(image, extent=[x*100, x*100+100, y*100, y*100+100])
        image_cache[comp_id] = (x*100, y*100)

        # Add tag
        ax.text(x*100 + 50, y*100 - 10, label, fontsize=10, ha='center')

    # Draw connections using port mapping
    for conn in dsl_dict.get("connections", []):
        src = conn["from"]
        dst = conn["to"]
        src_pos = port_map.get(src, {}).get("out", None)
        dst_pos = port_map.get(dst, {}).get("in", None)

        if src_pos and dst_pos:
            ax.annotate("",
                        xy=dst_pos, xycoords='data',
                        xytext=src_pos, textcoords='data',
                        arrowprops=dict(arrowstyle="->", color='black', lw=1.5))

    # Draw legend
    if show_legend:
        ax.text(1800, 1400, "LEGEND", fontsize=12, weight='bold')
        y_cursor = 1350
        for comp in dsl_dict["components"][:10]:  # limit for demo
            ax.text(1800, y_cursor, f"{comp['id']} → {comp['type']}", fontsize=8)
            y_cursor -= 20

    buf = io.BytesIO()
    fig.savefig(buf, format='svg', bbox_inches='tight')
    plt.close(fig)
    svg_string = buf.getvalue().decode('utf-8')
    return svg_string, port_map

def svg_to_png(svg_string: str) -> bytes:
    """Convert SVG string to PNG bytes."""
    return cairosvg.svg2png(bytestring=svg_string.encode("utf-8"))

def export_dxf(dsl_dict: Dict) -> bytes:
    """Convert P&ID components to a basic DXF."""
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    for comp in dsl_dict.get("components", []):
        x, y = comp.get("x", 0), comp.get("y", 0)
        label = comp.get("label", comp["id"])
        msp.add_circle((x * 10, y * 10), radius=5)
        msp.add_text(label, dxfattribs={"height": 2.5}).set_pos((x * 10 + 6, y * 10), align="LEFT")

    buf = io.BytesIO()
    doc.write(buf)
    return buf.getvalue()
