# advanced_rendering.py

class ProfessionalRenderer:
    """Enhanced renderer for professional P&ID output"""

    def __init__(self, booster_config=None):
        self.drawing_scale = 1.0
        self.line_weights = {
            'major_process': 3.0,
            'minor_process': 2.0,
            'utility': 2.0,
            'instrument_signal': 0.7,
            'electrical': 0.7,
            'border': 2.0,
            'equipment': 2.5,
            'text': 0.5
        }
        self.booster_config = booster_config or {}

    def render_professional_pnid(self, components, pipes, width=1600, height=1200):
        """Main rendering function for professional P&ID"""

        svg_parts = []

        # --- SVG Header ---
        svg_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
xmlns="http://www.w3.org/2000/svg" version="1.1"
style="font-family: Arial, sans-serif; background-color: white">''')

        # --- Draw Grid Outline (optional) ---
        svg_parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="gray" stroke-dasharray="10,5"/>')

        # --- Draw Components (simple placeholders) ---
        for idx, comp in enumerate(components):
            x = 100 + (idx % 4) * 300
            y = 100 + (idx // 4) * 200

            svg_parts.append(f'<rect x="{x}" y="{y}" width="100" height="60" fill="#f4f4f4" stroke="black" stroke-width="2"/>')
            svg_parts.append(f'<text x="{x+10}" y="{y+30}" font-size="12">{comp}</text>')

        # --- BOOSTER SECTION ---
        if "mechanical_vacuum_booster" in components and self.booster_config.get("enabled"):
            x, y = 600, 300  # Booster block position

            # Booster base block
            svg_parts.append(f'<rect x="{x}" y="{y}" width="120" height="60" fill="#EEE" stroke="black" stroke-width="2"/>')
            svg_parts.append(f'<text x="{x+10}" y="{y+20}" font-size="12">Booster</text>')

            # Purge port
            if self.booster_config.get("requires_purge"):
                svg_parts.append(f'<circle cx="{x+60}" cy="{y-10}" r="4" fill="blue"/>')
                svg_parts.append(f'<text x="{x+65}" y="{y-5}" font-size="10">Purge</text>')

            # Cooling ports
            if self.booster_config.get("requires_cooling"):
                svg_parts.append(f'<circle cx="{x+10}" cy="{y+30}" r="4" fill="lightblue"/>')
                svg_parts.append(f'<circle cx="{x+110}" cy="{y+30}" r="4" fill="lightblue"/>')
                svg_parts.append(f'<text x="{x+15}" y="{y+45}" font-size="10">CW In</text>')
                svg_parts.append(f'<text x="{x+70}" y="{y+45}" font-size="10">CW Out</text>')

            # Automation/safety overlays
            overlay_y = y + 55
            if self.booster_config.get("automation_ready"):
                svg_parts.append(f'<text x="{x+10}" y="{overlay_y}" font-size="10" fill="green">PLC Ready</text>')
                overlay_y += 12
            if self.booster_config.get("requires_vfd"):
                svg_parts.append(f'<text x="{x+10}" y="{overlay_y}" font-size="10" fill="orange">VFD</text>')

        # --- SVG Footer ---
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)
