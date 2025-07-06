import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import io
import ezdxf

# --- SIZING & GRID CONSTANTS ---
min_width = 100
max_width = 180
min_height = 100
max_height = 300
margin_y = 100
std_width = min_width
std_height = min_height
tall_height = max_height
PADDING = 60
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"
ARROW_WIDTH = 14
ARROW_HEIGHT = 20
GRID_ROWS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
GRID_COLS = list(range(1, 20))

# COMPONENTS: position hints (x_hint: column, y_hint: row), tall for vertical equipment
BASE_COMPONENTS = [
    {"type": "Flame Arrestor", "tag": "FA-001", "symbol": "flame_arrestor.png", "x_hint": 4, "y_hint": 2},
    {"type": "Suction Filter", "tag": "SF-001", "symbol": "suction_filter.png", "x_hint": 4, "y_hint": 4},
    {"type": "Suction Condenser", "tag": "SC-001", "symbol": "suction_condenser.png", "x_hint": 4, "y_hint": 6},
    {"type": "Catch Pot", "tag": "CP-001", "symbol": "catch_pot_manual.png", "x_hint": 4, "y_hint": 8},
    {"type": "Catch Pot (Auto)", "tag": "CPA-001", "symbol": "catch_pot_auto.png", "x_hint": 4, "y_hint": 10},
    {"type": "Dry Pump Model KDP330", "tag": "DP-001", "symbol": "dry_pump_model.png", "x_hint": 4, "y_hint": 12},
    {"type": "Discharge Condenser", "tag": "DC-001", "symbol": "discharge_condenser.png", "x_hint": 4, "y_hint": 14},
    {"type": "Catch Pot (Manual, Disch)", "tag": "CPD-001", "symbol": "catch_pot_manual.png", "x_hint": 4, "y_hint": 16},
    {"type": "Catch Pot (Auto, Disch)", "tag": "CPAD-001", "symbol": "catch_pot_auto.png", "x_hint": 4, "y_hint": 18},
    {"type": "Discharge Silencer", "tag": "DS-001", "symbol": "discharge_silencer.png", "x_hint": 4, "y_hint": 20},
    {"type": "Receiver", "tag": "R-001", "symbol": "receiver.png", "x_hint": 4, "y_hint": 22},
    {"type": "Scrubber", "tag": "S-001", "symbol": "scrubber.png", "x_hint": 4, "y_hint": 24},
    # Side branches & panels
    {"type": "Control Panel (FLP)", "tag": "CPNL-001", "symbol": "flp_control_panel.png", "x_hint": 8, "y_hint": 12},
    {"type": "Solenoid Valve", "tag": "SV-001", "symbol": "solenoid_valve.png", "x_hint": 6, "y_hint": 8, "branch": True},
    {"type": "Pressure Gauge", "tag": "PG-001", "symbol": "pressure_gauge.png", "x_hint": 2, "y_hint": 10, "branch": True},
]

BASE_INLINE = [
    {"type": "Pressure Transmitter", "tag": "PT-001", "symbol": "pressure_transmitter.png", "x_hint": 4, "y_hint": 5},
    {"type": "Temperature Gauge", "tag": "TG-001", "symbol": "temperature_gauge.png", "x_hint": 4, "y_hint": 11},
    {"type": "Flow Switch", "tag": "FS-001", "symbol": "flow_switch.png", "x_hint": 4, "y_hint": 17},
    {"type": "Strainer", "tag": "STR-001", "symbol": "strainer.png", "x_hint": 4, "y_hint": 19},
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
    {"from": "R-001", "to": "S-001", "type": "Discharge Pipe", "flow_dir": "down"},
    # Side pipelines
    {"from": "CP-001", "to": "SV-001", "type": "Purge", "flow_dir": "right"},
    {"from": "CPA-001", "to": "PG-001", "type": "Gauge", "flow_dir": "left"},
    {"from": "DP-001", "to": "CPNL-001", "type": "Control", "flow_dir": "right"},
]

def list_symbol_pngs():
    try:
        return sorted([f for f in os.listdir("symbols") if f.lower().endswith(".png")])
    except Exception:
        return []

def get_font(size=14):
    try:
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

