import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import ezdxf
import io

# --- CONSTANTS ---
GRID_ROWS = list("ABCDEF")
GRID_COLS = list(range(1, 9))
GRID_SPACING = 250
SYMBOL_SIZE = 100
LEGEND_WIDTH = 350
TITLE_BLOCK_HEIGHT = 120
TITLE_BLOCK_WIDTH = 420
PADDING = 50
ARROW_WIDTH = 10
ARROW_HEIGHT = 6

TITLE_BLOCK_CLIENT = "Rajesh Ahuja"

# --- HELPERS ---

def auto_tag(prefix, existing_tags):
    n = 1
    while f"{prefix}-{n:03d}" in existing_tags:
        n += 1
    return f"{prefix}-{n:03d}"

def load_symbol(symbol_name):
    symbol_path = os.path.join("symbols", symbol_name)
    if os.path.isfile(symbol_path):
        img = Image.open(symbol_path).convert("RGBA").resize((SYMBOL_SIZE, SYMBOL_SIZE))
        return img
    return None

def draw_arrow(draw, start, end, color="black"):
    draw.line([start, end], fill=color, width=3)
    # Arrowhead at end
    arrow_tip = end
    dx = start[0]-end[0]
    dy = start[1]-end[1]
    length = (dx**2 + dy**2) ** 0.5
    if length == 0:
        length = 1
    ux = dx/length
    uy = dy/length
    p1 = (arrow_tip[0] + ARROW_WIDTH*ux - ARROW_HEIGHT*uy,
          arrow_tip[1] + ARROW_WIDTH*uy + ARROW_HEIGHT*ux)
    p2 = (arrow_tip[0] + ARROW_WIDTH*ux + ARROW_HEIGHT*uy,
          arrow_tip[1] + ARROW_WIDTH*uy - ARROW_HEIGHT*ux)
    draw.polygon([arrow_tip, p1, p2], outline=color, fill=None)

def draw_grid(draw, width, height, spacing=GRID_SPACING):
    for i in range(0, width, spacing):
        draw.line([(i, 0), (i, height)], fill="#e0e0e0", width=1)
    for j in range(0, height, spacing):
        draw.line([(0, j), (width, j)], fill="#e0e0e0", width=1)

def get_font(size=14):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def symbol_or_missing(symbol_name):
    symbol = load_symbol(symbol_name)
    if symbol:
        return symbol
    # Missing symbol: light gray box with text
    img = Image.new("RGBA", (SYMBOL_SIZE, SYMBOL_SIZE), (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5,5,SYMBOL_SIZE-5,SYMBOL_SIZE-5], outline="gray", width=2)
    font = get_font(12)
    draw.text((10, SYMBOL_SIZE//2-10), "Missing\nSymbol", fill="gray", font=font)
    return img

def component_grid_xy(row, col):
    x = PADDING + (col-1)*GRID_SPACING
    y = PADDING + GRID_ROWS.index(row)*GRID_SPACING
    return x, y

def today_str():
    return datetime.date.today().isoformat()

# --- LOAD CSVs ---
def load_csv(fname, defaults):
    if os.path.isfile(fname):
        df = pd.read_csv(fname)
        for col in defaults:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame([defaults])

equipment_df = load_csv("equipment_list.csv", {"type": "Dry Pump", "symbol": "dry_pump.png"})
pipeline_df = load_csv("pipeline_list.csv", {"from": "", "to": "", "type": "Process Pipe"})
inline_df = load_csv("inline_component_list.csv", {"type": "Check Valve", "symbol": "check_valve.png"})

# --- SESSION STATE ---
if "equipment" not in st.session_state:
    # On first run, populate the classic core stack
    default_types = [
        ("Dry Pump", "dry_pump.png"),
        ("Column", "column.png"),
        ("Condenser", "condenser.png"),
        ("Receiver", "receiver.png"),
    ]
    equipment = []
    default_rows = ["A", "B", "C", "D"]
    for i, (typ, sym) in enumerate(default_types):
        tag_prefix = "".join([w[0] for w in typ.split()]).upper()
        tag = f"{tag_prefix}-001"
        equipment.append({"type": typ, "tag": tag, "symbol": sym})
    st.session_state.equipment = equipment
    # Default grid layout: stack in first column
    st.session_state.grid = {}
    for i, eq in enumerate(equipment):
        st.session_state.grid[eq["tag"]] = (default_rows[i], 1)
if "pipelines" not in st.session_state:
    # Wire up the core stack
    st.session_state.pipelines = []
    tags = [eq["tag"] for eq in st.session_state.equipment]
    for i in range(len(tags)-1):
        st.session_state.pipelines.append({"from": tags[i], "to": tags[i+1], "type": "Process Pipe"})
if "inline" not in st.session_state:
    st.session_state.inline = []

# --- SIDEBAR: LEGEND ---
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
                "Tag Prefix": eq["tag"].split("-")[0]
            })
    legend_df = pd.DataFrame(legend_items)
    st.dataframe(legend_df, hide_index=True, width=LEGEND_WIDTH)

