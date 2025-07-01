# pid_drawer.py

from graphviz import Digraph

# This dictionary maps your equipment "Type" from Excel to a shape and color.
# You can customize these!
SHAPE_MAP = {
    'Tank':        {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'lightblue'},
    'Pump':        {'shape': 'triangle', 'style': 'filled', 'fillcolor': 'lightgreen'},
    'HeatExchanger':{'shape': 'box',      'style': 'filled', 'fillcolor': 'orange'},
    'Reactor':     {'shape': 'doublecircle', 'style': 'filled', 'fillcolor': 'pink'},
    'Vessel':      {'shape': 'ellipse',  'style': 'filled', 'fillcolor': 'lightgrey'},
    'Default':     {'shape': 'box',      'style': 'filled', 'fillcolor': 'grey'}
}

def generate_pid(df_equipment, df_piping):
    """
    This function takes your data and draws the P&ID.
    """
    # 1. Create a new blank diagram
    dot = Digraph(comment='Process and Instrumentation Diagram')
    dot.attr('node', shape='box', style='rounded') # Default style for nodes
    dot.attr(rankdir='LR') # Layout from Left to Right

    # 2. Add all the equipment from your Excel data
    for index, row in df_equipment.iterrows():
        tag = row['Tag']
        equip_type = row['Type']
        
        # Look up the shape and color from our map
        shape_attrs = SHAPE_MAP.get(equip_type, SHAPE_MAP['Default'])
        
        # Add the equipment to the diagram
        dot.node(name=tag, label=tag, **shape_attrs)

    # 3. Add all the pipes connecting the equipment
    for index, row in df_piping.iterrows():
        from_node = row['From']
        to_node = row['To']
        pipe_label = f"{row['PipeTag']}" # Label for the pipe
        
        # Add the pipe to the diagram
        dot.edge(from_node, to_node, label=pipe_label)
        
    return dot