def draw_arrow(draw, start, end, flow_dir, color="black"):
    # Draws pipe with arrows at both ends and mid-point (→, ↓)
    draw.line([start, end], fill=color, width=3)
    _arrow(draw, start, end, flow_dir, color)
    _arrow(draw, end, start, flow_dir, color)
    # Midpoint arrow symbol
    mx = (start[0] + end[0]) // 2
    my = (start[1] + end[1]) // 2
    if flow_dir == "down":
        draw.text((mx-7, my+8), "↓", fill=color, font=get_font(18))
    elif flow_dir == "right":
        draw.text((mx+8, my-9), "→", fill=color, font=get_font(18))
    elif flow_dir == "left":
        draw.text((mx-20, my-9), "←", fill=color, font=get_font(18))
    elif flow_dir == "up":
        draw.text((mx-7, my-20), "↑", fill=color, font=get_font(18))

def _arrow(draw, tip, tail, flow_dir, color):
    dx = tail[0]-tip[0]
    dy = tail[1]-tip[1]
    length = (dx**2 + dy**2) ** 0.5
    if length == 0: length = 1
    ux = dx/length
    uy = dy/length
    p1 = (tip[0] + ARROW_WIDTH*ux - ARROW_HEIGHT*uy, tip[1] + ARROW_WIDTH*uy + ARROW_HEIGHT*ux)
    p2 = (tip[0] + ARROW_WIDTH*ux + ARROW_HEIGHT*uy, tip[1] + ARROW_WIDTH*uy - ARROW_HEIGHT*ux)
    draw.polygon([tip, p1, p2], outline=color, fill=color)

def draw_grid(draw, width, height, spacing):
    for i in range(0, width, spacing):
        draw.line([(i, 0), (i, height)], fill="#e0e0e0", width=1)
    for j in range(0, height, spacing):
        draw.line([(0, j), (width, j)], fill="#e0e0e0", width=1)

