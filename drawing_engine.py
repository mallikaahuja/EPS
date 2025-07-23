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

def render_svg(dsl_dict: Dict, renderer: SymbolRenderer, positions: Dict,
               show_grid=True, show_legend=True, zoom=1.0) -> Tuple[str, Dict]:
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

    # Render components
    for comp in dsl_dict["components"]:
        comp_id = comp["id"]
        tag = comp.get("tag", comp_id)
        x, y = positions.get(comp_id, (0, 0))
        image_bytes, ports = renderer.render_symbol(comp_id.lower(), tag, size=zoom)

        port_map[comp_id] = {k: (x*100 + dx*100, y*100 + dy*100) for k, (dx, dy) in ports.items()}

        image = plt.imread(io.BytesIO(image_bytes), format='png')
        ax.imshow(image, extent=[x*100, x*100+100, y*100, y*100+100])
        ax.text(x*100 + 50, y*100 - 10, tag, fontsize=10, ha='center')
        image_cache[comp_id] = (x*100, y*100)

    # Draw connections
    for conn in dsl_dict.get("connections", []):
        src = conn["from"]["component"]
        dst = conn["to"]["component"]
        src_port = conn["from"].get("port", "outlet")
        dst_port = conn["to"].get("port", "inlet")
        conn_type = conn.get("type", "Process")

        src_pos = port_map.get(src, {}).get(src_port, None)
        dst_pos = port_map.get(dst, {}).get(dst_port, None)

        if src_pos and dst_pos:
            style = "dashed" if conn_type.lower() in ["instrument", "electrical", "pneumatic"] else "solid"
            color = "blue" if conn_type.lower() == "instrument" else "black"
            ax.annotate("",
                        xy=dst_pos, xycoords='data',
                        xytext=src_pos, textcoords='data',
                        arrowprops=dict(arrowstyle="->", linestyle=style, color=color, lw=1.5))

    # Draw control loop highlights
    for loop in dsl_dict.get("control_loops", []):
        for comp_id in loop["components"]:
            if comp_id in positions:
                x, y = positions[comp_id]
                ax.add_patch(patches.Circle((x*100 + 50, y*100 + 50), radius=60, fill=False,
                                            edgecolor='orange', linestyle='dashed', linewidth=2))
                ax.text(x*100 + 50, y*100 + 110, loop["id"], fontsize=8, ha='center', color='orange')

    # Draw legend
    if show_legend:
        ax.text(1800, 1400, "LEGEND", fontsize=12, weight='bold')
        y_cursor = 1350
        for comp in dsl_dict["components"][:12]:
            isa = comp.get("attributes", {}).get("isa_code", "")
            ax.text(1800, y_cursor, f"{comp['tag']} → {isa}", fontsize=8)
            y_cursor -= 20

    buf = io.BytesIO()
    fig.savefig(buf, format='svg', bbox_inches='tight')
    plt.close(fig)
    svg_string = buf.getvalue().decode('utf-8')
    return svg_string, port_map

def svg_to_png(svg_string: str) -> bytes:
    return cairosvg.svg2png(bytestring=svg_string.encode("utf-8"))

def export_dxf(dsl_dict: Dict) -> bytes:
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    for comp in dsl_dict.get("components", []):
        pos = comp.get("position", {})
        x, y = pos.get("x", 0), pos.get("y", 0)
        tag = comp.get("tag", comp["id"])
        msp.add_circle((x * 10, y * 10), radius=5)
        msp.add_text(tag, dxfattribs={"height": 2.5}).set_pos((x * 10 + 6, y * 10), align="LEFT")

    buf = io.BytesIO()
    doc.write(buf)
    return buf.getvalue()
