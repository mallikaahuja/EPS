from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import yaml
import pandas as pd
import logging
import networkx as nx

logging.basicConfig(level=logging.WARNING)

class ComponentType(Enum):
    PUMP = "CentrifugalPump"
    VESSEL = "Vessel"
    HEAT_EXCHANGER = "HeatExchanger"
    VALVE = "Valve"
    INSTRUMENT = "Instrument"
    FILTER = "Filter"
    COMPRESSOR = "Compressor"
    PIPE = "Pipe"
    NOZZLE = "Nozzle"
    FITTING = "Fitting"
    SAFETY = "Safety"
    UNKNOWN = "Unknown"

class ConnectionType(Enum):
    PROCESS = "Process"
    INSTRUMENT = "Instrument"
    ELECTRICAL = "Electrical"
    PNEUMATIC = "Pneumatic"

@dataclass
class DSLComponent:
    id: str
    tag: str
    type: ComponentType
    subtype: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Dict[str, float]] = None
    ports: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "tag": self.tag,
            "type": self.type.value,
            "subtype": self.subtype,
            "attributes": self.attributes,
            "position": self.position,
            "ports": self.ports
        }

@dataclass
class DSLConnection:
    id: str
    from_component: str
    to_component: str
    from_port: str
    to_port: str
    type: ConnectionType
    attributes: Dict[str, Any] = field(default_factory=dict)
    waypoints: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "from": {"component": self.from_component, "port": self.from_port},
            "to": {"component": self.to_component, "port": self.to_port},
            "type": self.type.value,
            "attributes": self.attributes,
            "waypoints": self.waypoints
        }

@dataclass
class DSLControlLoop:
    id: str
    type: str
    components: List[str]
    setpoint: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "components": self.components,
            "setpoint": self.setpoint,
            "attributes": self.attributes
        }

