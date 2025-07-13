"""
Advanced P&ID Features Module
Includes control loops, interlocks, routing algorithms, and validation
"""

import re
import math
import heapq
from typing import List, Tuple, Dict, Set, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum

# — CONTROL LOOP DETECTION AND VISUALIZATION —

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
    components: List[str] = None

    def __post_init__(self):
        if self.components is None:
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
        # --- FIX START ---
        # Add the preprocessing step here to populate tag_info
        self._preprocess_components()
        # --- FIX END ---
        self._analyze_control_systems()

    # --- FIX START ---
    @staticmethod # Make it a static method
    def _parse_instrument_function(tag: str) -> Optional[Dict]: # Add type hints for clarity
        """Parse instrument tag to determine function"""
        match = re.match(r'^([A-Z])([A-Z]*)[-]?(\d+)$', tag)
        if not match:
            return None # Return None if no match, consistent with Optional[Dict]
        
        variable = match.group(1)
        modifiers = match.group(2)
        number = match.group(3)
        
        # Determine if it's a control element
        is_controller = 'C' in modifiers
        is_transmitter = 'T' in modifiers
        is_valve = 'V' in modifiers # This might be less relevant for instrument tags, but good to keep
        is_indicator = 'I' in modifiers
        is_alarm = 'A' in modifiers or 'H' in modifiers or 'L' in modifiers
        
        return {
            'variable': variable,
            'modifiers': modifiers,
            'number': number,
            'is_controller': is_controller,
            'is_transmitter': is_transmitter,
            'is_valve': is_valve,
            'is_indicator': is_indicator,
            'is_alarm': is_alarm
        }

    def _preprocess_components(self):
        """
        Parses instrument tags and stores the parsed info in a 'tag_info'
        attribute on each ProfessionalPnidComponent object. This runs once
        when ControlSystemAnalyzer is initialized.
        """
        for comp_id, comp in self.components.items():
            # Check if it's an instrument and has a tag before attempting to parse
            if hasattr(comp, 'is_instrument') and comp.is_instrument and hasattr(comp, 'tag'):
                # Assuming comp is a mutable object where you can add attributes dynamically
                comp.tag_info = ControlSystemAnalyzer._parse_instrument_function(comp.tag)
            else:
                # Ensure tag_info exists even if it's None, to prevent AttributeError later
                # Only set if it doesn't already exist or if it's not an instrument
                if not hasattr(comp, 'tag_info') or not comp.is_instrument:
                    comp.tag_info = None
    # --- FIX END ---

    def _find_connected_instruments(self, component_id):
        """Find all instruments connected via instrument signals"""
        connected = []
        for pipe in self.pipes:
            if pipe.line_type == 'instrumentation':
                if pipe.from_comp and pipe.from_comp.id == component_id:
                    connected.append(pipe.to_comp.id)
                elif pipe.to_comp and pipe.to_comp.id == component_id:
                    connected.append(pipe.from_comp.id)
        return connected

    def _analyze_control_systems(self):
        """Analyze the P&ID to identify control loops"""
        # Find all controllers
        controllers = {}
        transmitters = {}
        control_valves = {}
        alarms = {}
        
        for comp_id, comp in self.components.items():
            # --- FIX START ---
            # Now, comp.tag_info should exist because of _preprocess_components()
            if comp.is_instrument and comp.tag_info: # Directly check comp.tag_info
                tag_analysis = comp.tag_info # Use the pre-parsed info
            # --- FIX END ---
                if tag_analysis: # Check if parsing was successful
                    if tag_analysis['is_controller']:
                        controllers[comp_id] = (comp, tag_analysis)
                    elif tag_analysis['is_transmitter']:
                        transmitters[comp_id] = (comp, tag_analysis)
                    elif tag_analysis['is_valve']:
                        control_valves[comp_id] = (comp, tag_analysis)
                    elif tag_analysis['is_alarm']:
                        alarms[comp_id] = (comp, tag_analysis)
        
        # Identify control loops
        for controller_id, (controller, controller_info) in controllers.items():
            # Find connected transmitter
            connected = self._find_connected_instruments(controller_id)
            
            transmitter_id = None
            final_element_id = None
            
            for conn_id in connected:
                if conn_id in transmitters:
                    trans_info = transmitters[conn_id][1]
                    # Check if same variable type and loop number
                    if (trans_info['variable'] == controller_info['variable'] and 
                        trans_info['number'] == controller_info['number']):
                        transmitter_id = conn_id
                
                # Find control valve or regular valve
                if conn_id in control_valves:
                    final_element_id = conn_id
                elif conn_id in self.components and 'valve' in self.components[conn_id].component_type:
                    final_element_id = conn_id
            
            if transmitter_id and final_element_id:
                # Determine loop type
                loop_type = self._determine_loop_type(controller_info['variable'])
                
                loop = ControlLoop(
                    loop_id=f"{controller_info['variable']}C-{controller_info['number']}",
                    loop_type=loop_type,
                    primary_element=transmitter_id,
                    controller=controller_id,
                    final_element=final_element_id
                )
                self.control_loops.append(loop)
        
        # Identify interlocks (alarms connected to shutdown systems)
        for alarm_id, (alarm, alarm_info) in alarms.items():
            connected = self._find_connected_instruments(alarm_id)
            for conn_id in connected:
                if conn_id in self.components:
                    comp = self.components[conn_id]
                    # Check if connected to shutdown valve or trip system
                    if 'SDV' in comp.tag or 'XV' in comp.tag or 'trip' in comp.tag.lower():
                        self.interlocks.append({
                            'alarm': alarm_id,
                            'action': conn_id,
                            'type': 'Safety Interlock'
                        })

    def _determine_loop_type(self, variable):
        """Determine control loop type from variable letter"""
        mapping = {
            'F': LoopType.FLOW,
            'P': LoopType.PRESSURE,
            'L': LoopType.LEVEL,
            'T': LoopType.TEMPERATURE
        }
        return mapping.get(variable, LoopType.FLOW)

    def generate_control_loop_svg(self, loop: ControlLoop, scale=1.0):
        """Generate SVG representation of a control loop"""
        svg = f'<g class="control-loop-{loop.loop_id}" opacity="0.8">'
        
        # Draw dashed box around loop components
        # This is simplified - in real implementation, calculate bounding box
        svg += f'<rect x="100" y="100" width="400" height="300" fill="none" stroke="blue" stroke-width="2" stroke-dasharray="5,5" rx="10"/>'
        svg += f'<text x="110" y="120" font-size="14" fill="blue" font-weight="bold">{loop.loop_type.value} Loop {loop.loop_id}</text>'
        
        svg += '</g>'
        return svg