# --- MAIN UI: TABLES ---
st.title("EPS Interactive P&ID Generator")

st.write("**Equipment, Pipeline & Inline Component Editor**")

# --- Editable equipment table ---
def editable_table(label, data, cols):
    df = pd.DataFrame(data)
    edited = st.data_editor(df, num_rows="dynamic", key=label)
    return edited.to_dict(orient="records")

# Add Equipment
st.subheader("Equipment")
equipment_opts = equipment_df["type"].unique().tolist()
symbol_map = dict(zip(equipment_df["type"], equipment_df["symbol"]))

new_eq_type = st.selectbox("Type", equipment_opts, key="new_eq_type")
if st.button("Add Equipment"):
    tag_prefix = "".join([w[0] for w in new_eq_type.split()]).upper()
    exist_tags = [eq["tag"] for eq in st.session_state.equipment]
    tag = auto_tag(tag_prefix, exist_tags)
    symbol = symbol_map.get(new_eq_type, "")
    # Default to next open grid position
    used = set(st.session_state.grid.values())
    found = False
    for r in GRID_ROWS:
        for c in GRID_COLS:
            if (r, c) not in used:
                found = True
                break
        if found:
            break
    st.session_state.equipment.append({"type": new_eq_type, "tag": tag, "symbol": symbol})
    st.session_state.grid[tag] = (r, c)
    st.rerun()

# Table for editing equipment
st.session_state.equipment = editable_table("equipment_editor", st.session_state.equipment, ["type", "tag", "symbol"])

# Inline components UI
st.subheader("Inline Components")
inline_opts = inline_df["type"].unique().tolist()
inline_symbol_map = dict(zip(inline_df["type"], inline_df["symbol"]))
new_inline_type = st.selectbox("Inline Type", inline_opts, key="new_inline_type")
if st.button("Add Inline Component"):
    tag_prefix = "".join([w[0] for w in new_inline_type.split()]).upper()
    exist_tags = [ic["tag"] for ic in st.session_state.inline]
    tag = auto_tag(tag_prefix, exist_tags)
    symbol = inline_symbol_map.get(new_inline_type, "")
    st.session_state.inline.append({"type": new_inline_type, "tag": tag, "symbol": symbol})
    st.rerun()
st.session_state.inline = editable_table("inline_editor", st.session_state.inline, ["type", "tag", "symbol"])

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
st.session_state.pipelines = editable_table("pipeline_editor", st.session_state.pipelines, ["from", "to", "type"])

