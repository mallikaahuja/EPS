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

# --- ENVIRONMENT VARIABLES (Railway: set these in your project) ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")

# --- SIDEBAR: Layout & Visual Controls ---
st.sidebar.markdown("### Layout & Visual Controls")
GRID_ROWS = st.sidebar.slider("Grid Rows", 6, 20, 12, 1, help="Number of grid rows (A–L = 12)")
GRID_COLS = st.sidebar.slider("Grid Columns", 6, 20, 12, 1, help="Number of grid columns (1–12 = 12)")
GRID_SPACING = st.sidebar.slider("Grid Spacing (px)", 60, 200, 120, 5, help="Distance between grid points")
SYMBOL_SCALE = st.sidebar.slider("Symbol Scale", 0.5, 2.0, 1.1, 0.1, help="Resize symbols relative to grid spacing")
MIN_WIDTH = st.sidebar.slider("Symbol Min Width", 20, 120, 60, 5)
MAX_WIDTH = st.sidebar.slider("Symbol Max Width", 80, 200, 140, 5)
PIPE_WIDTH = st.sidebar.slider("Pipe Width", 1, 8, 2)
TAG_FONT_SIZE = st.sidebar.slider("Tag Font Size", 8, 20, 12)
LEGEND_FONT_SIZE = st.sidebar.slider("Legend Font Size", 8, 20, 10)
ARROW_LENGTH = st.sidebar.slider("Arrow Length", 8, 30, 15)
MARGIN_Y = st.sidebar.slider("Vertical Margin Y", 40, 200, 100, 10)

PADDING = 60
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"

# --- Layout order and direction map for custom P&ID logic ---
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
    # Branches
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

BASE_COMPONENTS = [
    # main train, then branches (x_hint, y_hint will be auto-set)
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
    # Side branches
    {"type": "Control Panel (FLP)", "symbol": "flp_control_panel.png"},
    {"type": "Solenoid Valve", "symbol": "solenoid_valve.png"},
    {"type": "Pressure Gauge", "symbol": "pressure_gauge.png"},
]
BASE_INLINE = [
    {"type": "Pressure Transmitter", "symbol": "pressure_transmitter.png"},
    {"type": "Temperature Gauge", "symbol": "temperature_gauge.png"},
    {"type": "Flow Switch", "symbol": "flow_switch.png"},
    {"type": "Strainer", "symbol": "strainer.png"},
]
BASE_PIPELINES = [
    # (from_tag, to_tag, flow_dir)
    {"from": "FA-001", "to": "SF-001", "type": "Suction Pipe", "flow_dir": "down"},
    {"from": "SF-001", "to": "SC-001", "type": "Suction Pipe", "flow_dir": "down"},
    {"from": "SC-001", "to": "CP-001", "type": "Suction Pipe", "flow_dir": "down"},
    {"from": "CP-001", "to": "CPA-001", "type": "Suction Pipe", "flow_dir": "down"},
    {"from": "CPA-001", "to": "DP-001", "type": "Suction Pipe", "flow_dir": "down"},
    {"from": "DP-001", "to": "DC-001", "type": "Discharge Pipe", "flow_dir": "down"},
    {"from": "DC-001", "to": "CPD-001", "type": "Discharge Pipe", "flow_dir": "down"},
    {"from": "CPD-001", "to": "CPAD-001", "type": "Discharge Pipe", "flow_dir": "down"},
    {"from": "CPAD-001", "to": "DS-001", "type": "Discharge Pipe", "flow_dir": "down"},
    {"from": "DS-001", "to": "R-001", "type": "Discharge Pipe", "flow_dir": "down"},
    {"from": "R-001", "to": "S-001", "type": "Discharge Pipe", "flow_dir": "right"},
    # Side branches
    {"from": "CP-001", "to": "SV-001", "type": "Purge", "flow_dir": "right"},
    {"from": "CPA-001", "to": "PG-001", "type": "Gauge", "flow_dir": "left"},
    {"from": "DP-001", "to": "CPNL-001", "type": "Control", "flow_dir": "right"},
]

