# layout_engine.py

import pandas as pd
import json
import networkx as nx
from process_mapper import auto_sequence, get_src_dst
from utils import merge_layout_hints

# Load component port mappings
with open("component_mapping.json") as f:
    ports = json.load(f)
PORT_MAP = {}
for item in ports:
    comp = item["Component"]
    if comp not in PORT_MAP:
        PORT_MAP[comp] = {}
    PORT_MAP[comp][item["Port Name"]] = (item["dx"], item["dy"])

def compute_positions_and_routing(equipment_df, pipeline_df, inline_df):
    positions = {}

    # Try to use enhanced layout if available
    try:
        layout_df = pd.read_csv('enhanced_equipment_layout.csv')
        for _, row in layout_df.iterrows():
            comp_id = row.get("ID") or row.get("id")
            if comp_id and pd.notna(row.get("x")) and pd.notna(row.get("y")):
                positions[comp_id] = (float(row["x"]), float(row["y"]))
    except Exception as e:
        print(f"⚠️ Could not load enhanced layout: {e}")

    # Fallback to auto-sequencing if needed
    if not positions:
        process_order = auto_sequence(equipment_df, pipeline_df)
        for i, eq_id in enumerate(process_order):
            positions[eq_id] = (200 + i * 250, 400)

    # Ensure every equipment is placed
    for _, row in equipment_df.iterrows():
        if row["ID"] not in positions:
            positions[row["ID"]] = (100 + len(positions) * 100, 600)

    # Create connection graph for route logic
    G = nx.DiGraph()
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if src and dst:
            G.add_edge(src, dst)

    # Draw pipelines
    pipelines = []
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if not src or not dst or src not in positions or dst not in positions:
            continue

        src_port = row.get("Source Port", "discharge")
        dst_port = row.get("Destination Port", "suction")
        src_offset = PORT_MAP.get(src, {}).get(src_port, (0, 0))
        dst_offset = PORT_MAP.get(dst, {}).get(dst_port, (0, 0))

        src_xy = (positions[src][0] + src_offset[0], positions[src][1] + src_offset[1])
        dst_xy = (positions[dst][0] + dst_offset[0], positions[dst][1] + dst_offset[1])

        points = elbow_path(src_xy, dst_xy)
        pipelines.append({
            "src": src,
            "dst": dst,
            "points": points,
            "line_type": row.get("line_type", "process"),
            "line_number": row.get("line_number", "")
        })

    # Place inline components
    inlines = []
    for _, row in inline_df.iterrows():
        inline_id = row["ID"]
        pipeline_name = row.get("Pipeline", "")
        target_pipe = None

        for pipe in pipelines:
            if pipeline_name and pipeline_name in [f"{pipe['src']}_{pipe['dst']}", pipe.get("line_number", ""), pipe["src"], pipe["dst"]]:
                target_pipe = pipe
                break

        if target_pipe and len(target_pipe["points"]) >= 2:
            pts = target_pipe["points"]
            mid = len(pts) // 2
            pos = ((pts[mid-1][0] + pts[mid][0]) / 2, (pts[mid-1][1] + pts[mid][1]) / 2)
        else:
            pos = (300 + len(inlines) * 100, 500)

        inlines.append({
            "ID": inline_id,
            "pos": pos,
            "type": row.get("type", "valve"),
            "description": row.get("Description", "")
        })

    return positions, pipelines, inlines

def elbow_path(src, dst):
    x0, y0 = src
    x1, y1 = dst
    if abs(x0 - x1) < 30 or abs(y0 - y1) < 30:
        return [src, dst]
    else:
        return [(x0, y0), (x1, y0), (x1, y1)]
