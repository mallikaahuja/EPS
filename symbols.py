# symbols.py

import schemdraw
import schemdraw.elements as elm
from schemdraw import flow
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import io
from typing import Dict, Tuple, Optional


class SymbolRenderer:
    def __init__(self):
        self.port_map = {}  # For CNN-style port alignment logic

    def render_symbol(self, component_id: str, label: str = "", size: float = 1.0) -> Tuple[bytes, Dict]:
        """
        Main dispatcher: Given component_id, returns rendered PNG bytes and port positions
        """
        draw_method = self.symbol_map().get(component_id.lower())
        if not draw_method:
            return self.draw_generic(label), {}

        return draw_method(label, size)

    def draw_generic(self, label: str) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Box(w=3, h=2).label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (3, 1)}

    def symbol_map(self):
        return {
            # PUMPS
            'vacuum_pump': self.draw_vacuum_pump,
            'pump': self.draw_vacuum_pump,
            'centrifugal_pump': self.draw_centrifugal_pump,
            'gear_pump': self.draw_gear_pump,

            # VALVES
            'epo_butterfly_valve': self.draw_epo_butterfly_valve,
            'control_valve': self.draw_control_valve,
            'ball_valve': self.draw_ball_valve,
            'gate_valve': self.draw_gate_valve,

            # INSTRUMENTS
            'temperature_transmitter': self.draw_temp_transmitter,
            'pressure_transmitter': self.draw_pressure_transmitter,
            'temperature_gauge': self.draw_temp_gauge,
            'pressure_gauge': self.draw_pressure_gauge,
            'flow_switch': self.draw_flow_switch,
            'level_switch': self.draw_level_switch,
            'pressure_switch': self.draw_pressure_switch,

            # COMPONENTS
            'scrubber': self.draw_scrubber,
            'suction_condenser': self.draw_condenser,
            'discharge_condenser': self.draw_condenser,
            'flame_arrestor': self.draw_flame_arrestor,
            'suction_filter': self.draw_filter,
            'strainer': self.draw_strainer,
            'acg_filter': self.draw_filter,
            'base_plate': self.draw_base_plate,
            'cooling_tab': self.draw_cooling_tab,
            'flexible_connection': self.draw_flexible_connection,

            # ELECTRICAL
            'vfd': self.draw_vfd,
            'motor_10hp_2pole_b5': self.draw_motor,

            # PANELS
            'flp_control_panel': self.draw_control_panel,
            'split_control_panel': self.draw_control_panel,

            # VESSELS
            'vertical_vessel': self.draw_vertical_vessel,
            'tank': self.draw_tank,

            # LINES
            'n2_purge_line': self.draw_n2_purge_line,
            'interconnecting_piping': self.draw_pipe,
        }

    # === SYMBOL DRAWING FUNCTIONS ===

    def draw_vacuum_pump(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Circle(radius=1*size).label(label)
        d += flow.Line().right()
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_epo_butterfly_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='butterfly').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_centrifugal_pump(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Pump().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_gear_pump(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle().label(label)
        d += flow.Arc2(radius=1).right()
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_control_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='globe').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_ball_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='ball').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_gate_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='gate').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_temp_transmitter(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle().label('TT\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_pressure_transmitter(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle().label('PT\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_temp_gauge(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle().label('TG\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_pressure_gauge(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle().label('PG\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_flow_switch(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('FS\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_level_switch(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('LS\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_pressure_switch(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('PS\n'+label)
        return self.export_png(d), {'in': (0, -1)}

    def draw_scrubber(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Tank(h=2).label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (0, -1)}

    def draw_condenser(self, label, size):
        d = schemdraw.Drawing()
        d += flow.HeatExchanger().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_flame_arrestor(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Filter().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_filter(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Filter().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_strainer(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='y-strainer').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_base_plate(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label("Base\n"+label)
        return self.export_png(d), {}

    def draw_cooling_tab(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('Cool\n'+label)
        return self.export_png(d), {}

    def draw_flexible_connection(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Wave().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_vfd(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('VFD\n'+label)
        return self.export_png(d), {}

    def draw_motor(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Motor().label('MOTOR\n'+label)
        return self.export_png(d), {}

    def draw_control_panel(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Box().label('PANEL\n'+label)
        return self.export_png(d), {}

    def draw_vertical_vessel(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Tank(h=2.5).label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (0, -1)}

    def draw_tank(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Tank().label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (0, -1)}

    def draw_n2_purge_line(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Line().right().label('N2\n'+label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_pipe(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Line().right().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def export_png(self, drawing) -> bytes:
        f = io.BytesIO()
        drawing.save(f, format='png')
        return f.getvalue()
