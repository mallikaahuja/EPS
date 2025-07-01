# pid_drawer.py - Advanced Version

from graphviz import Digraph

def generate_pid(df_equipment, df_piping, df_inline):
    dot = Digraph(comment='Detailed P&ID')
    dot.attr(rankdir='TB', splines='ortho') # Top-to-Bottom layout, orthogonal lines
    dot.attr('node', shape='none', fixedsize='true', width='1.0', height='1.0') # Nodes are just images
    dot.attr('edge', arrowhead='none')

    # 1. Add all major equipment as nodes using their symbol images
    for _, row in df_equipment.iterrows():
        tag = str(row['Tag'])
        image_path = f"symbols/{row['Symbol_Image']}"
        # The label is placed below the image by using an HTML-like label
        label_html = f'''<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD><IMG SRC="{image_path}"/></TD></TR>
        <TR><TD>{tag}</TD></TR>
        </TABLE>
        >'''
        dot.node(name=tag, label=label_html)

    # 2. Process each pipe connection
    for _, pipe_row in df_piping.iterrows():
        pipe_tag = pipe_row['PipeTag']
        from_node = str(pipe_row['From_Tag'])
        to_node = str(pipe_row['To_Tag'])
        
        # Find all inline components for this specific pipe
        components_on_pipe = df_inline[df_inline['On_PipeTag'] == pipe_tag]
        
        last_connection_point = from_node
        
        if not components_on_pipe.empty:
            # If there are components, chain them together
            for _, comp_row in components_on_pipe.iterrows():
                comp_name = f"{pipe_tag}_{comp_row['Component_Tag']}"
                comp_image_path = f"symbols/{comp_row['Symbol_Image']}"
                comp_label = str(comp_row['Label'])

                # Create the node for the inline component
                dot.node(name=comp_name, image=comp_image_path, label=comp_label)
                
                # Connect the previous point to this new component
                dot.edge(last_connection_point, comp_name)
                last_connection_point = comp_name

        # Finally, connect the last point in the chain to the destination equipment
        dot.edge(last_connection_point, to_node)
        
    return dot
