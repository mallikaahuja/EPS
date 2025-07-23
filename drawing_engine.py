import networkx as nx
import plotly.graph_objects as go
from symbols import SymbolRenderer
import io
from PIL import Image
import base64

class DrawingEngine:
    def __init__(self):
        self.symbol_renderer = SymbolRenderer()
        self.graph = nx.DiGraph()
        self.positions = {}
        self.layout_spacing = (3, 3)
        self.symbol_size = 1.0
        self.tag_counter = {}

    def add_equipment(self, node_id: str, component_type: str, label: str = "", position=None):
        """Adds a component to the internal graph with optional fixed position"""
        label_with_tag = self.generate_tag(component_type, label)
        self.graph.add_node(node_id, type=component_type, label=label_with_tag)
        if position:
            self.positions[node_id] = position

    def add_connection(self, from_node: str, to_node: str):
        """Adds directional connection between two nodes"""
        self.graph.add_edge(from_node, to_node)

    def generate_tag(self, component_type, label):
        """Auto-generates ISA-style tag like PT-101"""
        base = ''.join([w[0].upper() for w in component_type.split('_')[:2]])
        count = self.tag_counter.get(base, 100)
        self.tag_counter[base] = count + 1
        return f"{base}-{count}\n{label}"

    def compute_layout(self):
        """Uses NetworkX spring layout if positions are not manually given"""
        if not self.positions:
            self.positions = nx.spring_layout(self.graph, scale=10, k=2)

    def render(self) -> go.Figure:
        """Main rendering function using Plotly"""
        self.compute_layout()
        fig = go.Figure()
        fig.update_layout(
            width=1600,
            height=1000,
            plot_bgcolor='white',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        # Draw connections (lines)
        for src, dst in self.graph.edges():
            x0, y0 = self.positions[src]
            x1, y1 = self.positions[dst]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines+markers',
                line=dict(color='black', width=2),
                marker=dict(size=4),
                hoverinfo='skip'
            ))

        # Draw nodes (symbols)
        for node_id, attrs in self.graph.nodes(data=True):
            comp_type = attrs.get("type", "box")
            label = attrs.get("label", "")
            img_bytes, ports = self.symbol_renderer.render_symbol(comp_type, label, self.symbol_size)

            # Decode image
            encoded = base64.b64encode(img_bytes).decode('utf-8')
            img_uri = f'data:image/png;base64,{encoded}'
            x, y = self.positions[node_id]

            fig.add_layout_image(
                dict(
                    source=f"{img_uri}",
                    xref="x", yref="y",
                    x=x - 1.5, y=y + 1.5,
                    sizex=3, sizey=3,
                    xanchor="left", yanchor="top",
                    layer="above"
                )
            )

        return fig

    def export_png(self, fig: go.Figure, path="output.png"):
        """Save Plotly figure as PNG"""
        fig.write_image(path, format='png')
