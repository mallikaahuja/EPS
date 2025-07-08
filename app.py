import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import io
import ezdxf
import openai
import requests
import base64
import json
import re

# Optional: If you have these files, load for future dynamic sizing/tag logic
try:
    from tag_rules import next_tag
    with open("isa_config.json") as f:
        ISA_CONFIG = json.load(f)
except Exception:
    next_tag = None
    ISA_CONFIG = {}

# --- ENVIRONMENT VARIABLES ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")

# --- SIDEBAR: Layout & Visual Controls ---
st.sidebar.markdown("### Layout & Visual Controls")
GRID_ROWS = st.sidebar.slider("Grid Rows", 6, 20, 12, 1)
GRID_COLS = st.sidebar.slider("Grid Columns", 6, 20, 12, 1)
GRID_SPACING = st.sidebar.slider("Grid Spacing (px)", 60, 220, 120, 5)
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 1.0, 2.0, 1.8, 0.05)
MIN_WIDTH = st.sidebar.slider("Symbol Min Width", 100, 180, 132, 4)
MAX_WIDTH = st.sidebar.slider("Symbol Max Width", 132, 220, 180, 4)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 6, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 24, 12)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)
ARROW_LENGTH = st.sidebar.slider("Arrow Length", 8, 40, 15)
PIPE_LABEL_FONT_SIZE = st.sidebar.slider("Pipe Label Size", 6, 16, 8)
PADDING = 80
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"

BASE_COMPONENTS = [
    {"type": "Flame Arrestor", "symbol": "flame_arrestor.png"},
    {"type": "Suction Filter", "symbol": "suction_filter.png"},
    {"type": "Suction Condenser", "symbol": "suction_condenser.png"},
    {"type": "Catch Pot", "symbol": "catch_pot_manual.png"},
    {"type": "Catch Pot (Auto)", "symbol": "catch_pot_auto.png"},
    {"type": "Dry Pump Model KDP330", "symbol": "dry_pump_model.png"},
    {"type": "Discharge Condenser", "symbol": "discharge_condenser.png"},
    {"type": "Catch Pot (Manual, Disch)", "symbol": "catch_pot_manual.png"},
    {"type": "Catch Pot (Auto, Disch)", "symbol": "catch_pot_auto.png"},
    {"type": "Discharge Silencer", "symbol": "discharge_silencer.png"},
    {"type": "Receiver", "symbol": "receiver.png"},
    {"type": "Scrubber", "symbol": "scrubber.png"},
    {"type": "Control Panel (FLP)", "symbol": "flp_control_panel.png"},
    {"type": "Solenoid Valve", "symbol": "solenoid_valve.png"},
    {"type": "Pressure Gauge", "symbol": "pressure_gauge.png"},
    {"type": "Pressure Transmitter", "symbol": "pressure_transmitter.png"},
    {"type": "Temperature Gauge", "symbol": "temperature_gauge.png"},
    {"type": "Flow Switch", "symbol": "flow_switch.png"},
    {"type": "Strainer", "symbol": "strainer.png"},
]
BASE_INLINES = [
    {"type": "Pressure Transmitter", "symbol": "pressure_transmitter.png"},
    {"type": "Temperature Gauge", "symbol": "temperature_gauge.png"},
    {"type": "Flow Switch", "symbol": "flow_switch.png"},
    {"type": "Strainer", "symbol": "strainer.png"},
]
BASE_PIPELINES = [
    {"from": "FA-001", "to": "SF-001", "type": "15 NB CWS", "flow_dir": "down"},
    {"from": "SF-001", "to": "SC-001", "type": "15 NB CWS", "flow_dir": "down"},
    {"from": "SC-001", "to": "CP-001", "type": "15 NB CWS", "flow_dir": "down"},
    {"from": "CP-001", "to": "CPA-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "CPA-001", "to": "DP-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "DP-001", "to": "DC-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "DC-001", "to": "CPD-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "CPD-001", "to": "CPAD-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "CPAD-001", "to": "DS-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "DS-001", "to": "R-001", "type": "15 NB", "flow_dir": "down"},
    {"from": "R-001", "to": "S-001", "type": "15 NB", "flow_dir": "right"},
    # Side branches
    {"from": "CP-001", "to": "SV-001", "type": "15 NB CW", "flow_dir": "right"},
    {"from": "CPA-001", "to": "PG-001", "type": "10 NB", "flow_dir": "left"},
    {"from": "DP-001", "to": "CPNL-001", "type": "SIGNAL", "flow_dir": "right"},
]