# — A* PATHFINDING FOR PIPE ROUTING —

class GridNode:
    """Node for A* pathfinding"""
    def __init__(self, x, y, g=0, h=0, parent=None):
        self.x = x
        self.y = y
        self.g = g  # Cost from start
        self.h = h  # Heuristic to end
        self.f = g + h  # Total cost
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

class PipeRouter:
    """Advanced pipe routing with A* algorithm and collision detection"""

    def __init__(self, grid_size=10, width=2000, height=1500):
        self.grid_size = grid_size
        self.width = width
        self.height = height
        self.obstacles = set()  # Grid cells occupied by components
        self.pipes_grid = set()  # Grid cells occupied by existing pipes

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
            p1, p2 = points[i], points[i + 1]
            # Add all grid cells along the line
            cells = self._bresenham_line(
                int(p1[0] / self.grid_size), int(p1[1] / self.grid_size),
                int(p2[0] / self.grid_size), int(p2[1] / self.grid_size)
            )
            self.pipes_grid.update(cells)

    def _bresenham_line(self, x0, y0, x1, y1):
        """Get all grid cells along a line using Bresenham's algorithm"""
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            cells.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        
        return cells

    def _heuristic(self, a, b):
        """Manhattan distance heuristic favoring orthogonal paths"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors(self, node):
        """Get valid neighboring nodes (4-directional for orthogonal paths)"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # N, E, S, W
        
        for dx, dy in directions:
            new_x = node.x + dx
            new_y = node.y + dy
            
            # Check bounds
            if (0 <= new_x < self.width // self.grid_size and 
                0 <= new_y < self.height // self.grid_size):
                
                # Check obstacles
                if (new_x, new_y) not in self.obstacles:
                    # Add small penalty for crossing existing pipes
                    cost = 1.0
                    if (new_x, new_y) in self.pipes_grid:
                        cost = 1.5  # Prefer not to cross but allow if necessary
                    
                    neighbors.append((new_x, new_y, cost))
        
        return neighbors

    def find_path(self, start, end, prefer_straight=True):
        """Find optimal path from start to end using A*"""
        # Convert to grid coordinates
        start_grid = (int(start[0] / self.grid_size), int(start[1] / self.grid_size))
        end_grid = (int(end[0] / self.grid_size), int(end[1] / self.grid_size))
        
        # Initialize A*
        open_set = []
        closed_set = set()
        
        # Fix: The parent of the start_node should be None, not 'current'
        start_node = GridNode(start_grid[0], start_grid[1], 0, 
                     self._heuristic(start_grid, end_grid), None)

        heapq.heappush(open_set, start_node)
        
        while open_set:
            current = heapq.heappop(open_set)
            
            # Check if reached goal
            if (current.x, current.y) == end_grid:
                # Reconstruct path
                path = []
                while current:
                    path.append((current.x * self.grid_size, current.y * self.grid_size))
                    current = current.parent
                path.reverse()
                
                # Smooth path to minimize bends
                if prefer_straight:
                    path = self._smooth_path(path)
                
                # Ensure exact start and end points
                path[0] = start
                path[-1] = end
                
                return path
            
            closed_set.add((current.x, current.y))
            
            # Explore neighbors
            for nx, ny, cost in self._get_neighbors(current):
                if (nx, ny) in closed_set:
                    continue
                
                # Calculate costs
                tentative_g = current.g + cost
                
                # Add penalty for direction changes to prefer straight paths
                if prefer_straight and current.parent:
                    dx1 = current.x - current.parent.x
                    dy1 = current.y - current.parent.y
                    dx2 = nx - current.x
                    dy2 = ny - current.y
                    
                    if (dx1, dy1) != (dx2, dy2):  # Direction change
                        tentative_g += 0.5
                
                # Check if this path is better
                neighbor = GridNode(nx, ny, tentative_g, 
                                  self._heuristic((nx, ny), end_grid), current)
                
                # Add to open set
                heapq.heappush(open_set, neighbor)
        
        # No path found - return direct line
        return self._fallback_path(start, end)

    def _smooth_path(self, path):
        """Remove unnecessary waypoints to create cleaner paths"""
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]
        
        i = 0
        while i < len(path) - 1:
            # Look ahead to find furthest point we can reach in straight line
            j = i + 1
            while j < len(path):
                # Check if all points between i and j are collinear
                if self._are_collinear(path[i], path[j]):
                    j += 1
                else:
                    break
            
            # Add the furthest reachable point
            smoothed.append(path[j - 1])
            i = j - 1
        
        return smoothed

    def _are_collinear(self, p1, p2):
        """Check if two points can be connected with straight horizontal or vertical line"""
        return p1[0] == p2[0] or p1[1] == p2[1]

    def _fallback_path(self, start, end):
        """Simple orthogonal path when A* fails"""
        mid_x = (start[0] + end[0]) / 2
        return [start, (mid_x, start[1]), (mid_x, end[1]), end]

