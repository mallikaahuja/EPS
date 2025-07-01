# pid_drawer.py

from graphviz import Digraph

# This dictionary maps equipment "Type" from Excel to a shape and color.
SHAPE_MAP = {
    'Tank':        {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'lightblue'},
    'Pump':        {'shape': 'triangle', 'style': 'filled', 'fillcolor': 'lightgreen', 'orientation': '270'},
    'HeatExchanger':{'shape': 'box',      'style': 'filled', 'fillcolor': 'orange'},
    'Reactor':     {'shape': 'doublecircle', 'style': 'filled', 'fillcolor': 'pink'},
    'Vessel':      {'shape': 'ellipse',  'style': 'filled', 'fillcolor': 'lightgrey'},
    'Default':     {'shape': 'box',      'style': 'filled', 'fillcolor': 'grey'}
}

def generate_pid(df_equipment, df_piping):
    # 1. Create a new blank diagram
    dot = Digraph(comment='Process and Instrumentation Diagram')
    dot.attr(rankdir='LR', size='15,8') # Layout from Left to Right
    dot.attr('node', shape='box', style='rounded')

    # 2. Add all the equipment (nodes)
    for index, row in df_equipment.iterrows():
        tag = row['Tag']
        equip_type = row.get('Type', 'Default') # Use .get() for safety
        description = row.get('Description', '')
        
        shape_attrs = SHAPE_MAP.get(equip_type, SHAPE_MAP['Default']).copy()
        
        label = f"{tag}\n{description}"
        dot.node(name=tag, label=label, **shape_attrs)

    # 3. Add all the pipes (edges)
    for index, row in df_piping.iterrows():
        from_node = row['From']
        to_node = row['To']
        pipe_label = f"{row.get('PipeTag', '')}\n{row.get('Size', '')}\" {row.get('Fluid', '')}"
        
        dot.edge(from_node, to_node, label=pipe_label)
        
    return dot
