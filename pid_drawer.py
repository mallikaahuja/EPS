# pid_drawer.py - Modified to use the folder "PN&D-Symbols-library"

from graphviz import Digraph
import os 

def generate_pid(df_equipment, df_piping, df_inline):
    dot = Digraph(comment='Detailed P&ID')
    dot.attr(rankdir='TB', splines='ortho', nodesep='1.0', ranksep='1.5')
    dot.attr('node', shape='none', fixedsize='true', width='1.0', height='1.0', fontsize='10')
    dot.attr('edge', arrowhead='none')

    # --- 1. Add Major Equipment ---
    for _, row in df_equipment.iterrows():
        tag = str(row['Tag'])
        image_filename = str(row['Symbol_Image'])
        
        # <<< CHANGE IS HERE
        image_path = f"PN&D-Symbols-library/{image_filename}"

        if not os.path.exists(image_path):
            print(f"!!! WARNING: Image not found for equipment '{tag}': {image_path}")
            dot.node(name=tag, label=f"{tag}\n(img missing)", shape='box', style='dashed')
            continue

        dot.node(name=tag, label=tag, image=image_path)

    # --- 2. Add In-Line Components ---
    for _, pipe_row in df_piping.iterrows():
        pipe_tag = str(pipe_row['PipeTag'])
        from_node = str(pipe_row['From_Tag'])
        to_node = str(pipe_row['To_Tag'])
        
        components_on_pipe = df_inline[df_inline['On_PipeTag'] == pipe_tag]
        last_connection_point = from_node
        
        if not components_on_pipe.empty:
            for _, comp_row in components_on_pipe.iterrows():
                comp_name = f"{pipe_tag}_{comp_row['Component_Tag']}"
                comp_label = str(comp_row['Label'])
                comp_image_filename = str(comp_row['Symbol_Image'])

                # <<< CHANGE IS HERE
                comp_image_path = f"PN&D-Symbols-library/{comp_image_filename}"

                if not os.path.exists(comp_image_path):
                    print(f"!!! WARNING: Image not found for component '{comp_name}': {comp_image_path}")
                    dot.node(name=comp_name, label=f"{comp_label}\n(img missing)", shape='circle', style='dashed')
                else:
                    dot.node(name=comp_name, label=comp_label, image=comp_image_path)
                
                dot.edge(last_connection_point, comp_name)
                last_connection_point = comp_name

        dot.edge(last_connection_point, to_node)
        
    return dot