def circled_tag(draw, x, y, tag, position="bottom"):
    # Draw a circle with tag text inside
    font = get_font(16)
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
    w, h = draw.textsize(tag, font=font)
    draw.text((cx-w//2, cy-h//2), tag, fill="black", font=font)

def auto_size_and_layout(components):
    y_hints = [c["y_hint"] for c in components]
    max_y = max(y_hints) + 2
    grid_spacing = 100 + margin_y
    canvas_h = grid_spacing * max_y + PADDING*2 + TITLE_BLOCK_HEIGHT
    canvas_w = 1200
    for c in components:
        # Tall for columnar
        if any(word in c["type"].lower() for word in ["column", "condenser", "filter", "scrubber"]):
            c["height"] = max_height
            c["width"] = std_width
        else:
            c["height"] = std_height
            c["width"] = std_width
    return grid_spacing, canvas_w, canvas_h

# --- SESSION STATE ---
if "equipment" not in st.session_state:
    st.session_state.equipment = [dict(x) for x in BASE_COMPONENTS]
    st.session_state.inline = [dict(x) for x in BASE_INLINE]
    st.session_state.pipelines = [dict(x) for x in BASE_PIPELINES]
    st.session_state.tag_position = "bottom"

# Layout calculation
all_components = st.session_state.equipment + st.session_state.inline
grid_spacing, canvas_w, canvas_h = auto_size_and_layout(all_components)
coord_map = {}
for c in all_components:
    x = PADDING + c["x_hint"] * grid_spacing
    y = PADDING + c["y_hint"] * grid_spacing
    coord_map[c["tag"]] = (x, y)

# --- LEGEND / BOM ---
with st.sidebar:
    st.header("Legend / BOM")
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
    legend_df = pd.DataFrame(legend_items)
    st.dataframe(legend_df, hide_index=True, width=LEGEND_WIDTH)

# --- MAIN UI: TABLES ---
st.title("EPS Interactive P&ID Generator")
st.write("**Equipment, Pipeline & Inline Component Editor**")
st.selectbox("Tag Circle Position", ["left", "top", "bottom", "right"], key="tag_position")

# --- CANVAS PREVIEW ---
st.subheader("P&ID Drawing (Professional Layout)")
img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
draw_grid(draw, canvas_w, canvas_h, grid_spacing)

# Draw all equipment
for eq in st.session_state.equipment:
    tag = eq["tag"]
    typ = eq["type"]
    symbol = eq["symbol"]
    x, y = coord_map[tag]
    width, height = eq.get("width", std_width), eq.get("height", std_height)
    symbol_img = symbol_or_missing(symbol, width, height)
    img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
    font = get_font(14)
    draw.text((x, y+height//2+20), tag, anchor="mm", fill="black", font=font)
    circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

# Draw inline components
for ic in st.session_state.inline:
    tag = ic["tag"]
    x, y = coord_map[tag]
    width, height = ic.get("width", std_width), ic.get("height", std_height)
    symbol_img = symbol_or_missing(ic["symbol"], width, height)
    img.paste(symbol_img, (int(x-width//2), int(y-height//2)), symbol_img)
    font = get_font(12)
    draw.text((x, y+height//2+20), tag, anchor="mm", fill="black", font=font)
    circled_tag(draw, x, y, tag, position=st.session_state.tag_position)

# Draw pipelines - always orthogonal, arrows at joints, circled tags
for idx, pl in enumerate(st.session_state.pipelines):
    from_tag = pl["from"]
    to_tag = pl["to"]
    flow_dir = pl.get("flow_dir", "down")
    if from_tag in coord_map and to_tag in coord_map:
        x1, y1 = coord_map[from_tag]
        x2, y2 = coord_map[to_tag]
        # Orthogonal routing: horizontal then vertical or vice versa
        if flow_dir == "down":
            mx, my = x1, y2
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "right":
            mx, my = x2, y1
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "left":
            mx, my = x2, y1
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        elif flow_dir == "up":
            mx, my = x1, y2
            draw.line([(x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (mx, my), flow_dir)
            draw_arrow(draw, (mx, my), (x2, y2), flow_dir)
        # Circled tag at each joint
        circled_tag(draw, x1, y1, str(idx+1), position="left")
        circled_tag(draw, x2, y2, str(idx+1), position="right")
        # Pipe type label
        draw.text(((x1+x2)//2, (y1+y2)//2-18), pl["type"], anchor="mm", fill="gray", font=get_font(12))

# Draw legend box (top right)
legend_x = canvas_w - LEGEND_WIDTH - PADDING
legend_y = PADDING
draw.rectangle([legend_x, legend_y, canvas_w-PADDING, legend_y+30*(len(legend_items)+2)], outline="black", width=2)
font = get_font()
draw.text((legend_x+10, legend_y+5), "Legend / BOM", fill="black", font=font)
for i, item in enumerate(legend_items):
    draw.text((legend_x+10, legend_y+30*(i+1)+5), f"{item['Type']} [{item['Tag']}]", fill="black", font=font)
    symbol = symbol_or_missing(item["Symbol"], std_width, std_height)
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
        width = eq.get("width", std_width)
        height = eq.get("height", std_height)
        msp.add_lwpolyline([(x-width//2, y-height//2), (x+width//2, y-height//2), (x+width//2, y+height//2), (x-width//2, y+height//2), (x-width//2, y-height//2)], close=True)
        msp.add_text(tag, dxfattribs={"height": 20}).set_pos((x, y+height//2+20))
    for pl in st.session_state.pipelines:
        from_tag = pl["from"]
        to_tag = pl["to"]
        if from_tag in coord_map and to_tag in coord_map:
            x1, y1 = coord_map[from_tag]
            x2, y2 = coord_map[to_tag]
            mx, my = x1, y2
            msp.add_lwpolyline([(x1, y1), (mx, my), (x2, y2)])
    msp.add_text("EPS Interactive P&ID", dxfattribs={"height": 30}).set_pos((tb_x+10, tb_y+10))
    msp.add_text(f"Date: {today_str()}", dxfattribs={"height": 20}).set_pos((tb_x+10, tb_y+40))
    msp.add_text("Sheet: 1 of 1", dxfattribs={"height": 20}).set_pos((tb_x+10, tb_y+70))
    msp.add_text(f"CLIENT: {TITLE_BLOCK_CLIENT}", dxfattribs={"height": 20}).set_pos((tb_x+220, tb_y+10))
    buf = io.BytesIO()
    doc.saveas(buf)
    return buf.getvalue()

if st.button("Download DXF"):
    dxf_bytes = export_dxf()
    st.download_button("Save DXF", data=dxf_bytes, file_name="pid.dxf", mime="application/dxf")

missing_syms = [eq["symbol"] for eq in st.session_state.equipment+st.session_state.inline if not load_symbol(eq["symbol"], std_width, std_height)]
if missing_syms:
    st.warning(f"Missing symbols: {', '.join(set(missing_syms))} (shown as gray box). Please add PNGs in /symbols.")

# --- AI SUGGESTIONS (placeholder) ---
st.sidebar.markdown("### 💡 AI Suggestions (coming soon)")
st.sidebar.info("• Improve suction pressure by resizing filter\n• Add bypass for maintenance\n• Use jacketed condenser for energy saving\n• Suggestions will appear here automatically with full layout.")
