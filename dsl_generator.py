from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import yaml
import pandas as pd
import logging

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

    def add_component_from_row(self, row: pd.Series, layout_df: Optional[pd.DataFrame] = None) -> None:
        comp_id = row["ID"]
        comp_type = self._map_component_type(str(row.get("type", "")))
        tag_prefix = row.get("tag_prefix", "U")
        tag = f"{tag_prefix}-{comp_id}"

        position = None
        if layout_df is not None:
            match = layout_df[layout_df["id"] == comp_id]
            if not match.empty:
                position = {"x": float(match.iloc[0]["x"]), "y": float(match.iloc[0]["y"])}

        ports = []
        if isinstance(row.get("port_definitions"), str):
            try:
                parsed_ports = json.loads(row["port_definitions"])
                for name, coords in parsed_ports.items():
                    ports.append({
                        "name": name,
                        "type": "process",
                        "position": {"dx": coords[0], "dy": coords[1]}
                    })
            except Exception as e:
                logging.warning(f"Port parsing failed for {comp_id}: {e}")

        component = DSLComponent(
            id=comp_id,
            tag=tag,
            type=comp_type,
            subtype=row.get("subtype", ""),
            attributes={
                "name": row.get("name", ""),
                "manufacturer": row.get("manufacturer", ""),
                "cost": row.get("cost_usd", ""),
                "efficiency": row.get("efficiency_pct", ""),
                "isa_code": row.get("isa_code", ""),
                "description": row.get("Description", ""),
                "width": row.get("default_width_px", ""),
                "height": row.get("default_height_px", "")
            },
            position=position,
            ports=ports
        )

        self.components[comp_id] = component

    def add_connection_from_row(self, row: pd.Series) -> None:
        conn_id = row.get("id", f"CONN-{len(self.connections)+1:03d}")
        conn_type = self._map_connection_type(row.get("line_type", "process"))

        waypoints = []
        if isinstance(row.get("waypoints"), str):
            try:
                parsed = json.loads(row["waypoints"])
                if isinstance(parsed, list):
                    # Format 1: [[x, y], [x, y]]
                    if all(isinstance(p, list) and len(p) == 2 for p in parsed):
                        waypoints = [{"x": float(p[0]), "y": float(p[1])} for p in parsed]
                    # Format 2: [{"x": ..., "y": ...}, ...]
                    elif all(isinstance(p, dict) and "x" in p and "y" in p for p in parsed):
                        waypoints = [{"x": float(p["x"]), "y": float(p["y"])} for p in parsed]
            except Exception as e:
                logging.warning(f"Waypoint parsing failed for connection {conn_id}: {e}")

        conn = DSLConnection(
            id=conn_id,
            from_component=row.get("from_component"),
            to_component=row.get("to_component"),
            from_port=row.get("from_port", "outlet"),
            to_port=row.get("to_port", "inlet"),
            type=conn_type,
            attributes={
                "line_number": row.get("line_number", ""),
                "with_arrow": row.get("with_arrow", "")
            },
            waypoints=waypoints
        )
        self.connections[conn.id] = conn

    def generate_from_csvs(
        self,
        equipment_df: pd.DataFrame,
        inline_df: pd.DataFrame,
        pipeline_df: pd.DataFrame,
        connection_df: pd.DataFrame,
        layout_df: Optional[pd.DataFrame] = None
    ) -> None:
        for _, row in pd.concat([equipment_df, inline_df]).iterrows():
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
