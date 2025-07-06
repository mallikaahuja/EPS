import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import ezdxf
import io
import math

# --- CONSTANTS ---
MIN_SYMBOL_SIZE = 80
MAX_SYMBOL_SIZE = 140
MIN_GRID_SPACING = 160
MAX_GRID_SPACING = 260
PADDING = 50
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
TITLE_BLOCK_CLIENT = "Rajesh Ahuja"
ARROW_WIDTH = 10
ARROW_HEIGHT = 15

GRID_ROWS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
GRID_COLS = list(range(1, 20))

# --- BASE COMPONENTS from REFERENCE ---
BASE_COMPONENTS = [
    {"type": "Flame Arrestor", "tag": "FA-001", "symbol": "flame_arrestor.png"},
    {"type": "Suction Filter", "tag": "SF-001", "symbol": "suction_filter.png"},
    {"type": "Suction Condenser", "tag": "SC-001", "symbol": "suction_condenser.png"},
    {"type": "Catch Pot", "tag": "CP-001", "symbol": "catch_pot_manual.png"},
    {"type": "Catch Pot (Auto)", "tag": "CPA-001", "symbol": "catch_pot_auto.png"},
    {"type": "Dry Pump Model KDP330", "tag": "DP-001", "symbol": "dry_pump_model.png"},
    {"type": "Discharge Condenser", "tag": "DC-001", "symbol": "discharge_condenser.png"},
    {"type": "Catch Pot (Manual, Disch)", "tag": "CPD-001", "symbol": "catch_pot_manual.png"},
    {"type": "Catch Pot (Auto, Disch)", "tag": "CPAD-001", "symbol": "catch_pot_auto.png"},
    {"type": "Discharge Silencer", "tag": "DS-001", "symbol": "discharge_silencer.png"},
    {"type": "Receiver", "tag": "R-001", "symbol": "receiver.png"},
    {"type": "Scrubber", "tag": "S-001", "symbol": "scrubber.png"},
    {"type": "Control Panel (FLP)", "tag": "CPNL-001", "symbol": "flp_control_panel.png"},
]

BASE_INLINE = [
    {"type": "Pressure Transmitter", "tag": "PT-001", "symbol": "pressure_transmitter.png"},
    {"type": "Temperature Transmitter", "tag": "TT-001", "symbol": "temperature_transmitter.png"},
    {"type": "Temperature Gauge", "tag": "TG-001", "symbol": "temperature_gauge.png"},
    {"type": "EPO Valve", "tag": "V-001", "symbol": "epo_valve.png"},
    {"type": "Solenoid Valve", "tag": "SV-001", "symbol": "solenoid_valve.png"},
    {"type": "Pressure Switch", "tag": "PS-001", "symbol": "pressure_switch.png"},
    {"type": "Flow Switch", "tag": "FS-001", "symbol": "flow_switch.png"},
    {"type": "Strainer", "tag": "STR-001", "symbol": "strainer.png"},
]

BASE_PIPELINES = [
    {"from": "FA-001", "to": "SF-001", "type": "Suction Pipe"},
    {"from": "SF-001", "to": "SC-001", "type": "Suction Pipe"},
    {"from": "SC-001", "to": "CP-001", "type": "Suction Pipe"},
    {"from": "CP-001", "to": "CPA-001", "type": "Suction Pipe"},
    {"from": "CPA-001", "to": "DP-001", "type": "Suction Pipe"},
    {"from": "DP-001", "to": "DC-001", "type": "Discharge Pipe"},
    {"from": "DC-001", "to": "CPD-001", "type": "Discharge Pipe"},
    {"from": "CPD-001", "to": "CPAD-001", "type": "Discharge Pipe"},
    {"from": "CPAD-001", "to": "DS-001", "type": "Discharge Pipe"},
    {"from": "DS-001", "to": "R-001", "type": "Discharge Pipe"},
    {"from": "R-001", "to": "S-001", "type": "Discharge Pipe"},
]

def auto_tag(prefix, existing_tags):
    n = 1
    while f"{prefix}-{n:03d}" in existing_tags:
        n += 1
    return f"{prefix}-{n:03d}"

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