def get_font(size=14, bold=False):
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def today_str():
    return datetime.date.today().isoformat()

def load_symbol(symbol_name, width, height):
    symbol_path = os.path.join("symbols", symbol_name)
    if os.path.isfile(symbol_path):
        img = Image.open(symbol_path).convert("RGBA").resize((width, height))
        return img
    # --- Stability AI fallback if enabled and API key is set ---
    if STABILITY_API_KEY:
        prompt = f"Clean ISA S5.1 style black-and-white transparent symbol for {symbol_name.split('.')[0].replace('_',' ')}"
        engine = "stable-diffusion-xl-1024-v1-0"
        try:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "authorization": f"Bearer {STABILITY_API_KEY}",
                    "accept": "application/json"
                },
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
    r = 24
    if position == "left":
        cx, cy = x-40, y
    elif position == "top":
        cx, cy = x, y-40
    elif position == "bottom":
        cx, cy = x, y+40
    elif position == "right":
        cx, cy = x+40, y
    else:
        cx, cy = x, y
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="black", fill="white", width=2)
    bbox = draw.textbbox((0,0), tag, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w//2, cy - h//2), tag, fill="black", font=font)

def draw_arrow(draw, start, end, flow_dir, color="black"):
    draw.line([start, end], fill=color, width=PIPE_WIDTH)
    _arrow(draw, start, end, flow_dir, color)
    _arrow(draw, end, start, flow_dir, color)
    mx = (start[0] + end[0]) // 2
    my = (start[1] + end[1]) // 2
    font = get_font(ARROW_LENGTH)
    if flow_dir == "down":
        draw.text((mx-7, my+8), "↓", fill=color, font=font)
    elif flow_dir == "right":
        draw.text((mx+8, my-9), "→", fill=color, font=font)
    elif flow_dir == "left":
        draw.text((mx-20, my-9), "←", fill=color, font=font)
    elif flow_dir == "up":
        draw.text((mx-7, my-20), "↑", fill=color, font=font)

def _arrow(draw, tip, tail, flow_dir, color):
    dx = tail[0]-tip[0]
    dy = tail[1]-tip[1]
    length = (dx**2 + dy**2) ** 0.5
    if length == 0: length = 1
    ux = dx/length
    uy = dy/length
    p1 = (tip[0] + ARROW_LENGTH*ux - ARROW_LENGTH*uy, tip[1] + ARROW_LENGTH*uy + ARROW_LENGTH*ux)
    p2 = (tip[0] + ARROW_LENGTH*ux + ARROW_LENGTH*uy, tip[1] + ARROW_LENGTH*uy - ARROW_LENGTH*ux)
    draw.polygon([tip, p1, p2], outline=color, fill=color)

def draw_grid(draw, width, height, spacing):
    for i in range(0, width, spacing):
        draw.line([(i, 0), (i, height)], fill="#e0e0e0", width=1)
    for j in range(0, height, spacing):
        draw.line([(0, j), (width, j)], fill="#e0e0e0", width=1)

def auto_layout(components, layout_order, direction_map):
    pos_map = {}
    col = GRID_COLS // 2
    row = 2
    # Defensive: ensure we only assign layout to dicts missing x_hint/y_hint or if forced
    for comp in components:
        ctype = comp.get("type")
        # Always assign for layout_order, or if missing x_hint/y_hint
        if ctype in layout_order or ("x_hint" not in comp or "y_hint" not in comp):
            comp["x_hint"] = col
            comp["y_hint"] = row
            pos_map[ctype] = (col, row)
            row += 2
    # Branches
    for comp in components:
        ctype = comp.get("type")
        if ctype not in layout_order:
            if direction_map.get(ctype, "") == "right":
                comp["x_hint"] = col + 4
                comp["y_hint"] = pos_map.get("Dry Pump Model KDP330", (col, 10))[1]
            elif direction_map.get(ctype, "") == "left":
                comp["x_hint"] = col - 2
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

def generate_ai_suggestions(component_list):
    if not OPENAI_API_KEY:
        return [
            "🔧 Maintenance: Inspect filters and strainers regularly.",
            "💡 Utility: Add bypass for easier maintenance.",
            "🌱 Sustainability: Use heat recovery in condensers.",
        ]
    comp_names = ", ".join([f"{c['type']} ({c['tag']})" for c in component_list])
    prompt = f"""You are an expert process engineer.
Given these P&ID components and tags: {comp_names}
Suggest:
1. Maintenance reminders (for reliability)
2. Utility/cooling/steam optimization ideas
3. Sustainability upgrades (reduce loss, improve energy)
4. Efficiency improvements specific to this train

Please answer in concise bullet points and always include at least one sustainability idea.
"""
    try:
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert process engineer for chemical plants and vacuum systems."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=256,
            temperature=0.7,
        )
        msg = resp["choices"][0]["message"]["content"]
        return [f"• {l.strip()}" for l in msg.split("\n") if l.strip()]
    except Exception as e:
        return [
            f"AI suggestion error: {e}",
            "Fallback: Inspect all suction-side filters monthly.",
            "Add condensate recovery to reduce water loss.",
        ]