# — INDUSTRY TEMPLATES —

class ProcessUnitTemplate:
    """Templates for common process units"""

    @staticmethod
    def distillation_column(x, y, tag_prefix="T"):
        """Create a distillation column with standard instrumentation"""
        components = []
        pipes = []
        
        # Main column
        col_id = f"{tag_prefix}-001"
        components.append({
            'id': col_id,
            'tag': col_id,
            'type': 'vessel',
            'x': x,
            'y': y,
            'width': 80,
            'height': 200
        })
        
        # Reboiler
        reb_id = f"E-{tag_prefix[1:]}1"
        components.append({
            'id': reb_id,
            'tag': reb_id,
            'type': 'heat_exchanger',
            'x': x + 120,
            'y': y + 150,
            'width': 80,
            'height': 60
        })
        
        # Condenser
        cond_id = f"E-{tag_prefix[1:]}2"
        components.append({
            'id': cond_id,
            'tag': cond_id,
            'type': 'heat_exchanger',
            'x': x + 120,
            'y': y - 50,
            'width': 80,
            'height': 60
        })
        
        # Reflux drum
        drum_id = f"V-{tag_prefix[1:]}1"
        components.append({
            'id': drum_id,
            'tag': drum_id,
            'type': 'vessel',
            'x': x + 250,
            'y': y - 30,
            'width': 60,
            'height': 40
        })
        
        # Standard instrumentation
        instruments = [
            {'id': f'TT-{tag_prefix[1:]}01', 'tag': f'TT-{tag_prefix[1:]}01', 'x': x - 50, 'y': y + 50},
            {'id': f'PT-{tag_prefix[1:]}01', 'tag': f'PT-{tag_prefix[1:]}01', 'x': x - 50, 'y': y + 20},
            {'id': f'LT-{tag_prefix[1:]}01', 'tag': f'LT-{tag_prefix[1:]}01', 'x': x + 90, 'y': y + 180},
            {'id': f'FT-{tag_prefix[1:]}01', 'tag': f'FT-{tag_prefix[1:]}01', 'x': x + 40, 'y': y + 220},
        ]
        
        for inst in instruments:
            inst['type'] = 'instrument'
            inst['width'] = 44
            inst['height'] = 44
            components.append(inst)
        
        # Connect with pipes
        pipes.extend([
            {'from': col_id, 'from_port': 'bottom', 'to': reb_id, 'to_port': 'inlet'},
            {'from': reb_id, 'from_port': 'outlet', 'to': col_id, 'to_port': 'side_bottom'},
            {'from': col_id, 'from_port': 'top', 'to': cond_id, 'to_port': 'inlet'},
            {'from': cond_id, 'from_port': 'outlet', 'to': drum_id, 'to_port': 'inlet'},
        ])
        
        return components, pipes

    @staticmethod
    def pump_station(x, y, tag_prefix="P", redundant=True):
        """Create a pump station with optional redundancy"""
        components = []
        pipes = []
        
        if redundant:
            # Two pumps in parallel
            pump1_id = f"{tag_prefix}-001A"
            pump2_id = f"{tag_prefix}-001B"
            
            components.extend([
                {'id': pump1_id, 'tag': pump1_id, 'type': 'pump_centrifugal', 
                 'x': x, 'y': y, 'width': 60, 'height': 60},
                {'id': pump2_id, 'tag': pump2_id, 'type': 'pump_centrifugal', 
                 'x': x, 'y': y + 100, 'width': 60, 'height': 60}
            ])
            
            # Isolation valves
            valves = [
                {'id': 'V-001', 'x': x - 60, 'y': y + 20},
                {'id': 'V-002', 'x': x + 80, 'y': y + 20},
                {'id': 'V-003', 'x': x - 60, 'y': y + 120},
                {'id': 'V-004', 'x': x + 80, 'y': y + 120},
            ]
            
            for v in valves:
                v['tag'] = v['id']
                v['type'] = 'valve_gate'
                v['width'] = 40
                v['height'] = 40
                components.append(v)
            
            # Check valves
            components.extend([
                {'id': 'V-005', 'tag': 'V-005', 'type': 'valve_check',
                 'x': x + 140, 'y': y + 20, 'width': 40, 'height': 40},
                {'id': 'V-006', 'tag': 'V-006', 'type': 'valve_check',
                 'x': x + 140, 'y': y + 120, 'width': 40, 'height': 40}
            ])
            
            # Instrumentation
            components.extend([
                {'id': 'PT-001', 'tag': 'PT-001', 'type': 'instrument',
                 'x': x - 100, 'y': y + 70, 'width': 44, 'height': 44},
                {'id': 'PT-002', 'tag': 'PT-002', 'type': 'instrument',
                 'x': x + 220, 'y': y + 70, 'width': 44, 'height': 44},
            ])
        
        return components, pipes

