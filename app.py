import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io
import ezdxf
import openai
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="EPS Interactive P&ID Generator", page_icon="🧠")
SYMBOLS_PATH = "symbols"  # This is the folder in your GitHub repo
os.makedirs(SYMBOLS_PATH, exist_ok=True) # Ensure local cache directory exists

# --- DATA LOADING ---
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        st.error(f"Required data file not found: {file_name}. Please ensure it is in your repository.")
        return pd.DataFrame()
    return pd.read_csv(file_name)

equipment_df = load_data("equipment_list.csv")
pipeline_df = load_data("pipeline_list.csv")
inline_df = load_data("inline_component_list.csv")

# --- SESSION STATE ---
if "equipment" not in st.session_state: st.session_state.equipment = []
if "pipelines" not in st.session_state: st.session_state.pipelines = []
if "inline" not in st.session_state: st.session_state.inline = []

# --- ALL FUNCTIONS DEFINED AT THE TOP TO PREVENT NameError ---

def auto_tag(prefix, all_tags):
    count = 1
    while f"{prefix}-{count:03}" in all_tags:
        count += 1
    return f"{prefix}-{count:03}"

def generate_and_save_symbol_ai(component_type, filename):
    st.info(f"Symbol '{filename}' not found. Generating new symbol with AI for '{component_type}'...")
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("AI Error: OPENAI_API_KEY not found in Railway environment variables.")
            return None
        
        # CORRECTED: Use the modern `openai.OpenAI()` client
        client = openai.OpenAI(api_key=api_key)
        prompt = f"A simple, clean, black and white, 2D P&ID symbol for a '{component_type}'. Minimalist engineering schematic style on a pure white background, no text, no shadows, transparent background."
        
        with st.spinner(f"DALL-E 3 is creating symbol for {component_type}..."):
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
            )
            b64_data = response.data[0].b64_json
            image_data = base64.b64decode(b64_data)
        
        save_path = os.path.join(SYMBOLS_PATH, filename)
        with open(save_path, "wb") as f:
            f.write(image_data)
        
        st.success(f"New symbol '{filename}' created! Please note this is saved for the current session only. Reloading...")
        st.rerun()
        
    except Exception as e:
        st.error(f"AI Image Generation Failed: {e}")
        return None

def get_component_image(image_name, component_type):
    try:
        image_path = os.path.join(SYMBOLS_PATH, image_name)
        if os.path.exists(image_path):
            return Image.open(image_path).convert("RGBA").resize((80, 80))
        else:
            # This will trigger AI generation and a rerun of the app
            generate_and_save_symbol_ai(component_type, image_name)
            return None 
    except Exception as e:
        st.warning(f"Error loading image '{image_name}': {e}")

    # Fallback placeholder image if anything fails
    img = Image.new("RGBA", (80, 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0), (79,79)], outline="red", width=2)
    draw.text((10, 25), f"FAILED:\n{component_type}", fill="red")
    return img

def render_pid_image():
    if not st.session_state.equipment: return None
    eq_positions = {eq['tag']: 150 + i * 250 for i, eq in enumerate(st.session_state.equipment)}
    canvas_width = max(1200, len(st.session_state.equipment) * 250 + 200)
    canvas = Image.new("RGBA", (canvas_width, 400), (240, 242, 246, 255)) # Light grey background
    draw = ImageDraw.Draw(canvas)
    
    for eq in st.session_state.equipment:
        img = get_component_image(eq["image_name"], eq['type'])
        if img:
            x_pos = eq_positions[eq['tag']]
            canvas.paste(img, (x_pos - 40, 150), img)
            draw.text((x_pos, 240), eq["tag"], fill="black", anchor="ms")

    for pipe in st.session_state.pipelines:
        start_x = eq_positions.get(pipe['from'])
        end_x = eq_positions.get(pipe['to'])
        if start_x is None or end_x is None: continue
        
        inline_comps = sorted([c for c in st.session_state.inline if c['pipe_tag'] == pipe['tag']], key=lambda x: x['tag'])
        num_segments = len(inline_comps) + 1
        points = [start_x + (end_x - start_x) * (i / num_segments) for i in range(num_segments + 1)]
        
        for i in range(len(points) - 1):
            draw.line([(points[i] + 40, 190), (points[i+1] - 40, 190)], fill="black", width=2)
            if i == len(points) - 2:
                draw.polygon([(points[i+1]-40, 185), (points[i+1]-30, 190), (points[i+1]-40, 195)], fill="black")

        for i, comp in enumerate(inline_comps):
            img = get_component_image(comp["image_name"], comp['type'])
            if img:
                img_x = start_x + (end_x - start_x) * (i + 1) / num_segments
                canvas.paste(img, (int(img_x) - 40, 150), img)
                draw.text((img_x, 240), comp["tag"], fill="black", anchor="ms")
    return canvas

