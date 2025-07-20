# professional_symbols_fixed.py

"""
Professional P&ID Symbols - Using Industry Standard Libraries
Part 1: Core Infrastructure and Basic Symbols
Uses schemdraw + plotly for professional quality output
"""
import schemdraw
import schemdraw.elements as elm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional

class ProfessionalPIDRenderer:
    """
    Professional P&ID renderer using industry-standard libraries
    Integrates with your existing AI system while providing professional quality
    """
    def __init__(self):
        self.symbols = {}
        self.connections = []
        self.drawing = None
        self.plotly_fig = None

        # Professional color scheme
        self.colors = {
            'equipment': '#000000',
            'process_line': '#000000',
            'signal_line': '#0066CC',
            'utility_line': '#666666',
            'liquid': '#4A90E2',
            'gas': '#E8F4FD',
            'background': '#FFFFFF'
        }

        # Load your existing mappings
        self.load_component_mappings()

    def load_component_mappings(self):
        """Load your existing component mappings"""
        try:
            with open('component_mapping.json', 'r') as f:
                self.component_mapping = json.load(f)
        except FileNotFoundError:
            self.component_mapping = {}

    def create_professional_pid(self, equipment_data: List[Dict],
                                connections_data: List[Dict],
                                title: str = "Process Flow Diagram") -> go.Figure:
        """
        Create professional P&ID using plotly (better than matplotlib)
        Integrates with your existing AI equipment detection
        """
        # Create figure with professional layout
        fig = make_subplots(rows=1, cols=1,
                            subplot_titles=[title],
                            specs=[[{"secondary_y": False}]])

        # Set professional styling
        fig.update_layout(
            width=1600,
            height=1200,
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            font=dict(family="Arial", size=12, color=self.colors['equipment']),
            title=dict(text=title, x=0.5, font=dict(size=16, color=self.colors['equipment'])),
            showlegend=False,
            margin=dict(l=50, r=50, t=80, b=50)
        )

        # Draw equipment symbols
        for equipment in equipment_data:
            self.add_professional_symbol(fig, equipment)

        # Draw process lines
        for connection in connections_data:
            self.add_professional_line(fig, connection)

        # Add professional border and title block
        self.add_title_block(fig)
        self.add_drawing_border(fig)

        # Set axis properties for technical drawing
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='lightgray',
            showticklabels=False, range=[0, 20], constrain='domain'
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='lightgray',
            showticklabels=False, range=[0, 15], scaleanchor="x", scaleratio=1
        )

        self.plotly_fig = fig
        return fig

    def add_professional_symbol(self, fig: go.Figure, equipment: Dict):
        """Add professional equipment symbol using plotly shapes"""
        symbol_type = equipment.get('type', 'generic').lower()
        x, y = equipment.get('x', 0), equipment.get('y', 0)
        size = equipment.get('size', 1.0)
        label = equipment.get('label', '')

        if symbol_type in ['pump', 'centrifugal_pump', 'p']:
            self.draw_pump_plotly(fig, x, y, size, label)
        elif symbol_type in ['tank', 'storage_tank', 't']:
            self.draw_tank_plotly(fig, x, y, size, label)
        elif symbol_type in ['heat_exchanger', 'hx', 'he']:
            self.draw_hx_plotly(fig, x, y, size, label)
        elif symbol_type in ['control_valve', 'cv']:
            self.draw_control_valve_plotly(fig, x, y, size, label)
        elif symbol_type in ['flow_meter', 'ft']:
            self.draw_flow_transmitter_plotly(fig, x, y, size, label)
        else:
            self.draw_generic_equipment_plotly(fig, x, y, size, label)

    def draw_pump_plotly(self, fig: go.Figure, x: float, y: float,
                         size: float, label: str):
        """Professional centrifugal pump using plotly shapes"""
        radius = 0.8 * size

        # Main pump casing (circle)
        fig.add_shape(
            type="circle",
            x0=x-radius, y0=y-radius, x1=x+radius, y1=y+radius,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Suction nozzle (rectangle)
        suction_width = 0.5 * size
        suction_height = 0.3 * size
        fig.add_shape(
            type="rect",
            x0=x-radius-suction_width, y0=y-suction_height/2,
            x1=x-radius, y1=y+suction_height/2,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Discharge nozzle (rectangle)
        discharge_width = 0.25 * size
        discharge_height = 0.5 * size
        fig.add_shape(
            type="rect",
            x0=x-discharge_width/2, y0=y+radius,
            x1=x+discharge_width/2, y1=y+radius+discharge_height,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Impeller vanes (lines)
        impeller_radius = radius * 0.6
        angles = np.linspace(0, 2*np.pi, 7)[:-1]  # 6 vanes

        for angle in angles:
            start_r = impeller_radius * 0.3
            end_r = impeller_radius * 0.9
            curve_angle = angle + np.pi/8

            start_x = x + start_r * np.cos(angle)
            start_y = y + start_r * np.sin(angle)
            end_x = x + end_r * np.cos(curve_angle)
            end_y = y + end_r * np.sin(curve_angle)

            fig.add_shape(
                type="line",
                x0=start_x, y0=start_y, x1=end_x, y1=end_y,
                line=dict(color=self.colors['equipment'], width=2)
            )

        # Center hub (small circle)
        hub_radius = impeller_radius * 0.15
        fig.add_shape(
            type="circle",
            x0=x-hub_radius, y0=y-hub_radius, x1=x+hub_radius, y1=y+hub_radius,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor=self.colors['equipment']
        )

        # Equipment label
        fig.add_annotation(
            x=x, y=y-radius-0.6*size,
            text=label,
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

    def draw_tank_plotly(self, fig: go.Figure, x: float, y: float,
                         size: float, label: str):
        """Professional storage tank using plotly shapes"""
        width = 2.0 * size
        height = 3.0 * size

        # Main tank shell (rectangle)
        fig.add_shape(
            type="rect",
            x0=x-width/2, y0=y-height/2, x1=x+width/2, y1=y+height/2,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Top elliptical head
        head_height = 0.3 * size
        # Approximate ellipse with path
        theta = np.linspace(0, np.pi, 50)
        ellipse_x = x + (width/2) * np.cos(theta)
        ellipse_y = y + height/2 + (head_height/2) * np.sin(theta)

        fig.add_shape(
            type="path",
            path=f"M {ellipse_x[0]},{ellipse_y[0]} " +
                  " ".join([f"L {ex},{ey}" for ex, ey in zip(ellipse_x[1:], ellipse_y[1:])]),
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Bottom elliptical head
        ellipse_y_bottom = y - height/2 - (head_height/2) * np.sin(theta)
        fig.add_shape(
            type="path",
            path=f"M {ellipse_x[0]},{ellipse_y_bottom[0]} " +
                  " ".join([f"L {ex},{ey}" for ex, ey in zip(ellipse_x[1:], ellipse_y_bottom[1:])]),
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Liquid level (80% full)
        liquid_level = y - height/2 + 0.8 * height
        fig.add_shape(
            type="rect",
            x0=x-width/2+0.05, y0=y-height/2+0.1,
            x1=x+width/2-0.05, y1=liquid_level,
            line=dict(color=self.colors['liquid'], width=0),
            fillcolor=f"rgba(74,144,226,0.3)"
        )

        # Liquid level indicator line
        fig.add_shape(
            type="line",
            x0=x-width/2, y0=liquid_level, x1=x+width/2, y1=liquid_level,
            line=dict(color=self.colors['liquid'], width=2, dash="dash")
        )

        # Bottom outlet nozzle
        nozzle_width = 0.2 * size
        fig.add_shape(
            type="rect",
            x0=x-nozzle_width/2, y0=y-height/2-0.4*size,
            x1=x+nozzle_width/2, y1=y-height/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Top vent nozzle
        fig.add_shape(
            type="rect",
            x0=x+width/3-nozzle_width/2, y0=y+height/2,
            x1=x+width/3+nozzle_width/2, y1=y+height/2+0.3*size,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Side inlet nozzle
        fig.add_shape(
            type="rect",
            x0=x-width/2-0.3*size, y0=y+height/4-nozzle_width/2,
            x1=x-width/2, y1=y+height/4+nozzle_width/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Level gauge
        gauge_x = x + width/2 + 0.15 * size
        fig.add_shape(
            type="line",
            x0=gauge_x, y0=y-height/2, x1=gauge_x, y1=y+height/2,
            line=dict(color=self.colors['equipment'], width=3)
        )

        # Equipment label
        fig.add_annotation(
            x=x, y=y-height/2-0.7*size,
            text=label,
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

    def draw_hx_plotly(self, fig: go.Figure, x: float, y: float,
                       size: float, label: str):
        """Professional shell-and-tube heat exchanger"""
        shell_length = 4.0 * size
        shell_diameter = 1.5 * size

        # Main shell (rectangle)
        fig.add_shape(
            type="rect",
            x0=x-shell_length/2, y0=y-shell_diameter/2,
            x1=x+shell_length/2, y1=y+shell_diameter/2,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Tube bundle (parallel lines)
        tube_start_x = x - shell_length/2 + 0.3 * size
        tube_end_x = x + shell_length/2 - 0.3 * size
        for i in range(9):
            tube_y = y - shell_diameter/2 + (i + 1) * shell_diameter / 10
            fig.add_shape(
                type="line",
                x0=tube_start_x, y0=tube_y, x1=tube_end_x, y1=tube_y,
                line=dict(color=self.colors['equipment'], width=1.5)
            )

        # Shell nozzles
        nozzle_size = 0.25 * size

        # Hot inlet (top)
        fig.add_shape(
            type="rect",
            x0=x-shell_length/4-nozzle_size/2, y0=y+shell_diameter/2,
            x1=x-shell_length/4+nozzle_size/2, y1=y+shell_diameter/2+0.5*size,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Hot outlet (bottom)
        fig.add_shape(
            type="rect",
            x0=x+shell_length/4-nozzle_size/2, y0=y-shell_diameter/2-0.5*size,
            x1=x+shell_length/4+nozzle_size/2, y1=y-shell_diameter/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Cold inlet (left)
        fig.add_shape(
            type="rect",
            x0=x-shell_length/2-0.4*size, y0=y-nozzle_size/2,
            x1=x-shell_length/2, y1=y+nozzle_size/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # Cold outlet (right)
        fig.add_shape(
            type="rect",
            x0=x+shell_length/2, y0=y-nozzle_size/2,
            x1=x+shell_length/2+0.4*size, y1=y+nozzle_size/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # HX designation
        fig.add_annotation(
            x=x, y=y,
            text="HX",
            showarrow=False,
            font=dict(size=14, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

        # Equipment label
        fig.add_annotation(
            x=x, y=y-shell_diameter/2-0.8*size,
            text=label,
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

    def draw_control_valve_plotly(self, fig: go.Figure, x: float, y: float,
                                  size: float, label: str):
        """Professional control valve with pneumatic actuator"""
        body_width = 0.8 * size
        body_height = 0.6 * size

        # Valve body (rounded rectangle approximated with path)
        fig.add_shape(
            type="rect",
            x0=x-body_width/2, y0=y-body_height/2,
            x1=x+body_width/2, y1=y+body_height/2,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Valve seat (horizontal line)
        fig.add_shape(
            type="line",
            x0=x-body_width*0.35, y0=y-body_height/4,
            x1=x+body_width*0.35, y1=y-body_height/4,
            line=dict(color=self.colors['equipment'], width=3)
        )

        # Valve plug (triangle approximation)
        plug_points = [
            [x-0.1*size, y+body_height/4],
            [x+0.1*size, y+body_height/4],
            [x, y-body_height/4+0.05*size],
            [x-0.1*size, y+body_height/4]
        ]
        plug_x = [p[0] for p in plug_points]
        plug_y = [p[1] for p in plug_points]
        fig.add_shape(
            type="path",
            path=f"M {plug_x[0]},{plug_y[0]} " +
                  " ".join([f"L {px},{py}" for px, py in zip(plug_x[1:], plug_y[1:])]) + " Z",
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor=self.colors['equipment']
        )

        # Valve stem
        stem_length = 1.0 * size
        fig.add_shape(
            type="line",
            x0=x, y0=y+body_height/2, x1=x, y1=y+body_height/2+stem_length,
            line=dict(color=self.colors['equipment'], width=4)
        )

        # Pneumatic actuator (ellipse approximated with circle)
        actuator_radius = 0.5 * size
        actuator_y = y + body_height/2 + stem_length
        fig.add_shape(
            type="circle",
            x0=x-actuator_radius, y0=actuator_y-actuator_radius*0.5,
            x1=x+actuator_radius, y1=actuator_y+actuator_radius*0.5,
            line=dict(color=self.colors['equipment'], width=3),
            fillcolor="rgba(255,255,255,0)"
        )

        # Control signal line
        signal_x = x + actuator_radius + 0.2 * size
        fig.add_shape(
            type="line",
            x0=x+actuator_radius, y0=actuator_y, x1=signal_x, y1=actuator_y,
            line=dict(color=self.colors['signal_line'], width=2, dash="dash")
        )

        # I/P converter
        fig.add_shape(
            type="rect",
            x0=signal_x, y0=actuator_y-0.15*size,
            x1=signal_x+0.3*size, y1=actuator_y+0.15*size,
            line=dict(color=self.colors['signal_line'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )

        # I/P label
        fig.add_annotation(
            x=signal_x+0.15*size, y=actuator_y,
            text="I/P",
            showarrow=False,
            font=dict(size=8, color=self.colors['signal_line'])
        )

        # Fail closed indicator
        fig.add_annotation(
            x=x, y=actuator_y-0.2*size,
            text="FC",
            showarrow=False,
            font=dict(size=10, color="black"),
            bgcolor="yellow",
            bordercolor="black",
            borderwidth=1
        )

        # Equipment label
        fig.add_annotation(
            x=x, y=y-body_height/2-0.5*size,
            text=label,
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

    def draw_flow_transmitter_plotly(self, fig: go.Figure, x: float, y: float,
                                     size: float, label: str):
        """Professional flow transmitter"""
        radius = 0.4 * size

        # Instrument circle
        fig.add_shape(
            type="circle",
            x0=x-radius, y0=y-radius, x1=x+radius, y1=y+radius,
            line=dict(color=self.colors['equipment'], width=2.5),
            fillcolor="white"
        )

        # Function letters
        fig.add_annotation(
            x=x, y=y,
            text="FT",
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment'])
        )

        # Signal line
        fig.add_shape(
            type="line",
            x0=x, y0=y+radius, x1=x, y1=y+radius+0.5*size,
            line=dict(color=self.colors['signal_line'], width=2, dash="dash")
        )

        # Instrument label
        fig.add_annotation(
            x=x, y=y-radius-0.3*size,
            text=label,
            showarrow=False,
            font=dict(size=10, color=self.colors['equipment'])
        )

    def draw_generic_equipment_plotly(self, fig: go.Figure, x: float, y: float,
                                      size: float, label: str):
        """Generic equipment symbol"""
        width = 1.0 * size
        height = 1.0 * size

        fig.add_shape(
            type="rect",
            x0=x-width/2, y0=y-height/2, x1=x+width/2, y1=y+height/2,
            line=dict(color=self.colors['equipment'], width=2),
            fillcolor="rgba(255,255,255,0)"
        )
        fig.add_annotation(
            x=x, y=y,
            text="?",
            showarrow=False,
            font=dict(size=14, color=self.colors['equipment'])
        )
        fig.add_annotation(
            x=x, y=y-height/2-0.3*size,
            text=label,
            showarrow=False,
            font=dict(size=12, color=self.colors['equipment']),
            bgcolor="white",
            bordercolor=self.colors['equipment'],
            borderwidth=1
        )

    def add_professional_line(self, fig: go.Figure, connection: Dict):
        """Add professional process lines"""
        start = connection.get('start', (0, 0))
        end = connection.get('end', (0, 0))
        line_type = connection.get('type', 'process')
        line_styles = {
            'process': {'color': self.colors['process_line'], 'width': 3, 'dash': None},
            'signal': {'color': self.colors['signal_line'], 'width': 2, 'dash': 'dash'},
            'utility': {'color': self.colors['utility_line'], 'width': 2, 'dash': 'dot'}
        }
        style = line_styles.get(line_type, line_styles['process'])
        fig.add_shape(
            type="line",
            x0=start[0], y0=start[1], x1=end[0], y1=end[1],
            line=dict(color=style['color'], width=style['width'], dash=style['dash'])
        )

    def add_title_block(self, fig: go.Figure):
        """Add professional title block"""
        # Title block (bottom right)
        fig.add_shape(
            type="rect",
            x0=14, y0=1, x1=19.5, y1=3.5,
            line=dict(color="black", width=2),
            fillcolor="white"
        )
        fig.add_annotation(
            x=16.75, y=3,
            text="PROCESS FLOW DIAGRAM",
            showarrow=False,
            font=dict(size=12, color="black")
        )
        fig.add_annotation(
            x=16.75, y=2.2,
            text="AI Generated P&ID",
            showarrow=False,
            font=dict(size=10, color="black", family="Arial")
        )
        fig.add_annotation(
            x=14.2, y=1.2,
            text="Drawing No: AI-PID-001",
            showarrow=False,
            font=dict(size=8, color="black")
        )
        fig.add_annotation(
            x=19.3, y=1.2,
            text="Rev: A",
            showarrow=False,
            font=dict(size=8, color="black")
        )

    def add_drawing_border(self, fig: go.Figure):
        """Add professional drawing border"""
        fig.add_shape(
            type="rect",
            x0=0.5, y0=0.5, x1=19.5, y1=14.5,
            line=dict(color="black", width=3),
            fillcolor="rgba(255,255,255,0)"
        )