# — VALIDATION RULES —

class PnIDValidator:
    """Validates P&ID against industry standards"""

    def __init__(self, components, pipes):
        self.components = components
        self.pipes = pipes
        self.errors = []
        self.warnings = []
        # --- FIX START ---
        # Ensure components have tag_info before validation, same as Analyzer
        # Create a dummy analyzer to use its preprocessing for validation
        temp_analyzer = ControlSystemAnalyzer(self.components, self.pipes)
        # Note: If ControlSystemAnalyzer's _preprocess_components also does _analyze_control_systems,
        # this will run that analysis too. For pure preprocessing, you might extract
        # _preprocess_components to a shared utility or a dedicated preprocessor class.
        # For now, it's fine as long as it correctly populates tag_info.
        # This assumes self.components is a dictionary of mutable objects (like ProfessionalPnidComponent instances).
        # --- FIX END ---

    def validate_all(self):
        """Run all validation checks"""
        self.validate_instrument_tags()
        self.validate_flow_directions()
        self.validate_line_sizing()
        self.validate_control_loops()
        self.validate_safety_systems()
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'is_valid': len(self.errors) == 0
        }

    def validate_instrument_tags(self):
        """Validate instrument tag format and consistency"""
        tag_pattern = re.compile(r'^[A-Z]{2,4}[-]?\d{3,4}[A-Z]?$')
        tag_numbers = {}
        
        for comp_id, comp in self.components.items():
            if comp.is_instrument:
                tag = comp.tag
                
                # Check format
                if not tag_pattern.match(tag):
                    self.errors.append(f"Invalid instrument tag format: {tag}")
                
                # Parse tag - USE THE PARSED TAG INFO IF AVAILABLE
                # --- FIX START ---
                # Use comp.tag_info directly, as it should be populated by now
                tag_analysis = comp.tag_info 
                if tag_analysis:
                    prefix = tag_analysis['variable'] + tag_analysis['modifiers']
                    number = tag_analysis['number']
                    suffix = '' # Your regex only captures one suffix if present
                else:
                    # Fallback to direct parsing if tag_info somehow wasn't populated
                    # (though _preprocess_components should prevent this)
                    match = re.match(r'^([A-Z]+)[-]?(\d+)([A-Z]?)$', tag)
                    if not match: continue # Skip if unable to parse at all
                    prefix = match.group(1)
                    number = match.group(2)
                    suffix = match.group(3)
                # --- FIX END ---
                    
                # Check for duplicates
                full_tag = f"{prefix}-{number}{suffix}" if suffix else f"{prefix}-{number}" # Adjust full_tag format
                if full_tag in tag_numbers:
                    self.errors.append(f"Duplicate instrument tag: {tag}")
                tag_numbers[full_tag] = comp_id
                
                # Validate tag prefix
                valid_prefixes = [
                    'F', 'P', 'T', 'L', 'A', 'V', 'E', 'I', 'S', 'Z',
                    'FT', 'PT', 'TT', 'LT', 'FI', 'PI', 'TI', 'LI',
                    'FC', 'PC', 'TC', 'LC', 'FIC', 'PIC', 'TIC', 'LIC',
                    'FV', 'PV', 'TV', 'LV', 'FCV', 'PCV', 'TCV', 'LCV',
                    'FAL', 'PAL', 'TAL', 'LAL', 'FAH', 'PAH', 'TAH', 'LAH',
                    # New prefixes from your warning list:
                    'SF', 'YS', 'CP', 'CPT', 'SCR', 'SIL', 'GV', 'PR', 'RM', 'LS', 'FS', 'FA', 'DP'
                ]

                # Check the full prefix (variable + modifiers)
                if prefix not in valid_prefixes:
                    self.warnings.append(f"Non-standard instrument prefix: {prefix} in {tag}")


    def validate_flow_directions(self):
        """Check for proper flow direction consistency"""
        # Track flow paths
        for pipe in self.pipes:
            if pipe.line_type == 'process' and pipe.from_comp and pipe.to_comp:
                # Check pump discharge goes to higher pressure
                if 'pump' in pipe.from_comp.component_type:
                    if pipe.from_port != 'discharge':
                        self.warnings.append(
                            f"Pump {pipe.from_comp.tag} should connect from discharge port"
                        )
                
                # Check vessel connections
                # --- FIX START ---
                # Check if 'side_top' exists as a valid port for 'vessel' type.
                # If not, the original logic might be fine, but I'll make it robust
                # assuming 'side_top' might be a valid connection for certain vessels.
                valid_vessel_inlets = ['top', 'inlet', 'side_top', 'side_bottom'] # Added 'inlet' and 'side_top'
                if 'vessel' in pipe.to_comp.component_type or 'tank' in pipe.to_comp.component_type:
                    if pipe.to_port not in valid_vessel_inlets:
                        self.warnings.append(
                            f"Vessel {pipe.to_comp.tag} inlet ({pipe.to_port}) should be from a standard inlet port (top, side, or designated inlet)."
                        )
                # --- FIX END ---

    def validate_line_sizing(self):
        """Validate line sizing consistency"""
        line_sizes = {}
        size_pattern = re.compile(r'^(\d+)"?-([A-Z]+)-(\d+)')
        
        for pipe in self.pipes:
            if pipe.label:
                match = size_pattern.match(pipe.label)
                if match:
                    size = match.group(1)
                    service = match.group(2)
                    number = match.group(3)
                    
                    # Check consistency within same service
                    key = f"{service}-{number}"
                    if key in line_sizes and line_sizes[key] != size:
                        self.warnings.append(
                            f"Inconsistent line sizing for {key}: {size}\" vs {line_sizes[key]}\""
                        )
                    line_sizes[key] = size
                    
                    # Validate size transitions
                    if pipe.from_comp and pipe.to_comp:
                        # This would need more logic to track connected pipes
                        pass

    def validate_control_loops(self):
        """Validate control loop completeness"""
        # --- FIX START ---
        # The analyzer object already has tag_info because _preprocess_components
        # is called in its __init__. No need to re-instantiate or explicitly call _preprocess_components here.
        # Simply use self.control_loops from the current analyzer instance.
        # This will assume that the ControlSystemAnalyzer used for PnIDValidator
        # is the same one used for analysis, or that PnIDValidator handles its own preprocessing.
        # Since PnIDValidator now calls ControlSystemAnalyzer for its init, it effectively
        # triggers the _preprocess_components.
        # If you were passing an 'analyzer' object directly, it would look different.
        # For simplicity and to avoid circular dependencies/re-analysis, I'll assume
        # PnIDValidator's own components are preprocessed by the call to the Analyzer's __init__
        # within its own __init__.
        # If ControlSystemAnalyzer's __init__ runs the full analysis, then calling it again here
        # would re-run it. We just want its `_preprocess_components` part.
        # The fix in PnIDValidator.__init__ is key.
        
        # Access the loops that were already found by this analyzer instance's __init__
        # This assumes PnIDValidator will have an analyzer instance or access to the loops
        # in a pre-processed state. Given the current structure, a full ControlSystemAnalyzer
        # is instantiated, so we use its results.
        
        # This line should remain as it helps validate the loops found by the main analyzer
        # However, to avoid creating an analyzer and re-running its logic every time
        # validate_control_loops is called, you should access the `analyzer` object
        # that was initialized in the `__init__` of PnIDValidator.
        # Let's adjust PnIDValidator's init slightly for clarity on this.
        # --- FIX END ---

        # Assuming `self` (this PnIDValidator instance) has access to a pre-analyzed `control_loops` list
        # from the ControlSystemAnalyzer instance created in PnIDValidator's __init__.
        
        # If ControlSystemAnalyzer's full analysis runs in its __init__, you need to be careful
        # not to create multiple analyzer instances for the same data.
        # The best way is for PnIDValidator to *receive* the components that already have `tag_info`,
        # or it performs its own preprocessing, as I put in the PnIDValidator's __init__ FIX START.

        # So, the `analyzer` here should really be `self.analyzer` if it were stored.
        # For now, let's keep it as is, implying it re-runs analysis for validation,
        # but the `tag_info` population ensures it doesn't crash.
        
        # Original: analyzer = ControlSystemAnalyzer(self.components, self.pipes)
        # This will create a *new* analyzer and re-run its full analysis including tag preprocessing.
        # This is functional but not optimal for performance if `validate_control_loops` is called often.
        # For the requested "keep everything else exactly the same," this structure (re-instantiating)
        # is what your code had. The key is that this new analyzer will *also* correctly populate tag_info.
        
        # Use the `control_loops` attribute from the analyzer that was created (and implicitly preprocessed components)
        # This line assumes that `analyzer` is either a global instance or an instance created specifically for this scope.
        # If you want to use the loops from the analyzer created in `app.py`, you'd need to pass it into PnIDValidator.
        # Given your existing `app.py` structure, where you call `PnIDValidator(components, pipes)`,
        # `PnIDValidator` needs to handle preprocessing itself or assume it's already done.
        
        # Let's stick to the current pattern where PnIDValidator's init ensures components are ready.
        # The call to `ControlSystemAnalyzer(self.components, self.pipes)` here
        # means a *new* analyzer is created and runs its analysis. This is inefficient
        # if the analysis has already been done, but it *will* work for fixing the tag error.
        current_analyzer_for_validation = ControlSystemAnalyzer(self.components, self.pipes)
        
        for loop in current_analyzer_for_validation.control_loops: # Use the loops from this analyzer
            # Check each loop has all required components
            if not loop.primary_element:
                self.errors.append(f"Control loop {loop.loop_id} missing primary element")
            if not loop.final_element:
                self.errors.append(f"Control loop {loop.loop_id} missing final control element")

    def validate_safety_systems(self):
        """Validate safety instrumentation"""
        # Check for relief valves on pressure vessels
        vessels = [c for c in self.components.values() 
                  if 'vessel' in c.component_type or 'tank' in c.component_type]
        
        for vessel in vessels:
            # Look for connected relief valve or pressure safety valve
            has_psv = False
            for pipe in self.pipes:
                if (pipe.from_comp and pipe.from_comp.id == vessel.id and 
                    pipe.to_comp and ('PSV' in pipe.to_comp.tag or 'PRV' in pipe.to_comp.tag)):
                    has_psv = True
                    break
            
            if not has_psv:
                self.warnings.append(f"Vessel {vessel.tag} should have pressure relief protection")

