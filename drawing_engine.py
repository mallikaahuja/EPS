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
    image_cache = {} # This will store component's base (x,y) for fallback positions

    # Render components
    for comp in dsl_dict["components"]:
        comp_id = comp["id"]
        tag = comp.get("tag", comp_id)
        # Use position from DSL if available, otherwise use provided 'positions' dict (from layout_engine)
        comp_position = comp.get("position")
        if comp_position:
            x, y = comp_position.get("x", 0), comp_position.get("y", 0)
        else:
            x, y = positions.get(comp_id, (0, 0)) # Fallback to positions from layout engine if DSL has none

        # Note: The `symbols.py` render_symbol method returns image_bytes and a dict of ports relative to symbol (0,0)
        # It's important that this `size` parameter matches the expected symbol size for `extent`.
        # Assuming symbols are rendered to 100x100 for simplicity as per your `ax.imshow` extent
        image_bytes, symbol_ports_relative = renderer.render_symbol(comp_id.lower(), tag, size=100) # Assuming size is 100 for calculation

        # Calculate absolute port positions
        # symbol_ports_relative: {'inlet': (dx, dy), 'outlet': (dx, dy)}
        port_map[comp_id] = {
            p_name: (x + p_dx, y + p_dy) # Port coordinates are relative to component's (x,y)
            for p_name, (p_dx, p_dy) in symbol_ports_relative.items()
        }

        # The extent should match the physical size of the symbol on the plot.
        # If your symbols are consistently 100x100 in size, this is correct.
        ax.imshow(plt.imread(io.BytesIO(image_bytes), format='png'), extent=[x, x+100, y, y+100])
        ax.text(x + 50, y - 10, tag, fontsize=10, ha='center')
        image_cache[comp_id] = (x, y) # Store base (x,y) for fallback connection points


    # REPLACED SECTION: Draw connections
    connections_drawn = 0
    for conn in dsl_dict.get("connections", []):
        try:
            # Handle nested structure from DSLConnection.to_dict()
            if isinstance(conn.get("from"), dict):
                src = conn["from"]["component"]
                dst = conn["to"]["component"] 
                src_port_name = conn["from"].get("port", "outlet")
                dst_port_name = conn["to"].get("port", "inlet")
            else:
                # Handle flat structure (fallback from older DSL versions or different CSVs)
                src = conn.get("from_component", conn.get("from", ""))
                dst = conn.get("to_component", conn.get("to", ""))
                src_port_name = conn.get("from_port", "outlet")
                dst_port_name = conn.get("to_port", "inlet")
            
            conn_type = conn.get("type", "Process")

            # Try to get precise port positions
            src_pos = port_map.get(src, {}).get(src_port_name, None)
            dst_pos = port_map.get(dst, {}).get(dst_port_name, None)
            
            # Fallback to component center positions if specific ports not found
            if not src_pos and src in image_cache:
                # Assuming image_cache stores (x, y) as the bottom-left corner of the symbol
                x_comp, y_comp = image_cache[src]
                src_pos = (x_comp + 50, y_comp + 50) # Center of a 100x100 symbol
            if not dst_pos and dst in image_cache:
                x_comp, y_comp = image_cache[dst]
                dst_pos = (x_comp + 50, y_comp + 50) # Center of a 100x100 symbol

            if src_pos and dst_pos:
                style = "dashed" if conn_type.lower() in ["instrument", "electrical", "pneumatic"] else "solid"
                color = "blue" if conn_type.lower() == "instrument" else "black"
                
                # Check for waypoints (if present in DSLConnection)
                waypoints = conn.get("waypoints", [])
                
                # Plot the main connection line
                path_coords = [src_pos] + waypoints + [dst_pos]
                
                # Extract x and y coordinates
                line_xs = [p["x"] if isinstance(p, dict) else p[0] for p in path_coords]
                line_ys = [p["y"] if isinstance(p, dict) else p[1] for p in path_coords]
                
                ax.plot(line_xs, line_ys, linestyle=style, color=color, lw=1.5, marker='o' if waypoints else '')
                
                # Add arrow at the end
                ax.annotate("",
                            xy=dst_pos, xycoords='data',
                            xytext=path_coords[-2] if len(path_coords) > 1 else src_pos, textcoords='data',
                            arrowprops=dict(arrowstyle="->", linestyle=style, color=color, lw=1.5, mutation_scale=15)) # Increased mutation_scale for visibility
                
                connections_drawn += 1
                print(f"🔗 Connected {src} → {dst} (Type: {conn_type})")
            else:
                print(f"⚠️  Could not find valid positions for connection from '{src}' to '{dst}'. src_pos: {src_pos}, dst_pos: {dst_pos}")

        except Exception as e:
            print(f"❌ Failed to draw connection {conn.get('id', 'unknown')}: {e}")

    print(f"🔗 Drew {connections_drawn} connections")

    # Draw control loop highlights
    for loop in dsl_dict.get("control_loops", []):
        for comp_id in loop["components"]:
            # Use positions from DSLComponent if available, else from the `positions` dict
            comp_obj = next((c for c in dsl_dict["components"] if c["id"] == comp_id), None)
            if comp_obj and comp_obj.get("position"):
                x, y = comp_obj["position"]["x"], comp_obj["position"]["y"]
            elif comp_id in positions:
                x, y = positions[comp_id]
            else:
                continue # Skip if component position not found

            # Assuming 100x100 symbol for circle centering
            ax.add_patch(patches.Circle((x + 50, y + 50), radius=60, fill=False,
                                        edgecolor='orange', linestyle='dashed', linewidth=2))
            ax.text(x + 50, y + 110, loop["id"], fontsize=8, ha='center', color='orange')

    # Draw legend
    if show_legend:
        # Adjust legend position to not overlap with components
        legend_x = ax.get_xlim()[1] - 200 # 200 units from the right edge
        legend_y = ax.get_ylim()[1] - 100 # 100 units from the top edge
        
        ax.text(legend_x, legend_y, "LEGEND", fontsize=12, weight='bold', ha='right')
        y_cursor = legend_y - 20
        
        # Limit the number of items in the legend to avoid clutter
        # Only show items if their tag is unique or useful for legend
        added_to_legend = set()
        for comp in dsl_dict["components"]:
            tag = comp.get("tag", comp["id"])
            isa = comp.get("attributes", {}).get("isa_code", "")
            legend_entry = f"{tag} → {isa}"
            if legend_entry not in added_to_legend:
                ax.text(legend_x, y_cursor, legend_entry, fontsize=8, ha='right')
                y_cursor -= 20
                added_to_legend.add(legend_entry)
            if len(added_to_legend) >= 12: # Limit legend entries
                break

    buf = io.BytesIO()
    fig.savefig(buf, format='svg', bbox_inches='tight')
    plt.close(fig)
    svg_string = buf.getvalue().decode('utf-8')
    return svg_string, port_map

