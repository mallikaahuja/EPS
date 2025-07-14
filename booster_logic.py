# booster_logic.py

def evaluate_booster_requirements(
    flow_rate,
    pressure,
    process_vapor_type,
    contamination_sensitive,
    primary_pump_type,
    automation_level,
):
    """
    Decides if a booster is required and what configuration it needs.
    """

    booster_needed = False
    warnings = []
    booster_config = {
        "enabled": False,
        "requires_purge": False,
        "requires_cooling": False,
        "is_oil_free": True,
        "compatible_with_primary": True,
        "requires_vfd": False,
        "requires_bypass": False,
        "automation_ready": False
    }

    # Rule 1: Booster recommended if high flow and deep vacuum
    if flow_rate > 1000 and pressure < 10:
        booster_needed = True
        booster_config["enabled"] = True

    # Rule 2: Check primary pump compatibility
    compatible_pairs = {
        "Dry Screw Vacuum Pump": True,
        "Liquid Ring Vacuum Pump": True,
        "Rotary Vane Vacuum Pump": False
    }
    booster_config["compatible_with_primary"] = compatible_pairs.get(primary_pump_type, False)
    if not booster_config["compatible_with_primary"]:
        warnings.append(f"⚠️ Booster not compatible with selected primary pump: {primary_pump_type}")

    # Rule 3: Process vapor check
    if process_vapor_type in ["corrosive", "condensable"]:
        booster_config["requires_purge"] = True
        booster_config["requires_cooling"] = True

    # Rule 4: Seal/lubrication type
    if contamination_sensitive:
        booster_config["is_oil_free"] = True
    else:
        booster_config["is_oil_free"] = False

    # Rule 5: Pressure match (validation)
    if pressure > 100:
        booster_config["enabled"] = False
        warnings.append("⚠️ Booster not recommended at rough vacuum (>100 mbar)")

    # Rule 6: Safety features
    booster_config["requires_vfd"] = True
    booster_config["requires_bypass"] = True

    # Rule 7: Automation integration
    if automation_level.lower() in ["plc", "scada", "full"]:
        booster_config["automation_ready"] = True

    return booster_config, warnings