class DSLGenerator:
    def __init__(self):
        self.components: Dict[str, DSLComponent] = {}
        self.connections: Dict[str, DSLConnection] = {}
        self.control_loops: List[DSLControlLoop] = []
        self.metadata = {}

    # ADDED HELPER METHOD: get_csv_value
    def get_csv_value(self, row: pd.Series, possible_columns: list, default=""):
        """Get value from CSV row, trying multiple possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                return row[col]
        return default

    def set_metadata(self, project, drawing_number, revision, date, company="EPS"):
        self.metadata = {
            "project": project,
            "drawing_number": drawing_number,
            "revision": revision,
            "date": date,
            "company": company
        }

    def _map_component_type(self, type_str: str) -> ComponentType:
        type_str = type_str.lower()
        mapping = {
            "pump": ComponentType.PUMP,
            "vessel": ComponentType.VESSEL,
            "tank": ComponentType.VESSEL,
            "condenser": ComponentType.HEAT_EXCHANGER,
            "exchanger": ComponentType.HEAT_EXCHANGER,
            "valve": ComponentType.VALVE,
            "filter": ComponentType.FILTER,
            "instrument": ComponentType.INSTRUMENT,
            "compressor": ComponentType.COMPRESSOR,
            "pipe": ComponentType.PIPE,
            "nozzle": ComponentType.NOZZLE,
            "fitting": ComponentType.FITTING,
            "safety": ComponentType.SAFETY,
        }
        for key, comp_type in mapping.items():
            if key in type_str:
                return comp_type
        return ComponentType.UNKNOWN

    def _map_connection_type(self, type_str: str) -> ConnectionType:
        mapping = {
            "process": ConnectionType.PROCESS,
            "instrument": ConnectionType.INSTRUMENT,
            "electrical": ConnectionType.ELECTRICAL,
            "pneumatic": ConnectionType.PNEUMATIC
        }
        return mapping.get(type_str.lower(), ConnectionType.PROCESS)

    # REPLACED METHOD: add_component_from_row
    def add_component_from_row(self, row: pd.Series, layout_df: Optional[pd.DataFrame] = None) -> None:
        """FIXED - handles various CSV column name formats"""
        
        # Get ID from various possible column names
        comp_id = self.get_csv_value(row, ['ID', 'id', 'component_id'])
        if not comp_id:
            raise ValueError(f"No ID found in row: {dict(row)}")
        
        # Get type from various possible column names  
        type_str = self.get_csv_value(row, ['type', 'Type', 'component_type', 'subtype'])
        comp_type = self._map_component_type(type_str)
        
        # Generate tag
        tag_prefix = self.get_csv_value(row, ['tag_prefix'], comp_id.split('-')[0] if '-' in comp_id else 'U')
        tag = f"{tag_prefix}-{comp_id}" if not comp_id.startswith(tag_prefix) else comp_id
        
        # Get position from layout_df
        position = None
        if layout_df is not None and not layout_df.empty:
            # Try different ID column names in layout
            layout_row = None
            for id_col in ['ID', 'id', 'component_id']:
                if id_col in layout_df.columns:
                    matches = layout_df[layout_df[id_col] == comp_id]
                    if not matches.empty:
                        layout_row = matches.iloc[0]
                        break
            
            if layout_row is not None:
                x = self.get_csv_value(layout_row, ['x', 'X', 'pos_x', 'x_position'], 0)
                y = self.get_csv_value(layout_row, ['y', 'Y', 'pos_y', 'y_position'], 0)
                position = {"x": float(x), "y": float(y)}
        
        # Default position if none found
        if position is None:
            num_existing = len(self.components)
            position = {
                "x": float(100 + (num_existing % 5) * 150),
                "y": float(100 + (num_existing // 5) * 100)
            }
        
        # Create the DSLComponent object (NOT a string!)
        component = DSLComponent(
            id=comp_id,
            tag=tag,
            type=comp_type,
            subtype=self.get_csv_value(row, ['subtype', 'Subtype']),
            attributes={
                "name": self.get_csv_value(row, ['name', 'Name']),
                "description": self.get_csv_value(row, ['Description', 'description']),
                "isa_code": self.get_csv_value(row, ['isa_code', 'ISA_Code']),
                "manufacturer": self.get_csv_value(row, ['manufacturer']),
                "width": self.get_csv_value(row, ['default_width_px', 'width'], 80),
                "height": self.get_csv_value(row, ['default_height_px', 'height'], 60)
            },
            position=position,
            ports=[
                {"name": "inlet", "type": "process", "position": {"dx": 0, "dy": 0.5}},
                {"name": "outlet", "type": "process", "position": {"dx": 1, "dy": 0.5}}
            ]
        )
        
        # Store the DSLComponent object (verify this!)
        self.components[comp_id] = component
        print(f"✅ Stored component {comp_id} as {type(component)}")

    # REPLACED METHOD: add_connection_from_row
    def add_connection_from_row(self, row: pd.Series) -> None:
        """FIXED - handles various CSV connection formats"""
        
        # Get connection ID
        conn_id = self.get_csv_value(row, ['ID', 'id', 'connection_id'], f"CONN-{len(self.connections)+1:03d}")
        
        # Get from/to components with various column names
        from_comp = self.get_csv_value(row, ['From', 'from', 'from_component', 'source'])
        to_comp = self.get_csv_value(row, ['To', 'to', 'to_component', 'target'])
        
        if not from_comp or not to_comp:
            print(f"⚠️  Skipping connection {conn_id} - missing from ({from_comp}) or to ({to_comp})")
            return
        
        # Verify components exist  
        if from_comp not in self.components:
            print(f"⚠️  Warning: from_component '{from_comp}' not in DSL components")
        if to_comp not in self.components:
            print(f"⚠️  Warning: to_component '{to_comp}' not in DSL components")
        
        conn_type = self._map_connection_type(self.get_csv_value(row, ['line_type', 'type'], 'process'))
        
        # Create DSLConnection object
        connection = DSLConnection(
            id=conn_id,
            from_component=from_comp,
            to_component=to_comp, 
            from_port=self.get_csv_value(row, ['from_port'], 'outlet'),
            to_port=self.get_csv_value(row, ['to_port'], 'inlet'),
            type=conn_type,
            attributes={
                "line_number": self.get_csv_value(row, ['line_number']),
                "with_arrow": True
            }
        )
        
        # Store the DSLConnection object
        self.connections[conn_id] = connection
        print(f"✅ Added connection: {from_comp} → {to_comp}")

    def detect_control_loops(self):
        isa_mapping = {
            "LT": "LIC",
            "FT": "FIC",
            "PT": "PIC",
            "TT": "TIC"
        }

        isa_lookup = {}
        for comp_id, comp in self.components.items():
            isa_code = str(comp.attributes.get("isa_code", "")).upper()
            if isa_code:
                isa_lookup[isa_code] = comp_id

        for sensor_prefix, controller_prefix in isa_mapping.items():
            for sensor_code, sensor_id in isa_lookup.items():
                if sensor_code.startswith(sensor_prefix):
                    base = sensor_code[len(sensor_prefix):]
                    controller_code = controller_prefix + base
                    valve_code = "V" + base

                    controller_id = isa_lookup.get(controller_code)
                    valve_id = isa_lookup.get(valve_code)

                    if controller_id and valve_id:
                        self.control_loops.append(DSLControlLoop(
                            id=f"{sensor_code}_loop",
                            type=controller_prefix,
                            components=[sensor_id, controller_id, valve_id]
                        ))

    def generate_from_csvs(
        self,
        equipment_df: pd.DataFrame,
        inline_df: pd.DataFrame,
        pipeline_df: pd.DataFrame, # This might be unused now if connection_df is primary
        connection_df: pd.DataFrame,
        layout_df: Optional[pd.DataFrame] = None
    ) -> None:
        # Concatenate equipment and inline components for processing
        # Ensure both are not empty before concatenating
        all_components_df = pd.DataFrame()
        if not equipment_df.empty:
            all_components_df = pd.concat([all_components_df, equipment_df])
        if not inline_df.empty:
            all_components_df = pd.concat([all_components_df, inline_df])

        for _, row in all_components_df.iterrows():
            self.add_component_from_row(row, layout_df)
            
        for _, row in connection_df.iterrows():
            self.add_connection_from_row(row)

    def to_dsl(self, format: str = "json") -> str:
        dsl = {
            "metadata": self.metadata,
            "components": [c.to_dict() for c in self.components.values()],
            "connections": [c.to_dict() for c in self.connections.values()],
            "control_loops": [l.to_dict() for l in self.control_loops]
        }
        return yaml.dump(dsl) if format == "yaml" else json.dumps(dsl, indent=2)