def svg_to_png(svg_string: str) -> bytes:
    import cairosvg
    try:
        # output_width=2400 should scale it up. Make sure it's sufficiently large for detail.
        return cairosvg.svg2png(bytestring=svg_string.encode("utf-8"), output_width=2400)
    except Exception as e:
        raise RuntimeError(f"PNG export failed: {e}")

def export_dxf(dsl_dict: Dict) -> bytes:
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Scale factor for DXF, as DXF coordinates are usually in drawing units (mm, inches, etc.)
    # and not necessarily pixels. A factor of 10-20 is common if 1 unit = 1 pixel initially.
    DXF_SCALE = 10 

    for comp in dsl_dict.get("components", []):
        pos = comp.get("position", {})
        x, y = pos.get("x", 0), pos.get("y", 0)
        tag = comp.get("tag", comp["id"])
        
        # Draw a simple representation for components (e.g., a rectangle or circle)
        # Assuming component size of 100x100 for visual consistency with SVG
        width_dxf = comp.get("attributes", {}).get("width", 100) * DXF_SCALE
        height_dxf = comp.get("attributes", {}).get("height", 100) * DXF_SCALE
        x_dxf = x * DXF_SCALE
        y_dxf = y * DXF_SCALE

        # Add a rectangle for the component
        msp.add_lwpolyline(
            [
                (x_dxf, y_dxf),
                (x_dxf + width_dxf, y_dxf),
                (x_dxf + width_dxf, y_dxf + height_dxf),
                (x_dxf, y_dxf + height_dxf),
                (x_dxf, y_dxf) # Close the rectangle
            ],
            dxfattribs={"layer": "COMPONENTS", "color": 1} # Color 1=red
        )
        
        # Add tag text
        msp.add_text(tag, dxfattribs={
            "height": 5 * DXF_SCALE, # Adjust text height as needed
            "layer": "TEXT",
            "color": 7 # Color 7=white/black
        }).set_pos((x_dxf + width_dxf / 2, y_dxf - 10 * DXF_SCALE), align="MIDDLE_CENTER") # Position text below component

    # Draw connections in DXF
    for conn in dsl_dict.get("connections", []):
        src_id = conn["from"]["component"] if isinstance(conn.get("from"), dict) else conn.get("from_component", "")
        dst_id = conn["to"]["component"] if isinstance(conn.get("to"), dict) else conn.get("to_component", "")

        src_comp = next((c for c in dsl_dict["components"] if c["id"] == src_id), None)
        dst_comp = next((c for c in dsl_dict["components"] if c["id"] == dst_id), None)

        if src_comp and dst_comp:
            src_pos = src_comp.get("position")
            dst_pos = dst_comp.get("position")

            if src_pos and dst_pos:
                # Simple line between component centers for DXF export
                src_x_center = (src_pos.get("x", 0) + src_comp.get("attributes", {}).get("width", 100)/2) * DXF_SCALE
                src_y_center = (src_pos.get("y", 0) + src_comp.get("attributes", {}).get("height", 100)/2) * DXF_SCALE
                dst_x_center = (dst_pos.get("x", 0) + dst_comp.get("attributes", {}).get("width", 100)/2) * DXF_SCALE
                dst_y_center = (dst_pos.get("y", 0) + dst_comp.get("attributes", {}).get("height", 100)/2) * DXF_SCALE

                msp.add_line((src_x_center, src_y_center), (dst_x_center, dst_y_center),
                             dxfattribs={"layer": "CONNECTIONS", "color": 2}) # Color 2=yellow

    buf = io.BytesIO()
    doc.write(buf)
    return buf.getvalue()