def load_symbol(symbol_name, symbol_size):
    symbol_path = os.path.join("symbols", symbol_name)
    if os.path.isfile(symbol_path):
        img = Image.open(symbol_path).convert("RGBA").resize((symbol_size, symbol_size))
        return img
    return None

def symbol_or_missing(symbol_name, symbol_size):
    symbol = load_symbol(symbol_name, symbol_size)
    if symbol:
        return symbol
    img = Image.new("RGBA", (symbol_size, symbol_size), (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5,5,symbol_size-5,symbol_size-5], outline="gray", width=2)
    font = get_font(12)
    draw.text((10, symbol_size//2-10), "Missing\nSymbol", fill="gray", font=font)
    return img

def draw_arrow(draw, start, end, arrow_width, arrow_height, color="black"):
    draw.line([start, end], fill=color, width=3)
    _arrow(draw, end, start, arrow_width, arrow_height, color)
    _arrow(draw, start, end, arrow_width, arrow_height, color)

def _arrow(draw, tip, tail, arrow_width, arrow_height, color):
    dx = tail[0]-tip[0]
    dy = tail[1]-tip[1]
    length = (dx**2 + dy**2) ** 0.5
    if length == 0:
        length = 1
    ux = dx/length
    uy = dy/length
    p1 = (tip[0] + arrow_width*ux - arrow_height*uy,
          tip[1] + arrow_width*uy + arrow_height*ux)
    p2 = (tip[0] + arrow_width*ux + arrow_height*uy,
          tip[1] + arrow_width*uy - arrow_height*ux)
    draw.polygon([tip, p1, p2], outline=color, fill=color)

def draw_grid(draw, width, height, spacing):
    for i in range(0, width, spacing):
        draw.line([(i, 0), (i, height)], fill="#e0e0e0", width=1)
    for j in range(0, height, spacing):
        draw.line([(0, j), (width, j)], fill="#e0e0e0", width=1)

# --- AUTO-SIZING & AUTO-ARRANGEMENT LOGIC ---
def compute_auto_sizing(equipment_count):
    # Try to fit all equipment into 75% of a 1600px canvas
    max_canvas_h = 1400
    min_spacing = MIN_GRID_SPACING
    max_spacing = MAX_GRID_SPACING
    min_size = MIN_SYMBOL_SIZE
    max_size = MAX_SYMBOL_SIZE

    # vertical stack, one spacing per equipment + one at top and bottom
    needed_h = (equipment_count+1) * min_spacing
    grid_spacing = min(max_spacing, max(min_spacing, max_canvas_h // (equipment_count+1)))
    symbol_size = min(max_size, max(min_size, int(grid_spacing*0.5)))

    return grid_spacing, symbol_size

def auto_grid(equipment, grid_spacing):
    grid = {}
    col_main = 4
    col_panel = 7
    row_letters = GRID_ROWS
    row_idx = 0
    for eq in equipment:
        name = eq["type"].lower()
        tag = eq["tag"]
        # Panels placed to the right at the same row as main equipment
        if "panel" in name or "control" in name:
            grid[tag] = (row_letters[max(row_idx-1, 0)], col_panel)
        else:
            grid[tag] = (row_letters[row_idx], col_main)
            row_idx += 1
    return grid

def component_grid_xy(row, col, grid_spacing):
    x = PADDING + (col-1)*grid_spacing
    y = PADDING + GRID_ROWS.index(row)*grid_spacing
    return x, y

# --- SESSION STATE ---
if "equipment" not in st.session_state:
    st.session_state.equipment = [dict(x) for x in BASE_COMPONENTS]
    n_eq = len(st.session_state.equipment)
    grid_spacing, symbol_size = compute_auto_sizing(n_eq)
    st.session_state.grid_spacing = grid_spacing
    st.session_state.symbol_size = symbol_size
    st.session_state.grid = auto_grid(st.session_state.equipment, grid_spacing)
if "pipelines" not in st.session_state:
    st.session_state.pipelines = [dict(x) for x in BASE_PIPELINES]
if "inline" not in st.session_state:
    st.session_state.inline = [dict(x) for x in BASE_INLINE]

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

# --- UI: EDIT TABLES ---
st.title("EPS Interactive P&ID Generator")
st.write("**Equipment, Pipeline & Inline Component Editor**")

def editable_equipment_table(label, data):
    df = pd.DataFrame(data)
    available_pngs = list_symbol_pngs()
    edited_rows = []
    for idx, row in df.iterrows():
        c1, c2, c3 = st.columns([3,2,2])
        with c1:
            typ = st.text_input(f"Type {idx+1}", value=row["type"], key=f"type_{label}_{idx}")
        with c2:
            tag = st.text_input(f"Tag {idx+1}", value=row["tag"], key=f"tag_{label}_{idx}")
        with c3:
            symbol = st.selectbox(
                f"Symbol {idx+1}",
                available_pngs,
                index=available_pngs.index(row["symbol"]) if row["symbol"] in available_pngs else 0,
                key=f"symbol_{label}_{idx}"
            ) if available_pngs else row["symbol"]
        edited_rows.append({"type": typ, "tag": tag, "symbol": symbol})
    return edited_rows

def editable_inline_table(label, data):
    df = pd.DataFrame(data)
    available_pngs = list_symbol_pngs()
    edited_rows = []
    for idx, row in df.iterrows():
        c1, c2, c3 = st.columns([3,2,2])
        with c1:
            typ = st.text_input(f"Type (inline) {idx+1}", value=row["type"], key=f"type_inline_{label}_{idx}")
        with c2:
            tag = st.text_input(f"Tag (inline) {idx+1}", value=row["tag"], key=f"tag_inline_{label}_{idx}")
        with c3:
            symbol = st.selectbox(
                f"Symbol (inline) {idx+1}",
                available_pngs,
                index=available_pngs.index(row["symbol"]) if row["symbol"] in available_pngs else 0,
                key=f"symbol_inline_{label}_{idx}"
            ) if available_pngs else row["symbol"]
        edited_rows.append({"type": typ, "tag": tag, "symbol": symbol})
    return edited_rows

def editable_pipeline_table(label, data):
    df = pd.DataFrame(data)
    edited_rows = []
    for idx, row in df.iterrows():
        c1, c2, c3 = st.columns([3,3,3])
        with c1:
            frm = st.text_input(f"From {idx+1}", value=row["from"], key=f"from_{label}_{idx}")
        with c2:
            to = st.text_input(f"To {idx+1}", value=row["to"], key=f"to_{label}_{idx}")
        with c3:
            typ = st.text_input(f"Type {idx+1}", value=row["type"], key=f"type_{label}_pipe_{idx}")
        edited_rows.append({"from": frm, "to": to, "type": typ})
    return edited_rows

# --- AUTO-RESIZE LOGIC ON CHANGE ---
n_eq = len(st.session_state.equipment)
grid_spacing, symbol_size = compute_auto_sizing(n_eq)
if grid_spacing != st.session_state.get('grid_spacing', 0) or symbol_size != st.session_state.get('symbol_size', 0):
    st.session_state.grid_spacing = grid_spacing
    st.session_state.symbol_size = symbol_size
    st.session_state.grid = auto_grid(st.session_state.equipment, grid_spacing)

# Equipment table
st.subheader("Equipment")
available_pngs = list_symbol_pngs()
new_eq_type = st.text_input("New Equipment Type", key="new_eq_type")
new_eq_symbol = st.selectbox("Symbol", available_pngs, key="new_eq_symbol") if available_pngs else ""
if st.button("Add Equipment"):
    tag_prefix = "".join([w[0] for w in new_eq_type.split()]).upper()
    exist_tags = [eq["tag"] for eq in st.session_state.equipment]
    tag = auto_tag(tag_prefix, exist_tags)
    st.session_state.equipment.append({"type": new_eq_type, "tag": tag, "symbol": new_eq_symbol})
    # After change, recompute grid and sizing!
    n_eq = len(st.session_state.equipment)
    grid_spacing, symbol_size = compute_auto_sizing(n_eq)
    st.session_state.grid_spacing = grid_spacing
    st.session_state.symbol_size = symbol_size
    st.session_state.grid = auto_grid(st.session_state.equipment, grid_spacing)
    st.rerun()
st.session_state.equipment = editable_equipment_table("equipment_editor", st.session_state.equipment)

# Inline table
st.subheader("Inline Components")
new_inline_type = st.text_input("New Inline Type", key="new_inline_type")
new_inline_symbol = st.selectbox("Inline Symbol", available_pngs, key="new_inline_symbol") if available_pngs else ""
if st.button("Add Inline Component"):
    tag_prefix = "".join([w[0] for w in new_inline_type.split()]).upper()
    exist_tags = [ic["tag"] for ic in st.session_state.inline]
    tag = auto_tag(tag_prefix, exist_tags)
    st.session_state.inline.append({"type": new_inline_type, "tag": tag, "symbol": new_inline_symbol})
    st.rerun()
st.session_state.inline = editable_inline_table("inline_editor", st.session_state.inline)

# Pipelines UI
st.subheader("Pipelines")
if len(st.session_state.equipment) >= 2:
    from_opts = [eq["tag"] for eq in st.session_state.equipment]
    to_opts = [eq["tag"] for eq in st.session_state.equipment]
    new_from = st.selectbox("From", from_opts, key="new_pipe_from")
    new_to = st.selectbox("To", to_opts, key="new_pipe_to")
    if st.button("Add Pipeline"):
        st.session_state.pipelines.append({"from": new_from, "to": new_to, "type": "Process Pipe"})
        st.rerun()
st.session_state.pipelines = editable_pipeline_table("pipeline_editor", st.session_state.pipelines)

# --- Editable grid positions (auto-arranged, but you can also adjust manually) ---
st.subheader("Edit Equipment Grid Positions (auto-arranged unless you change them)")
for idx, eq in enumerate(st.session_state.equipment):
    tag = eq["tag"]
    r, c = st.session_state.grid.get(tag, (GRID_ROWS[0], GRID_COLS[0]))
    col1, col2 = st.columns(2)
    with col1:
        new_r = st.selectbox(
            f"Row for {tag}",
            GRID_ROWS,
            index=GRID_ROWS.index(r),
            key=f"row_{tag}_{idx}"
        )
    with col2:
        new_c = st.selectbox(
            f"Col for {tag}",
            GRID_COLS,
            index=GRID_COLS.index(c),
            key=f"col_{tag}_{idx}"
        )
    st.session_state.grid[tag] = (new_r, new_c)

# --- CANVAS PREVIEW ---
st.subheader("P&ID Drawing (Auto-sized, Auto-arranged)")
canvas_w = max(LEGEND_WIDTH+PADDING*2+st.session_state.grid_spacing*(max(GRID_COLS)), 1200)
canvas_h = st.session_state.grid_spacing*(n_eq+2) + PADDING*2 + TITLE_BLOCK_HEIGHT

img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
draw_grid(draw, canvas_w, canvas_h, st.session_state.grid_spacing)

# Draw all equipment
for eq in st.session_state.equipment:
    tag = eq["tag"]
    typ = eq["type"]
    symbol = eq["symbol"]
    r, c = st.session_state.grid.get(tag, (GRID_ROWS[0], GRID_COLS[0]))
    x, y = component_grid_xy(r, c, st.session_state.grid_spacing)
    symbol_img = symbol_or_missing(symbol, st.session_state.symbol_size)
    img.paste(symbol_img, (x+st.session_state.grid_spacing//2-st.session_state.symbol_size//2, y+st.session_state.grid_spacing//2-st.session_state.symbol_size//2), symbol_img)
    font = get_font(14)
    draw.text((x+st.session_state.grid_spacing//2, y+st.session_state.grid_spacing//2+st.session_state.symbol_size//2+15), tag, anchor="mm", fill="black", font=font)

# Draw pipelines (orthogonal, arrows at both ends)
for idx, pl in enumerate(st.session_state.pipelines):
    from_tag = pl["from"]
    to_tag = pl["to"]
    if from_tag in st.session_state.grid and to_tag in st.session_state.grid:
        x1, y1 = component_grid_xy(*st.session_state.grid[from_tag], st.session_state.grid_spacing)
        x2, y2 = component_grid_xy(*st.session_state.grid[to_tag], st.session_state.grid_spacing)
        x1 += st.session_state.grid_spacing//2
        y1 += st.session_state.grid_spacing//2
        x2 += st.session_state.grid_spacing//2
        y2 += st.session_state.grid_spacing//2
        if x1 == x2 or y1 == y2:
            draw.line([ (x1, y1), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (x2, y2), ARROW_WIDTH, ARROW_HEIGHT)
        else:
            mx = x1
            my = y2
            draw.line([ (x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (mx, my), (x2, y2), ARROW_WIDTH, ARROW_HEIGHT)
            draw_arrow(draw, (x1, y1), (mx, my), ARROW_WIDTH, ARROW_HEIGHT)
        draw.text(((x1+x2)//2, (y1+y2)//2-12), pl["type"], anchor="mm", fill="gray", font=get_font(12))

# Draw inline components (mid-pipe)
for idx, ic in enumerate(st.session_state.inline):
    if idx < len(st.session_state.pipelines):
        pl = st.session_state.pipelines[idx]
        from_tag = pl["from"]
        to_tag = pl["to"]
        x1, y1 = component_grid_xy(*st.session_state.grid[from_tag], st.session_state.grid_spacing)
        x2, y2 = component_grid_xy(*st.session_state.grid[to_tag], st.session_state.grid_spacing)
        mx = (x1 + x2)//2 + st.session_state.grid_spacing//2
        my = (y1 + y2)//2 + st.session_state.grid_spacing//2
        symbol_img = symbol_or_missing(ic["symbol"], st.session_state.symbol_size)
        img.paste(symbol_img, (mx-st.session_state.symbol_size//2, my-st.session_state.symbol_size//2), symbol_img)
        font = get_font(12)
        draw.text((mx, my+st.session_state.symbol_size//2+10), ic["tag"], anchor="mm", fill="black", font=font)

# Draw legend box (top right)
legend_x = canvas_w - LEGEND_WIDTH - PADDING
legend_y = PADDING
draw.rectangle([legend_x, legend_y, canvas_w-PADDING, legend_y+30*(len(legend_items)+2)], outline="black", width=2)
font = get_font()
draw.text((legend_x+10, legend_y+5), "Legend / BOM", fill="black", font=font)
for i, item in enumerate(legend_items):
    draw.text((legend_x+10, legend_y+30*(i+1)+5), f"{item['Type']} [{item['Tag']}]", fill="black", font=font)
    symbol = symbol_or_missing(item["Symbol"], st.session_state.symbol_size)
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
        x, y = component_grid_xy(*st.session_state.grid[tag], st.session_state.grid_spacing)
        msp.add_lwpolyline([(x, y), (x+st.session_state.symbol_size, y), (x+st.session_state.symbol_size, y+st.session_state.symbol_size), (x, y+st.session_state.symbol_size), (x, y)], close=True)
        msp.add_text(tag, dxfattribs={"height": 20}).set_pos((x, y+st.session_state.symbol_size+20))
    for pl in st.session_state.pipelines:
        from_tag = pl["from"]
        to_tag = pl["to"]
        if from_tag in st.session_state.grid and to_tag in st.session_state.grid:
            x1, y1 = component_grid_xy(*st.session_state.grid[from_tag], st.session_state.grid_spacing)
            x2, y2 = component_grid_xy(*st.session_state.grid[to_tag], st.session_state.grid_spacing)
            mx = x1
            my = y2
            msp.add_lwpolyline([ (x1, y1), (mx, my), (x2, y2)])
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

missing_syms = [eq["symbol"] for eq in st.session_state.equipment+st.session_state.inline if not load_symbol(eq["symbol"], st.session_state.symbol_size)]
if missing_syms:
    st.warning(f"Missing symbols: {', '.join(set(missing_syms))} (shown as gray box). Please add PNGs in /symbols.")
