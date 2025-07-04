import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path
import os
import openai
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Intelligent P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = Path("symbols")
TEMP_DIR = Path("temp_placeholders")
TEMP_DIR.mkdir(exist_ok=True)

# --- COMPONENT LIBRARY ---
# This dictionary MUST match the standardized filenames in your "symbols" folder.
AVAILABLE_COMPONENTS = {
    # This should be your full, standardized list
    "Vertical Vessel": "vertical_vessel.png",
    "Butterfly Valve": "butterfly_valve.png",
    "Gate Valve": "gate_valve.png",
    # etc...
}
EQUIPMENT_TYPES = sorted(["Vertical Vessel", "Dry Pump Model", "Discharge Condenser", "Scrubber"])
INLINE_TYPES = sorted([comp for comp in AVAILABLE_COMPONENTS if comp not in EQUIPMENT_TYPES])


# --- HELPER FUNCTIONS ---
def create_placeholder_image(text, path):
    try:
        img = Image.new('RGB', (100, 75), color=(240, 240, 240))
        d = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        d.rectangle([0,0,99,74], outline="black")
        d.text((10,30), f"MISSING:\n{text}", fill=(0,0,0), font=font)
        img.save(path)
        return str(path)
    except Exception:
        return None

def get_ai_suggestions():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI suggestions disabled. `OPENAI_API_KEY` not found in Railway variables."
    client = openai.OpenAI(api_key=api_key)
    description = "Review P&ID data: " + str(st.session_state.get('p_and_id_data', {}))
    prompt = f"You are a senior process engineer. Review this P&ID data and provide 3 concise, actionable recommendations for improving safety or operability. Focus on missing items like isolation valves or basic instrumentation.\n\nP&ID DATA:\n{description}"
    try:
        with st.spinner("🤖 AI Engineer is analyzing..."):
            response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.5, max_tokens=200)
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not get AI suggestions. Error: {e}"

def generate_graphviz_dot(dfs):
    dot = Digraph('P&ID')
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.2', label='P&ID Live Preview', labelloc='t', fontsize='16')
    equipment_df = dfs.get('Equipment', pd.DataFrame())
    piping_df = dfs.get('Piping', pd.DataFrame())
    inline_df = dfs.get('In-Line_Components', pd.DataFrame())
    if equipment_df.empty: return dot

    with dot.subgraph(name='cluster_main_process') as c:
        c.attr(label='Main Process Flow', style='dashed')
        for _, equip in equipment_df.iterrows():
            tag = equip['Tag']; img_filename = equip['Symbol_Image']; img_path = SYMBOLS_DIR / img_filename
            if not img_path.exists():
                img_path = create_placeholder_image(equip['Type'], TEMP_DIR / img_filename)
            c.node(tag, label=tag, image=str(img_path), shape='none', imagepos='tc', labelloc='b')

    for _, pipe in piping_df.iterrows():
        components_on_pipe = inline_df[inline_df['On_PipeTag'] == pipe['PipeTag']]
        last_node = pipe['From_Tag']
        for _, comp in components_on_pipe.iterrows():
            comp_name = f"{comp['Component_Tag']}_{pipe['PipeTag']}"
            img_filename = comp['Symbol_Image']; img_path = SYMBOLS_DIR / img_filename
            if not img_path.exists():
                img_path = create_placeholder_image(comp['Description'], TEMP_DIR / img_filename)
            dot.node(comp_name, label=comp['Component_Tag'], image=str(img_path), shape='none', imagepos='tc', labelloc='b')
            dot.edge(last_node, comp_name, label=pipe['PipeTag'])
            last_node = comp_name
        dot.edge(last_node, pipe['To_Tag'])
    return dot

# --- UI ---
st.title("🧠 Intelligent P&ID Generator")

with st.sidebar:
    st.header("1. Load P&ID Data")
    uploaded_file = st.file_uploader("Upload your standardized P&ID Excel file.", type=["xlsx"])
    if uploaded_file:
        if 'p_and_id_data' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
            try:
                st.session_state.p_and_id_data = pd.read_excel(uploaded_file, sheet_name=None)
                st.session_state.file_name = uploaded_file.name
                st.success(f"Loaded `{uploaded_file.name}` successfully!")
            except Exception as e:
                st.error(f"Failed to read Excel file: {e}")

if 'p_and_id_data' in st.session_state:
    data_frames = st.session_state.p_and_id_data
    preview_tab, ai_tab, data_tab = st.tabs(["P&ID Preview", "AI Suggestions", "Data Tables"])

    with preview_tab:
        st.subheader("P&ID Live Preview")
        with st.container(height=600, border=True):
            dot = generate_graphviz_dot(data_frames)
            st.graphviz_chart(dot)
            try:
                png_data = dot.pipe(format='png')
                st.download_button("Download as PNG", png_data, "p_and_id.png", "image/png", use_container_width=True)
            except Exception as e:
                st.error(f"PNG Export failed: {e}")

    with ai_tab:
        st.subheader("🤖 AI Engineer Co-pilot")
        if st.button("Analyze P&ID"):
            suggestions = get_ai_suggestions()
            st.markdown(suggestions)

    with data_tab:
        st.subheader("P&ID Data from Excel")
        for name, df in data_frames.items():
            st.write(f"**Sheet: `{name}`**"); st.dataframe(df)
else:
    st.info("Upload an Excel file in the sidebar to begin.")
