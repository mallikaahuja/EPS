"""
Advanced P&ID Features Module
Includes control loops, interlocks, routing algorithms, and validation
"""

import re
import math
import heapq
from typing import List, Tuple, Dict, Set, Optional
import numpy as np
from dataclasses import dataclass, field
from enum import Enum

# --- CONTROL LOOP DETECTION AND VISUALIZATION ---

class LoopType(Enum):
    FLOW = "Flow Control"
    PRESSURE = "Pressure Control"
    LEVEL = "Level Control"
    TEMPERATURE = "Temperature Control"
    CASCADE = "Cascade Control"
    RATIO = "Ratio Control"
    FEEDFORWARD = "Feedforward Control"

@dataclass
class ControlLoop:
    """Represents a control loop in the P&ID"""
    loop_id: str
    loop_type: LoopType
    primary_element: str  # e.g., FT-101
    controller: str       # e.g., FIC-101
    final_element: str    # e.g., FCV-101 or V-003
    setpoint_source: Optional[str] = None  # For cascade loops
    components: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.components:
            self.components = [self.primary_element, self.controller, self.final_element]
            if self.setpoint_source:
                self.components.append(self.setpoint_source)

class ControlSystemAnalyzer:
    """Analyzes P&ID for control loops and interlocks"""

    def __init__(self, components, pipes):
        self.components = components
        self.pipes = pipes
        self.control_loops = []
        self.interlocks = []
        self._preprocess_components()
        self._analyze_control_systems()

    @staticmethod
    def _parse_instrument_function(tag: str) -> Optional[Dict]:
        """Parse instrument tag to determine function"""
        match = re.match(r'^([A-Z])([A-Z]*)[-]?(\d+)$', tag)
        if not match:
            return None

        variable = match.group(1)
        modifiers = match.group(2)
        number = match.group(3)

        return {
            'variable': variable,
            'modifiers': modifiers,
            'number': number,
            'is_controller': 'C' in modifiers,
            'is_transmitter': 'T' in modifiers,
            'is_valve': 'V' in modifiers,
            'is_indicator': 'I' in modifiers,
            'is_alarm': 'A' in modifiers or 'H' in modifiers or 'L' in modifiers
        }

    def _preprocess_components(self):
        """
        Parses instrument tags and stores the parsed info in a 'tag_info'
        attribute on each component object/dict.
        """
        for comp_id, comp in self.components.items():
            is_instrument = False
            tag = None

            if isinstance(comp, dict):
                comp_type = comp.get('type', '')
                is_instrument = comp_type == 'instrument' or 'transmitter' in comp_type or 'gauge' in comp_type
                tag = comp.get('ID', '')
            elif hasattr(comp, 'type'): # Assuming an object structure
                comp_type = getattr(comp, 'type', '')
                is_instrument = comp_type == 'instrument' or 'transmitter' in comp_type or 'gauge' in comp_type
                tag = getattr(comp, 'id', '')
            
            if is_instrument and tag:
                tag_info = self._parse_instrument_function(tag)
                if isinstance(comp, dict):
                    comp['tag_info'] = tag_info
                else:
                    setattr(comp, 'tag_info', tag_info)
            else:
                if isinstance(comp, dict):
                    comp['tag_info'] = None
                else:
                    setattr(comp, 'tag_info', None)


    def _find_connected_instruments(self, component_id):
        """Find all instruments connected via instrument signals"""
        connected = []
        for pipe in self.pipes:
            pipe_type = pipe.get('type', '')
            from_comp_id = pipe.get('from', {}).get('component')
            to_comp_id = pipe.get('to', {}).get('component')

            if pipe_type in ['Instrument', 'instrumentation']:
                if from_comp_id == component_id:
                    connected.append(to_comp_id)
                elif to_comp_id == component_id:
                    connected.append(from_comp_id)
        return connected

    def _analyze_control_systems(self):
        """Analyze the P&ID to identify control loops"""
        controllers, transmitters, control_valves, alarms = {}, {}, {}, {}

        for comp_id, comp in self.components.items():
            tag_info = comp.get('tag_info') if isinstance(comp, dict) else getattr(comp, 'tag_info', None)
            if tag_info:
                if tag_info['is_controller']:
                    controllers[comp_id] = (comp, tag_info)
                elif tag_info['is_transmitter']:
                    transmitters[comp_id] = (comp, tag_info)
                elif tag_info['is_valve']:
                    control_valves[comp_id] = (comp, tag_info)
                elif tag_info['is_alarm']:
                    alarms[comp_id] = (comp, tag_info)

        for controller_id, (controller, controller_info) in controllers.items():
            connected = self._find_connected_instruments(controller_id)
            transmitter_id, final_element_id = None, None

            for conn_id in connected:
                if conn_id in transmitters:
                    trans_info = transmitters[conn_id][1]
                    if (trans_info['variable'] == controller_info['variable'] and
                        trans_info['number'] == controller_info['number']):
                        transmitter_id = conn_id
                
                if conn_id in control_valves:
                    final_element_id = conn_id
                elif conn_id in self.components:
                    comp_type = self.components[conn_id].get('type', '')
                    if 'valve' in comp_type:
                        final_element_id = conn_id

            if transmitter_id and final_element_id:
                loop_type = self._determine_loop_type(controller_info['variable'])
                loop = ControlLoop(
                    loop_id=f"{controller_info['variable']}C-{controller_info['number']}",
                    loop_type=loop_type,
                    primary_element=transmitter_id,
                    controller=controller_id,
                    final_element=final_element_id
                )
                self.control_loops.append(loop)

        for alarm_id, (alarm, alarm_info) in alarms.items():
            connected = self._find_connected_instruments(alarm_id)
            for conn_id in connected:
                if conn_id in self.components:
                    comp = self.components[conn_id]
                    comp_tag = comp.get('id', '')
                    if 'SDV' in comp_tag or 'XV' in comp_tag or 'trip' in comp_tag.lower():
                        self.interlocks.append({
                            'alarm': alarm_id,
                            'action': conn_id,
                            'type': 'Safety Interlock'
                        })

    def _determine_loop_type(self, variable):
        """Determine control loop type from variable letter"""
        mapping = {
            'F': LoopType.FLOW, 'P': LoopType.PRESSURE,
            'L': LoopType.LEVEL, 'T': LoopType.TEMPERATURE
        }
        return mapping.get(variable, LoopType.FLOW)

    def generate_control_loop_svg(self, loop: ControlLoop, scale=1.0):
        """Generate SVG representation of a control loop"""
        svg = f'<g class="control-loop-{loop.loop_id}" opacity="0.8">'
        svg += f'<rect x="100" y="100" width="400" height="300" fill="none" stroke="blue" stroke-width="2" stroke-dasharray="5,5" rx="10"/>'
        svg += f'<text x="110" y="120" font-size="14" fill="blue" font-weight="bold">{loop.loop_type.value} Loop {loop.loop_id}</text>'
        svg += '</g>'
        return svg

