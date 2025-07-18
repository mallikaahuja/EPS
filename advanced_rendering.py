"""
Advanced P&ID Rendering Engine
Professional-quality rendering with detailed symbols, annotations, and layout
"""

import math
from typing import List, Tuple, Dict, Optional
import numpy as np

class ProfessionalRenderer:
    """Enhanced renderer for professional P&ID output"""

    def __init__(self):
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
        
    def render_professional_pnid(self, components, pipes, width=1600, height=1200):
        """Main rendering function for professional P&ID"""
        
        svg_parts = []
        
        # Start SVG with professional settings
        svg_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
xmlns="http://www.w3.org/2000/svg" version="1.1"
style="font-family: Arial, sans-serif; background-color: white;">''')

        # Add comprehensive definitions
        svg_parts.append(self._create_definitions())
        
        # Add layers in correct order
        svg_parts.append('<g id="grid-layer" opacity="0.3">')
        svg_parts.append(self._create_grid(width, height))
        svg_parts.append('</g>')
        
        svg_parts.append('<g id="border-layer">')
        svg_parts.append(self._create_drawing_border(width, height))
        svg_parts.append('</g>')
        
        svg_parts.append('<g id="equipment-layer">')
        for comp in components.values():
            svg_parts.append(self._render_component(comp))
        svg_parts.append('</g>')
        
        svg_parts.append('<g id="piping-layer">')
        for pipe in pipes:
            svg_parts.append(self._render_pipe(pipe))
        svg_parts.append('</g>')
        
        svg_parts.append('<g id="annotation-layer">')
        svg_parts.append(self._add_annotations(components, pipes))
        svg_parts.append('</g>')
        
        svg_parts.append('<g id="title-block-layer">')
        svg_parts.append(self._create_title_block(width, height))
        svg_parts.append('</g>')
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)

    def _create_definitions(self):
        """Create comprehensive SVG definitions"""
        return '''<defs>
    <pattern id="hatch45" patternUnits="userSpaceOnUse" width="4" height="4">
        <path d="M 0,4 L 4,0" stroke="#666" stroke-width="0.5"/>
    </pattern>

    <pattern id="crosshatch" patternUnits="userSpaceOnUse" width="4" height="4">
        <path d="M 0,4 L 4,0 M 0,0 L 4,4" stroke="#666" stroke-width="0.5"/>
    </pattern>

    <linearGradient id="metalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
        <stop offset="50%" style="stop-color:#e0e0e0;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#b0b0b0;stop-opacity:1" />
    </linearGradient>

    <radialGradient id="buttonGradient">
        <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#cccccc;stop-opacity:1" />
    </radialGradient>

    <filter id="dropShadow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
        <feOffset dx="2" dy="2" result="offsetblur"/>
        <feComponentTransfer>
            <feFuncA type="linear" slope="0.3"/>
        </feComponentTransfer>
        <feMerge>
            <feMergeNode/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>

    <marker id="arrow-process" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto" markerUnits="strokeWidth">
        <path d="M 0,0 L 12,6 L 0,12 L 3,6 Z" fill="black"/>
    </marker>

    <marker id="arrow-signal" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
        <path d="M 0,0 L 10,5 L 0,10" fill="none" stroke="black" stroke-width="1"/>
    </marker>

    <marker id="dim-arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto">
        <path d="M 0,0 L 5,5 L 0,10" fill="none" stroke="black" stroke-width="1"/>
    </marker>
