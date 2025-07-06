import streamlit as st
import pandas as pd
import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf import const as ezdxf_const # Import the const module for alignment

# --- CONFIGURATION ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

try:
    FONT = ImageFont.truetype("arial.ttf", 14)
except:
    FONT = ImageFont.load_default()

# --- DATA LOADING ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- SESSION STATE INITIALIZATION ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- ALL FUNCTIONS DEFINED AT THE TOP ---

def auto_tag(prefix, existing_items):
    """Generates a new, unique tag based on a prefix."""
    existing_tags = [item['tag'] for item in existing_items]
    count = 1
    while f"{prefix}-{count:03}" in existing_tags:
        count += 1
    return f"{prefix}-{count:03}"

def generate_symbol_stability(type_name, image_name):
    """Generates an image using Stability AI with the correct API format."""
    if not STABILITY_API_KEY:
        st.error("Missing STABILITY_API_KEY in environment variables.")
        return None
    
    st.info(f"Generating ISA-compliant symbol for '{type_name}' with Stability AI...")
    prompt = f"ISA S5.1 standard P&ID symbol for '{type_name}', professional 2D engineering schematic icon. Clean, black line art. No text, no shadows, pure white background."
    
    try:
        # CORRECTED: Use multipart/form-data by passing prompt to 'files' parameter
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "image/png" # Explicitly request a PNG image
            },
            files={"prompt": (None, prompt)},
            data={"output_format": "png", "aspect_ratio": "1:1"}
        )
        
        if response.status_code == 200:
            outpath = os.path.join(SYMBOLS_CACHE_DIR, image_name)
            with open(outpath, "wb") as f:
                f.write(response.content)
            st.success(f"New symbol '{image_name}' created! Reloading...")
            st.rerun()
        else:
            st.error(f"Stability API Error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"Image generation request failed: {e}")

def get_image(image_name, type_name):
    """Fetches an image from the cache or generates it if it doesn't exist."""
    path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    if not os.path.exists(path):
        generate_symbol_stability(type_name, image_name)
        return None  # The app will rerun after generation
    
    if os.path.exists(path):
        return Image.open(path).convert("RGBA").resize((100, 100))
    
    return None

def render_pid_diagram():
    """Draws the P&ID diagram using PIL/Pillow."""
    canvas = Image.new("RGBA", (2000, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    tag_positions = {}
    grid_spacing = 250

    # Draw Equipment
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 150 + (i % 5) * grid_spacing
        y = 200 + (i // 5) * 300
        tag_positions[eq["tag"]] = (x, y)
        img = get_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
            draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Draw Pipelines
    for pipe in st.session_state.components["pipelines"]:
        start = tag_positions.get(pipe["from"])
        end = tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            # Draw arrow
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")

    # Draw In-line Components
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if pipe and pipe["from"] in tag_positions and pipe["to"] in tag_positions:
            x1, y1 = tag_positions[pipe["from"]]
            x2, _ = tag_positions[pipe["to"]]
            mid_x = int((x1 + x2) / 2) + 50
            mid_y = y1 + 50
            img = get_image(comp["symbol"], comp["type"])
            if img:
                # Erase line segment and draw component
                draw.line([(mid_x - 50, mid_y), (mid_x + 50, mid_y)], fill="white", width=5)
                canvas.paste(img, (mid_x - 50, mid_y-50), img)
            draw.text((mid_x, mid_y + 60), comp["tag"], fill="black", font=FONT, anchor="ms")

    return canvas

def generate_dxf_file():
    """Generates a DXF file from the current P&ID state with the corrected syntax."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 150
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        # CORRECTED: Use .set_placement() and the imported ezdxf.const enum
        text = msp.add_text(eq["tag"], dxfattribs={"height": 2.5})
        text.set_placement((x + 15, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def canvas_to_bytes(img):
    """Helper function to convert a PIL Image to bytes for download."""
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["equipment"])
        st.text_input("Generated Tag", value=tag, disabled=True)
        if st.button("➕ Add Equipment"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    st.header("Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        if to_opts:
            to_tag = st.selectbox("To", to_opts)
            tag = auto_tag("P", st.session_state.components["pipelines"])
            st.text_input("New Pipeline Tag", value=tag, disabled=True, key=f"pipe_tag_{tag}")
            if st.button("➕ Add Pipeline"):
                st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
                st.rerun()
        else:
            st.info("Need at least two different equipment.")

    st.header("Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("In-line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], st.session_state.components["inline"])
        st.text_input("New In-line Tag", value=tag, disabled=True, key=f"inline_tag_{tag}")
        if st.button("➕ Add Inline"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": row["Symbol_Image"]})
            st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN PAGE UI ---
st.title("🧠 EPS Interactive P&ID Generator")
st.subheader("📋 Component Summary")
col1, col2, col3 = st.columns(3)
with col1: st.dataframe(st.session_state.components["equipment"])
with col2: st.dataframe(st.session_state.components["pipelines"])
with col3: st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")
diagram = render_pid_diagram()
if diagram:
    st.image(diagram)
    st.subheader("📤 Export")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download PNG", canvas_to_bytes(diagram), "p_and_id.png", "image/png")
    with c2:
        st.download_button("Download DXF", generate_dxf_file(), "p_and_id.dxf", "application/dxf")