# --- SESSION STATE ---
if "equipment" not in st.session_state:
    eqs = [dict(x) for x in BASE_COMPONENTS]
    eqs = auto_layout(eqs, layout_order, component_direction_map)
    eqs = auto_tag(eqs, tag_prefix_map)
    st.session_state.equipment = eqs
    ils = [dict(x) for x in BASE_INLINE]
    ils = auto_tag(ils, tag_prefix_map)
    st.session_state.inline = ils
    st.session_state.pipelines = [dict(x) for x in BASE_PIPELINES]
    st.session_state.tag_position = "bottom"

# --- FIX: Always (re-)layout and (re-)tag before using coordinates ---
st.session_state.equipment = auto_layout(st.session_state.equipment, layout_order, component_direction_map)
st.session_state.equipment = auto_tag(st.session_state.equipment, tag_prefix_map)
st.session_state.inline = auto_tag(st.session_state.inline, tag_prefix_map)

all_components = st.session_state.equipment + st.session_state.inline
coord_map = {}
for c in all_components:
    # Defensive: provide fallback for any missing x_hint/y_hint
    x_hint = c.get("x_hint")
    y_hint = c.get("y_hint")
    if x_hint is None or y_hint is None:
        # fallback to layout function
        st.session_state.equipment = auto_layout(st.session_state.equipment, layout_order, component_direction_map)
        x_hint = c.get("x_hint", GRID_COLS // 2)
        y_hint = c.get("y_hint", 2)
    width = int(GRID_SPACING * SYMBOL_SCALE)
    height = int(width * 2) if any(word in c["type"].lower() for word in ["column", "condenser", "filter", "scrubber"]) else width
    c["width"] = max(MIN_WIDTH, min(MAX_WIDTH, width))
    c["height"] = max(MIN_WIDTH, min(MAX_WIDTH*2, height))
    x = PADDING + x_hint * GRID_SPACING
    y = PADDING + y_hint * GRID_SPACING
    coord_map[c["tag"]] = (x, y)

canvas_w = (GRID_COLS+6) * GRID_SPACING
canvas_h = (GRID_ROWS+6) * GRID_SPACING

# --- LEGEND / BOM ---
legend_items = []
used_types = set()
for eq in st.session_state.equipment:
    if eq["type"] not in used_types:
        used_types.add(eq["type"])
        legend_items.append({
            "Type": eq["type"],
            "Symbol": eq["symbol"],
            "Tag": eq["tag"]
        })
for ic in st.session_state.inline:
    if ic["type"] not in used_types:
        used_types.add(ic["type"])
        legend_items.append({
            "Type": ic["type"],
            "Symbol": ic["symbol"],
            "Tag": ic["tag"]
        })

# --- MAIN UI ---
st.title("EPS Interactive P&ID Generator")
st.write("**Equipment, Pipeline & Inline Component Editor**")
st.selectbox("Tag Circle Position", ["left", "top", "bottom", "right"], key="tag_position")

# --- CANVAS PREVIEW ---
st.subheader("P&ID Drawing (Professional Layout)")
img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
draw_grid(draw, canvas_w, canvas_h, GRID_SPACING)

# Draw all equipment
for eq in st.session_state.equipment:
    tag = eq["tag"]
    typ = eq["type"]
    symbol = eq["symbol"]
    x, y = coord_map[tag]
    width, height = eq.get("width", MIN_WIDTH), eq.get("height", MIN_WIDTH)
    symbol_img = symbol_or_missing(symbol, width, height)
    img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
    font = get_font(TAG_FONT_SIZE, bold=True)
    draw.text((x, y+height//2+20), tag, anchor="mm", fill="black", font=font)
    circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

# Draw inline components
for ic in st.session_state.inline:
    tag = ic["tag"]
    x, y = coord_map[tag]
    width, height = ic.get("width", MIN_WIDTH), ic.get("height", MIN_WIDTH)
    symbol_img = symbol_or_missing(ic["symbol"], width, height)
    img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
    font = get_font(TAG_FONT_SIZE, bold=True)
    draw.text((x, y+height//2+20), tag, anchor="mm", fill="black", font=font)
    circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

# Draw pipelines (elbowed, arrows, circled tags at joints)
for idx, pl in enumerate(st.session_state.pipelines):
    from_tag = pl["from"]
    to_tag = pl["to"]
    flow_dir = pl.get("flow_dir", "down")
    if from_tag in coord_map and to_tag in coord_map:
        x1, y1 = coord_map[from_tag]
        x2, y2 = coord_map[to_tag]
        if flow_dir == "down":
            mx, my = x1, y2
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=PIPE_WIDTH)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "right":
            mx, my = x2, y1
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=PIPE_WIDTH)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "left":
            mx, my = x2, y1
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=PIPE_WIDTH)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "up":
            mx, my = x1, y2
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=PIPE_WIDTH)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        circled_tag(draw, x1, y1, str(idx+1), position="left")
        circled_tag(draw, x2, y2, str(idx+1), position="right")
        draw.text(((x1+x2)//2, (y1+y2)//2-18), pl["type"], anchor="mm", fill="gray", font=get_font(TAG_FONT_SIZE))

# Draw legend box and BOM on canvas
legend_x = canvas_w - LEGEND_WIDTH - PADDING
legend_y = PADDING
draw.rectangle([legend_x, legend_y, canvas_w-PADDING, legend_y+30*(len(legend_items)+2)], outline="black", width=2)
font = get_font(LEGEND_FONT_SIZE)
draw.text((legend_x+10, legend_y+5), "Legend / BOM", fill="black", font=font)
for i, item in enumerate(legend_items):
    draw.text((legend_x+10, legend_y+30*(i+1)+5), f"{item['Type']} [{item['Tag']}]", fill="black", font=font)
    symbol = symbol_or_missing(item["Symbol"], MIN_WIDTH, MIN_WIDTH)
    img.paste(symbol, (legend_x+220, legend_y+30*(i+1)), symbol)

# Draw title block (bottom right)
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
    for eq in st.session_state.equipment:
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
            mx, my = x1, y2
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

ai_ideas = generate_ai_suggestions(st.session_state.equipment)
with st.expander("🔍 AI Suggestions & Improvements", expanded=True):
    for idea in ai_ideas:
        st.markdown(idea)

missing_syms = [eq["symbol"] for eq in st.session_state.equipment+st.session_state.inline if not load_symbol(eq["symbol"], MIN_WIDTH, MIN_WIDTH)]
if missing_syms:
    st.warning(f"Missing symbols: {', '.join(set(missing_syms))} (shown as gray box). Please add PNGs in /symbols or let Stability AI generate fallback PNGs.")
