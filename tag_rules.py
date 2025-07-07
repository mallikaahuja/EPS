def next_tag(type_name, tag_counts, isa_config):
    prefix = isa_config.get(type_name, {}).get("tag_prefix", type_name[:2].upper())
    tag_counts.setdefault(prefix, 1)
    tag = f"{prefix}-{tag_counts[prefix]:03d}"
    tag_counts[prefix] += 1
    return tag
