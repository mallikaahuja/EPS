import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io
import ezdxf
from ezdxf import const as ezdxf_const
import openai
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS P&ID Generator", layout="wide")
SYMBOLS_DIR = "symbols"
os.makedirs(SYMBOLS_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 15)
except IOError:
    FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_csv(filename):
    return pd.read_csv(filename) if os.path.exists(filename) else pd.DataFrame()

equipment_options = load_csv("equipment_list.csv")
pipeline_options = load_csv("pipeline_list.csv")
inline_options = load_csv("inline_component_list.csv")

# --- INIT SESSION STATE ---
for key in ['equipment', 'pipelines', 'inline']:
    if key not in st.session_state:
        st.session_state[key] = []

# --- ALL FUNCTIONS DEFINED AT THE TOP ---

def auto_tag(prefix, existing_tags):
    """
    CORRECTED: Checks for a new tag directly in the list of existing tags.
    """
    n = 1
    # The loop now correctly checks if the generated tag string exists in the list of strings
    while f"{prefix}-{n:03}" in existing_tags:
        n += 1
    return f"{prefix}-{n:03}"

def generate_symbol_with_dalle(type_name, image_name):
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        prompt = f"Clean, black and white industry-standard 2D P&ID symbol for '{type_name}'. No text. Transparent background. Vector or schematic style. Matches ISA and engineering P&ID legends."
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024", # Corrected size
            response_format="b64_json"
        )
        b64_image = response.data[0].b64_json
        image_data = base64.b64decode(b64_image)
        with open(os.path.join(SYMBOLS_DIR, image_name), "wb") as f:
            f.write(image_data)
        st.success(f"New symbol '{image_name}' created with AI! Reloading.")
        st.rerun()
    except Exception as e:
        st.error(f"AI symbol generation failed: {e}")

def get_symbol_image(image_name, type_name):
    path = os.path.join(SYMBOLS_DIR, image_name)
    if not os.path.exists(path):
        generate_symbol_with_dalle(type_name, image_name)
        return None
    try:
        return Image.open(path).convert("RGBA").resize((80, 80))
    except Exception as e:
        st.warning(f"Failed to load image '{path}': {e}")
        return Image.new("RGBA", (80, 80), (255, 255, 255, 0))

def render_pid_image():
    if not st.session_state.equipment:
        return None
    
    width = 200 * (len(st.session_state.equipment) + 1) + 150
    canvas = Image.new("RGBA", (width, 500), (240, 242, 246, 255))
    draw = ImageDraw.Draw(canvas)
    
    eq_pos = {eq['tag']: 150 + i * 200 for i, eq in enumerate(st.session_state.equipment)}

    for eq in st.session_state.equipment:
        x = eq_pos[eq['tag']]
        img = get_symbol_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x - 40, 150), img)
            draw.text((x, 240), eq["tag"], fill="black", font=FONT, anchor="ms")
            
    for pipe in st.session_state.pipelines:
        x1, x2 = eq_pos.get(pipe["from"]), eq_pos.get(pipe["to"])
        if x1 and x2:
            draw.line([(x1 + 40, 190), (x2 - 40, 190)], fill="black", width=2)
            draw.polygon([(x2 - 45, 185), (x2 - 35, 190), (x2 - 45, 195)], fill="black")
    
        inline_comps = [c for c in st.session_state.inline if c['pipe_tag'] == pipe['tag']]
        num_segments = len(inline_comps) + 1
        
        for i, inline in enumerate(inline_comps):
            mid_x = x1 + (x2 - x1) * ((i + 1) / num_segments)
            img = get_symbol_image(inline["symbol"], inline["type"])
            if img:
                canvas.paste(img, (int(mid_x) - 40, 150), img)
                draw.text((mid_x, 240), inline["tag"], fill="black", font=FONT, anchor="ms")
                
    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.equipment):
        x = i * 50
        msp.add_lwpolyline([(x, 0), (x + 20, 0), (x + 20, 20), (x, 20), (x, 0)])
        text = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        text.set_placement((x + 10, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def get_ai_suggestions():
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        summary = "\n".join([f"- {e['tag']} ({e['type']})" for e in st.session_state.equipment])
        prompt = f"You are a senior process engineer. Suggest 5 improvements for a P&ID with: \n{summary}"
        chat = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}], temperature=0.4)
        return chat.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def canvas_to_bytes(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# --- SIDEBAR UI ---
st.sidebar.header("Add Equipment")
if not equipment_options.empty:
    eq_type = st.sidebar.selectbox("Equipment Type", equipment_options["type"].unique())
    eq_row = equipment_options[equipment_options["type"] == eq_type].iloc[0]
    # This line now correctly calls the fixed auto_tag function
    eq_tag = auto_tag(eq_row["Tag Prefix"], [e["tag"] for e in st.session_state.equipment])
    st.sidebar.text_input("New Tag", value=eq_tag, disabled=True)
    if st.sidebar.button("➕ Add Equipment"):
        st.session_state.equipment.append({"type": eq_type, "tag": eq_tag, "symbol": eq_row["Symbol_Image"]})
        st.rerun()

st.sidebar.header("Add Pipeline")
if len(st.session_state.equipment) >= 2:
    from_tag = st.sidebar.selectbox("From", [e["tag"] for e in st.session_state.equipment])
    to_tag_options = [e["tag"] for e in st.session_state.equipment if e["tag"] != from_tag]
    if to_tag_options:
        to_tag = st.sidebar.selectbox("To", to_tag_options)
        tag = auto_tag("P", [p["tag"] for p in st.session_state.pipelines])
        st.sidebar.text_input("New Pipeline Tag", value=tag, disabled=True)
        if st.sidebar.button("➕ Add Pipeline"):
            st.session_state.pipelines.append({"tag": tag, "from": from_tag, "to": to_tag})
            st.rerun()

st.sidebar.header("Add In-Line Component")
if st.session_state.pipelines and not inline_options.empty:
    inline_type = st.sidebar.selectbox("In-Line Type", inline_options["type"].unique())
    inline_row = inline_options[inline_options["type"] == inline_type].iloc[0]
    pipe_tag = st.sidebar.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines])
    tag = auto_tag(inline_row["Tag Prefix"], [i["tag"] for i in st.session_state.inline])
    st.sidebar.text_input("New In-line Tag", value=tag, disabled=True)
    if st.sidebar.button("➕ Add In-Line"):
        st.session_state.inline.append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": inline_row["Symbol_Image"]})
        st.rerun()

if st.sidebar.button("🗑 Reset All", use_container_width=True):
    for k in ['equipment', 'pipelines', 'inline']: st.session_state[k] = []
    st.rerun()

# --- MAIN UI ---
st.title("🧠 EPS Interactive P&ID Generator")

st.subheader("🔍 Components Overview")
col1, col2, col3 = st.columns(3)
col1.dataframe(st.session_state.equipment, use_container_width=True)
col2.dataframe(st.session_state.pipelines, use_container_width=True)
col3.dataframe(st.session_state.inline, use_container_width=True)

st.markdown("---")
st.subheader("📊 P&ID Diagram Preview")
canvas = render_pid_image()
if canvas:
    st.image(canvas)
    c1, c2 = st.columns(2)
    c1.download_button("Download PNG", data=canvas_to_bytes(canvas), file_name="p_and_id.png", mime="image/png", use_container_width=True)
    c2.download_button("Download DXF", data=generate_dxf(), file_name="p_and_id.dxf", mime="application/dxf", use_container_width=True)

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Analyzing P&ID..."):
        st.markdown(get_ai_suggestions())
