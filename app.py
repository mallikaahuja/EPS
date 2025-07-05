import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io
import ezdxf
import openai
import requests
import psycopg2
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
# We still need a local cache folder for the current session
SYMBOLS_CACHE_PATH = "symbols_cache" 
os.makedirs(SYMBOLS_CACHE_PATH, exist_ok=True)

# --- DATABASE MANAGER ---
# This class correctly handles connecting to and using the database.
class DBPersistence:
    def __init__(self):
        self.conn = None
        self.conn_url = os.environ.get("DATABASE_URL")
        if not self.conn_url:
            st.error("DATABASE_URL environment variable not found. Please add a PostgreSQL service in Railway.")
            st.stop()
        self.connect()
        self.create_table()

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.conn_url)
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            self.conn = None

    def create_table(self):
        if not self.conn: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS generated_symbols (
                        filename TEXT PRIMARY KEY,
                        image_data BYTEA NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    def get_symbol(self, filename):
        if not self.conn: return None
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT image_data FROM generated_symbols WHERE filename = %s;", (filename,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.conn.rollback()
            return None

    def save_symbol(self, filename, image_data):
        if not self.conn: return
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO generated_symbols (filename, image_data) VALUES (%s, %s) ON CONFLICT (filename) DO NOTHING;",
                    (filename, psycopg2.Binary(image_data))
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

db = DBPersistence()

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name): return pd.DataFrame()
    return pd.read_csv(file_name)

