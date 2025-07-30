# symbols.py - FIXED VERSION with better error handling and debugging

import schemdraw
import schemdraw.elements as elm
from schemdraw import flow
import matplotlib.pyplot as plt
import io
from typing import Dict, Tuple
import traceback

class SymbolRenderer:
    def __init__(self):
        self.port_map = {}
        print("🎨 SymbolRenderer initialized with schemdraw")

    def export_png(self, drawing) -> bytes:
        """Fixed PNG export with better error handling"""
        try:
            # Set up the drawing properly
            buf = io.BytesIO()
            
            # Get the image data directly from schemdraw
            img_data = drawing.get_imagedata('png')
            
            if img_data and len(img_data) > 0:
                return img_data
            else:
                # Fallback: try matplotlib method
                drawing.draw()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
                plt.close()
                png_data = buf.getvalue()
                buf.close()
                return png_data
                
        except Exception as e:
            print(f"❌ PNG export failed: {e}")
            # Return a minimal fallback image
            return self._create_fallback_png()

    def _create_fallback_png(self) -> bytes:
        """Create a simple fallback PNG when schemdraw fails"""
        try:
            fig, ax = plt.subplots(figsize=(2, 1))
            ax.text(0.5, 0.5, 'ERR', ha='center', va='center', fontsize=12)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            png_data = buf.getvalue()
            buf.close()
            return png_data
        except:
            return b''  # Empty bytes as last resort

    def render_symbol(self, component_id: str, label: str = "", size: float = 1.0) -> Tuple[bytes, Dict]:
        """Fixed render_symbol with comprehensive debugging"""
        
        print(f"🔧 Rendering symbol for: {component_id} (label: {label})")
        
        try:
            # Clean up component_id for mapping
            clean_id = component_id.lower().strip()
            
            # Get the drawing method
            symbol_map = self.symbol_map()
            draw_method = symbol_map.get(clean_id)
            
            if not draw_method:
                print(f"⚠️  No symbol defined for: {component_id}, available symbols: {list(symbol_map.keys())[:10]}...")
                return self.draw_generic(label)
            
            # Call the drawing method
            print(f"✅ Found symbol method for {clean_id}")
            png_bytes, ports = draw_method(label, size)
            
            if png_bytes and len(png_bytes) > 0:
                print(f"✅ Symbol rendered successfully: {len(png_bytes)} bytes")
                return png_bytes, ports
            else:
                print(f"❌ Symbol method returned empty data")
                return self.draw_generic(label)
                
        except Exception as e:
            print(f"❌ Symbol rendering failed for {component_id}: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return self.draw_generic(label)

    def draw_generic(self, label: str) -> Tuple[bytes, Dict]:
        """Fixed generic symbol with better schemdraw handling"""
        try:
            print(f"🔨 Drawing generic symbol for: {label}")
            d = schemdraw.Drawing()
            d.add(flow.Box(w=3, h=2).label(label))
            
            png_bytes = self.export_png(d)
            ports = {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
            
            print(f"✅ Generic symbol created: {len(png_bytes)} bytes")
            return png_bytes, ports
            
        except Exception as e:
            print(f"❌ Generic symbol failed: {e}")
            return self._create_fallback_png(), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}

    def symbol_map(self) -> Dict[str, callable]:
        """Enhanced symbol mapping with more component types"""
        return {
            # Equipment from your CSV
            'eb-001': self.draw_expansion_bellow,
            'ys-001': self.draw_strainer,
            'v-001': self.draw_gate_valve,
            'fa-001': self.draw_filter,
            'v-002': self.draw_gate_valve,
            
            # Generic types
            'expansion_bellows': self.draw_expansion_bellow,
            'expansionbellows': self.draw_expansion_bellow,
            'fitting': self.draw_expansion_bellow,
            
            'y_strainer': self.draw_strainer,
            'ystrainer': self.draw_strainer,
            'filter': self.draw_filter,
            'strainer': self.draw_strainer,
            
            'gate_valve': self.draw_gate_valve,
            'valve': self.draw_gate_valve,
            
            'flame_arrestor': self.draw_filter,
            'flamearrestor': self.draw_filter,
            'safety': self.draw_filter,
            
            # Pumps
            'dry_screw_pump': self.draw_vacuum_pump,
            'centrifugal_pump': self.draw_centrifugal_pump,
            'gear_pump': self.draw_gear_pump,
            'pump': self.draw_vacuum_pump,

            # Valves
            'epo_butterfly_valve': self.draw_butterfly_valve,
            'control_valve': self.draw_control_valve,
            'ball_valve': self.draw_ball_valve,
            'temperature_control_valve': self.draw_control_valve,
            'solenoid_valve': self.draw_control_valve,

            # Transmitters & Instruments
            'pressure_transmitter': self.draw_circle_labeled('PT'),
            'temperature_transmitter': self.draw_circle_labeled('TT'),
            'flow_transmitter': self.draw_circle_labeled('FT'),
            'level_transmitter': self.draw_circle_labeled('LT'),
            'pressure_switch': self.draw_square_labeled('PS'),

            # Filters
            'acg_filter': self.draw_filter,
            'suction_filter': self.draw_filter,

            # Vessels
            'vapour_condenser': self.draw_condenser,
            'catch_pot': self.draw_vertical_vessel,
            'receiver': self.draw_vertical_vessel,
            'tank': self.draw_vertical_vessel,

            # Other
            'motor': self.draw_motor,
            'vfd': self.draw_box_labeled('VFD'),
        }

    # === FIXED Symbol drawing functions ===
    def draw_vacuum_pump(self, label, size):
        """Fixed vacuum pump with error handling"""
        try:
            d = schemdraw.Drawing()
            # Use a more basic pump representation if flow.Pump doesn't work
            try:
                d.add(flow.Pump().label(label))
            except:
                # Fallback to circle with P
                d.add(flow.Circle(radius=1).label(f'P\n{label}'))
            
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Vacuum pump drawing failed: {e}")
            return self.draw_generic(label)

    def draw_centrifugal_pump(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Circle(radius=1).label(f'CP\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Centrifugal pump drawing failed: {e}")
            return self.draw_generic(label)

    def draw_gate_valve(self, label, size):
        try:
            d = schemdraw.Drawing()
            # Try schemdraw valve, fallback to box
            try:
                d.add(flow.Valve().label(label))
            except:
                d.add(flow.Box(w=1, h=1).label(f'V\n{label}'))
            
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Gate valve drawing failed: {e}")
            return self.draw_generic(label)

    def draw_strainer(self, label, size):
        try:
            d = schemdraw.Drawing()
            # Y-strainer representation
            try:
                d.add(flow.Filter().label(f'Y\n{label}'))
            except:
                d.add(flow.Box(w=1.5, h=1).label(f'STR\n{label}'))
            
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Strainer drawing failed: {e}")
            return self.draw_generic(label)

    def draw_filter(self, label, size):
        try:
            d = schemdraw.Drawing()
            try:
                d.add(flow.Filter().label(label))
            except:
                d.add(flow.Box(w=1.5, h=1.5).label(f'F\n{label}'))
            
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Filter drawing failed: {e}")
            return self.draw_generic(label)

    def draw_expansion_bellow(self, label, size):
        try:
            d = schemdraw.Drawing()
            # Create expansion bellows representation
            try:
                d.add(flow.Wire().to('right', 2).label(label, loc='bottom'))
                # Add bellows indication
                d.add(elm.Line().up(0.3).at(d.here).color('blue'))
                d.add(elm.Line().down(0.3).at(d.here).color('blue'))
            except:
                d.add(flow.Box(w=2, h=0.8).label(f'EB\n{label}'))
            
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            print(f"❌ Expansion bellow drawing failed: {e}")
            return self.draw_generic(label)

    def draw_circle_labeled(self, tag):
        def draw(label, size):
            try:
                d = schemdraw.Drawing()
                d.add(flow.Circle(radius=0.8).label(f"{tag}\n{label}"))
                return self.export_png(d), {'connection': (0.5, 0)}
            except Exception as e:
                print(f"❌ Circle labeled drawing failed: {e}")
                return self.draw_generic(f"{tag}-{label}")
        return draw

    def draw_square_labeled(self, tag):
        def draw(label, size):
            try:
                d = schemdraw.Drawing()
                d.add(flow.Box(w=1.2, h=1.2).label(f"{tag}\n{label}"))
                return self.export_png(d), {'connection': (0.5, 0)}
            except Exception as e:
                print(f"❌ Square labeled drawing failed: {e}")
                return self.draw_generic(f"{tag}-{label}")
        return draw

    def draw_condenser(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=2, h=1.5).label(f'COND\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_vertical_vessel(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=1.2, h=2.5).label(label))
            return self.export_png(d), {'inlet': (0.5, 1), 'outlet': (0.5, 0)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_motor(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Circle(radius=1).label(f'M\n{label}'))
            return self.export_png(d), {'connection': (0, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_box_labeled(self, text):
        def draw(label, size):
            try:
                d = schemdraw.Drawing()
                d.add(flow.Box(w=2, h=1.5).label(f"{text}\n{label}"))
                return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
            except Exception as e:
                return self.draw_generic(f"{text}-{label}")
        return draw

    # Keep all your other existing methods...
    def draw_butterfly_valve(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=1, h=1).label(f'BV\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_control_valve(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=1, h=1).label(f'CV\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_ball_valve(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Circle(radius=0.6).label(f'BV\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_gear_pump(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=1.5, h=1.2).label(f'GP\n{label}'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_scrubber(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(flow.Box(w=1.5, h=3).label(f"SCR\n{label}"))
            return self.export_png(d), {'inlet': (0.5, 1), 'outlet': (0.5, 0)}
        except Exception as e:
            return self.draw_generic(label)

    def draw_pipe_labeled(self, tag):
        def draw(label, size):
            try:
                d = schemdraw.Drawing()
                d.add(elm.Line().right(2).label(f"{tag}\n{label}", loc='top'))
                return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
            except Exception as e:
                return self.draw_generic(f"{tag}-{label}")
        return draw

    def draw_flexible(self, label, size):
        try:
            d = schemdraw.Drawing()
            d.add(elm.Line().right(2).label(f"FLEX\n{label}", loc='top'))
            return self.export_png(d), {'inlet': (0, 0.5), 'outlet': (1, 0.5)}
        except Exception as e:
            return self.draw_generic(label)

# ADD THIS TEST FUNCTION to test your symbol renderer directly

def test_symbol_renderer():
    """Test function to verify schemdraw symbol renderer"""
    renderer = SymbolRenderer()

    test_components = ['EB-001', 'YS-001', 'V-001', 'pump', 'valve', 'filter']

    for comp in test_components:
        print(f"\n🧪 Testing {comp}:")
        try:
            # The label and size arguments are required by render_symbol
            png_bytes, ports = renderer.render_symbol(comp, comp, 1.0)
            print(f"  Result: {len(png_bytes)} bytes, {ports}")
        except Exception as e:
            print(f"  Failed: {e}")

# Uncomment to test:
# test_symbol_renderer()