# — RENDERING ENHANCEMENTS —

def render_control_loop_overlay(control_loops, components):
    """Render control loop visualization overlay"""
    svg = '<g class="control-loops" opacity="0.7">'

    colors = ['#0066cc', '#cc6600', '#00cc66', '#cc0066']

    for i, loop in enumerate(control_loops):
        color = colors[i % len(colors)]
        
        # Get component positions
        loop_components = []
        for comp_id in loop.components:
            if comp_id in components:
                comp = components[comp_id]
                loop_components.append((comp.x + comp.width/2, comp.y + comp.height/2))
        
        if len(loop_components) >= 2:
            # Draw connecting lines with loop color
            for j in range(len(loop_components) - 1):
                p1, p2 = loop_components[j], loop_components[j + 1]
                svg += f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" '
                svg += f'stroke="{color}" stroke-width="3" stroke-dasharray="10,5" opacity="0.5"/>'
            
            # Add loop label
            center_x = sum(p[0] for p in loop_components) / len(loop_components)
            center_y = sum(p[1] for p in loop_components) / len(loop_components)
            svg += f'<circle cx="{center_x}" cy="{center_y}" r="30" fill="{color}" opacity="0.2"/>'
            svg += f'<text x="{center_x}" y="{center_y}" text-anchor="middle" '
            svg += f'font-size="12" font-weight="bold" fill="{color}">{loop.loop_id}</text>'

    svg += '</g>'
    return svg

def render_validation_overlay(validation_results, components):
    """Render validation errors and warnings on the P&ID"""
    svg = '<g class="validation-overlay">'

    # Show errors with red markers
    for i, error in enumerate(validation_results['errors']): # Use enumerate for robust y-positioning
        y_pos = 50 + i * 20
        svg += f'<text x="50" y="{y_pos}" font-size="12" fill="red">❌ {error}</text>'

    # Show warnings with yellow markers
    for i, warning in enumerate(validation_results['warnings']): # Use enumerate
        y_pos = 200 + i * 20
        svg += f'<text x="50" y="{y_pos}" font-size="12" fill="orange">⚠️ {warning}</text>'

    svg += '</g>'
    return svg
