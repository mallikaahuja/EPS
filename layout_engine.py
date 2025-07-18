import pandas as pd
import json
from process_mapper import auto_sequence, detect_process_flow
from utils import merge_layout_hints

# Load component port mapping
with open("component_mapping.json") as f:
    ports = json.load(f)
PORT_MAP = {}
for item in ports:
    comp = item["Component"]
    if comp not in PORT_MAP:
        PORT_MAP[comp] = {}
    PORT_MAP[comp][item["Port Name"]] = (item["dx"], item["dy"])

def compute_positions_and_routing(equipment_df, pipeline_df, inline_df):
    # Step 1: Use process_mapper for logical process order
    process_order = auto_sequence(equipment_df, pipeline_df)

    # Step 2: Load enhanced equipment layout hints (if available)
    try:
        enhanced_layout = pd.read_csv('enhanced_equipment_layout.csv')
        equipment_df = merge_layout_hints(equipment_df, enhanced_layout)
    except Exception:
        pass  # fallback: ignore if not found

    # Step 3: Place equipment according to process_order, with y-hints if present
    x0, y0, x_gap = 180, 320, 300
    positions = {}
    for i, eq_id in enumerate(process_order):
        eq_row = equipment_df[equipment_df["ID"] == eq_id]
        if not eq_row.empty:
            y_hint = eq_row.iloc[0].get("Y_hint", y0)
            positions[eq_id] = (x0 + i * x_gap, y_hint if pd.notnull(y_hint) else y0)

    # Step 4: Place leftovers (not in process order)
    for _, row in equipment_df.iterrows():
        if row["ID"] not in positions:
            positions[row["ID"]] = (x0 + (len(positions) * x_gap), y0)

    # Step 5: Pipe routing—use pipes_connections.csv if present
    pipelines = []
    try:
        pipes_connections = pd.read_csv('pipes_connections.csv')
        for _, row in pipes_connections.iterrows():
            src = row["Source"]
            dst = row["Destination"]
            src_port = row.get("Source Port", "discharge")
            dst_port = row.get("Destination Port", "suction")
            src_xy = tuple(map(sum, zip(positions.get(src, (0, 0)), PORT_MAP.get(src, {}).get(src_port, (0, 0)))))
            dst_xy = tuple(map(sum, zip(positions.get(dst, (0, 0)), PORT_MAP.get(dst, {}).get(dst_port, (0, 0)))))
            points = [(row["X1"], row["Y1"]), (row["X2"], row["Y2"])] if "X1" in row and "Y1" in row else [src_xy, dst_xy]
            pipelines.append({"src": src, "dst": dst, "points": points})
    except Exception:
        # fallback: auto-route pipes using basic elbow logic
        for _, row in pipeline_df.iterrows():
            src, dst = row["Source"], row["Destination"]
            src_port, dst_port = row.get("Source Port", "discharge"), row.get("Destination Port", "suction")
            src_xy = tuple(map(sum, zip(positions.get(src, (0, 0)), PORT_MAP.get(src, {}).get(src_port, (0, 0)))))
            dst_xy = tuple(map(sum, zip(positions.get(dst, (0, 0)), PORT_MAP.get(dst, {}).get(dst_port, (0, 0)))))
            points = elbow_path(src_xy, dst_xy)
            pipelines.append({"src": src, "dst": dst, "points": points})

    # Step 6: Place inline components (valves/meters) on pipelines
    inlines = []
    for _, row in inline_df.iterrows():
        # Try to map by pipeline tag, else assign to first pipe as fallback
        for pipe in pipelines:
            if row["Pipeline"] == pipe["src"] or row["Pipeline"] == pipe["dst"]:
                pts = pipe["points"]
                idx = len(pts) // 2
                pos = pts[idx]
                inlines.append({"ID": row["ID"], "pos": pos})
                break
        else:
            if pipelines:
                pts = pipelines[0]["points"]
                pos = pts[len(pts) // 2]
                inlines.append({"ID": row["ID"], "pos": pos})

    return positions, pipelines, inlines

def elbow_path(src, dst):
    x0, y0 = src
    x1, y1 = dst
    if abs(x0-x1) < 30 or abs(y0-y1) < 30:
        return [(x0, y0), (x1, y1)]
    else:
        return [(x0, y0), (x1, y0), (x1, y1)]