</defs>'''

    def _create_grid(self, width, height):
        """Create construction grid"""
        grid_svg = []
        
        # Major grid lines every 100 units
        for x in range(0, width, 100):
            grid_svg.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#cccccc" stroke-width="0.5"/>')
        for y in range(0, height, 100):
            grid_svg.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#cccccc" stroke-width="0.5"/>')
        
        # Minor grid lines every 25 units
        for x in range(0, width, 25):
            if x % 100 != 0:
                grid_svg.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#eeeeee" stroke-width="0.25"/>')
        for y in range(0, height, 25):
            if y % 100 != 0:
                grid_svg.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#eeeeee" stroke-width="0.25"/>')
        
        return ''.join(grid_svg)

    def _create_drawing_border(self, width, height):
        """Create professional drawing border with zones"""
        border_svg = []
        
        # Outer border
        border_svg.append(f'<rect x="10" y="10" width="{width-20}" height="{height-20}" '
                         f'fill="none" stroke="black" stroke-width="{self.line_weights["border"]}"/>')
        
        # Inner border
        border_svg.append(f'<rect x="20" y="20" width="{width-40}" height="{height-40}" '
                         f'fill="none" stroke="black" stroke-width="1"/>')
        
        # Zone markers (A-Z horizontally, 1-20 vertically)
        zone_width = (width - 40) / 10
        zone_height = (height - 40) / 10
        
        for i in range(10):
            # Top markers
            x = 20 + i * zone_width + zone_width / 2
            letter = chr(65 + i)  # A-J
            border_svg.append(f'<text x="{x}" y="15" text-anchor="middle" font-size="10">{letter}</text>')
            # Bottom markers
            border_svg.append(f'<text x="{x}" y="{height-5}" text-anchor="middle" font-size="10">{letter}</text>')
            
            # Left markers
            y = 20 + i * zone_height + zone_height / 2
            border_svg.append(f'<text x="15" y="{y+3}" text-anchor="middle" font-size="10">{i+1}</text>')
            # Right markers
            border_svg.append(f'<text x="{width-15}" y="{y+3}" text-anchor="middle" font-size="10">{i+1}</text>')
        
        return ''.join(border_svg)

    def _render_component(self, component):
        """Render component with professional details"""
        from professional_symbols import get_component_symbol, create_professional_instrument_bubble
        
        if component.is_instrument:
            return create_professional_instrument_bubble(
                component.tag, 
                component.x + component.width/2, 
                component.y + component.height/2
            )
        
        # Get professional symbol
        symbol = get_component_symbol(component.component_type)
        if not symbol:
            # Fallback to basic shape
            return self._render_basic_component(component)
        
        # Apply transformations
        transform = f'translate({component.x},{component.y})'
        if component.rotation:
            cx = component.width / 2
            cy = component.height / 2
            transform += f' rotate({component.rotation},{cx},{cy})'
        
        svg = f'<g transform="{transform}" class="component-{component.id}">'
        
        # Add shadow for 3D effect on major equipment
        if component.component_type in ['pump_centrifugal', 'vessel_vertical', 'heat_exchanger']:
            svg += f'<g filter="url(#dropShadow)">'
        
        # Scale the symbol to fit
        svg += f'<g transform="scale({component.width/80},{component.height/80})">'
        svg += symbol
        svg += '</g>'
        
        if component.component_type in ['pump_centrifugal', 'vessel_vertical', 'heat_exchanger']:
            svg += '</g>'
        
        # Add tag label with background
        if component.tag:
            tag_y = component.height + 15
            text_width = len(component.tag) * 8
            
            # Tag background
            svg += f'<rect x="{component.width/2 - text_width/2 - 2}" y="{tag_y - 12}" '
            svg += f'width="{text_width + 4}" height="16" fill="white" stroke="black" stroke-width="0.5"/>'
            
            # Tag text
            svg += f'<text x="{component.width/2}" y="{tag_y}" text-anchor="middle" '
            svg += f'font-size="11" font-weight="bold">{component.tag}</text>'
        
        svg += '</g>'
        return svg

    def _render_pipe(self, pipe):
        """Render pipe with professional quality"""
        if len(pipe.points) < 2:
            return ''
        
        # Determine line weight based on pipe size
        line_weight = self._get_line_weight_from_spec(pipe.label)
        
        # Create smooth path with proper corners
        path = self._create_smooth_pipe_path(pipe.points)
        
        # Line style based on type
        stroke_style = self._get_stroke_style(pipe.line_type)
        
        svg = f'<g class="pipe-{pipe.id}">'
        
        # Shadow for major process lines
        if pipe.line_type == 'process' and line_weight > 2:
            svg += f'<path d="{path}" fill="none" stroke="#cccccc" '
            svg += f'stroke-width="{line_weight + 1}" stroke-linejoin="round" '
            svg += f'stroke-linecap="round" opacity="0.3" '
            svg += f'transform="translate(1,1)"/>'
        
        # Main pipe
        svg += f'<path d="{path}" fill="none" stroke="{stroke_style["color"]}" '
        svg += f'stroke-width="{line_weight}" stroke-linejoin="round" '
        svg += f'stroke-linecap="round"'
        
        if stroke_style.get('dash'):
            svg += f' stroke-dasharray="{stroke_style["dash"]}"'
        
        if pipe.with_arrow:
            svg += ' marker-end="url(#arrow-process)"'
        
        svg += '/>'
        
        # Add pipe specification label
        if pipe.label:
            svg += self._add_pipe_label(pipe.points, pipe.label)
        
        svg += '</g>'
        return svg

    def _create_smooth_pipe_path(self, points):
        """Create smooth path with rounded corners"""
        if len(points) < 2:
            return ''
        
        # Start path
        path = f'M {points[0][0]},{points[0][1]}'
        
        # Add line segments with rounded corners
        for i in range(1, len(points) - 1):
            prev = points[i-1]
            curr = points[i]
            next_pt = points[i+1]
            
            # Calculate corner radius based on angle
            radius = self._calculate_corner_radius(prev, curr, next_pt)
            
            if radius > 0:
                # Create rounded corner
                path += self._create_rounded_corner(prev, curr, next_pt, radius)
            else:
                # Sharp corner
                path += f' L {curr[0]},{curr[1]}'
        
        # Last point
        path += f' L {points[-1][0]},{points[-1][1]}'
        
        return path

    def _calculate_corner_radius(self, p1, p2, p3):
        """Calculate appropriate corner radius based on angle"""
        # Calculate angle between line segments
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Skip if points are too close
        if math.sqrt(v1[0]**2 + v1[1]**2) < 10 or math.sqrt(v2[0]**2 + v2[1]**2) < 10:
            return 0
        
        # Calculate angle
        angle = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
        angle = abs(angle)
        
        # Use larger radius for 90-degree turns
        if abs(angle - math.pi/2) < 0.1 or abs(angle - 3*math.pi/2) < 0.1:
            return 10
        else:
            return 5

    def _create_rounded_corner(self, p1, p2, p3, radius):
        """Create SVG path for rounded corner"""
        # This is simplified - full implementation would calculate proper arc
        return f' L {p2[0]},{p2[1]}'

    def _get_line_weight_from_spec(self, spec):
        """Determine line weight from pipe specification"""
        if not spec:
            return 2
        
        # Extract size from spec (e.g., "2"-PG-101-CS" -> 2 inch)
        import re
        match = re.match(r'^(\d+)"', spec)
        if match:
            size = int(match.group(1))
            # Scale line weight with pipe size
            if size <= 1:
                return 1.5
            elif size <= 2:
                return 2
            elif size <= 4:
                return 2.5
            elif size <= 6:
                return 3
            else:
                return 3.5
        
        return 2

    def _get_stroke_style(self, line_type):
        """Get stroke style for line type"""
        styles = {
            'process': {'color': '#000000', 'dash': None},
            'process_line': {'color': '#000000', 'dash': None},
            'instrumentation': {'color': '#000000', 'dash': '5,3'},
            'instrument_signal': {'color': '#000000', 'dash': '5,3'},
            'electrical': {'color': '#000000', 'dash': '2,2'},
            'pneumatic': {'color': '#000000', 'dash': '8,2,2,2'},
            'hydraulic': {'color': '#000000', 'dash': '10,3,3,3'},
        }
        
        return styles.get(line_type, styles['process'])

    def _add_pipe_label(self, points, label):
        """Add pipe specification label"""
        if len(points) < 2:
            return ''
        
        # Find best position for label (middle of longest segment)
        longest_segment = 0
        longest_idx = 0
        
        for i in range(len(points) - 1):
            length = math.sqrt(
                (points[i+1][0] - points[i][0])**2 + 
                (points[i+1][1] - points[i][1])**2
            )
            if length > longest_segment:
                longest_segment = length
                longest_idx = i
        
        # Calculate label position
        p1 = points[longest_idx]
        p2 = points[longest_idx + 1]
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        
        # Calculate angle for text rotation
        angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
        if angle > 90 or angle < -90:
            angle += 180
        
        # Create label with background
        text_width = len(label) * 7
        text_height = 14
        
        svg = f'<g transform="translate({mid_x},{mid_y}) rotate({angle})">'
        
        # Background
        svg += f'<rect x="{-text_width/2 - 2}" y="-8" width="{text_width + 4}" height="{text_height}" '
        svg += f'fill="white" stroke="none"/>'
        
        # Text
        svg += f'<text x="0" y="3" text-anchor="middle" font-size="10" '
        svg += f'font-family="Arial, sans-serif">{label}</text>'
        
        svg += '</g>'
        return svg

    def _add_annotations(self, components, pipes):
        """Add technical annotations and dimensions"""
        annotations = []
        
        # Add flow direction indicators
        for pipe in pipes:
            if pipe.line_type == 'process' and len(pipe.points) >= 2:
                # Add flow arrows along the pipe
                for i in range(0, len(pipe.points) - 1, 3):
                    if i + 1 < len(pipe.points):
                        p1 = pipe.points[i]
                        p2 = pipe.points[i + 1]
                        mid_x = (p1[0] + p2[0]) / 2
                        mid_y = (p1[1] + p2[1]) / 2
                        
                        angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
                        
                        annotations.append(
                            f'<path d="M {mid_x},{mid_y} l 5,0" '
                            f'transform="rotate({angle} {mid_x} {mid_y})" '
                            f'stroke="black" stroke-width="1.5" '
                            f'marker-end="url(#arrow-signal)"/>'
                        )
        
        # Add equipment callouts
        for comp in components.values():
            if comp.component_type in ['pump_centrifugal', 'heat_exchanger', 'vessel_vertical']:
                # Add callout line and text
                callout_x = comp.x + comp.width + 20
                callout_y = comp.y + comp.height / 2
                
                annotations.append(
                    f'<line x1="{comp.x + comp.width}" y1="{comp.y + comp.height/2}" '
                    f'x2="{callout_x}" y2="{callout_y}" '
                    f'stroke="black" stroke-width="0.5" stroke-dasharray="2,2"/>'
                )
                
                # Add equipment data
                if comp.component_type == 'pump_centrifugal':
                    annotations.append(
                        f'<text x="{callout_x + 5}" y="{callout_y - 5}" font-size="8">'
                        f'Flow: 100 GPM</text>'
                    )
                    annotations.append(
                        f'<text x="{callout_x + 5}" y="{callout_y + 5}" font-size="8">'
                        f'Head: 50 ft</text>'
                    )
        
        return ''.join(annotations)

    def _create_title_block(self, width, height):
        """Create detailed title block"""
        tb_width = 594  # A4 width in landscape
        tb_height = 180
        tb_x = width - tb_width - 30
        tb_y = height - tb_height - 30
        
        title_block = f'<g transform="translate({tb_x},{tb_y})">'
        
        # Main border
        title_block += f'<rect x="0" y="0" width="{tb_width}" height="{tb_height}" '
        title_block += f'fill="white" stroke="black" stroke-width="2"/>'
        
        # Grid lines
        divisions = [40, 80, 120, 140, 160]
        for y in divisions:
            title_block += f'<line x1="0" y1="{y}" x2="{tb_width}" y2="{y}" '
            title_block += f'stroke="black" stroke-width="1"/>'
        
        # Vertical divisions
        title_block += f'<line x1="200" y1="0" x2="200" y2="140" stroke="black" stroke-width="1"/>'
        title_block += f'<line x1="400" y1="0" x2="400" y2="140" stroke="black" stroke-width="1"/>'
        
        # Company logo area
        title_block += f'<rect x="10" y="10" width="180" height="60" fill="none" stroke="black" stroke-width="0.5"/>'
        title_block += f'<text x="100" y="45" text-anchor="middle" font-size="20" font-weight="bold">EPS</text>'
        
        # Project title
        title_block += f'<text x="300" y="30" text-anchor="middle" font-size="16" font-weight="bold">PIPING AND INSTRUMENTATION DIAGRAM</text>'
        title_block += f'<text x="300" y="50" text-anchor="middle" font-size="12">SUCTION FILTER + KDP-330</text>'
        
        # Drawing details
        fields = [
            ("DWG NO:", "EPSPL-V2526-TP-01", 210, 90),
            ("REV:", "0", 420, 90),
            ("DATE:", "2024-01-15", 210, 110),
            ("SCALE:", "1:1", 420, 110),
            ("DRAWN:", "ABC", 210, 130),
            ("CHECKED:", "XYZ", 420, 130),
        ]
        
        for label, value, x, y in fields:
            title_block += f'<text x="{x}" y="{y}" font-size="10">{label}</text>'
            title_block += f'<text x="{x + 60}" y="{y}" font-size="10" font-weight="bold">{value}</text>'
        
        # Notes section
        title_block += f'<text x="10" y="{tb_height - 15}" font-size="8">NOTES:</text>'
        title_block += f'<text x="10" y="{tb_height - 5}" font-size="8">1. ALL DIMENSIONS IN MM UNLESS NOTED OTHERWISE</text>'
        
        title_block += '</g>'
        return title_block

# Specialized equipment templates matching reference

def create_suction_filter_system():
    """Create a suction filter system matching the reference P&ID"""
    components = []
    pipes = []

    # Main equipment positions (matching reference layout)
    equipment = [
        # Suction filter
        {'id': 'F-001', 'tag': 'F-001', 'Component': 'filter', 
         'x': 300, 'y': 200, 'Width': 80, 'Height': 120, 'rotation': 0},
        
        # Pump
        {'id': 'P-001', 'tag': 'KDP-330', 'Component': 'pump_centrifugal', 
         'x': 500, 'y': 250, 'Width': 80, 'Height': 80, 'rotation': 0},
        
        # Gate valves
        {'id': 'V-001', 'tag': 'V-001', 'Component': 'valve_gate', 
         'x': 200, 'y': 240, 'Width': 60, 'Height': 80, 'rotation': 0},
        
        {'id': 'V-002', 'tag': 'V-002', 'Component': 'valve_gate', 
         'x': 620, 'y': 260, 'Width': 60, 'Height': 80, 'rotation': 0},
        
        # Pressure relief valve
        {'id': 'PSV-001', 'tag': 'PSV-001', 'Component': 'psv', 
         'x': 380, 'y': 150, 'Width': 40, 'Height': 60, 'rotation': 0},
        
        # Drain valve
        {'id': 'V-003', 'tag': 'V-003', 'Component': 'valve_gate', 
         'x': 300, 'y': 350, 'Width': 40, 'Height': 60, 'rotation': 0},
        
        # Expansion bellows
        {'id': 'EB-001', 'tag': 'EB-001', 'Component': 'expansion_joint', 
         'x': 150, 'y': 245, 'Width': 40, 'Height': 30, 'rotation': 0},
        
        # Control panel
        {'id': 'CP-001', 'tag': 'CP-001', 'Component': 'control_panel', 
         'x': 800, 'y': 100, 'Width': 120, 'Height': 160, 'rotation': 0},
        
        # Motor
        {'id': 'M-001', 'tag': 'M-001', 'Component': 'motor', 
         'x': 500, 'y': 150, 'Width': 80, 'Height': 80, 'rotation': 0},
    ]

    # Instrumentation
    instruments = [
        # Pressure transmitters
        {'id': 'PT-001', 'tag': 'PT-001', 'Component': 'instrument', 
         'x': 350, 'y': 300, 'Width': 44, 'Height': 44},
        
        {'id': 'PT-002', 'tag': 'PT-002', 'Component': 'instrument', 
         'x': 550, 'y': 320, 'Width': 44, 'Height': 44},
        
        # Pressure indicators
        {'id': 'PI-001', 'tag': 'PI-001', 'Component': 'instrument', 
         'x': 250, 'y': 200, 'Width': 44, 'Height': 44},
        
        {'id': 'PI-002', 'tag': 'PI-002', 'Component': 'instrument', 
         'x': 650, 'y': 280, 'Width': 44, 'Height': 44},
        
        # Temperature indicators
        {'id': 'TI-001', 'tag': 'TI-001', 'Component': 'instrument', 
         'x': 450, 'y': 220, 'Width': 44, 'Height': 44},
        
        # Flow indicator
        {'id': 'FI-001', 'tag': 'FI-001', 'Component': 'instrument', 
         'x': 700, 'y': 290, 'Width': 44, 'Height': 44},
        
        # Level switches
        {'id': 'LSH-001', 'tag': 'LSH-001', 'Component': 'instrument', 
         'x': 340, 'y': 180, 'Width': 44, 'Height': 44},
        
        {'id': 'LSL-001', 'tag': 'LSL-001', 'Component': 'instrument', 
         'x': 340, 'y': 260, 'Width': 44, 'Height': 44},
    ]

    # Add rotation to instruments
    for inst in instruments:
        inst['rotation'] = 0

    components.extend(equipment)
    components.extend(instruments)

    # Process piping
    process_pipes = [
        # Inlet piping
        {'Pipe No.': 'L-001', 'Label': '6"-PS-001-CS', 
         'From Component': 'INLET', 'From Port': 'outlet', 
         'To Component': 'EB-001', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(50, 260), (150, 260)]',
         'pipe_type': 'process_line'},
        
        {'Pipe No.': 'L-002', 'Label': '6"-PS-002-CS', 
         'From Component': 'EB-001', 'From Port': 'outlet', 
         'To Component': 'V-001', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(190, 260), (200, 260)]',
         'pipe_type': 'process_line'},
        
        {'Pipe No.': 'L-003', 'Label': '6"-PS-003-CS', 
         'From Component': 'V-001', 'From Port': 'outlet', 
         'To Component': 'F-001', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(260, 260), (300, 260)]',
         'pipe_type': 'process_line'},
        
        # Filter to pump
        {'Pipe No.': 'L-004', 'Label': '6"-PS-004-CS', 
         'From Component': 'F-001', 'From Port': 'outlet', 
         'To Component': 'P-001', 'To Port': 'suction',
         'Polyline Points (x, y)': '[(380, 260), (420, 260), (420, 290), (500, 290)]',
         'pipe_type': 'process_line'},
        
        # Pump discharge
        {'Pipe No.': 'L-005', 'Label': '4"-PD-005-CS', 
         'From Component': 'P-001', 'From Port': 'discharge', 
         'To Component': 'V-002', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(540, 250), (540, 300), (620, 300)]',
         'pipe_type': 'process_line'},
        
        {'Pipe No.': 'L-006', 'Label': '4"-PD-006-CS', 
         'From Component': 'V-002', 'From Port': 'outlet', 
         'To Component': 'OUTLET', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(680, 300), (750, 300)]',
         'pipe_type': 'process_line'},
        
        # Relief line
        {'Pipe No.': 'L-007', 'Label': '2"-PR-007-CS', 
         'From Component': 'F-001', 'From Port': 'top', 
         'To Component': 'PSV-001', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(340, 200), (340, 180), (380, 180)]',
         'pipe_type': 'process_line'},
        
        # Drain line
        {'Pipe No.': 'L-008', 'Label': '2"-DR-008-CS', 
         'From Component': 'F-001', 'From Port': 'bottom', 
         'To Component': 'V-003', 'To Port': 'inlet',
         'Polyline Points (x, y)': '[(340, 320), (340, 350)]',
         'pipe_type': 'process_line'},
    ]

    # Control wiring
    control_pipes = [
        # Motor control
        {'Pipe No.': 'EC-001', 'Label': '', 
         'From Component': 'CP-001', 'From Port': 'bottom', 
         'To Component': 'M-001', 'To Port': 'top',
         'Polyline Points (x, y)': '[(860, 260), (860, 340), (540, 340), (540, 150)]',
         'pipe_type': 'electrical'},
        
        # Pressure transmitter signals
        {'Pipe No.': 'IS-001', 'Label': '', 
         'From Component': 'PT-001', 'From Port': 'right', 
         'To Component': 'CP-001', 'To Port': 'left',
         'Polyline Points (x, y)': '[(394, 322), (750, 322), (750, 180), (800, 180)]',
         'pipe_type': 'instrumentation'},
        
        {'Pipe No.': 'IS-002', 'Label': '', 
         'From Component': 'PT-002', 'From Port': 'right', 
         'To Component': 'CP-001', 'To Port': 'left',
         'Polyline Points (x, y)': '[(594, 342), (750, 342), (750, 200), (800, 200)]',
         'pipe_type': 'instrumentation'},
        
        # Level switches
        {'Pipe No.': 'IS-003', 'Label': '', 
         'From Component': 'LSH-001', 'From Port': 'right', 
         'To Component': 'CP-001', 'To Port': 'left',
         'Polyline Points (x, y)': '[(384, 202), (750, 202), (750, 140), (800, 140)]',
         'pipe_type': 'instrumentation'},
        
        {'Pipe No.': 'IS-004', 'Label': '', 
         'From Component': 'LSL-001', 'From Port': 'right', 
         'To Component': 'CP-001', 'To Port': 'left',
         'Polyline Points (x, y)': '[(384, 282), (750, 282), (750, 160), (800, 160)]',
         'pipe_type': 'instrumentation'},
    ]

    pipes.extend(process_pipes)
    pipes.extend(control_pipes)

    return components, pipes
