# process_mapper.py

import pandas as pd
import networkx as nx

def get_src_dst(row):
    """Robust source-destination detection from various pipeline column names."""
    src = row.get("Source") or row.get("Start") or row.get("From") or row.get("ID")
    dst = row.get("Destination") or row.get("End") or row.get("To")
    return src, dst

def auto_sequence(equipment_df, pipeline_df):
    """Topological sequencing of equipment using connection graph."""
    G = nx.DiGraph()
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if src and dst:
            G.add_edge(src, dst)

    try:
        ordered = list(nx.topological_sort(G))
        return ordered
    except nx.NetworkXUnfeasible:
        # Fall back to linear order if cycles exist
        return list(equipment_df["ID"])

def detect_process_flow(equipment_df, pipeline_df):
    """Returns a dict of source → destination mapping (process flow)."""
    flow_map = {}
    for _, row in pipeline_df.iterrows():
        src, dst = get_src_dst(row)
        if src and dst:
            if src not in flow_map:
                flow_map[src] = []
            flow_map[src].append(dst)
    return flow_map

def get_equipment_type_map(equipment_df):
    """Returns ID → Type/Description map from equipment."""
    id_type = {}
    for _, row in equipment_df.iterrows():
        eq_id = row["ID"]
        eq_type = row.get("type") or row.get("Type") or row.get("Description", "")
        id_type[eq_id] = eq_type
    return id_type

def group_equipment_by_section(equipment_df, pipeline_df):
    """Groups components into logical sections based on type or tag pattern."""
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
        elif "compressor" in desc:
            section = "Compressors"
        elif "panel" in desc:
            section = "Control Panels"

        if section not in groups:
            groups[section] = []
        groups[section].append(row["ID"])

    return groups

def extract_control_candidates(equipment_df):
    """Returns instruments, controllers, and control valves from equipment using ISA patterns."""
    control_blocks = {
        "transmitters": [],
        "controllers": [],
        "valves": []
    }

    for _, row in equipment_df.iterrows():
        tag = row.get("ID", "")
        isa = str(row.get("isa_code", "")).upper()

        if isa.startswith("PT") or isa.startswith("TT") or isa.startswith("LT") or isa.startswith("FT"):
            control_blocks["transmitters"].append(tag)
        elif "IC" in isa or "TC" in isa or "PC" in isa or "LC" in isa:
            control_blocks["controllers"].append(tag)
        elif "V" in isa or isa.endswith("V"):
            control_blocks["valves"].append(tag)

    return control_blocks
