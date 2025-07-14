# process_mapper.py

def map_process_to_eps_products(industry, flow_rate, pressure, application, compliance):
    """
    Returns a list of recommended EPS systems based on customer input.
    """

    # Normalize inputs
    industry = industry.lower()
    application = application.lower()
    compliance = [c.lower() for c in compliance]

    recommendations = []

    # Flow tiers (in m³/h or l/h depending on system)
    def is_low_flow(val): return val < 100
    def is_medium_flow(val): return 100 <= val <= 1000
    def is_high_flow(val): return val > 1000

    # Vacuum range (mbar)
    def is_deep_vacuum(p): return p < 10
    def is_medium_vacuum(p): return 10 <= p < 100
    def is_rough_vacuum(p): return p >= 100

    # Main product logic
    if "drying" in application or "solvent" in application or "distillation" in application:
        if is_deep_vacuum(pressure):
            recommendations.append("Dry Screw Vacuum Pump")
            if is_high_flow(flow_rate):
                recommendations.append("Mechanical Vacuum Booster")
        elif is_medium_vacuum(pressure):
            recommendations.append("Liquid Ring Vacuum Pump")
        elif is_rough_vacuum(pressure):
            recommendations.append("Rotary Vane Vacuum Pump")

    elif "evaporation" in application or "concentration" in application:
        if is_high_flow(flow_rate):
            recommendations.append("Multi Effect Evaporator (MEE)")
        elif is_medium_flow(flow_rate):
            recommendations.append("Agitated Thin Film Evaporator (ATFE)")
        else:
            recommendations.append("Short Path Distillation Unit (SPDU)")

    elif "filtration" in application:
        recommendations.append("Agitated Nutsche Filter Dryer")

    elif "packaging" in application:
        recommendations.append("Rotary Vane Vacuum Pump")
        recommendations.append("Beverage Processing & Packaging Lines")

    elif "effluent" in application or "waste" in industry:
        recommendations.append("Effluent Treatment/ZLD Systems")
        if is_high_flow(flow_rate):
            recommendations.append("Twin Lobe Root Air Blower")

    # Add compliance-sensitive filters
    if "pharma" in industry or "food" in industry:
        if "dry screw vacuum pump" not in recommendations:
            recommendations.insert(0, "Dry Screw Vacuum Pump")
        if "rotary vane vacuum pump" in recommendations and "cGMP" in compliance:
            recommendations = [r for r in recommendations if r != "Rotary Vane Vacuum Pump"]
            recommendations.insert(0, "Dry Screw Vacuum Pump")

    # Always include control/automation optionally
    recommendations.append("Control Panels, Automation, Spares")

    # Deduplicate while preserving order
    seen = set()
    final = []
    for r in recommendations:
        if r not in seen:
            final.append(r)
            seen.add(r)

    return final
