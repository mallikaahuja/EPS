import streamlit as st
import pandas as pd
import os
import io
import ezdxf
from ezdxf import const as ezdxf_const
from PIL import Image, ImageDraw, ImageFont
import openai
import base64

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="EPS P&ID Generator", page_icon="🧠")
SYMBOLS_DIR = "symbols_cache"
os.makedirs(SYMBOLS_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except:
    FONT = ImageFont.load_default()

# --- Load CSVs ---
@st.cache_data
def load_csv(file): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")

# --- Session state init ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
if "loop_counter" not in st.session_state:
    st.session_state.loop_counter = 100

# --- Tagging & Image Functions ---
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

def isa_tag(isa_code):
    st.session_state.loop_counter += 1
    return f"{isa_code}-{st.session_state.loop_counter:03}"

def dalle_generate(type_name, image_name):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        st.error("OPENAI_API_KEY not set.")
        return
    client = openai.OpenAI(api_key=key)
    prompt = f"Professional ISA 5.1 P&ID symbol for '{type_name}', black line art, schematic style, transparent background, 2D."
    try:
        res = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024", response_format="b64_json")
        image_data = base64.b64decode(res.data[0].b64_json)
        with open(os.path.join(SYMBOLS_DIR, image_name), "wb") as f: f.write(image_data)
    except Exception as e:
        st.warning(f"Image gen failed: {e}")

def get_image(image_name, type_name):
    path = os.path.join(SYMBOLS_DIR, image_name)
    if not os.path.exists(path): dalle_generate(type_name, image_name)
    if os.path.exists(path): return Image.open(path).convert("RGBA").resize((100, 100))
    return None
    # --- P&ID Rendering ---
def render_pid():
    canvas = Image.new("RGBA", (2400, 1500), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    grid_spacing = 200
    tag_pos = {}

    # Draw equipment
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = 100 + (i % 5) * grid_spacing
        y = 150 + (i // 5) * 300
        tag_pos[eq["tag"]] = (x, y)
        img = get_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
        draw.text((x + 50, y + 110), eq["tag"], fill="black", font=FONT, anchor="ms")

    # Draw pipelines
    for pipe in st.session_state.components["pipelines"]:
        start = tag_pos.get(pipe["from"])
        end = tag_pos.get(pipe["to"])
        if start and end:
            x1, y1 = start[0] + 100, start[1] + 50
            x2, y2 = end[0], end[1] + 50
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
            draw.polygon([(x2 - 10, y2 - 6), (x2, y2), (x2 - 10, y2 + 6)], fill="black")
            draw.polygon([(x1 + 10, y1 - 6), (x1, y1), (x1 + 10, y1 + 6)], fill="black")

    # Inline components
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if not pipe: continue
        from_pos = tag_pos.get(pipe["from"])
        to_pos = tag_pos.get(pipe["to"])
        if not from_pos or not to_pos: continue
        mx = int((from_pos[0] + to_pos[0]) / 2 + 50)
        my = from_pos[1] + 30
        img = get_image(comp["symbol"], comp["type"])
        if img:
            canvas.paste(img, (mx - 50, my), img)
            draw.text((mx, my + 110), comp["tag"], fill="black", font=FONT, anchor="ms")

    # Draw dynamic legend
    draw.rectangle([(1800, 50), (2380, 1450)], outline="black", width=2)
    draw.text((1850, 60), "LEGEND", font=FONT, fill="black")
    y_cursor = 100
    all_types = list(
        {e["type"] for e in st.session_state.components["equipment"]}
        | {i["type"] for i in st.session_state.components["inline"]}
    )
    for t in all_types:
        draw.text((1850, y_cursor), f"• {t}", font=FONT, fill="black")
        y_cursor += 30

    return canvas

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 100
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(eq["tag"], dxfattribs={"height": 1.5}).set_placement((x+15, -5), align=ezdxf_const.TOP_CENTER)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

def get_ai_suggestions():
    try:
        key = os.environ.get("OPENAI_API_KEY")
        if not key: return "⚠️ AI unavailable"
        client = openai.OpenAI(api_key=key)
        tags = ", ".join([f"{e['tag']}({e['type']})" for e in st.session_state.components["equipment"]])
        prompt = f"As a senior process engineer, suggest 5 improvements for this P&ID: {tags}."
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {e}"
        # --- SIDEBAR ---
with st.sidebar:
    st.header("➕ Add Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Equipment Type", equipment_df["type"].unique())
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        st.text_input("Generated Tag", value=tag, disabled=True)
        if st.button("Add Equipment"):
            st.session_state.components["equipment"].append({
                "type": eq_type,
                "tag": tag,
                "symbol": row["Symbol_Image"]
            })
            st.rerun()

    st.header("🔗 Add Pipeline")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]])
        to_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        to_tag = st.selectbox("To", to_opts)
        pipe_tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        st.text_input("Pipeline Tag", value=pipe_tag, disabled=True)
        if st.button("Add Pipeline"):
            st.session_state.components["pipelines"].append({
                "tag": pipe_tag,
                "from": from_tag,
                "to": to_tag
            })
            st.rerun()

    st.header("🔧 Add In-Line Component")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("In-Line Type", inline_df["type"].unique())
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]])
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        st.text_input("In-Line Tag", value=tag, disabled=True)
        if st.button("Add In-Line"):
            st.session_state.components["inline"].append({
                "type": inline_type,
                "tag": tag,
                "pipe_tag": pipe_tag,
                "symbol": row["Symbol_Image"]
            })
            st.rerun()

    if st.button("🗑️ Reset All"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.rerun()

# --- MAIN PAGE ---
st.title("🧠 EPS Interactive P&ID Generator")

st.subheader("📋 Component Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### Equipment")
    st.dataframe(st.session_state.components["equipment"])
with col2:
    st.markdown("#### Pipelines")
    st.dataframe(st.session_state.components["pipelines"])
with col3:
    st.markdown("#### In-Line Components")
    st.dataframe(st.session_state.components["inline"])

st.markdown("---")
st.subheader("🖼️ P&ID Preview")

canvas = render_pid()
if canvas:
    st.image(canvas)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.download_button("Download PNG", buf.getvalue(), "pid_diagram.png", "image/png")
    with col_dl2:
        st.download_button("Download DXF", generate_dxf_file(), "pid_diagram.dxf", "application/dxf")

st.markdown("---")
st.subheader("🤖 AI Engineer Suggestions")
if st.button("Get AI Suggestions"):
    st.markdown(get_ai_suggestions())
    # --- ISA LOGIC PANEL ---
st.markdown("---")
st.subheader("🧠 ISA-Based Control Logic")

# Generate a logic map based on tag types and equipment
logic_entries = []
loop_count = 101  # Start loop numbers from 101

for eq in st.session_state.components["equipment"]:
    tag = eq["tag"]
    type_ = eq["type"]

    # Example: Add pressure transmitters for vacuum-related tags
    if "vacuum" in type_.lower() or "pump" in type_.lower():
        logic_entries.append({
            "Loop": f"PT-{loop_count}",
            "Device": tag,
            "Function": "Vacuum Pressure Transmitter"
        })
        loop_count += 1
        logic_entries.append({
            "Loop": f"PC-{loop_count}",
            "Device": tag,
            "Function": "Vacuum PID Controller"
        })
        loop_count += 1
        logic_entries.append({
            "Loop": f"PV-{loop_count}",
            "Device": tag,
            "Function": "Vacuum Control Valve"
        })
        loop_count += 1

    # Example: Add safety interlocks for dryers, evaporators
    if any(kw in type_.lower() for kw in ["dryer", "evaporator", "heater"]):
        logic_entries.append({
            "Loop": f"TSH-{loop_count}",
            "Device": tag,
            "Function": "Temperature Safety High Interlock"
        })
        loop_count += 1
        logic_entries.append({
            "Loop": f"LSL-{loop_count}",
            "Device": tag,
            "Function": "Low Level Interlock"
        })
        loop_count += 1

# --- DISPLAY LOGIC TABLE ---
if logic_entries:
    logic_df = pd.DataFrame(logic_entries)
    st.markdown("#### 🧾 Logic Function Map")
    st.dataframe(logic_df, use_container_width=True)
else:
    st.info("Add vacuum/process equipment to view logic mapping.")