# --- A* PATHFINDING FOR PIPE ROUTING ---

class GridNode:
    """Node for A* pathfinding"""
    def __init__(self, x, y, g=0, h=0, parent=None):
        self.x, self.y = x, y
        self.g, self.h = g, h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other): return self.f < other.f
    def __eq__(self, other): return self.x == other.x and self.y == other.y
    def __hash__(self): return hash((self.x, self.y))

class PipeRouter:
    """Advanced pipe routing with A* algorithm and collision detection"""

    def __init__(self, grid_size=10, width=2000, height=1500):
        self.grid_size = grid_size
        self.width, self.height = width, height
        self.obstacles = set()
        self.pipes_grid = set()

    def add_component_obstacle(self, x, y, width, height, padding=20):
        """Add component as obstacle with padding"""
        start_x = max(0, int((x - padding) / self.grid_size))
        start_y = max(0, int((y - padding) / self.grid_size))
        end_x = min(self.width // self.grid_size, int((x + width + padding) / self.grid_size))
        end_y = min(self.height // self.grid_size, int((y + height + padding) / self.grid_size))
        for gx in range(start_x, end_x + 1):
            for gy in range(start_y, end_y + 1):
                self.obstacles.add((gx, gy))

    def add_pipe_path(self, points):
        """Add existing pipe path to avoid crossings"""
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            cells = self._bresenham_line(
                int(p1[0] / self.grid_size), int(p1[1] / self.grid_size),
                int(p2[0] / self.grid_size), int(p2[1] / self.grid_size)
            )
            self.pipes_grid.update(cells)

    def _bresenham_line(self, x0, y0, x1, y1):
        """Get all grid cells along a line using Bresenham's algorithm"""
        cells, dx, dy = [], abs(x1 - x0), abs(y1 - y0)
        sx, sy = 1 if x0 < x1 else -1, 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            cells.append((x0, y0))
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy
        return cells

    def _heuristic(self, a, b):
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors(self, node):
        """Get valid neighboring nodes (4-directional for orthogonal paths)"""
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = node.x + dx, node.y + dy
            if (0 <= new_x < self.width // self.grid_size and 0 <= new_y < self.height // self.grid_size):
                if (new_x, new_y) not in self.obstacles:
                    cost = 1.5 if (new_x, new_y) in self.pipes_grid else 1.0
                    neighbors.append((new_x, new_y, cost))
        return neighbors

    def find_path(self, start, end, prefer_straight=True):
        """Find optimal path from start to end using A*"""
        start_grid = (int(start[0] / self.grid_size), int(start[1] / self.grid_size))
        end_grid = (int(end[0] / self.grid_size), int(end[1] / self.grid_size))
        open_set, closed_set = [], set()
        start_node = GridNode(start_grid[0], start_grid[1], 0, self._heuristic(start_grid, end_grid))
        heapq.heappush(open_set, start_node)

        while open_set:
            current = heapq.heappop(open_set)
            if (current.x, current.y) == end_grid:
                path = []
                while current:
                    path.append((current.x * self.grid_size, current.y * self.grid_size))
                    current = current.parent
                path.reverse()
                path = self._smooth_path(path) if prefer_straight else path
                path[0], path[-1] = start, end
                return path

            closed_set.add((current.x, current.y))
            for nx, ny, cost in self._get_neighbors(current):
                if (nx, ny) in closed_set: continue
                tentative_g = current.g + cost
                if prefer_straight and current.parent:
                    if (current.x - current.parent.x, current.y - current.parent.y) != (nx - current.x, ny - current.y):
                        tentative_g += 0.5
                neighbor = GridNode(nx, ny, tentative_g, self._heuristic((nx, ny), end_grid), current)
                heapq.heappush(open_set, neighbor)

        return self._fallback_path(start, end)

    def _smooth_path(self, path):
        """Remove unnecessary waypoints to create cleaner paths"""
        if len(path) <= 2: return path
        smoothed = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = i + 1
            while j < len(path):
                if self._are_collinear(path[i], path[j]):
                    j += 1
                else: break
            smoothed.append(path[j - 1])
            i = j - 1
        return smoothed

    def _are_collinear(self, p1, p2):
        """Check if two points can be connected with a straight horizontal or vertical line"""
        return p1[0] == p2[0] or p1[1] == p2[1]

    def _fallback_path(self, start, end):
        """Simple orthogonal path when A* fails"""
        mid_x = (start[0] + end[0]) / 2
        return [start, (mid_x, start[1]), (mid_x, end[1]), end]

# --- INDUSTRY TEMPLATES ---

class ProcessUnitTemplate:
    """Templates for common process units"""

    @staticmethod
    def distillation_column(x, y, tag_prefix="T"):
        """Create a distillation column with standard instrumentation"""
        components = []
        pipes = []

        col_id = f"{tag_prefix}-001"
        components.append({'id': col_id, 'type': 'vessel', 'x': x, 'y': y, 'width': 80, 'height': 200})
        reb_id = f"E-{tag_prefix[1:]}1"
        components.append({'id': reb_id, 'type': 'heat_exchanger', 'x': x + 120, 'y': y + 150, 'width': 80, 'height': 60})
        cond_id = f"E-{tag_prefix[1:]}2"
        components.append({'id': cond_id, 'type': 'heat_exchanger', 'x': x + 120, 'y': y - 50, 'width': 80, 'height': 60})
        drum_id = f"V-{tag_prefix[1:]}1"
        components.append({'id': drum_id, 'type': 'vessel', 'x': x + 250, 'y': y - 30, 'width': 60, 'height': 40})

        instruments = [
            {'id': f'TT-{tag_prefix[1:]}01', 'x': x - 50, 'y': y + 50},
            {'id': f'PT-{tag_prefix[1:]}01', 'x': x - 50, 'y': y + 20},
            {'id': f'LT-{tag_prefix[1:]}01', 'x': x + 90, 'y': y + 180},
            {'id': f'FT-{tag_prefix[1:]}01', 'x': x + 40, 'y': y + 220},
        ]
        for inst in instruments:
            inst.update({'type': 'instrument', 'width': 44, 'height': 44})
            components.append(inst)

        pipes.extend([
            {'from': {'component': col_id, 'port': 'bottom'}, 'to': {'component': reb_id, 'port': 'inlet'}},
            {'from': {'component': reb_id, 'port': 'outlet'}, 'to': {'component': col_id, 'port': 'side_bottom'}},
            {'from': {'component': col_id, 'port': 'top'}, 'to': {'component': cond_id, 'port': 'inlet'}},
            {'from': {'component': cond_id, 'port': 'outlet'}, 'to': {'component': drum_id, 'port': 'inlet'}},
        ])

        return components, pipes

    @staticmethod
    def pump_station(x, y, tag_prefix="P", redundant=True):
        """Create a pump station with optional redundancy"""
        components, pipes = [], []
        if redundant:
            pump1_id, pump2_id = f"{tag_prefix}-001A", f"{tag_prefix}-001B"
            components.extend([
                {'id': pump1_id, 'type': 'pump_centrifugal', 'x': x, 'y': y, 'width': 60, 'height': 60},
                {'id': pump2_id, 'type': 'pump_centrifugal', 'x': x, 'y': y + 100, 'width': 60, 'height': 60}
            ])
            valves = [
                {'id': 'V-001', 'x': x - 60, 'y': y + 20}, {'id': 'V-002', 'x': x + 80, 'y': y + 20},
                {'id': 'V-003', 'x': x - 60, 'y': y + 120}, {'id': 'V-004', 'x': x + 80, 'y': y + 120},
            ]
            for v in valves:
                v.update({'type': 'valve_gate', 'width': 40, 'height': 40})
                components.append(v)
            components.extend([
                {'id': 'V-005', 'type': 'valve_check', 'x': x + 140, 'y': y + 20, 'width': 40, 'height': 40},
                {'id': 'V-006', 'type': 'valve_check', 'x': x + 140, 'y': y + 120, 'width': 40, 'height': 40}
            ])
            components.extend([
                {'id': 'PT-001', 'type': 'instrument', 'x': x - 100, 'y': y + 70, 'width': 44, 'height': 44},
                {'id': 'PT-002', 'type': 'instrument', 'x': x + 220, 'y': y + 70, 'width': 44, 'height': 44},
            ])
        return components, pipes

# --- VALIDATION RULES ---

class PnIDValidator:
    """Validates P&ID against industry standards"""

    def __init__(self, components, pipes):
        self.components = {c['id']: c for c in components}
        self.pipes = pipes
        self.errors = []
        self.warnings = []
        ControlSystemAnalyzer(self.components, self.pipes)

    def validate_all(self):
        """Run all validation checks"""
        self.errors, self.warnings = [], []
        self.validate_instrument_tags()
        self.validate_flow_directions()
        self.validate_line_sizing()
        self.validate_control_loops()
        self.validate_safety_systems()
        return {'errors': self.errors, 'warnings': self.warnings, 'is_valid': len(self.errors) == 0}

    def validate_instrument_tags(self):
        """Validate instrument tag format and consistency"""
        tag_pattern = re.compile(r'^[A-Z]{2,4}[-]?\d{3,4}[A-Z]?$')
        tag_numbers = {}
        for comp_id, comp in self.components.items():
            comp_type = comp.get('type', '')
            is_instrument = 'instrument' in comp_type or 'transmitter' in comp_type or 'gauge' in comp_type
            tag = comp.get('id', '')
            if is_instrument and tag:
                if not tag_pattern.match(tag):
                    self.errors.append(f"Invalid instrument tag format: {tag}")
                tag_info = comp.get('tag_info')
                if tag_info:
                    full_tag = f"{tag_info['variable']}{tag_info['modifiers']}-{tag_info['number']}"
                    if full_tag in tag_numbers:
                        self.errors.append(f"Duplicate instrument tag: {tag}")
                    tag_numbers[full_tag] = comp_id

    def validate_flow_directions(self):
        """Check for proper flow direction consistency"""
        for pipe in self.pipes:
            if pipe.get('type') == 'Process':
                from_id = pipe.get('from', {}).get('component')
                to_id = pipe.get('to', {}).get('component')
                if from_id in self.components and to_id in self.components:
                    from_comp = self.components[from_id]
                    to_comp = self.components[to_id]
                    if 'pump' in from_comp.get('type', '') and pipe.get('from', {}).get('port') != 'discharge':
                        self.warnings.append(f"Pump {from_id} should connect from discharge port")
                    to_type = to_comp.get('type', '')
                    if 'vessel' in to_type or 'tank' in to_type:
                        if pipe.get('to', {}).get('port') not in ['top', 'inlet', 'side_top', 'side_bottom', 'gas_inlet', 'inlet_top']:
                            self.warnings.append(f"Vessel {to_id} inlet ({pipe.get('to', {}).get('port')}) is non-standard")

    def validate_line_sizing(self):
        """Validate line sizing consistency (simplified)"""
        line_sizes = {}
        for pipe in self.pipes:
            label = pipe.get('attributes', {}).get('line_number', '')
            if "NB" in label:
                try:
                    size = int(label.split(" ")[0])
                    if label in line_sizes and line_sizes[label] != size:
                        self.warnings.append(f"Inconsistent sizing for line: {label}")
                    line_sizes[label] = size
                except (ValueError, IndexError):
                    pass

    def validate_control_loops(self):
        """Validate control loop completeness"""
        analyzer = ControlSystemAnalyzer(self.components, self.pipes)
        for loop in analyzer.control_loops:
            if not loop.primary_element:
                self.errors.append(f"Control loop {loop.loop_id} missing primary element")
            if not loop.final_element:
                self.errors.append(f"Control loop {loop.loop_id} missing final control element")

    def validate_safety_systems(self):
        """Validate safety instrumentation"""
        vessels = {cid: c for cid, c in self.components.items() if 'vessel' in c.get('type', '')}
        for vessel_id, vessel in vessels.items():
            has_psv = False
            for pipe in self.pipes:
                if pipe.get('from', {}).get('component') == vessel_id:
                    to_id = pipe.get('to', {}).get('component')
                    if to_id in self.components:
                        to_tag = self.components[to_id].get('id', '')
                        if 'PSV' in to_tag or 'PRV' in to_tag:
                            has_psv = True; break
            if not has_psv:
                self.warnings.append(f"Vessel {vessel_id} may be missing pressure relief protection")

    def run_validation(self, dsl_json=None):
        """Simple wrapper for compatibility"""
        result = self.validate_all()
        return result["errors"] + result["warnings"]

# --- RENDERING ENHANCEMENTS ---

def render_control_loop_overlay(control_loops, layout_nodes):
    """Render control loop visualization overlay"""
    svg = '<g class="control-loops" opacity="0.7">'
    colors = ['#0066cc', '#cc6600', '#00cc66', '#cc0066']
    for i, loop in enumerate(control_loops):
        color = colors[i % len(colors)]
        loop_coords = []
        for comp_id in loop.components:
            if comp_id in layout_nodes:
                node = layout_nodes[comp_id]
                loop_coords.append((node.x + node.width/2, node.y + node.height/2))
        if len(loop_coords) >= 2:
            for j in range(len(loop_coords) - 1):
                p1, p2 = loop_coords[j], loop_coords[j+1]
                svg += f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="{color}" stroke-width="3" stroke-dasharray="10,5" opacity="0.5"/>'
            center_x = sum(p[0] for p in loop_coords) / len(loop_coords)
            center_y = sum(p[1] for p in loop_coords) / len(loop_coords)
            svg += f'<circle cx="{center_x}" cy="{center_y}" r="30" fill="{color}" opacity="0.2"/>'
            svg += f'<text x="{center_x}" y="{center_y}" text-anchor="middle" font-size="12" font-weight="bold" fill="{color}">{loop.loop_id}</text>'
    svg += '</g>'
    return svg

def render_validation_overlay(validation_results, layout_nodes):
    """Render validation errors and warnings on the P&ID"""
    svg = '<g class="validation-overlay">'
    y_pos = 50
    for error in validation_results['errors']:
        svg += f'<text x="50" y="{y_pos}" font-size="12" fill="red">❌ {error}</text>'
        y_pos += 20
    y_pos += 20
    for warning in validation_results['warnings']:
        svg += f'<text x="50" y="{y_pos}" font-size="12" fill="orange">⚠️ {warning}</text>'
        y_pos += 20
    svg += '</g>'
    return svg

def add_control_logic_block(svg: str, booster_config: dict) -> str:
    """Append a control logic block (PLC, VFD, Interlocks) to the SVG diagram."""
    block_x, block_y = 1200, 100
    logic_svg = f"""
<g id="control_logic_block">
    <rect x="{block_x}" y="{block_y}" width="280" height="160" fill="white" stroke="black" stroke-width="2"/>
    <text x="{block_x + 10}" y="{block_y + 20}" font-size="14" font-weight="bold">Control Logic</text>
"""
    if booster_config.get("automation_ready"):
        logic_svg += f'<text x="{block_x + 10}" y="{block_y + 50}" font-size="12">🟢 PLC Enabled</text>'
    if booster_config.get("requires_vfd"):
        logic_svg += f'<text x="{block_x + 10}" y="{block_y + 70}" font-size="12">⚙️ VFD Controlled</text>'
    if booster_config.get("requires_bypass"):
        logic_svg += f'<text x="{block_x + 10}" y="{block_y + 90}" font-size="12">🔁 Bypass Valve Installed</text>'
    if booster_config.get("requires_purge"):
        logic_svg += f'<text x="{block_x + 10}" y="{block_y + 110}" font-size="12">💨 Purge Interlock</text>'
    if booster_config.get("requires_cooling"):
        logic_svg += f'<text x="{block_x + 10}" y="{block_y + 130}" font-size="12">❄️ Cooling Loop Enabled</text>'

    logic_svg += '</g>'
    return svg.replace("</svg>", logic_svg + "</svg>")
