import pandas as pd

def get_src_dst(row):
    src = row.get("Source") or row.get("Start") or row.get("From") or row.get("ID")
    dst = row.get("Destination") or row.get("End") or row.get("To")
    return src, dst

def auto_sequence(equipment_df, pipeline_df):
    forward = {}
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if not src or not dst:
            continue  # skip bad rows
        if src not in forward:
            forward[src] = []
        forward[src].append(dst)
    all_ids = set(equipment_df["ID"])
    all_src = set(src for src in forward)
    all_dst = set(d for dsts in forward.values() for d in dsts)
    possible_starts = list(all_src - all_dst)
    if not possible_starts:
        possible_starts = [equipment_df.iloc[0]["ID"]]
    result = []
    seen = set()
    def dfs(node):
        if node in seen or node not in all_ids:
            return
        seen.add(node)
        result.append(node)
        for nbr in forward.get(node, []):
            dfs(nbr)
    dfs(possible_starts[0])
    for eq in all_ids:
        if eq not in result:
            result.append(eq)
    return result

def detect_process_flow(equipment_df, pipeline_df):
    process_graph = {}
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if not src or not dst:
            continue
        if src not in process_graph:
            process_graph[src] = []
        process_graph[src].append(dst)
    return process_graph

def get_equipment_type_map(equipment_df):
    id_type = {}
    for _, row in equipment_df.iterrows():
        eq_id = row["ID"]
        eq_type = row.get("Type", "") or row.get("Description", "")
        id_type[eq_id] = eq_type
    return id_type

def group_equipment_by_section(equipment_df, pipeline_df):
    groups = {}
    for _, row in equipment_df.iterrows():
        section = "Ungrouped"
        desc = str(row.get("Description", "")).lower()
        if "pump" in desc:
            section = "Pumps"
        elif "condenser" in desc:
            section = "Condensers"
        elif "receiver" in desc:
            section = "Receivers"
        elif "tank" in desc or "vessel" in desc:
            section = "Tanks/Vessels"
        elif "scrubber" in desc:
            section = "Scrubbers"
        elif "filter" in desc:
            section = "Filters"
        if section not in groups:
            groups[section] = []
        groups[section].append(row["ID"])
    return groups
