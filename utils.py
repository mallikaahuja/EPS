def merge_layout_hints(equipment_df, enhanced_layout_df):
    # Normalize column names to lowercase for consistent merging
    equipment_df = equipment_df.rename(columns=lambda x: x.strip().lower())
    enhanced_layout_df = enhanced_layout_df.rename(columns=lambda x: x.strip().lower())

    # Merge on 'id' column now that both are lowercase
    merged = pd.merge(equipment_df, enhanced_layout_df, on="id", how="left")

    # Restore original casing if needed downstream
    merged = merged.rename(columns={"id": "ID"})
    return merged
