import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai
import ezdxf
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Intelligent P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True) # Create a temporary directory for placeholders

# --- HELPER FUNCTIONS ---

def create_placeholder_image(text, path):
    """✅ 7. Creates a placeholder image with text if a symbol is missing."""
    try:
        img = Image.new('RGB', (100, 75), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        # Use a built-in font if available, otherwise default
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except IOError:
            font = ImageFont.load_default()
        d.rectangle([0,0,99,74], outline="black")
        d.text((10,30), f"MISSING:\n{text}", fill=(0,0,0), font=font)
        img.save(path)
        return str(path)
    except Exception as e:
        st.error(f"Failed to create placeholder image: {e}")
        return None

def get_ai_suggestions(dfs):
    """✅ 4. Fetches engineering suggestions from OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY") # ✅ 1. Uses os.environ for Railway
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in environment variables."

    client = openai.OpenAI(api_key=api_key)
    
    # Create a detailed text description of the P&ID for the AI
    description = "Review this P&ID data for standard engineering practice:\n"
    description += "EQUIPMENT:\n" + "\n".join([f"- {e['Tag']} ({e['Type']})" for _, e in dfs['Equipment'].iterrows()]) + "\n"
    description += "PIPELINES:\n" + "\n".join([f"- {p['PipeTag']} (from {p['From_Tag']} to {p['To_Tag']})" for _, p in dfs['Piping'].iterrows()]) + "\n"
    if 'In-Line_Components' in dfs and not dfs['In-Line_Components'].empty:
        description += "IN-LINE ITEMS:\n" + "\n".join([f"- {c['Component_Tag']} ({c['Description']}) on {c['On_PipeTag']}" for _, c in dfs['In-Line_Components'].iterrows()])
    
    prompt = (
        "You are an expert senior process engineer. Based on the following P&ID data, provide 3 concise, "
        "actionable recommendations for improving safety, operability, or adhering to standards. "
        "Focus on missing items like isolation valves, check valves, vents, drains, or instrumentation.\n\n"
        f"P&ID DATA:\n{description}"
    )
    
    try:
        with st.spinner("🤖 AI Engineer is analyzing the P&ID..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5, max_tokens=200
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not get AI suggestions. Error: {e}"

def generate_graphviz_dot(dfs):
    """✅ 5. Generates the P&ID with automatic layout logic."""
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.2', label='P&ID Live Preview', labelloc='t', fontsize='16')
    
    equipment_df = dfs.get('Equipment', pd.DataFrame())
    piping_df = dfs.get('Piping', pd.DataFrame())
    inline_df = dfs.get('In-Line_Components', pd.DataFrame())

    # Auto-layout based on common process flow
    pump_tags = equipment_df[equipment_df['Type'].str.contains("Pump", case=False)]['Tag'].tolist()
    
    with dot.subgraph(name='cluster_main_process') as c:
        c.attr(label='Main Process Flow', style='dashed')
        for _, equip in equipment_df.iterrows():
            tag = equip['Tag']
            img_filename = equip['Symbol_Image']
            img_path = SYMBOLS_DIR / img_filename
            
            if not img_path.exists():
                placeholder_path = TEMP_DIR / img_filename
                create_placeholder_image(equip['Type'], placeholder_path)
                img_path = placeholder_path

            c.node(tag, label=tag, image=str(img_path), shape='none', imagepos='tc', labelloc='b')

    # Connect components with in-line items
    for _, pipe in piping_df.iterrows():
        components_on_pipe = inline_df[inline_df['On_PipeTag'] == pipe['PipeTag']]
        last_node = pipe['From_Tag']
        
        for _, comp in components_on_pipe.iterrows():
            comp_name = f"{comp['Component_Tag']}_{pipe['PipeTag']}"
            img_filename = comp['Symbol_Image']
            img_path = SYMBOLS_DIR / img_filename

            if not img_path.exists():
                placeholder_path = TEMP_DIR / img_filename
                create_placeholder_image(comp['Description'], placeholder_path)
                img_path = placeholder_path

            dot.node(comp_name, label=comp['Component_Tag'], image=str(img_path), shape='none', imagepos='tc', labelloc='b')
            dot.edge(last_node, comp_name, label=pipe['PipeTag'])
            last_node = comp_name
        
        dot.edge(last_node, pipe['To_Tag'])

    return dot

def create_dxf_data(dfs):
    """✅ 3. Creates a simplified DXF file for download."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    y_pos = 0
    # A very simplified layout for DXF
    for _, equip in dfs['Equipment'].iterrows():
        msp.add_circle((0, y_pos), radius=2, dxfattribs={"layer": "Equipment"})
        msp.add_text(equip['Tag'], dxfattribs={'height': 0.5}).set_pos((3, y_pos))
        y_pos -= 10
    return doc.encode()

# --- STREAMLIT APP UI ---
st.title("🧠 Intelligent P&ID Generator")

with st.sidebar:
    st.header("1. Load P&ID Data")
    uploaded_file = st.file_uploader(
        "Upload your standardized P&ID Excel file.",
        type=["xlsx"]
    )
    # Load data from the uploaded file into session state
    if uploaded_file:
        if 'p_and_id_data' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
            try:
                sheets = pd.read_excel(uploaded_file, sheet_name=None)
                st.session_state.p_and_id_data = sheets
                st.session_state.file_name = uploaded_file.name
                st.success(f"Loaded `{uploaded_file.name}` successfully!")
            except Exception as e:
                st.error(f"Failed to read Excel file: {e}")

if 'p_and_id_data' in st.session_state:
    data_frames = st.session_state.p_and_id_data
    
    # Define tabs for the main interface
    preview_tab, ai_tab, data_tab, export_tab = st.tabs(["P&ID Preview", "AI Suggestions", "Data Tables", "Export"])

    with preview_tab:
        st.subheader("P&ID Live Preview")
        # ✅ 2. Scrollable/Zoomable Preview Panel
        with st.container(height=600, border=True):
            dot = generate_graphviz_dot(data_frames)
            st.graphviz_chart(dot)

    with ai_tab:
        st.subheader("🤖 AI Engineer Co-pilot")
        st.info("Click the button to get standard engineering practice recommendations based on your current P&ID.")
        if st.button("Analyze P&ID"):
            suggestions = get_ai_suggestions(data_frames)
            st.markdown(suggestions)

    with data_tab:
        st.subheader("✅ 6. P&ID Data from Excel")
        st.info("Verify the data loaded from your Excel file.")
        for name, df in data_frames.items():
            st.write(f"**Sheet: `{name}`**")
            st.dataframe(df)

    with export_tab:
        st.subheader("⬇️ Export Your Diagram")
        
        # PNG Download
        try:
            dot = generate_graphviz_dot(data_frames)
            png_data = dot.pipe(format='png')
            st.download_button("Download P&ID as PNG", png_data, "p_and_id.png", "image/png", use_container_width=True)
        except Exception as e:
            st.error(f"PNG Export failed: {e}")
        
        # DXF Download
        try:
            dxf_data = create_dxf_data(data_frames)
            st.download_button("Download as DXF", dxf_data, "p_and_id.dxf", "application/dxf", use_container_width=True)
        except Exception as e:
            st.error(f"DXF Export failed: {e}")
else:
    st.info("Please upload an Excel file in the sidebar to begin.")
