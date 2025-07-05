import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf import const as ezdxf_const
import openai
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
import psycopg2

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_CACHE_DIR = "symbols_cache" # Temporary local folder for this session
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 15)
except IOError:
    FONT = ImageFont.load_default()

# --- DATABASE MANAGER ---
class DBPersistence:
    def __init__(self):
        self.conn = None
        self.conn_url = os.environ.get("DATABASE_URL")
        if not self.conn_url:
            st.error("FATAL: DATABASE_URL not found. Please add a PostgreSQL service in Railway and ensure it's linked.")
            st.stop()
        self.connect()
        self.create_table()

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.conn_url)
        except Exception as e:
            st.error(f"Database connection failed: {e}")

    def create_table(self):
        if not self.conn: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS generated_symbols (
                        filename TEXT PRIMARY KEY, image_data BYTEA NOT NULL
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
        except: self.conn.rollback(); return None

    def save_symbol(self, filename, image_data):
        if not self.conn: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("INSERT INTO generated_symbols (filename, image_data) VALUES (%s, %s) ON CONFLICT (filename) DO NOTHING;", (filename, psycopg2.Binary(image_data)))
            self.conn.commit()
        except: self.conn.rollback()

db = DBPersistence()

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    return pd.read_csv(file_name) if os.path.exists(file_name) else pd.DataFrame()

equipment_options = load_data("equipment_list.csv")
inline_options = load_data("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS ---
def auto_tag(prefix, existing_tags):
    count = 1
    while f"{prefix}-{count:03}" in existing_tags: count += 1
    return f"{prefix}-{count:03}"

def generate_and_save_symbol_ai(component_type, filename):
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("AI Error: OPENAI_API_KEY not set in environment variables.")
            return
        client = openai.OpenAI(api_key=api_key)
        prompt = f"A professional, clean, black line-art P&ID symbol for a '{component_type}'. Standard engineering schematic. Pure white transparent background. No text, shadows, or 3D effects. 2D symbol only."
        with st.spinner(f"DALL·E is creating symbol for {component_type}..."):
            response = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024", response_format="b64_json")
            image_data = base64.b64decode(response.data[0].b64_json)
        db.save_symbol(filename, image_data)
        st.success(f"New uniform symbol saved to database! Reloading...")
        st.rerun()
    except Exception as e:
        st.error(f"AI symbol generation failed: {e}")

def get_symbol_image(image_name, component_type):
    cache_path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if os.path.exists(cache_path):
        return Image.open(cache_path).convert("RGBA").resize((100, 100))
    db_data = db.get_symbol(image_name)
    if db_data:
        with open(cache_path, "wb") as f: f.write(db_data)
        return Image.open(io.BytesIO(db_data)).convert("RGBA").resize((100, 100))
    generate_and_save_symbol_ai(component_type, image_name)
    return None

def render_professional_pid():
    if not st.session_state.components['equipment']: return None
    canvas_width, canvas_height = 2000, 1200
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (240, 242, 246, 255))
    draw = ImageDraw.Draw(canvas)
    layout_map = {comp['tag']: (i * 2 + 1, 2) for i, comp in enumerate(st.session_state.components['equipment'])}
    node_positions = {}
    for eq in st.session_state.components['equipment']:
        tag = eq['tag']
        if tag in layout_map:
            col, row = layout_map[tag]
            px, py = col * 150, row * 200
            node_positions[tag] = {'x': px, 'y': py, 'in': (px-50, py), 'out': (px+50, py)}
            img = get_symbol_image(eq["symbol"], eq["type"])
            if img:
                canvas.paste(img, (px - 50, py - 50), img)
                draw.text((px, py + 60), tag, fill="black", font=FONT, anchor="ms")
    for pipe in st.session_state.components['pipelines']:
        start_pos, end_pos = node_positions.get(pipe["from"]), node_positions.get(pipe["to"])
        if start_pos and end_pos:
            inline_comps = [c for c in st.session_state.components['inline'] if c['pipe_tag'] == pipe['tag']]
            num_segments = len(inline_comps) + 1
            points = [start_pos] + [{'x': start_pos['x'] + (i+1)/num_segments * (end_pos['x']-start_pos['x']), 'y': start_pos['y']} for i in range(len(inline_comps))] + [end_pos]
            for i in range(len(points) - 1):
                p1 = points[i]['out'] if i==0 else (points[i]['x']+50, points[i]['y'])
                p2 = points[i+1]['in'] if i+1==len(points)-1 else (points[i+1]['x']-50, points[i+1]['y'])
                draw.line([p1, p2], fill="black", width=3)
            draw.polygon([(end_pos['in'][0]-10, end_pos['in'][1]-6), (end_pos['in'][0], end_pos['in'][1]), (end_pos['in'][0]-10, end_pos['in'][1]+6)], fill="black")
            for i, comp in enumerate(inline_comps):
                pos = points[i+1]
                img = get_symbol_image(comp["symbol"], comp["type"])
                if img:
                    canvas.paste(img, (int(pos['x']) - 50, int(pos['y']) - 50), img)
                    draw.text((pos['x'], pos['y'] + 60), comp['tag'], fill="black", font=FONT, anchor="ms")
    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components['equipment']):
        x = i * 50
        msp.add_lwpolyline([(x, 0), (x+20, 0), (x+20, 20), (x, 20), (x, 0)])
        text = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        text.set_placement((x + 10, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def get_ai_suggestions():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key: return "⚠️ AI service unavailable: OPENAI_API_KEY not set."
        client = openai.OpenAI(api_key=api_key)
        summary = ", ".join([f"{e['tag']} ({e['type']})" for e in st.session_state.components['equipment']])
        prompt = f"As a senior process engineer, provide 5 specific design and safety improvements for a P&ID containing: {summary}."
        response = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"⚠️ AI Error: {e}"

def canvas_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("P&ID Builder")
    st.markdown("---")
    with st.expander("➕ Add Equipment", expanded=True):
        if not equipment_options.empty:
            eq_type = st.selectbox("Equipment Type", equipment_options["type"].unique(), key="eq_type_select")
            eq_row = equipment_options[equipment_options["type"] == eq_type].iloc[0]
            eq_tag = auto_tag(eq_row["Tag Prefix"], [e["tag"] for e in st.session_state.components['equipment']])
            st.text_input("New Tag", value=eq_tag, disabled=True, key="eq_tag_display")
            if st.button("Add Equipment"):
                st.session_state.components['equipment'].append({"type": eq_type, "tag": eq_tag, "symbol": eq_row["Symbol_Image"]})
                st.rerun()
    with st.expander("🔗 Add Pipeline"):
        if len(st.session_state.components['equipment']) >= 2:
            from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components['equipment']], key="pipe_from")
            to_opts = [e["tag"] for e in st.session_state.components['equipment'] if e["tag"] != from_tag]
            if to_opts:
                to_tag = st.selectbox("To", to_opts, key="pipe_to")
                tag = auto_tag("P", [p["tag"] for p in st.session_state.components['pipelines']])
                st.text_input("New Pipeline Tag", value=tag, disabled=True, key="pipe_tag_display")
                if st.button("Add Pipeline"):
                    st.session_state.components['pipelines'].append({"tag": tag, "from": from_tag, "to": to_tag})
                    st.rerun()
    with st.expander("🔧 Add In-Line Component"):
        if st.session_state.components['pipelines'] and not inline_options.empty:
            inline_type = st.selectbox("In-Line Type", inline_options["type"].unique(), key="inline_type_select")
            inline_row = inline_options[inline_options["type"] == inline_type].iloc[0]
            pipe_tag = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components['pipelines']], key="inline_pipe_select")
            tag = auto_tag(inline_row["Tag Prefix"], [i["tag"] for i in st.session_state.components['inline']])
            st.text_input("New In-line Tag", value=tag, disabled=True, key="inline_tag_display")
            if st.button("Add In-Line"):
                st.session_state.components['inline'].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": inline_row["Symbol_Image"]})
                st.rerun()
    if st.sidebar.button("🗑 Reset All", use_container_width=True, type="secondary"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN PAGE ---
st.title("🧠 EPS Interactive P&ID Generator")
with st.container(border=True):
    st.subheader("Current Project Components")
    col1, col2, col3 = st.columns(3)
    with col1: st.dataframe(st.session_state.components['equipment'], use_container_width=True)
    with col2: st.dataframe(st.session_state.components['pipelines'], use_container_width=True)
    with col3: st.dataframe(st.session_state.components['inline'], use_container_width=True)

st.markdown("---")
st.subheader("📊 P&ID Diagram Preview")
canvas = render_professional_pid()
if canvas:
    st.image(canvas)
    st.subheader("📤 Export P&ID")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download PNG", data=canvas_to_bytes(canvas), file_name="p_and_id.png", mime="image/png", use_container_width=True)
    with col2:
        dxf_data = generate_dxf()
        st.download_button("Download DXF", data=dxf_data, file_name="p_and_id.dxf", mime="application/dxf", use_container_width=True)
else:
    st.info("Add components in the sidebar to generate a P&ID.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing P&ID..."):
        st.markdown(get_ai_suggestions())
