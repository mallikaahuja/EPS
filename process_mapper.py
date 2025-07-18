import pandas as pd

def auto_sequence(equipment_df, pipeline_df):
    """
    Returns a list of equipment IDs in a logical process sequence (left to right),
    based on pipeline connections. Can be improved for more complex processes.
    """
    # Build forward connection map
    forward = {}
    for _, row in pipeline_df.iterrows():
        src, dst = row["Source"], row["Destination"]
        if src not in forward:
            forward[src] = []
        forward[src].append(dst)

    # Identify all unique IDs
    all_ids = set(equipment_df["ID"])
    # Find possible "start" nodes: appear as source but not as destination
    all_src = set(pipeline_df["Source"])
    all_dst = set(pipeline_df["Destination"])
    possible_starts = list(all_src - all_dst)
    if not possible_starts:
        # Fallback: pick first equipment in file
        possible_starts = [equipment_df.iloc[0]["ID"]]

    # Depth-first process order from first "start"
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

    # Add leftovers that weren't connected
    for eq in all_ids:
        if eq not in result:
            result.append(eq)
    return result

def detect_process_flow(equipment_df, pipeline_df):
    """
    Returns a dict representing the adjacency/process graph for all equipment.
    """
    process_graph = {}
    for _, row in pipeline_df.iterrows():
        src, dst = row["Source"], row["Destination"]
        if src not in process_graph:
            process_graph[src] = []
        process_graph[src].append(dst)
    return process_graph

def get_equipment_type_map(equipment_df):
    """
    Returns a dict of equipment ID -> type for use in auto-grouping.
    """
    id_type = {}
    for _, row in equipment_df.iterrows():
        # Use column 'Type' or fall back to Description
        eq_id = row["ID"]
        eq_type = row.get("Type", "") or row.get("Description", "")
        id_type[eq_id] = eq_type
    return id_type

def group_equipment_by_section(equipment_df, pipeline_df):
    """
    Optionally group equipment into sections (e.g., by function or process step).
    Returns a dict section_name -> list of equipment IDs.
    """
    # Example: Group by substring in Description or a custom CSV field
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

# Optional: For more advanced layouts, you can implement topological sorting,
# handle loops/branches, or use the networkx package for graph traversal.
# This basic setup will work for most straightforward process P&IDs.
