def merge_layout_hints(equipment_df, enhanced_layout_df):
    # Merge layout hints by equipment ID (e.g., X_hint, Y_hint, orientation, etc.)
    return equipment_df.merge(enhanced_layout_df, on="ID", how="left")