# --- Editable grid positions ---
st.subheader("Edit Equipment Grid Positions")
for eq in st.session_state.equipment:
    tag = eq["tag"]
    r, c = st.session_state.grid.get(tag, (GRID_ROWS[0], GRID_COLS[0]))
    col1, col2 = st.columns(2)
    with col1:
        new_r = st.selectbox(f"Row for {tag}", GRID_ROWS, index=GRID_ROWS.index(r), key=f"row_{tag}")
    with col2:
        new_c = st.selectbox(f"Col for {tag}", GRID_COLS, index=GRID_COLS.index(c), key=f"col_{tag}")
    st.session_state.grid[tag] = (new_r, new_c)

# --- CANVAS PREVIEW ---
st.subheader("P&ID Drawing (Zoom/Scroll in Output)")
canvas_w = len(GRID_COLS)*GRID_SPACING + PADDING*2 + LEGEND_WIDTH
canvas_h = len(GRID_ROWS)*GRID_SPACING + PADDING*2 + TITLE_BLOCK_HEIGHT

img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
draw_grid(draw, canvas_w, canvas_h)

# Draw all equipment
for eq in st.session_state.equipment:
    tag = eq["tag"]
    typ = eq["type"]
    symbol = eq["symbol"]
    r, c = st.session_state.grid.get(tag, (GRID_ROWS[0], GRID_COLS[0]))
    x, y = component_grid_xy(r, c)
    symbol_img = symbol_or_missing(symbol)
    img.paste(symbol_img, (x, y), symbol_img)
    font = get_font()
    # Draw tag below symbol, centered
    draw.text((x+SYMBOL_SIZE//2, y+SYMBOL_SIZE+20), tag, anchor="mm", fill="black", font=font)
    # Callout circle at top-left of symbol
    draw.ellipse([x-15, y-15, x+15, y+15], outline="black", width=2)
    draw.text((x, y), str(tag), anchor="mm", fill="black", font=font)

# Draw pipelines
for pl in st.session_state.pipelines:
    from_tag = pl["from"]
    to_tag = pl["to"]
    if from_tag in st.session_state.grid and to_tag in st.session_state.grid:
        x1, y1 = component_grid_xy(*st.session_state.grid[from_tag])
        x2, y2 = component_grid_xy(*st.session_state.grid[to_tag])
        x1 += SYMBOL_SIZE//2
        y1 += SYMBOL_SIZE//2
        x2 += SYMBOL_SIZE//2
        y2 += SYMBOL_SIZE//2
        # Orthogonal lines: horizontal then vertical unless in same row or col
        if x1 == x2 or y1 == y2:
            draw.line([ (x1, y1), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (x1, y1), (x2, y2))
            draw_arrow(draw, (x2, y2), (x1, y1))
        else:
            mx = x1
            my = y2
            draw.line([ (x1, y1), (mx, my), (x2, y2)], fill="black", width=3)
            draw_arrow(draw, (mx, my), (x2, y2))
            draw_arrow(draw, (x1, y1), (mx, my))
# Draw inline components (mid-pipe)
for ic in st.session_state.inline:
    # Place in the middle of first pipeline for demo
    if st.session_state.pipelines:
        pl = st.session_state.pipelines[0]
        from_tag = pl["from"]
        to_tag = pl["to"]
        x1, y1 = component_grid_xy(*st.session_state.grid[from_tag])
        x2, y2 = component_grid_xy(*st.session_state.grid[to_tag])
        mx = (x1 + x2)//2
        my = (y1 + y2)//2
        symbol_img = symbol_or_missing(ic["symbol"])
        img.paste(symbol_img, (mx, my), symbol_img)
        font = get_font()
        draw.text((mx+SYMBOL_SIZE//2, my+SYMBOL_SIZE+20), ic["tag"], anchor="mm", fill="black", font=font)
# Draw legend box
legend_x = canvas_w - LEGEND_WIDTH - PADDING
legend_y = PADDING
draw.rectangle([legend_x, legend_y, canvas_w-PADDING, legend_y+30*(len(legend_items)+2)], outline="black", width=2)
font = get_font()
draw.text((legend_x+10, legend_y+5), "Legend / BOM", fill="black", font=font)
for i, item in enumerate(legend_items):
    draw.text((legend_x+10, legend_y+30*(i+1)+5), f"{item['Type']} ({item['Tag Prefix']})", fill="black", font=font)
    symbol = symbol_or_missing(item["Symbol"])
    img.paste(symbol, (legend_x+200, legend_y+30*(i+1)), symbol)
# Draw title block
tb_x = canvas_w - TITLE_BLOCK_WIDTH - PADDING
tb_y = canvas_h - TITLE_BLOCK_HEIGHT - PADDING
draw.rectangle([tb_x, tb_y, canvas_w-PADDING, canvas_h-PADDING], outline="black", width=2)
draw.text((tb_x+10, tb_y+10), "EPS Interactive P&ID", fill="black", font=font)
draw.text((tb_x+10, tb_y+40), f"Date: {today_str()}", fill="black", font=font)
draw.text((tb_x+10, tb_y+70), f"Page: 1 of 1", fill="black", font=font)
draw.text((tb_x+250, tb_y+10), f"CLIENT: {TITLE_BLOCK_CLIENT}", fill="black", font=font)
# Padding
draw.rectangle([PADDING, PADDING, canvas_w-PADDING, canvas_h-PADDING], outline="#bbbbbb", width=1)

# Show image
st.image(img, use_container_width=True)

# --- EXPORT PNG ---
buf = io.BytesIO()
img.save(buf, format="PNG")
st.download_button("Download PNG", data=buf.getvalue(), file_name="pid.png", mime="image/png")

# --- EXPORT DXF ---
def export_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()
    # Draw equipment as rectangles
    for eq in st.session_state.equipment:
        tag = eq["tag"]
        x, y = component_grid_xy(*st.session_state.grid[tag])
        msp.add_lwpolyline([(x, y), (x+SYMBOL_SIZE, y), (x+SYMBOL_SIZE, y+SYMBOL_SIZE), (x, y+SYMBOL_SIZE), (x, y)], close=True)
        msp.add_text(tag, dxfattribs={"height": 20}).set_pos((x, y+SYMBOL_SIZE+20))
    # Draw pipelines as polylines
    for pl in st.session_state.pipelines:
        from_tag = pl["from"]
        to_tag = pl["to"]
        if from_tag in st.session_state.grid and to_tag in st.session_state.grid:
            x1, y1 = component_grid_xy(*st.session_state.grid[from_tag])
            x2, y2 = component_grid_xy(*st.session_state.grid[to_tag])
            mx = x1
            my = y2
            msp.add_lwpolyline([ (x1, y1), (mx, my), (x2, y2)])
    # Add title block
    msp.add_text("EPS Interactive P&ID", dxfattribs={"height": 30}).set_pos((tb_x+10, tb_y+10))
    msp.add_text(f"Date: {today_str()}", dxfattribs={"height": 20}).set_pos((tb_x+10, tb_y+40))
    msp.add_text("Page: 1 of 1", dxfattribs={"height": 20}).set_pos((tb_x+10, tb_y+70))
    msp.add_text(f"CLIENT: {TITLE_BLOCK_CLIENT}", dxfattribs={"height": 20}).set_pos((tb_x+250, tb_y+10))
    buf = io.BytesIO()
    doc.saveas(buf)
    return buf.getvalue()

if st.button("Download DXF"):
    dxf_bytes = export_dxf()
    st.download_button("Save DXF", data=dxf_bytes, file_name="pid.dxf", mime="application/dxf")

# --- ERRORS & WARNINGS ---
missing_syms = [eq["symbol"] for eq in st.session_state.equipment+st.session_state.inline if not load_symbol(eq["symbol"])]
if missing_syms:
    st.warning(f"Missing symbols: {', '.join(set(missing_syms))} (shown as gray box). Please add PNGs in /symbols.")
