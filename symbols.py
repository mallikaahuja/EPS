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
            return self.draw_generic(label, size), {'in': (0, 1), 'out': (3, 1)}
        return draw_method(label, size)

    def draw_generic(self, label: str, size: float = 1.0) -> bytes:
        d = schemdraw.Drawing()
        d.config(fontsize=10 * size)
        box = d.add(flow.Box(w=3, h=2))
        d.label(label, loc='center')
        return self.export_png(d)

    def export_png(self, drawing: schemdraw.Drawing) -> bytes:
        """
        Renders a Schemdraw.Drawing object to PNG using a memory buffer.
        """
        fig = drawing.draw(show=False)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        plt.close(fig)
        return buf.getvalue()

    def symbol_map(self):
        return {
            # PUMPS
            'vacuum_pump': self.draw_vacuum_pump,
            'pump': self.draw_vacuum_pump,
            'centrifugal_pump': self.draw_centrifugal_pump,
            'gear_pump': self.draw_gear_pump,

            # VALVES
            'gate_valve': self.draw_gate_valve,
            'ball_valve': self.draw_ball_valve,
            'epo_valve': self.draw_epo_valve,

            # INSTRUMENTS
            'pressure_transmitter': self.draw_pt,
            'temperature_transmitter': self.draw_tt,
            'flow_transmitter': self.draw_ft,
            'level_transmitter': self.draw_lt,

            # ETC.
            'motor': self.draw_motor,
            'vfd': self.draw_vfd,
            'flame_arrestor': self.draw_flame_arrestor
        }

    # Sample symbol definitions
    def draw_vacuum_pump(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d.config(fontsize=10 * size)
        pump = d.add(flow.Box(w=3, h=2).label(label))
        return self.export_png(d), {'inlet': (0, 1), 'outlet': (3, 1)}

    def draw_centrifugal_pump(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        pump = d.add(elm.Pump())
        d.label(label, loc='center')
        return self.export_png(d), {'suction': (0, 0), 'discharge': (2, 0)}

    def draw_gear_pump(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        pump = d.add(flow.Circle().label(label))
        return self.export_png(d), {'inlet': (0, 1), 'outlet': (1, 1)}

    def draw_gate_valve(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += elm.Valve()
        d.label(label, loc='center')
        return self.export_png(d), {'in': (0, 0), 'out': (2, 0)}

    def draw_ball_valve(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Circle().label("BV")
        d.label(label, loc='center')
        return self.export_png(d), {'in': (0, 0), 'out': (2, 0)}

    def draw_epo_valve(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Box(w=2, h=1).label("EPO")
        d.label(label, loc='center')
        return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (2, 0.5)}

    def draw_motor(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Circle().label("M")
        d.label(label, loc='center')
        return self.export_png(d), {'in': (0, 0.5), 'out': (2, 0.5)}

    def draw_vfd(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Box(w=2, h=1).label("VFD")
        d.label(label, loc='center')
        return self.export_png(d), {'in': (0, 0.5), 'out': (2, 0.5)}

    def draw_flame_arrestor(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Box(w=2, h=1).label("FA")
        d.label(label, loc='center')
        return self.export_png(d), {'in': (0, 0.5), 'out': (2, 0.5)}

    def draw_pt(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += elm.Circle().label("PT")
        d.label(label, loc='center')
        return self.export_png(d), {'signal': (1, 0)}

    def draw_tt(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += elm.Circle().label("TT")
        d.label(label, loc='center')
        return self.export_png(d), {'signal': (1, 0)}

    def draw_ft(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += elm.Circle().label("FT")
        d.label(label, loc='center')
        return self.export_png(d), {'signal': (1, 0)}

    def draw_lt(self, label: str, size: float) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += elm.Circle().label("LT")
        d.label(label, loc='center')
        return self.export_png(d), {'signal': (1, 0)}