def generate_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    eq_positions = {eq['tag']: i * 40 for i, eq in enumerate(st.session_state.equipment)}
    for eq in st.session_state.equipment:
        x_pos = eq_positions[eq['tag']]
        msp.add_lwpolyline([(x_pos-5, -5), (x_pos+5, -5), (x_pos+5, 5), (x_pos-5, 5), (x_pos-5,-5)])
        text_entity = msp.add_text(eq["tag"], dxfattribs={"height": 1.5})
        # CORRECTED: Use set_placement for modern ezdxf
        text_entity.set_placement((x_pos, -8), align=ezdxf.const.TOP_CENTER)
    for pipe in st.session_state.pipelines:
        start_x = eq_positions.get(pipe['from'])
        end_x = eq_positions.get(pipe['to'])
        if start_x is not None and end_x is not None:
             msp.add_line((start_x + 5, 0), (end_x - 5, 0))
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

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("P&ID Builder")
    st.markdown("---")
    with st.expander("➕ Add Equipment", expanded=True):
        if not equipment_df.empty:
            eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
            eq_row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
            all_eq_tags = [e['tag'] for e in st.session_state.equipment]
            eq_tag = auto_tag(eq_row["Tag Prefix"], all_eq_tags)
            st.text_input("New Tag", value=eq_tag, disabled=True, key="eq_tag_display")
            if st.button("Add Equipment"):
                st.session_state.equipment.append({"type": eq_type, "tag": eq_tag, "image_name": eq_row["Symbol_Image"]})
                st.rerun()
    with st.expander("🔗 Add Pipeline"):
        if len(st.session_state.equipment) >= 2:
            all_pipe_tags = [p['tag'] for p in st.session_state.pipelines]
            pipe_tag = auto_tag("P", all_pipe_tags)
            from_eq_options = [e["tag"] for e in st.session_state.equipment]
            from_eq = st.selectbox("From", from_eq_options, key="from_pipe")
            to_options = [e["tag"] for e in st.session_state.equipment if e["tag"] != from_eq]
            if to_options:
                to_eq = st.selectbox("To", to_options, key="to_pipe")
                st.text_input("New Pipeline Tag", value=pipe_tag, disabled=True, key="pipe_tag_display")
                if st.button("Add Pipeline"):
                    st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq, "type": "Pipeline"})
                    st.rerun()
            else: st.info("Need two different equipment.")
        else: st.info("Add at least 2 equipment first.")
    with st.expander("🔧 Add In-Line Component"):
        if st.session_state.pipelines:
            if not inline_df.empty:
                inline_type = st.selectbox("In-line Type", inline_df["type"].unique())
                inline_row = inline_df[inline_df["type"] == inline_type].iloc[0]
                pipe_choice = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines])
                all_inline_tags = [i['tag'] for i in st.session_state.inline]
                inline_tag = auto_tag(inline_row["Tag Prefix"], all_inline_tags)
                st.text_input("New In-line Tag", value=inline_tag, disabled=True, key="inline_tag_display")
                if st.button("Add In-Line Component"):
                    st.session_state.inline.append({"type": inline_type, "tag": inline_tag, "pipe_tag": pipe_choice, "image_name": inline_row["Symbol_Image"]})
                    st.rerun()
            else: st.warning("inline_component_list.csv not loaded.")
        else: st.info("Add a pipeline first.")
    st.markdown("---")
    if st.button("Reset All", use_container_width=True, type="secondary"):
        for key in ["equipment", "pipelines", "inline"]: st.session_state[key] = []
        st.rerun()

# --- MAIN PAGE LAYOUT ---
st.title("🧠 EPS Interactive P&ID Generator")
with st.container(border=True):
    st.subheader("Current Project Components")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("###### Equipment")
        st.dataframe(st.session_state.equipment, hide_index=True, use_container_width=True)
    with col2:
        st.markdown("###### Pipelines")
        st.dataframe(st.session_state.pipelines, hide_index=True, use_container_width=True)
    with col3:
        st.markdown("###### In-Line Components")
        st.dataframe(st.session_state.inline, hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("🖼️ P&ID Diagram Preview")
pid_image = render_pid_image()
if pid_image:
    st.image(pid_image)
    st.subheader("📤 Export P&ID")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf = io.BytesIO()
        pid_image.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_layout.png", "image/png", use_container_width=True)
    with col_dl2:
        dxf_data = generate_dxf()
        if dxf_data:
            st.download_button("Download DXF", dxf_data, "pid_layout.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add some equipment to see the P&ID preview.")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get Suggestions"):
    with st.spinner("Asking the AI Engineer..."):
        st.markdown(get_ai_suggestions())
