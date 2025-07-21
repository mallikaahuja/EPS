import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import cairosvg
from io import BytesIO
import base64
import re
import ezdxf
from reportlab.lib.pagesizes import A1
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

# This is a placeholder for your actual symbol manager.
# You would need to implement this class separately.
from symbol_library_manager import SymbolLibraryManager, Symbol


@dataclass
class LayoutNode:
    """Represents a component in the layout"""
    id: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0
    symbol: Optional[Symbol] = None


class IndustryStandardRenderer:
    """Renders P&ID using industry-standard symbols and layout"""

    # Standard drawing sizes (mm)
    DRAWING_SIZES = {
        "A1": (841, 594),
        "A0": (1189, 841),
        "ANSI_D": (864, 559),
        "ANSI_E": (1118, 864)
    }

    def __init__(self, symbol_manager: SymbolLibraryManager = None):
        """Initialize renderer with symbol manager"""
        self.symbol_manager = symbol_manager or SymbolLibraryManager()
        self.layout_nodes = {}
        self.connections = []
        self.drawing_size = "A1"
        self.scale = 1.0

    def render_from_dsl(self, dsl_data: Dict, drawing_size: str = "A1") -> str:
        """Render P&ID from DSL data"""
        self.drawing_size = drawing_size
        
        # 1. Process connections first to make them available for layout optimization
        self._process_connections(dsl_data['connections'])
        
        # 2. Layout components on the grid
        self._layout_components(dsl_data['components'])
        
        # 3. Optimize the layout based on connections
        self._optimize_layout()
        
        # 4. Generate the final SVG
        svg = self._generate_svg(dsl_data)
        
        return svg

    def _layout_components(self, components: List[Dict]):
        """Layout components using industry-standard spacing"""
        # Group components by type for organized layout
        grouped = self._group_components_by_type(components)
        
        # Use grid-based layout with standard spacing
        grid_spacing_x = 150  # mm
        grid_spacing_y = 120  # mm
        margin = 50  # mm
        
        current_x = margin
        current_y = margin
        
        # Layout order following process flow
        layout_order = [
            "vessel", "pump", "compressor", "heat_exchanger",
            "valve", "instrument", "filter", "other"
        ]
        
        for group_type in layout_order:
            if group_type in grouped:
                for component in grouped[group_type]:
                    # Get symbol for component
                    symbol = self.symbol_manager.get_symbol(
                        component['type'],
                        component.get('subtype')
                    )
                    
                    # Create layout node
                    node = LayoutNode(
                        id=component['id'],
                        x=current_x,
                        y=current_y,
                        width=60,  # Standard symbol size
                        height=60,
                        symbol=symbol
                    )
                    
                    self.layout_nodes[component['id']] = node
                    
                    # Move to next position
                    current_x += grid_spacing_x
                    if current_x > self.DRAWING_SIZES[self.drawing_size][0] - margin - 60:
                        current_x = margin
                        current_y += grid_spacing_y
    
    def _group_components_by_type(self, components: List[Dict]) -> Dict[str, List[Dict]]:
        """Group components by their base type"""
        grouped = {}
        known_types = ["pump", "vessel", "heat_exchanger", "valve", "instrument", "filter", "compressor"]
        
        for comp in components:
            base_type = comp['type'].split('_')[0].lower()
            
            # Normalize types
            if base_type in ['centrifugalpump']:
                base_type = 'pump'
            elif base_type in ['tank', 'column']:
                base_type = 'vessel'
            elif base_type in ['condenser', 'cooler']:
                base_type = 'heat_exchanger'
            elif base_type not in known_types:
                base_type = 'other'
            
            if base_type not in grouped:
                grouped[base_type] = []
            
            grouped[base_type].append(comp)
        
        return grouped

    def _optimize_layout(self):
        """Optimize layout for better visual organization"""
        # Find connected components and align them
        for conn_data in self.connections:
            from_id = conn_data['from']['component']
            to_id = conn_data['to']['component']
            
            if from_id in self.layout_nodes and to_id in self.layout_nodes:
                from_node = self.layout_nodes[from_id]
                to_node = self.layout_nodes[to_id]
                
                # Align horizontally if close in Y
                if abs(from_node.y - to_node.y) < 30:
                    avg_y = (from_node.y + to_node.y) / 2
                    from_node.y = avg_y
                    to_node.y = avg_y

    def _process_connections(self, connections: List[Dict]):
        """Process and store connections"""
        self.connections = connections

    def _generate_svg(self, dsl_data: Dict) -> str:
        """Generate complete SVG drawing"""
        width, height = self.DRAWING_SIZES[self.drawing_size]
        
        svg_parts = [
            f'<svg width="{width}mm" height="{height}mm" ',
            f'viewBox="0 0 {width} {height}" ',
            'xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" ',
            'xmlns:xlink="[http://www.w3.org/1999/xlink](http://www.w3.org/1999/xlink)">\n'
        ]
        
        # Add definitions
        svg_parts.append(self._generate_defs())
        
        # Add drawing frame and title block
        svg_parts.append(self._generate_frame_and_title(dsl_data['metadata']))
        
        # Add grid (optional, for alignment)
        svg_parts.append(self._generate_grid(width, height))
        
        # Add piping/connections
        svg_parts.append(self._generate_connections())
        
        # Add components
        svg_parts.append(self._generate_components())
        
        # Add annotations and tags
        svg_parts.append(self._generate_annotations())

        # Add Bill of Materials and Legend
        svg_parts.append(self._generate_bom_and_legend(dsl_data))

        # Add HITL overlay for validation
        svg_parts.append(self._generate_hitl_overlay(dsl_data))
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)

    def _generate_defs(self) -> str:
        """Generate SVG definitions"""
        defs = ['<defs>\n']
        
        # Arrow markers for flow direction
        defs.append('''
            <marker id="arrowhead" markerWidth="10" markerHeight="10" 
                    refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="black"/>
            </marker>
        ''')
        
        # Line patterns for different pipe types
        defs.append('''
            <pattern id="instrument-line" patternUnits="userSpaceOnUse" 
                     width="8" height="1">
                <line x1="0" y1="0" x2="4" y2="0" stroke="black" stroke-width="1"/>
            </pattern>
        ''')
        
        defs.append('</defs>\n')
        return ''.join(defs)

    def _generate_frame_and_title(self, metadata: Dict) -> str:
        """Generate drawing frame and title block"""
        width, height = self.DRAWING_SIZES[self.drawing_size]
        
        frame = f'<g id="drawing-frame">\n'
        
        # Outer border
        frame += f'<rect x="0" y="0" width="{width}" height="{height}" '
        frame += 'fill="none" stroke="black" stroke-width="3"/>\n'
        
        # Title block (bottom right)
        tb_width = 180
        tb_height = 80
        tb_x = width - tb_width - 10
        tb_y = height - tb_height - 10
        
        frame += f'<rect x="{tb_x}" y="{tb_y}" width="{tb_width}" height="{tb_height}" '
        frame += 'fill="white" stroke="black" stroke-width="2"/>\n'
        
        # Title block content
        frame += f'<text x="{tb_x + 10}" y="{tb_y + 20}" font-size="16" font-weight="bold">'
        frame += f'{metadata.get("project", "PROJECT")}</text>\n'
        
        frame += f'<text x="{tb_x + 10}" y="{tb_y + 40}" font-size="12">'
        frame += f'Drawing: {metadata.get("drawing_number", "PID-001")}</text>\n'
        
        frame += f'<text x="{tb_x + 10}" y="{tb_y + 55}" font-size="12">'
        frame += f'Rev: {metadata.get("revision", "00")}</text>\n'
        
        frame += f'<text x="{tb_x + 10}" y="{tb_y + 70}" font-size="10">'
        frame += f'{metadata.get("company", "Company Name")}</text>\n'
        
        frame += '</g>\n'
        return frame

    def _generate_grid(self, width: int, height: int) -> str:
        """Generate alignment grid"""
        grid = '<g id="grid" opacity="0.1">\n'
        
        # Vertical lines
        for x in range(0, width, 50):
            grid += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" '
            grid += 'stroke="gray" stroke-width="0.5"/>\n'
        
        # Horizontal lines
        for y in range(0, height, 50):
            grid += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" '
            grid += 'stroke="gray" stroke-width="0.5"/>\n'
        
        grid += '</g>\n'
        return grid

    def _generate_connections(self) -> str:
        """Generate piping connections"""
        connections_svg = '<g id="connections">\n'
        
        for conn in self.connections:
            from_id = conn['from']['component']
            to_id = conn['to']['component']
            
            if from_id in self.layout_nodes and to_id in self.layout_nodes:
                from_node = self.layout_nodes[from_id]
                to_node = self.layout_nodes[to_id]
                
                # Calculate connection points based on ports
                from_point = self._get_port_position(from_node, conn['from']['port'])
                to_point = self._get_port_position(to_node, conn['to']['port'])
                
                # Determine line style based on connection type
                line_style = self._get_line_style(conn['type'])
                
                # Generate path (using orthogonal routing)
                path = self._generate_orthogonal_path(from_point, to_point)
                
                connections_svg += f'<path d="{path}" fill="none" '
                connections_svg += f'stroke="{line_style["stroke"]}" '
                connections_svg += f'stroke-width="{line_style["width"]}" '
                
                if line_style.get("dasharray"):
                    connections_svg += f'stroke-dasharray="{line_style["dasharray"]}" '
                
                if conn['attributes'].get('with_arrow', True):
                    connections_svg += 'marker-end="url(#arrowhead)" '
                
                connections_svg += '/>\n'
                
                # Add line number label if present
                if conn['attributes'].get('line_number'):
                    mid_x = (from_point[0] + to_point[0]) / 2
                    mid_y = (from_point[1] + to_point[1]) / 2
                    
                    connections_svg += f'<rect x="{mid_x - 40}" y="{mid_y - 10}" '
                    connections_svg += 'width="80" height="20" fill="white" stroke="black"/>\n'
                    
                    connections_svg += f'<text x="{mid_x}" y="{mid_y + 5}" '
                    connections_svg += 'text-anchor="middle" font-size="10" font-family="Arial">'
                    connections_svg += f'{conn["attributes"]["line_number"]}</text>\n'
        
        connections_svg += '</g>\n'
        return connections_svg

    def _generate_components(self) -> str:
        """Generate component symbols"""
        components_svg = '<g id="components">\n'
        
        for node_id, node in self.layout_nodes.items():
            if node.symbol and node.symbol.svg_content:
                # Use actual symbol SVG
                components_svg += f'<g transform="translate({node.x},{node.y})">\n'
                
                # Scale symbol to fit node dimensions
                components_svg += f'<g transform="scale({node.width/100},{node.height/100})">\n'
                # Extract SVG content without outer svg tags if present
                svg_content = node.symbol.svg_content
                if svg_content.startswith('<svg'):
                    # Extract content between svg tags
                    match = re.search(r'<svg[^>]*>(.*)</svg>', svg_content, re.DOTALL)
                    if match:
                        svg_content = match.group(1)
                components_svg += svg_content
                components_svg += '</g>\n'
                
                components_svg += '</g>\n'
            else:
                # Fallback to generic rectangle
                components_svg += f'<rect x="{node.x}" y="{node.y}" '
                components_svg += f'width="{node.width}" height="{node.height}" '
                components_svg += 'fill="white" stroke="black" stroke-width="2"/>\n'
                
                # Add text label
                components_svg += f'<text x="{node.x + node.width/2}" '
                components_svg += f'y="{node.y + node.height/2}" '
                components_svg += 'text-anchor="middle" font-size="10">'
                components_svg += f'{node_id}</text>\n'
        
        components_svg += '</g>\n'
        return components_svg

    def _generate_annotations(self) -> str:
        """Generate component tags and annotations"""
        annotations_svg = '<g id="annotations">\n'
        
        for node_id, node in self.layout_nodes.items():
            # Add tag bubble below component
            tag_x = node.x + node.width / 2
            tag_y = node.y + node.height + 20
            
            # ISA-style tag bubble
            annotations_svg += f'<circle cx="{tag_x}" cy="{tag_y}" r="15" '
            annotations_svg += 'fill="white" stroke="black" stroke-width="2"/>\n'
            
            # Split tag if it contains hyphen
            parts = node_id.split('-')
            if len(parts) == 2:
                # Two-line tag
                annotations_svg += f'<text x="{tag_x}" y="{tag_y - 3}" '
                annotations_svg += 'text-anchor="middle" font-size="10" font-weight="bold">'
                annotations_svg += f'{parts[0]}</text>\n'
                
                annotations_svg += f'<text x="{tag_x}" y="{tag_y + 8}" '
                annotations_svg += 'text-anchor="middle" font-size="8">'
                annotations_svg += f'{parts[1]}</text>\n'
            else:
                # Single line tag
                annotations_svg += f'<text x="{tag_x}" y="{tag_y + 4}" '
                annotations_svg += 'text-anchor="middle" font-size="10">'
                annotations_svg += f'{node_id}</text>\n'
        
        annotations_svg += '</g>\n'
        return annotations_svg

    def _get_port_position(self, node: LayoutNode, port_name: str) -> Tuple[float, float]:
        """Get absolute position of a port"""
        if node.symbol and node.symbol.ports and port_name in node.symbol.ports:
            port_offset = node.symbol.ports[port_name]
            x = node.x + port_offset['x'] * node.width
            y = node.y + port_offset['y'] * node.height
        else:
            # Default port positions
            if port_name in ['inlet', 'suction', 'left']:
                x = node.x
                y = node.y + node.height / 2
            elif port_name in ['outlet', 'discharge', 'right']:
                x = node.x + node.width
                y = node.y + node.height / 2
            elif port_name in ['top']:
                x = node.x + node.width / 2
                y = node.y
            elif port_name in ['bottom']:
                x = node.x + node.width / 2
                y = node.y + node.height
            else:
                # Center
                x = node.x + node.width / 2
                y = node.y + node.height / 2
        
        return (x, y)

    def _get_line_style(self, connection_type: str) -> Dict:
        """Get line style for connection type"""
        styles = {
            "Process": {"stroke": "black", "width": "3"},
            "Instrument": {"stroke": "black", "width": "1", "dasharray": "5,3"},
            "Electrical": {"stroke": "black", "width": "1", "dasharray": "2,2"},
            "Pneumatic": {"stroke": "black", "width": "1", "dasharray": "3,1,1,1"}
        }
        
        return styles.get(connection_type, styles["Process"])

    def _generate_orthogonal_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> str:
        """Generate orthogonal (right-angle) path between points"""
        x1, y1 = start
        x2, y2 = end
        
        # Simple orthogonal routing
        if abs(x2 - x1) > abs(y2 - y1):
            # Horizontal first
            mid_x = (x1 + x2) / 2
            path = f"M {x1},{y1} L {mid_x},{y1} L {mid_x},{y2} L {x2},{y2}"
        else:
            # Vertical first
            mid_y = (y1 + y2) / 2
            path = f"M {x1},{y1} L {x1},{mid_y} L {x2},{mid_y} L {x2},{y2}"
        
        return path

    def _generate_bom_and_legend(self, dsl_data: Dict) -> str:
        """Generate BOM table and legend"""
        bom_svg = '<g id="bom-legend">\n'
        start_x = 50
        start_y = self.DRAWING_SIZES[self.drawing_size][1] - 200
        row_height = 18

        # BOM Header
        headers = ["Tag", "Name", "Type", "Scope"]
        for i, header in enumerate(headers):
            bom_svg += f'<text x="{start_x + i * 100}" y="{start_y}" font-size="12" font-weight="bold">{header}</text>\n'

        # BOM Rows
        for row_idx, comp in enumerate(dsl_data.get("components", [])):
            y = start_y + row_height * (row_idx + 1)
            values = [
                comp.get("id", ""),
                comp.get("name", ""),
                comp.get("type", ""),
                comp.get("scope", "Unknown")
            ]
            for i, val in enumerate(values):
                bom_svg += f'<text x="{start_x + i * 100}" y="{y}" font-size="10">{val}</text>\n'

        # Legend Example
        legend_x = self.DRAWING_SIZES[self.drawing_size][0] - 300
        legend_y = self.DRAWING_SIZES[self.drawing_size][1] - 220
        bom_svg += f'<text x="{legend_x}" y="{legend_y}" font-size="12" font-weight="bold">Legend</text>\n'
        bom_svg += f'<text x="{legend_x}" y="{legend_y + 20}" font-size="10">➤ Solid line: Process</text>\n'
        bom_svg += f'<text x="{legend_x}" y="{legend_y + 35}" font-size="10">- - - Dash: Instrument</text>\n'
        bom_svg += f'<text x="{legend_x}" y="{legend_y + 50}" font-size="10">● ISA Bubble: Tag</text>\n'

        bom_svg += '</g>\n'
        return bom_svg

    def _generate_hitl_overlay(self, dsl_data: Dict) -> str:
        """Overlay for HITL validation (marks unconnected components)"""
        overlay_svg = '<g id="hitl-overlay">\n'
        connected = set()

        for conn in self.connections:
            connected.add(conn['from']['component'])
            connected.add(conn['to']['component'])

        for comp in dsl_data.get("components", []):
            cid = comp["id"]
            if cid not in connected and cid in self.layout_nodes:
                node = self.layout_nodes[cid]
                cx = node.x + node.width / 2
                cy = node.y + node.height / 2
                overlay_svg += f'<text x="{cx}" y="{cy}" font-size="30" fill="red" text-anchor="middle">✖</text>\n'

        overlay_svg += '</g>\n'
        return overlay_svg

    def export_to_png(self, svg_content: str, scale: float = 2.0) -> bytes:
        """Export SVG to PNG"""
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            scale=scale
        )
        return png_data

    def export_to_dxf(self, dsl_data: Dict) -> bytes:
        """Export to DXF format"""
        # Create new DXF document
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Add layers
        doc.layers.new(name='EQUIPMENT', dxfattribs={'color': 7})
        doc.layers.new(name='PIPING', dxfattribs={'color': 5})
        doc.layers.new(name='INSTRUMENTS', dxfattribs={'color': 6})
        doc.layers.new(name='ANNOTATIONS', dxfattribs={'color': 2})
        
        # Add components as blocks
        for node_id, node in self.layout_nodes.items():
            # Add rectangle for component
            msp.add_lwpolyline(
                [(node.x, node.y), 
                 (node.x + node.width, node.y),
                 (node.x + node.width, node.y + node.height),
                 (node.x, node.y + node.height),
                 (node.x, node.y)],
                dxfattribs={'layer': 'EQUIPMENT', 'closed': True}
            )
            
            # Add tag
            msp.add_text(
                node_id,
                dxfattribs={
                    'layer': 'ANNOTATIONS',
                    'height': 5,
                    'style': 'STANDARD'
                }
            ).set_pos((node.x + node.width/2, node.y + node.height + 10), align='MIDDLE_CENTER')
        
        # Add connections
        for conn in self.connections:
            from_id = conn['from']['component']
            to_id = conn['to']['component']
            
            if from_id in self.layout_nodes and to_id in self.layout_nodes:
                from_node = self.layout_nodes[from_id]
                to_node = self.layout_nodes[to_id]
                
                from_point = self._get_port_position(from_node, conn['from']['port'])
                to_point = self._get_port_position(to_node, conn['to']['port'])
                
                # Add polyline
                msp.add_lwpolyline(
                    [from_point, to_point],
                    dxfattribs={'layer': 'PIPING'}
                )
        
        # Export to bytes
        stream = BytesIO()
        doc.write(stream)
        return stream.getvalue()


