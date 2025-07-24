import schemdraw
import schemdraw.elements as elm
from schemdraw import flow
import matplotlib.pyplot as plt
import io
from typing import Dict, Tuple

class SymbolRenderer:
    def __init__(self):
        self.port_map = {}

    def export_png(self, drawing) -> bytes:
        buf = io.BytesIO()
        drawing.draw()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        return buf.getvalue()

    def render_symbol(self, component_id: str, label: str = "", size: float = 1.0) -> Tuple[bytes, Dict]:
        draw_method = self.symbol_map().get(component_id.lower())
        if not draw_method:
            print(f"[WARNING] No symbol defined for: {component_id}")
            return self.draw_generic(label)
        return draw_method(label, size)

    def draw_generic(self, label: str) -> Tuple[bytes, Dict]:
        d = schemdraw.Drawing()
        d += flow.Box(w=3, h=2).label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (3, 1)}

    def symbol_map(self) -> Dict[str, callable]:
        return {
            # Pumps
            'dry_screw_pump': self.draw_vacuum_pump,
            'centrifugal_pump': self.draw_centrifugal_pump,
            'gear_pump': self.draw_gear_pump,
            'kdp330': self.draw_vacuum_pump,
            'kdp_330_pump': self.draw_vacuum_pump,
            'pump': self.draw_vacuum_pump,

            # Valves
            'epo_butterfly_valve': self.draw_butterfly_valve,
            'control_valve': self.draw_control_valve,
            'gate_valve': self.draw_gate_valve,
            'ball_valve': self.draw_ball_valve,
            'temperature_control_valve': self.draw_control_valve,
            'solenoid_valve': self.draw_control_valve,

            # Transmitters & Instruments
            'pressure_transmitter': self.draw_circle_labeled('PT'),
            'pressure_transmitter_discharge': self.draw_circle_labeled('PT'),
            'temperature_transmitter': self.draw_circle_labeled('TT'),
            'temperature_transmitter_suction': self.draw_circle_labeled('TT'),
            'temperature_transmitter_discharge': self.draw_circle_labeled('TT'),
            'flow_transmitter': self.draw_circle_labeled('FT'),
            'level_transmitter': self.draw_circle_labeled('LT'),
            'pressure_switch': self.draw_square_labeled('PS'),
            'flow_switch': self.draw_square_labeled('FS'),
            'level_switch': self.draw_square_labeled('LS'),
            'temp_gauge_suction': self.draw_circle_labeled('T'),
            'temp_gauge_discharge': self.draw_circle_labeled('T'),
            'rotameter': self.draw_circle_labeled('R'),
            'tc': self.draw_square_labeled('TC'),

            # Filters
            'acg_filter': self.draw_filter,
            'suction_filter': self.draw_filter,
            'flame_arrestor': self.draw_filter,
            'flame_arrestor_suction': self.draw_filter,
            'flame_arrestor_discharge': self.draw_filter,
            'strainer': self.draw_strainer,

            # Condensers & Vessels
            'vapour_condenser': self.draw_condenser,
            'discharge_condenser': self.draw_condenser,
            'catch_pot': self.draw_vertical_vessel,
            'catch_pot_manual_drain': self.draw_vertical_vessel,
            'catch_pot_auto_drain': self.draw_vertical_vessel,
            'receiver': self.draw_vertical_vessel,
            'scrubber': self.draw_scrubber,
            'tank': self.draw_vertical_vessel,

            # Lines and Connections
            'n2_purge_line': self.draw_pipe_labeled('N₂'),
            'cooling_line': self.draw_pipe_labeled('Cool'),
            'discharge_line': self.draw_pipe_labeled('Disch'),
            'suction_line': self.draw_pipe_labeled('Suct'),
            'interconnecting_piping': self.draw_pipe_labeled('Interconnect'),
            'expansion_bellow': self.draw_expansion_bellow,
            'flex_conn_suction': self.draw_flexible,
            'flex_conn_discharge': self.draw_flexible,
            'drain_point': self.draw_pipe_labeled('Drain'),

            # Panels & Electrical
            'vfd': self.draw_box_labeled('VFD'),
            'motor': self.draw_motor,
            'motor_10hp_2pole_b5': self.draw_motor,
            'electrical_panel_box': self.draw_box_labeled('FLP/NFLP'),
            'flp_control_panel': self.draw_box_labeled('FLP Panel'),
            'split_control_panel': self.draw_box_labeled('Split Panel'),
            'control_panel': self.draw_box_labeled('CTRL'),

            # Other
            'base_plate': self.draw_box_labeled('Base'),
            'heated_panel': self.draw_box_labeled('Heater'),
            'cooling_tab': self.draw_box_labeled('Cool Tab'),
            'discharge_silencer': self.draw_box_labeled('Silencer'),
            'liquid_flushing_assembly': self.draw_box_labeled('Flush'),
            'n2_purge_assembly': self.draw_pipe_labeled('N₂ Purge'),
        }

    # === Symbol drawing functions ===
    def draw_vacuum_pump(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Pump().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_centrifugal_pump(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Circle(radius=1).label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_gear_pump(self, label, size):
        d = schemdraw.Drawing()
        d += flow.GearPump().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_butterfly_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='butterfly').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_control_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='globe').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_gate_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='gate').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_ball_valve(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='ball').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_circle_labeled(self, tag):
        def draw(label, size):
            d = schemdraw.Drawing()
            d += flow.Circle().label(f"{tag}\n{label}")
            return self.export_png(d), {'in': (0, -1)}
        return draw

    def draw_square_labeled(self, tag):
        def draw(label, size):
            d = schemdraw.Drawing()
            d += flow.Box().label(f"{tag}\n{label}")
            return self.export_png(d), {'in': (0, -1)}
        return draw

    def draw_condenser(self, label, size):
        d = schemdraw.Drawing()
        d += flow.HeatExchanger().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_filter(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Filter().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_strainer(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Valve(style='y-strainer').label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_expansion_bellow(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Wave().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_flexible(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Wave().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_box_labeled(self, text):
        def draw(label, size):
            d = schemdraw.Drawing()
            d += flow.Box().label(f"{text}\n{label}")
            return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}
        return draw

    def draw_motor(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Motor().label(label)
        return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}

    def draw_vertical_vessel(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Tank(h=2).label(label)
        return self.export_png(d), {'in': (0, 1), 'out': (0, -1)}

    def draw_scrubber(self, label, size):
        d = schemdraw.Drawing()
        d += flow.Tank(h=3).label("Scrubber\n"+label)
        return self.export_png(d), {'in': (0, 1), 'out': (0, -1)}

    def draw_pipe_labeled(self, tag):
        def draw(label, size):
            d = schemdraw.Drawing()
            d += flow.Line().right().label(f"{tag}\n{label}")
            return self.export_png(d), {'in': (-1, 0), 'out': (1, 0)}
        return draw