layout_order = [
    "Flame Arrestor", "Suction Filter", "Suction Condenser", "Catch Pot",
    "Catch Pot (Auto)", "Dry Pump Model KDP330", "Discharge Condenser",
    "Catch Pot (Manual, Disch)", "Catch Pot (Auto, Disch)", "Discharge Silencer",
    "Receiver", "Scrubber"
]
component_direction_map = {
    "Flame Arrestor": "bottom",
    "Suction Filter": "bottom",
    "Suction Condenser": "bottom",
    "Catch Pot": "bottom",
    "Catch Pot (Auto)": "bottom",
    "Dry Pump Model KDP330": "bottom",
    "Discharge Condenser": "bottom",
    "Catch Pot (Manual, Disch)": "bottom",
    "Catch Pot (Auto, Disch)": "bottom",
    "Discharge Silencer": "bottom",
    "Receiver": "bottom",
    "Scrubber": "right",
    "Control Panel (FLP)": "right",
    "Solenoid Valve": "right",
    "Pressure Gauge": "left",
}
tag_prefix_map = {
    "Flame Arrestor": "FA",
    "Suction Filter": "SF",
    "Suction Condenser": "SC",
    "Catch Pot": "CP",
    "Catch Pot (Auto)": "CPA",
    "Dry Pump Model KDP330": "DP",
    "Discharge Condenser": "DC",
    "Catch Pot (Manual, Disch)": "CPD",
    "Catch Pot (Auto, Disch)": "CPAD",
    "Discharge Silencer": "DS",
    "Receiver": "R",
    "Scrubber": "S",
    "Control Panel (FLP)": "CPNL",
    "Solenoid Valve": "SV",
    "Pressure Gauge": "PG",
    "Pressure Transmitter": "PT",
    "Temperature Gauge": "TG",
    "Flow Switch": "FS",
    "Strainer": "STR",
}

def get_font(size=14, bold=False):
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def today_str():
    return datetime.date.today().isoformat()

def draw_grid(draw, width, height, spacing):
    for i in range(0, width, spacing):
        draw.line([(i, 0), (i, height)], fill="#e0e0e0", width=1)
    for j in range(0, height, spacing):
        draw.line([(0, j), (width, j)], fill="#e0e0e0", width=1)

def get_symbol_pngs():
    symbol_dir = "symbols"
    if not os.path.exists(symbol_dir):
        return []
    return sorted([f for f in os.listdir(symbol_dir) if f.lower().endswith('.png')])

# --- Symbol name normalization logic ---
def normalize_symbol_name(name):
    """Normalize symbol names for best match: lower, underscores, remove special chars, .png suffix."""
    base = os.path.splitext(name)[0].lower()
    base = re.sub(r'[\s\-]+', '_', base)
    base = re.sub(r'[^a-z0-9_]', '', base)
    return base

def find_best_symbol_match(symbol_name, available_symbols):
    """Return the closest match for symbol_name in available_symbols."""
    # Normalize both symbol_name and available_symbols for best match
    normalized_wanted = normalize_symbol_name(symbol_name)
    normalized_dict = {normalize_symbol_name(fn): fn for fn in available_symbols}
    return normalized_dict.get(normalized_wanted, None)

def load_symbol(symbol_name, width, height):
    available = get_symbol_pngs()
    match = find_best_symbol_match(symbol_name, available)
    symbol_path = None
    if match:
        symbol_path = os.path.join("symbols", match)
    else:
        # fallback for legacy
        symbol_path = os.path.join("symbols", symbol_name)
    if symbol_path and os.path.isfile(symbol_path):
        img = Image.open(symbol_path).convert("RGBA").resize((width, height))
        return img
    if STABILITY_API_KEY:
        prompt = f"Clean ISA S5.1 style black-and-white transparent symbol for {os.path.splitext(symbol_name)[0].replace('_',' ')}"
        try:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={"authorization": f"Bearer {STABILITY_API_KEY}", "accept": "application/json"},
                json={
                    "prompt": prompt,
                    "output_format": "png",
                    "steps": 30,
                    "seed": 0,
                    "width": width,
                    "height": height,
                    "negative_prompt": "color, shading, background, label, icon, border, noise"
                },
                timeout=30
            )
            if response.ok and response.json().get("artifacts"):
                png_b64 = response.json()["artifacts"][0]["base64"]
                img_bytes = base64.b64decode(png_b64)
                with open(symbol_path, "wb") as f:
                    f.write(img_bytes)
                img = Image.open(io.BytesIO(img_bytes)).convert("RGBA").resize((width, height))
                return img
        except Exception as e:
            st.warning(f"Stability AI fallback failed: {e}")
    return None

