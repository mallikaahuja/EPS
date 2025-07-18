import pandas as pd
import json
from process_mapper import auto_sequence, detect_process_flow, get_src_dst
from utils import merge_layout_hints

with open("component_mapping.json") as f:
    ports = json.load(f)
PORT_MAP = {}
for item in ports:
    comp = item["Component"]
    if comp not in PORT_MAP:
        PORT_MAP[comp] = {}
    PORT_MAP[comp][item["Port Name"]] = (item["dx"], item["dy"])

def compute_positions_and_routing(equipment_df, pipeline_df, inline_df):
    # Try to use enhanced layout first
    positions = {}
    try:
        enhanced_layout = pd.read_csv('enhanced_equipment_layout.csv')
        for _, row in enhanced_layout.iterrows():
            eq_id = row.get('id') or row.get('ID')
            x = row.get('x', 0)
            y = row.get('y', 0)
            if eq_id and pd.notna(x) and pd.notna(y):
                positions[eq_id] = (float(x), float(y))
    except Exception as e:
        print(f"Could not load enhanced layout: {e}")

    # Fallback to auto-sequencing for any missing positions
    if not positions:
        process_order = auto_sequence(equipment_df, pipeline_df)
        x0, y0, x_gap = 180, 320, 200
        for i, eq_id in enumerate(process_order):
            if eq_id not in positions:
                positions[eq_id] = (x0 + i * x_gap, y0)

    # Ensure all equipment has positions
    for _, row in equipment_df.iterrows():
        if row["ID"] not in positions:
            # Place unpositioned items at the bottom
            positions[row["ID"]] = (100 + len(positions) * 50, 500)

    # Create pipelines from connections
    pipelines = []
    try:
        # First try to use pipes_connections.csv if it exists
        pipes_connections = pd.read_csv('pipes_connections.csv')
        for _, row in pipes_connections.iterrows():
            src = row.get('from_component', '')
            dst = row.get('to_component', '')
            src_port = row.get('from_port', 'outlet')
            dst_port = row.get('to_port', 'inlet')

            if src in positions and dst in positions:
                # Get port offsets
                src_offset = PORT_MAP.get(src, {}).get(src_port, (0, 0))
                dst_offset = PORT_MAP.get(dst, {}).get(dst_port, (0, 0))

                # Calculate actual connection points
                src_xy = (positions[src][0] + src_offset[0], positions[src][1] + src_offset[1])
                dst_xy = (positions[dst][0] + dst_offset[0], positions[dst][1] + dst_offset[1])

                # Check for waypoints
                waypoints = row.get('waypoints', '[]')
                if isinstance(waypoints, str) and waypoints != '[]':
                    try:
                        import json
                        waypoints_list = json.loads(waypoints)
                        points = [src_xy] + waypoints_list + [dst_xy]
                    except:
                        points = elbow_path(src_xy, dst_xy)
                else:
                    points = elbow_path(src_xy, dst_xy)

                pipelines.append({
                    "src": src,
                    "dst": dst,
                    "points": points,
                    "line_type": row.get('line_type', 'process'),
                    "line_number": row.get('line_number', '')
                })
    except FileNotFoundError:
        # Fallback to pipeline_df if pipes_connections.csv doesn't exist
        for _, row in pipeline_df.iterrows():
            src, dst = get_src_dst(row)
            if not src or not dst or src not in positions or dst not in positions:
                continue

            src_port = row.get("Source Port", "discharge")
            dst_port = row.get("Destination Port", "suction")

            # Get port offsets
            src_offset = PORT_MAP.get(src, {}).get(src_port, (0, 0))
            dst_offset = PORT_MAP.get(dst, {}).get(dst_port, (0, 0))

            # Calculate actual connection points
            src_xy = (positions[src][0] + src_offset[0], positions[src][1] + src_offset[1])
            dst_xy = (positions[dst][0] + dst_offset[0], positions[dst][1] + dst_offset[1])

            points = elbow_path(src_xy, dst_xy)
            pipelines.append({
                "src": src,
                "dst": dst,
                "points": points,
                "line_type": "process"
            })

    # Position inline components on their pipelines
    inlines = []
    for _, row in inline_df.iterrows():
        inline_id = row["ID"]
        pipeline_name = row.get("Pipeline", "")

        # Find the pipeline this inline component belongs to
        target_pipe = None
        for pipe in pipelines:
            # Check if the inline component is on this pipeline by matching pipeline ID or by src/dst
            if (pipeline_name and
                (pipeline_name == f"{pipe['src']}_{pipe['dst']}" or
                 pipeline_name in [pipe.get('line_number', ''), pipe['src'], pipe['dst']])):
                target_pipe = pipe
                break

        if target_pipe and len(target_pipe["points"]) >= 2:
            # Place at midpoint of pipeline
            pts = target_pipe["points"]
            if len(pts) == 2:
                # Simple line - place at midpoint
                pos = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
            else:
                # Multi-segment line - place on middle segment
                mid_idx = len(pts) // 2
                pos = ((pts[mid_idx-1][0] + pts[mid_idx][0]) / 2,
                       (pts[mid_idx-1][1] + pts[mid_idx][1]) / 2)

            inlines.append({
                "ID": inline_id,
                "pos": pos,
                "type": row.get("type", "valve"),
                "description": row.get("Description", "")
            })
        else:
            # Fallback positioning if pipeline not found
            inlines.append({
                "ID": inline_id,
                "pos": (300 + len(inlines) * 100, 400),
                "type": row.get("type", "valve"),
                "description": row.get("Description", "")
            })

    return positions, pipelines, inlines

def elbow_path(src, dst):
    x0, y0 = src
    x1, y1 = dst
    if abs(x0-x1) < 30 or abs(y0-y1) < 30:
        return [(x0, y0), (x1, y1)]
    else:
        return [(x0, y0), (x1, y0), (x1, y1)]