class PIDExporter:
    """Export P&ID to various formats"""

    @staticmethod
    def export_to_visio_xml(svg_content: str) -> str:
        """Export to Visio-compatible XML (VDX format)"""
        # Create VDX structure
        vdx = ET.Element('VisioDocument')
        vdx.set('xmlns', '[http://schemas.microsoft.com/visio/2003/core](http://schemas.microsoft.com/visio/2003/core)')
        
        # Add pages
        pages = ET.SubElement(vdx, 'Pages')
        page = ET.SubElement(pages, 'Page')
        page.set('ID', '0')
        page.set('Name', 'P&ID')
        
        # Convert SVG elements to Visio shapes
        # This is a simplified version - full implementation would be more complex
        shapes = ET.SubElement(page, 'Shapes')
        
        # Add shape for each component
        # ... implementation details would go here ...
        
        return ET.tostring(vdx, encoding='unicode')

    @staticmethod
    def export_to_pdf(svg_content: str, metadata: Dict) -> bytes:
        """Export to PDF with proper formatting"""
        # Create PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A1)
        
        # Add metadata
        c.setTitle(metadata.get('project', 'P&ID'))
        c.setAuthor(metadata.get('company', 'Company'))
        
        # Convert SVG to ReportLab drawing
        drawing = svg2rlg(BytesIO(svg_content.encode('utf-8')))
        if drawing:
            renderPDF.draw(drawing, c, 0, 0)
        
        c.save()
        buffer.seek(0)
        return buffer.read()