def symbol_or_missing(symbol_name, width, height):
    symbol = load_symbol(symbol_name, width, height)
    if symbol:
        return symbol
    img = Image.new("RGBA", (width, height), (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5,5,width-5,height-5], outline="gray", width=2)
    font = get_font(12)
    draw.text((10, height//2-10), "Missing\nSymbol", fill="gray", font=font)
    return img

def circled_tag(draw, x, y, tag, position="bottom"):
    font = get_font(TAG_FONT_SIZE, bold=True)
    r = 20
    if position == "left":
        cx, cy = x-38, y
    elif position == "top":
        cx, cy = x, y-38
    elif position == "bottom":
        cx, cy = x, y+38
    elif position == "right":
        cx, cy = x+38, y
    else:
        cx, cy = x, y
    draw.ellipse([cx-r+2, cy-r+2, cx+r+2, cy+r+2], fill=(180,180,180,80))
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="black", fill="#fff", width=2)
    bbox = draw.textbbox((0,0), tag.upper(), font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w//2, cy - h//2), tag.upper(), fill="black", font=font)

def draw_thin_arrow(draw, start, end, color="black"):
    from math import atan2, sin, cos, pi
    x0, y0 = start
    x1, y1 = end
    draw.line([start, end], fill=color, width=1)
    angle = atan2(y1-y0, x1-x0)
    length = ARROW_LENGTH
    arrow_angle = pi/7
    p1 = (int(x1 - length*cos(angle-arrow_angle)), int(y1 - length*sin(angle-arrow_angle)))
    p2 = (int(x1 - length*cos(angle+arrow_angle)), int(y1 - length*sin(angle+arrow_angle)))
    draw.polygon([end, p1, p2], fill=color, outline=color)

def draw_elbow_pipe(draw, x1, y1, x2, y2, flow_dir, label=None):
    mx, my = (x1, y2) if abs(x2-x1) < abs(y2-y1) else (x2, y1)
    draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=PIPE_WIDTH)
    draw_thin_arrow(draw, (mx, my), (x2, y2))
    if label:
        font = get_font(PIPE_LABEL_FONT_SIZE, bold=True)
        txt = label.upper()
        lx, ly = (mx, my) if abs(x2-x1) > abs(y2-y1) else ((x1+x2)//2, (y1+y2)//2)
        bbox = draw.textbbox((0,0), txt, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle([lx-w//2-2, ly-h//2-1, lx+w//2+2, ly+h//2+1], fill="#fff")
        draw.text((lx-w//2, ly-h//2), txt, fill="black", font=font)

def auto_layout(components, layout_order, direction_map):
    pos_map = {}
    col = GRID_COLS // 2
    row = 2
    for comp in components:
        ctype = comp.get("type")
        if ctype in layout_order or ("x_hint" not in comp or "y_hint" not in comp):
            comp["x_hint"] = col
            comp["y_hint"] = row
            pos_map[ctype] = (col, row)
            row += 2 if ctype != "Scrubber" else 0
    for comp in components:
        ctype = comp.get("type")
        if ctype not in layout_order:
            if direction_map.get(ctype, "") == "right":
                comp["x_hint"] = col + 4
                comp["y_hint"] = pos_map.get("Dry Pump Model KDP330", (col, 10))[1]
            elif direction_map.get(ctype, "") == "left":
                comp["x_hint"] = col - 3
                comp["y_hint"] = pos_map.get("Catch Pot (Auto)", (col, 6))[1]
            elif "x_hint" not in comp or "y_hint" not in comp:
                comp["x_hint"] = col + 2
                comp["y_hint"] = 4
    return components

def auto_tag(components, tag_prefix_map):
    tag_count = {}
    for comp in components:
        prefix = tag_prefix_map.get(comp["type"], comp["type"][:2].upper())
        tag_count.setdefault(prefix, 1)
        comp["tag"] = f"{prefix}-{tag_count[prefix]:03d}"
        tag_count[prefix] += 1
    return components

def reset_to_baseline():
    eqs = [dict(x) for x in BASE_COMPONENTS]
    eqs = auto_layout(eqs, layout_order, component_direction_map)
    eqs = auto_tag(eqs, tag_prefix_map)
    ils = [dict(x) for x in BASE_INLINES]
    ils = auto_tag(ils, tag_prefix_map)
    return eqs, ils

def generate_ai_suggestions(components, pipelines):
    if not OPENAI_API_KEY:
        return {
            "Process Optimization Tips": ["Reduce piping bends for improved flow."],
            "Utility Reduction & Sustainability": ["Reuse cooling water from scrubber loop."],
            "Maintenance & Safety Reminders": ["Inspect DP-001 every 60 cycles."]
        }
    tags = [c['tag'] for c in components]
    comp_types = [c['type'] for c in components]
    connections = [f"{p['from']}→{p['to']}" for p in pipelines]
    prompt = (
        f"Suggest process optimization, sustainability upgrades, and predictive maintenance for a process with: "
        f"{', '.join(comp_types)}. Connections: {', '.join(connections)}."
        " Return three lists: Process Optimization Tips, Utility Reduction & Sustainability, Maintenance & Safety Reminders."
    )
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert process engineer for chemical plants and vacuum systems."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=256,
            temperature=0.6,
            # Removed response_format to avoid error 400, just parse as JSON if possible.
        )
        msg = chat_response.choices[0].message.content
        # Try to extract three lists from the response robustly
        try:
            # Try to parse as JSON
            return json.loads(msg)
        except Exception:
            # Fallback: parse lists from markdown/text
            tips = {"Process Optimization Tips": [], "Utility Reduction & Sustainability": [], "Maintenance & Safety Reminders": []}
            current = None
            for line in msg.splitlines():
                if "optimization" in line.lower():
                    current = "Process Optimization Tips"
                elif "utility" in line.lower() or "sustainability" in line.lower():
                    current = "Utility Reduction & Sustainability"
                elif "maintenance" in line.lower() or "safety" in line.lower():
                    current = "Maintenance & Safety Reminders"
                elif line.strip().startswith(("-", "*")) and current:
                    tips[current].append(line.strip('-* ').strip())
            return tips
    except Exception as e:
        return {
            "Process Optimization Tips": [f"AI suggestion error: {e}"],
            "Utility Reduction & Sustainability": ["Fallback: Add condensate recovery to reduce water loss."],
            "Maintenance & Safety Reminders": ["Fallback: Inspect all suction-side filters monthly."]
        }

if "equipment" not in st.session_state:
    eqs, ils = reset_to_baseline()
    st.session_state.equipment = eqs
    st.session_state.inlines = ils
    st.session_state.pipelines = [dict(x) for x in BASE_PIPELINES]
    st.session_state.tag_position = "bottom"

st.title("EPS Interactive P&ID Generator")
st.write("**Equipment/Instrument Editor**")

with st.form("add_equipment_form"):
    types = sorted(set(c["type"] for c in BASE_COMPONENTS))
    symbol_pngs = get_symbol_pngs()
    new_type = st.selectbox("Component Type", types)
    new_symbol = st.selectbox("Symbol", symbol_pngs)
    add_equipment = st.form_submit_button("Add Equipment")
    if add_equipment:
        st.session_state.equipment.append({"type": new_type, "symbol": new_symbol})

if st.button("Reset to Reference Baseline (36 components)"):
    eqs, ils = reset_to_baseline()
    st.session_state.equipment = eqs
    st.session_state.inlines = ils

for idx, eq in enumerate(st.session_state.equipment):
    st.write(f"{eq['tag']}: {eq['type']} ({eq['symbol']})")
    if st.button(f"Remove Equipment {idx+1}", key=f"rm_eq_{idx}"):
        st.session_state.equipment.pop(idx)
        break

st.subheader("Inline Instruments")
with st.form("add_inline_form"):
    inline_types = sorted(set(c["type"] for c in BASE_INLINES))
    symbol_pngs = get_symbol_pngs()
    new_itype = st.selectbox("Inline Type", inline_types)
    new_isymbol = st.selectbox("Inline Symbol", symbol_pngs)
    add_inline = st.form_submit_button("Add Inline")
    if add_inline:
        st.session_state.inlines.append({"type": new_itype, "symbol": new_isymbol})

for idx, il in enumerate(st.session_state.inlines):
    st.write(f"{il['type']} ({il['symbol']})")
    if st.button(f"Remove Inline {idx+1}", key=f"rm_il_{idx}"):
        st.session_state.inlines.pop(idx)
        break

st.subheader("Pipelines")
with st.form("add_pipe_form"):
    tag_list = [c["tag"] for c in st.session_state.equipment]
    from_tag = st.selectbox("From", tag_list, key="pipe_from")
    to_tag = st.selectbox("To", tag_list, key="pipe_to")
    pipe_type = st.text_input("Pipe Label", "15 NB CWS")
    flow_dir = st.selectbox("Direction", ["down", "right", "left", "up"], index=0)
    add_pipe = st.form_submit_button("Add Pipeline")
    if add_pipe:
        st.session_state.pipelines.append({"from": from_tag, "to": to_tag, "type": pipe_type, "flow_dir": flow_dir})

for i, pl in enumerate(st.session_state.pipelines):
    st.write(f"{pl['from']} → {pl['to']} [{pl['type']}, {pl['flow_dir']}]")
    if st.button(f"Remove Pipeline {i+1}", key=f"rm_pipe_{i}"):
        st.session_state.pipelines.pop(i)
        break

st.selectbox("Tag Circle Position", ["left", "top", "bottom", "right"], key="tag_position")

st.session_state.equipment = auto_layout(st.session_state.equipment, layout_order, component_direction_map)
st.session_state.equipment = auto_tag(st.session_state.equipment, tag_prefix_map)
st.session_state.inlines = auto_tag(st.session_state.inlines, tag_prefix_map)

all_components = st.session_state.equipment + st.session_state.inlines
coord_map = {}
for c in all_components:
    x_hint = c.get("x_hint", GRID_COLS // 2)
    y_hint = c.get("y_hint", 2)
    width = int(GRID_SPACING * SYMBOL_SCALE)
    width = max(MIN_WIDTH, min(MAX_WIDTH, width))
    height = width
    if "Symbol_Width" in c:
        width = c["Symbol_Width"]
    if "Symbol_Height" in c:
        height = c["Symbol_Height"]
    c["width"] = width
    c["height"] = height
    x = PADDING + x_hint * GRID_SPACING
    y = PADDING + y_hint * GRID_SPACING
    coord_map[c["tag"]] = (x, y)

canvas_w = (GRID_COLS+6) * GRID_SPACING
canvas_h = (GRID_ROWS+6) * GRID_SPACING

st.subheader("P&ID Drawing (Reference-Style Orthogonal Layout)")
img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
draw_grid(draw, canvas_w, canvas_h, GRID_SPACING)

for eq in st.session_state.equipment:
    tag = eq["tag"]
    typ = eq["type"]
    symbol = eq["symbol"]
    x, y = coord_map[tag]
    width, height = eq.get("width", MIN_WIDTH), eq.get("height", MIN_WIDTH)
    symbol_img = symbol_or_missing(symbol, width, height)
    img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
    font = get_font(TAG_FONT_SIZE, bold=True)
    draw.text((x, y+height//2+22), tag.upper(), anchor="mm", fill="black", font=font)
    circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

for ic in st.session_state.inlines:
    tag = ic["tag"]
    x, y = coord_map.get(tag, (None, None))
    if x is not None and y is not None:
        width, height = ic.get("width", MIN_WIDTH), ic.get("height", MIN_WIDTH)
        symbol_img = symbol_or_missing(ic["symbol"], width, height)
        img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
        font = get_font(TAG_FONT_SIZE, bold=True)
        draw.text((x, y+height//2+22), tag.upper(), anchor="mm", fill="black", font=font)
        circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

for idx, pl in enumerate(st.session_state.pipelines):
    from_tag = pl["from"]
    to_tag = pl["to"]
    label = pl.get("type", "")
    flow_dir = pl.get("flow_dir", "down")
    if from_tag in coord_map and to_tag in coord_map:
        x1, y1 = coord_map[from_tag]
        x2, y2 = coord_map[to_tag]
        draw_elbow_pipe(draw, x1, y1, x2, y2, flow_dir, label=label)
        circled_tag(draw, x1, y1, str(idx+1), position="left")
        circled_tag(draw, x2, y2, str(idx+1), position="right")

legend_items = []
used_types = set()
for eq in st.session_state.equipment + st.session_state.inlines:
    if eq["type"] not in used_types:
        used_types.add(eq["type"])
        legend_items.append({
            "Type": eq["type"],
            "Symbol": eq["symbol"],
            "Tag": eq["tag"]
        })
legend_x = canvas_w - LEGEND_WIDTH - PADDING
legend_y = PADDING
draw.rectangle([legend_x, legend_y, canvas_w-PADDING, legend_y+28*(len(legend_items)+2)], outline="black", width=2)
font = get_font(LEGEND_FONT_SIZE)
draw.text((legend_x+10, legend_y+6), "Legend / BOM", fill="black", font=font)
for i, item in enumerate(legend_items):
    draw.text((legend_x+10, legend_y+28*(i+1)+6), f"{item['Type'].upper()} [{item['Tag']}]", fill="black", font=font)
    symbol = symbol_or_missing(item["Symbol"], MIN_WIDTH, MIN_WIDTH)
    img.paste(symbol, (legend_x+220, legend_y+28*(i+1)), symbol)

tb_x = canvas_w - TITLE_BLOCK_WIDTH - PADDING
tb_y = canvas_h - TITLE_BLOCK_HEIGHT - PADDING
draw.rectangle([tb_x, tb_y, canvas_w-PADDING, canvas_h-PADDING], outline="black", width=2)
font = get_font(14)
draw.text((tb_x+10, tb_y+10), "EPS Interactive P&ID", fill="black", font=font)
draw.text((tb_x+10, tb_y+40), f"Date: {today_str()}", fill="black", font=font)
draw.text((tb_x+10, tb_y+70), f"Sheet: 1 of 1", fill="black", font=font)
draw.text((tb_x+220, tb_y+10), f"CLIENT: {TITLE_BLOCK_CLIENT}", fill="black", font=font)
draw.rectangle([PADDING, PADDING, canvas_w-PADDING, canvas_h-PADDING], outline="#bbbbbb", width=1)

st.image(img, use_container_width=True)

buf = io.BytesIO()
img.save(buf, format="PNG")
st.download_button("Download PNG", data=buf.getvalue(), file_name="pid.png", mime="image/png")

def export_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for eq in st.session_state.equipment + st.session_state.inlines:
        tag = eq["tag"]
        x, y = coord_map[tag]
        width = eq.get("width", MIN_WIDTH)
        height = eq.get("height", MIN_WIDTH)
        msp.add_lwpolyline([(x-width//2, y-height//2), (x+width//2, y-height//2), (x+width//2, y+height//2), (x-width//2, y+height//2), (x-width//2, y-height//2)], close=True)
        txt = msp.add_text(tag, dxfattribs={"height": TAG_FONT_SIZE})
        txt.dxf.insert = (x, y+height//2+20)
    for pl in st.session_state.pipelines:
        from_tag = pl["from"]
        to_tag = pl["to"]
        if from_tag in coord_map and to_tag in coord_map:
            x1, y1 = coord_map[from_tag]
            x2, y2 = coord_map[to_tag]
            mx, my = (x1, y2) if abs(x2-x1) < abs(y2-y1) else (x2, y1)
            msp.add_lwpolyline([(x1, y1), (mx, my), (x2, y2)])
    msp.add_text("EPS Interactive P&ID", dxfattribs={"height": 30}).dxf.insert = (tb_x+10, tb_y+10)
    msp.add_text(f"Date: {today_str()}", dxfattribs={"height": 20}).dxf.insert = (tb_x+10, tb_y+40)
    msp.add_text("Sheet: 1 of 1", dxfattribs={"height": 20}).dxf.insert = (tb_x+10, tb_y+70)
    msp.add_text(f"CLIENT: {TITLE_BLOCK_CLIENT}", dxfattribs={"height": 20}).dxf.insert = (tb_x+220, tb_y+10)
    buf = io.BytesIO()
    doc.saveas(buf)
    return buf.getvalue()

if st.button("Download DXF"):
    dxf_bytes = export_dxf()
    st.download_button("Save DXF", data=dxf_bytes, file_name="pid.dxf", mime="application/dxf")

ai_suggestions_dict = generate_ai_suggestions(st.session_state.equipment, st.session_state.pipelines)
with st.sidebar.expander("🤖 AI Suggestions & Improvements", expanded=True):
    for group, tips in ai_suggestions_dict.items():
        st.markdown(f"**{group}**")
        for tip in tips:
            st.markdown(f"- {tip}")

# --- Enhanced: only warn for truly missing symbols after matching/normalizing ---
available_symbols = get_symbol_pngs()
missing_syms = []
for eq in st.session_state.equipment+st.session_state.inlines:
    if not find_best_symbol_match(eq["symbol"], available_symbols):
        missing_syms.append(eq["symbol"])
if missing_syms:
    st.warning(f"Missing symbols: {', '.join(set(missing_syms))} (shown as gray box). Please add PNGs in /symbols or let Stability AI generate fallback PNGs.")
