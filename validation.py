def validate_pid(equipment_df, pipeline_df, positions, pipelines):
    errors = []
    all_equipment = set(equipment_df["ID"])
    pipeline_src = set(pipe["src"] for pipe in pipelines)
    pipeline_dst = set(pipe["dst"] for pipe in pipelines)
    unconnected = all_equipment - (pipeline_src | pipeline_dst)
    if unconnected:
        errors.append(f"Unconnected equipment: {', '.join(unconnected)}")
    # Check for floating inline components
    # Check for flow continuity/cycles etc as needed
    return errors