equipment_df = load_data("equipment_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- SESSION STATE ---
for key in ["equipment", "pipelines", "inline"]:
    if key not in st.session_state: st.session_state[key] = []

# --- CORE FUNCTIONS ---
def auto_tag(prefix, all_tags):
    count = 1
    while f"{prefix}-{count:03}" in all_tags: count += 1
    return f"{prefix}-{count:03}"

def generate_and_save_symbol_ai(component_type, filename):
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("AI Error: OPENAI_API_KEY not found.")
            return
        client = openai.OpenAI(api_key=api_key)
        prompt = f"A professional, clean, black line-art P&ID symbol for a '{component_type}'. Standard engineering schematic. Pure white transparent background. No text, shadows, or 3D effects. 2D symbol only."
        with st.spinner(f"DALL-E is creating a uniform symbol for {component_type}..."):
            response = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024", response_format="b64_json")
            b64_data = response.data[0].b64_json
            image_data = base64.b64decode(b64_data)
        db.save_symbol(filename, image_data)
        st.success(f"New uniform symbol saved to database! Reloading...")
        st.rerun()
    except Exception as e:
        st.error(f"AI Image Generation Failed: {e}")

def get_symbol_path_from_db(image_name, component_type):
    """THE CORRECT LOGIC: DB first, then AI. No local file check."""
    local_cache_path = os.path.join(SYMBOLS_CACHE_PATH, image_name)
    # Check the local cache first to avoid re-downloading in the same session
    if os.path.exists(local_cache_path):
        return local_cache_path
        
    # Not in cache, check the permanent database
    db_image_data = db.get_symbol(image_name)
    if db_image_data:
        # Save to local cache for this session and return the path
        with open(local_cache_path, "wb") as f: f.write(db_image_data)
        return local_cache_path
    
    # Not in DB, generate with AI. This will trigger a rerun.
    generate_and_save_symbol_ai(component_type, image_name)
    return None

def generate_pnid_graph():
    # This function now uses the correct logic
    dot = Digraph('P&ID')
    dot.attr('graph', rankdir='LR', splines='ortho', ranksep='2', nodesep='1')
    dot.attr('node', shape='none', imagepos='tc', labelloc='b', fontsize='10')
    
    for eq in st.session_state.equipment:
        eq_details = equipment_df[equipment_df["type"] == eq["type"]].iloc[0]
        img_path = get_symbol_path_from_db(eq_details["Symbol_Image"], eq["type"])
        if img_path:
            dot.node(eq["tag"], label=eq["tag"], image=img_path)
            
    for pipe in st.session_state.pipelines:
        last_node = pipe["from"]
        components_on_pipe = [c for c in st.session_state.inline if c["pipe_tag"] == pipe["tag"]]
        for i, comp in enumerate(components_on_pipe):
            node_name = f"{comp['tag']}_{i}"
            comp_details = inline_df[inline_df["type"] == comp["type"]].iloc[0]
            img_path = get_symbol_path_from_db(comp_details["Symbol_Image"], comp["type"])
            if img_path:
                dot.node(node_name, label=comp["tag"], image=img_path)
            dot.edge(last_node, node_name)
            last_node = node_name
        dot.edge(last_node, pipe["to"])
    return dot

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    eq_positions = {eq['tag']: (i * 40, 0) for i, eq in enumerate(st.session_state.equipment)}
    for eq in st.session_state.equipment:
        x_pos, y_pos = eq_positions[eq['tag']]
        msp.add_lwpolyline([(x_pos-5, y_pos-5), (x_pos+5, y_pos-5), (x_pos+5, y_pos+5), (x_pos-5, y_pos+5), (x_pos-5,-5)])
        text_entity = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        text_entity.set_placement((x_pos, y_pos - 8), align=ezdxf.const.TOP_CENTER)
    for pipe in st.session_state.pipelines:
        start_pos = eq_positions.get(pipe['from'])
        end_pos = eq_positions.get(pipe['to'])
        if start_pos and end_pos:
            msp.add_line((start_pos[0] + 5, start_pos[1]), (end_pos[0] - 5, end_pos[1]))
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode('utf-8')

def get_ai_suggestions():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key: return "⚠️ AI service unavailable: OPENAI_API_KEY not set."
        client = openai.OpenAI(api_key=api_key)
        eq_list = ", ".join([f"{e['tag']}({e['type']})" for e in st.session_state.equipment])
        prompt = f"Given a P&ID with components: {eq_list}, suggest 5 specific design improvements."
        response = client.chat.completions.create(model="gpt-4", messages=[{"role": "system", "content": "You are a senior process engineer."}, {"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI service error: {e}"

# --- UI LAYOUT ---
with st.sidebar:
    st.title("P&ID Builder")
    with st.expander("➕ Add Equipment", expanded=True):
        if not equipment_df.empty:
            eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
            eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
            eq_tag = auto_tag(eq_row["Tag Prefix"], [e['tag'] for e in st.session_state.equipment])
            st.text_input("New Tag", value=eq_tag, disabled=True, key="eq_tag_display")
            if st.button("Add Equipment"):
                st.session_state.equipment.append({"type": eq_type, "tag": eq_tag})
                st.rerun()
    with st.expander("🔗 Add Pipeline"):
        if len(st.session_state.equipment) >= 2:
            from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment])
            to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], index=min(1, len(st.session_state.equipment)-1))
            pipe_tag = auto_tag("P", [p['tag'] for p in st.session_state.pipelines])
            st.text_input("New Pipeline Tag", value=pipe_tag, disabled=True, key="pipe_tag_display")
            if st.button("Add Pipeline"):
                st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
                st.rerun()
    with st.expander("🔧 Add In-Line Component"):
        if st.session_state.pipelines:
            inline_type = st.selectbox("In-line Type", inline_df["type"].unique())
            inline_row = inline_df[inline_df["type"] == inline_type].iloc[0]
            pipe_choice = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines])
            inline_tag = auto_tag(inline_row["Tag Prefix"], [i['tag'] for i in st.session_state.inline])
            st.text_input("New In-line Tag", value=inline_tag, disabled=True, key="inline_tag_display")
            if st.button("Add In-Line Component"):
                st.session_state.inline.append({"type": inline_type, "tag": inline_tag, "pipe_tag": pipe_choice})
                st.rerun()
    if st.sidebar.button("Reset All", use_container_width=True, type="secondary"):
        st.session_state.equipment, st.session_state.pipelines, st.session_state.inline = [], [], []
        st.rerun()

st.title("🧠 EPS Interactive P&ID Generator")
with st.container(border=True):
    st.subheader("Current Project Components")
    c1,c2,c3 = st.columns(3)
    with c1: st.dataframe(st.session_state.equipment)
    with c2: st.dataframe(st.session_state.pipelines)
    with c3: st.dataframe(st.session_state.inline)

st.markdown("---")
st.subheader("🖼️ P&ID Diagram Preview")
if st.session_state.equipment:
    graph = generate_pnid_graph()
    if graph:
        st.graphviz_chart(graph)
        st.subheader("📤 Export P&ID")
        col1, col2 = st.columns(2)
        with col1:
            try:
                png_data = graph.pipe(format='png')
                st.download_button("Download PNG", png_data, "pid_layout.png", "image/png", use_container_width=True)
            except Exception as e:
                st.error(f"PNG Export failed: {e}")
        with col2:
            dxf_data = generate_dxf()
            st.download_button("Download DXF", dxf_data, "pid_layout.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add some equipment to see the P&ID preview.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Thinking..."):
        st.markdown(get_ai_suggestions())
