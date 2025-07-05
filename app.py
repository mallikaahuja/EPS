import streamlit as st
import pandas as pd
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf import const as ezdxf_const
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 16)
    SMALL_FONT = ImageFont.truetype("arial.ttf", 12)
except IOError:
    FONT = ImageFont.load_default()
    SMALL_FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_csv(filename):
    return pd.read_csv(filename) if os.path.exists(filename) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
pipeline_df = load_csv("pipeline_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- SESSION STATE ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- CORE FUNCTIONS (DEFINED AT TOP) ---

def auto_tag(prefix, existing):
    count = 1
    existing_tags = [item['tag'] for item in existing]
    while f"{prefix}-{count:03}" in existing_tags:
        count += 1
    return f"{prefix}-{count:03}"

def generate_image_stability(prompt, image_name):
    api_key = os.environ.get("STABILITY_API_KEY")
    if not api_key:
        st.error("Missing STABILITY_API_KEY. Please add it to your Railway environment variables.")
        return None
    
    st.info(f"Generating symbol for '{image_name}' with Stability AI...")
    try:
        response = requests.post(
            f"https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 512,
                "width": 512,
                "samples": 1,
                "steps": 30,
            },
        )
        if response.status_code != 200:
            st.error(f"Stability API Error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        for i, image in enumerate(data["artifacts"]):
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
            st.success(f"New symbol '{image_name}' created! Reloading...")
            st.rerun() # Rerun to load the new image
            
    except Exception as e:
        st.error(f"Image generation request failed: {e}")
    return None

def get_symbol_image(type_name, image_name):
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        prompt = f"ISA S5.1 style black-and-white schematic 2D icon for '{type_name}', professional engineering P&ID symbol, PNG, no text or shadows, perfectly centered, on a pure white background."
        generate_image_stability(prompt, image_name)
        return None # App will rerun, so we exit here
    try:
        return Image.open(path).convert("RGBA").resize((100, 100))
    except Exception:
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (99,99)], outline="red", width=2)
        draw.text((10, 40), f"LOAD\nFAILED", fill="red", font=SMALL_FONT)
        return img

def render_pid_diagram():
    if not st.session_state.components["equipment"]: return None
    
    canvas = Image.new("RGBA", (2000, 1200), "white")
    draw = ImageDraw.Draw(canvas)
    tag_positions = {}
    
    # Simple grid layout for now, can be replaced with more complex logic
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x, y = 200 + i * 300, 500
        tag_positions[eq["tag"]] = (x, y)
        img = get_symbol_image(eq["type"], eq["symbol"])
        if img:
            canvas.paste(img, (x - 50, y - 50), img)
        draw.text((x, y + 60), eq["tag"], fill="black", font=FONT, anchor="ms")
        
    for pipe in st.session_state.components["pipelines"]:
        start, end = tag_positions.get(pipe["from"]), tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start
            x2, y2 = end
            draw.line([(x1 + 50, y1), (x2 - 50, y2)], fill="black", width=3)
            # Draw arrow
            draw.polygon([(x2 - 50, y2 - 6), (x2 - 40, y2), (x2 - 50, y2 + 6)], fill="black")
            
            # Draw inline components
            inline_comps = [c for c in st.session_state.components["inline"] if c['pipe_tag'] == pipe['tag']]
            num_segments = len(inline_comps) + 1
            for i, comp in enumerate(inline_comps):
                frac = (i + 1) / num_segments
                mid_x, mid_y = int(x1 + frac * (x2 - x1)), y1
                img = get_symbol_image(comp["type"], comp["symbol"])
                if img:
                    canvas.paste(img, (mid_x - 50, mid_y - 50), img)
                draw.text((mid_x, mid_y + 60), comp["tag"], fill="black", font=FONT, anchor="ms")

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30)], close=True)
        # --- CORRECTED EZDXF SYNTAX ---
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        text.set_placement((x + 15, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def canvas_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.sidebar.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["equipment"])
        st.sidebar.text_input("Generated Tag", value=tag, disabled=True, key=f"eq_tag_{eq_type}")
        if st.sidebar.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    st.sidebar.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.sidebar.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_tag_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        if to_tag_opts:
            to_tag = st.sidebar.selectbox("To", to_tag_opts)
            tag = auto_tag("PL", st.session_state.components["pipelines"])
            st.sidebar.text_input("New Pipeline Tag", value=tag, disabled=True, key=f"pipe_tag_{tag}")
            if st.sidebar.button("➕ Add Pipeline"):
                st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
                st.rerun()
                
    st.sidebar.header("Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.sidebar.selectbox("In-line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.sidebar.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["inline"])
        st.sidebar.text_input("New In-line Tag", value=tag, disabled=True, key=f"inline_tag_{tag}")
        if st.sidebar.button("➕ Add In-Line"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    if st.sidebar.button("🔄 Reset All", use_container_width=True):
        for k in st.session_state.components: st.session_state.components[k] = []
        st.rerun()

# --- MAIN PAGE UI ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Component Summary")
col1, col2, col3 = st.columns(3)
col1.dataframe(st.session_state.components["equipment"], use_container_width=True)
col2.dataframe(st.session_state.components["pipelines"], use_container_width=True)
col3.dataframe(st.session_state.components["inline"], use_container_width=True)

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    st.subheader("📤 Export P&ID")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button("Download PNG", canvas_to_bytes(diagram), "pid.png", "image/png", use_container_width=True)
    with d_col2:
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf", use_container_width=True)
else:
    st.info("Add components from the sidebar to begin.")
