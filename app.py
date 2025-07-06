import streamlit as st
import pandas as pd
import os
import io
from PIL import Image, ImageDraw, ImageFont
import ezdxf
import requests
import base64
from io import BytesIO
from requests_toolbelt.multipart.encoder import MultipartEncoder

# --- CONFIG ---
st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")
SYMBOLS_DIR = "symbols"
SYMBOLS_CACHE_DIR = "symbols_cache"
os.makedirs(SYMBOLS_CACHE_DIR, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

# Font fallback logic
try:
    FONT = ImageFont.truetype("arial.ttf", 14)
    FONT_LARGE = ImageFont.truetype("arial.ttf", 20)
except Exception:
    FONT = ImageFont.load_default()
    FONT_LARGE = ImageFont.load_default()

# --- DATA LOADERS ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

equipment_df = load_csv("equipment_list.csv")
inline_df = load_csv("inline_component_list.csv")
pipeline_df = load_csv("pipeline_list.csv")

# --- STATE INIT ---
if "components" not in st.session_state:
    st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}

# --- TAGGING ---
def auto_tag(prefix, existing):
    count = 1
    while f"{prefix}-{count:03}" in existing:
        count += 1
    return f"{prefix}-{count:03}"

# --- AI SYMBOL GENERATION (Stability AI) ---
def generate_symbol_stability(type_name, image_name):
    prompt = f"A clean ISA 5.1 standard black-and-white engineering symbol for a {type_name}, transparent background, schematic style."
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    m = MultipartEncoder(
        fields={
            "prompt": prompt,
            "mode": "text-to-image",
            "output_format": "png",
            "model": "stable-diffusion-xl-1024-v1-0",
            "aspect_ratio": "1:1"
        }
    )
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*",
        "Content-Type": m.content_type
    }
    response = requests.post(url, headers=headers, data=m)

    if response.status_code == 200:
        image_data = response.content
        path = os.path.join(SYMBOLS_DIR, image_name)
        with open(path, "wb") as f:
            f.write(image_data)
        # Also save to cache for immediate use
        cache_path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
        with open(cache_path, "wb") as f:
            f.write(image_data)
        st.info(f"AI symbol generated and saved as {image_name}")
    else:
        st.warning(f"⚠️ Stability API Error {response.status_code}: {response.text}")

# --- AI PREDICTIVE SUGGESTIONS (OpenAI) ---
def ai_predictive_suggestions(prompt, model="gpt-4o"):
    if not OPENAI_API_KEY:
        return "OpenAI API key not set."
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "system", "content": "You are a P&ID expert. Suggest errors, typical improvements, or missing components for the given P&ID list."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 256,
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"OpenAI error: {r.status_code} {r.text}"
    except Exception as e:
        return str(e)

# --- SYMBOLS ---
def get_symbol_path(image_name):
    # Priority: cache, then symbols
    cache_path = os.path.join(SYMBOLS_CACHE_DIR, image_name)
    symbols_path = os.path.join(SYMBOLS_DIR, image_name)
    if os.path.exists(cache_path):
        return cache_path
    elif os.path.exists(symbols_path):
        return symbols_path
    else:
        return None

def get_image(image_name, type_name=None, allow_ai=True):
    path = get_symbol_path(image_name)
    if path and os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA").resize((100, 100))
        except Exception:
            return None
    # If requested and missing, AI-generate on demand
    if allow_ai and type_name and STABILITY_API_KEY:
        generate_symbol_stability(type_name, image_name)
        path = get_symbol_path(image_name)
        if path and os.path.exists(path):
            return Image.open(path).convert("RGBA").resize((100, 100))
    return None

def missing_symbol_image():
    # Red cross placeholder
    img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.line((10, 10, 90, 90), fill="red", width=8)
    d.line((10, 90, 90, 10), fill="red", width=8)
    d.rectangle((5, 5, 95, 95), outline="gray", width=3)
    d.text((50, 50), "?", fill="red", font=FONT_LARGE, anchor="mm")
    return img

# --- PNG/DXF EXPORT ---
def generate_png(diagram_img):
    buf = BytesIO()
    diagram_img.save(buf, format="PNG")
    return buf.getvalue()

def generate_dxf_file():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = i * 150
        msp.add_lwpolyline([(x, 0), (x+30, 0), (x+30, 30), (x, 30), (x, 0)])
        msp.add_text(eq["tag"], dxfattribs={"height": 2.5, "insert": (x, 35)})
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")

# --- P&ID DRAWING LOGIC ---
def render_pid_diagram():
    # A3: 3508x2480 px at 300dpi, but reserve margin for legend/title
    width, height = 3508, 2480
    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    grid_spacing = 250
    x0, y0 = 150, 250  # left margin, top margin

    tag_positions = {}
    # Draw grid
    for gx in range(0, width, grid_spacing):
        draw.line([(gx, 0), (gx, height)], fill=(220, 220, 220, 100), width=1)
    for gy in range(0, height, grid_spacing):
        draw.line([(0, gy), (width, gy)], fill=(220, 220, 220, 100), width=1)

    # Draw scope boxes (dashed)
    eq_count = len(st.session_state.components["equipment"])
    if eq_count > 0:
        left = x0 - 80
        top = y0 - 60
        right = x0 + min(4, eq_count-1)*grid_spacing + 180
        bottom = y0 + 180
        # EPSPL SCOPE
        for i in range(left, right, 15):
            draw.line([(i, top), (i+7, top)], fill="black", width=3)
            draw.line([(i, bottom), (i+7, bottom)], fill="black", width=3)
        for i in range(top, bottom, 15):
            draw.line([(left, i), (left, i+7)], fill="black", width=3)
            draw.line([(right, i), (right, i+7)], fill="black", width=3)
        draw.text((left+10, top-30), "EPSPL SCOPE", font=FONT, fill="black")
        # CUSTOMER SCOPE
        if eq_count > 4:
            left2 = right + 40
            right2 = left2 + (eq_count-4)*grid_spacing + 100
            for i in range(left2, right2, 15):
                draw.line([(i, top), (i+7, top)], fill="black", width=3)
                draw.line([(i, bottom), (i+7, bottom)], fill="black", width=3)
            for i in range(top, bottom, 15):
                draw.line([(left2, i), (left2, i+7)], fill="black", width=3)
                draw.line([(right2, i), (right2, i+7)], fill="black", width=3)
            draw.text((left2+10, top-30), "CUSTOMER SCOPE", font=FONT, fill="black")

    # Draw equipment (row)
    for i, eq in enumerate(st.session_state.components["equipment"]):
        x = x0 + (i % 8) * grid_spacing
        y = y0
        tag_positions[eq["tag"]] = (x, y)
        img = get_image(eq["symbol"], eq["type"])
        if img:
            canvas.paste(img, (x, y), img)
        else:
            # Draw missing symbol
            canvas.paste(missing_symbol_image(), (x, y), missing_symbol_image())
        # Tag in circle below
        draw.ellipse([(x+35, y+110), (x+65, y+140)], fill="white", outline="black", width=2)
        draw.text((x+50, y+125), eq["tag"], fill="black", font=FONT, anchor="mm")
        # Equipment name below tag (optional)
        draw.text((x+50, y+150), eq["type"], fill="gray", font=FONT, anchor="mm")

    # Draw pipelines (orthogonal, arrows)
    for pipe in st.session_state.components["pipelines"]:
        start = tag_positions.get(pipe["from"])
        end = tag_positions.get(pipe["to"])
        if start and end:
            x1, y1 = start[0]+50, start[1]+100
            x2, y2 = end[0]+50, end[1]+100
            path = [(x1, y1), (x1, y1+40), (x2, y1+40), (x2, y2)]
            draw.line(path, fill="black", width=4)
            # Arrowhead at end
            dx, dy = 0, 20
            draw.polygon([(x2, y2+dy), (x2-10, y2+dy-6), (x2+10, y2+dy-6)], fill="black")
            # Arrowhead at start
            draw.polygon([(x1, y1-dy), (x1-10, y1-dy+6), (x1+10, y1-dy+6)], fill="black")
            # Pipe tag
            draw.text(((x1+x2)//2, y1+25), pipe["tag"], fill="blue", font=FONT, anchor="mm")

    # Draw inline components (mid-pipe)
    for comp in st.session_state.components["inline"]:
        pipe = next((p for p in st.session_state.components["pipelines"] if p["tag"] == comp["pipe_tag"]), None)
        if pipe and pipe["from"] in tag_positions and pipe["to"] in tag_positions:
            start = tag_positions[pipe["from"]]
            end = tag_positions[pipe["to"]]
            mx = (start[0]+end[0])//2 + 50
            my = start[1]+120
            img = get_image(comp["symbol"], comp["type"])
            if img:
                canvas.paste(img, (mx-50, my), img)
            else:
                canvas.paste(missing_symbol_image(), (mx-50, my), missing_symbol_image())
            draw.ellipse([(mx-15, my+110), (mx+15, my+140)], fill="white", outline="black", width=2)
            draw.text((mx, my+125), comp["tag"], fill="black", font=FONT, anchor="mm")
            draw.text((mx, my+150), comp["type"], fill="gray", font=FONT, anchor="mm")

    # LEGEND/BOM (Right Sidebar)
    legend_x, legend_y = width-650, 100
    draw.rectangle([(legend_x, legend_y), (width-50, legend_y+420)], outline="black", width=2)
    draw.text((legend_x+15, legend_y+10), "LEGEND / BILL OF MATERIAL", font=FONT_LARGE, fill="black")
    # Table headers
    headers = ["No", "Symbol", "Type", "Tag", "Qty", "Note"]
    for j, h in enumerate(headers):
        draw.text((legend_x+15+j*90, legend_y+50), h, font=FONT, fill="black")
    # List all used component types
    bom_rows = []
    for eq in st.session_state.components["equipment"]:
        bom_rows.append({
            "type": eq["type"], "tag": eq["tag"], "symbol": eq["symbol"], "note": ""
        })
    for comp in st.session_state.components["inline"]:
        bom_rows.append({
            "type": comp["type"], "tag": comp["tag"], "symbol": comp["symbol"], "note": "[AI-generated]" if "ai" in comp.get("symbol","").lower() else ""
        })
    # Count quantities by (type, symbol)
    from collections import Counter
    counts = Counter((r["type"], r["symbol"]) for r in bom_rows)
    used = []
    for idx, ((typ, sym), qty) in enumerate(counts.items(), 1):
        row = next(r for r in bom_rows if r["type"]==typ and r["symbol"]==sym)
        y = legend_y+80+idx*32
        draw.text((legend_x+15, y), str(idx), font=FONT, fill="black")
        # Symbol preview
        img = get_image(sym, typ, allow_ai=False)
        if img:
            thumb = img.resize((28,28))
        else:
            thumb = missing_symbol_image().resize((28,28))
        canvas.paste(thumb, (legend_x+55, y-7), thumb)
        draw.text((legend_x+95, y), typ, font=FONT, fill="black")
        draw.text((legend_x+185, y), row["tag"], font=FONT, fill="black")
        draw.text((legend_x+275, y), str(qty), font=FONT, fill="black")
        draw.text((legend_x+335, y), row["note"], font=FONT, fill="red" if row["note"] else "gray")

    # TITLE BLOCK (Bottom-Right)
    tb_x, tb_y = width-700, height-180
    draw.rectangle([(tb_x, tb_y), (width-50, tb_y+120)], outline="black", width=2)
    tb_lines = [
        f"Project: EPS P&ID Generator",
        f"Drawing No.: EPSPL-XXXX-YY",
        f"Sheet: 1 of 1   Date: {pd.Timestamp.today().strftime('%Y-%m-%d')}",
        f"Drawn/Checked: [Name]",
        f"Scale: 1:1 (A3 300 DPI)",
    ]
    for i, line in enumerate(tb_lines):
        draw.text((tb_x+20, tb_y+15+i*22), line, font=FONT, fill="black")

    return canvas

# --- PNG CHECKER & VALIDATOR ---
def validate_symbols():
    used_symbols = set()
    for eq in st.session_state.components["equipment"]:
        used_symbols.add(eq["symbol"])
    for comp in st.session_state.components["inline"]:
        used_symbols.add(comp["symbol"])
    for pipe in st.session_state.components.get("pipelines", []):
        if "symbol" in pipe: used_symbols.add(pipe["symbol"])
    # List all PNG filenames in symbols/
    all_pngs = {f for f in os.listdir(SYMBOLS_DIR) if f.lower().endswith(".png")}
    missing = sorted([s for s in used_symbols if s not in all_pngs])
    extra = sorted([p for p in all_pngs if p not in used_symbols])
    return missing, extra

# --- MAIN UI ---
st.markdown("# 🧠 EPS Interactive P&ID Generator")
st.caption("ISA/ISO-compliant, AI-assisted, PNG/DXF export, error-proof P&ID schematic builder")

# --- Toolbar ---
toolbar1, toolbar2, toolbar3, toolbar4, toolbar5, toolbar6 = st.columns([1,1,1,1,2,2])
with toolbar1:
    if st.button("🆕 New"):
        st.session_state.components = {"equipment": [], "pipelines": [], "inline": []}
        st.experimental_rerun()
with toolbar2:
    if st.button("💾 Save (Download JSON)"):
        st.download_button("Download Project", data=io.StringIO(str(st.session_state.components)).getvalue(), file_name="pid_project.json")
with toolbar3:
    if st.button("🖨 PNG Export"):
        diagram = render_pid_diagram()
        st.download_button("Download PNG", generate_png(diagram), "pid.png", "image/png")
with toolbar4:
    if st.button("📐 DXF Export"):
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf")
with toolbar5:
    if st.button("🧹 Validate Symbols"):
        missing, extra = validate_symbols()
        if not missing and not extra:
            st.success("All required symbols are present! 🎉")
        else:
            if missing:
                st.error(f"Missing PNGs: {', '.join(missing)}")
            if extra:
                st.warning(f"Extra PNGs (not referenced): {', '.join(extra)}")
with toolbar6:
    if st.button("⚙️ Settings"):
        st.info("Settings panel coming soon. For now, edit CSVs or add components below.")

st.markdown("---")

# --- DRAWING CANVAS + LEGEND/BOM ---
col_canvas, col_legend = st.columns([2.3, 1.2])
with col_canvas:
    st.subheader("🖼️ P&ID Drawing (Zoom/Scroll in Output)")
    diagram = render_pid_diagram()
    st.image(diagram, use_column_width=True)
    # Download buttons
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download PNG", generate_png(diagram), "pid.png", "image/png")
    with c2:
        st.download_button("Download DXF", generate_dxf_file(), "pid.dxf", "application/dxf")

with col_legend:
    st.subheader("📑 Legend / BOM")
    # Live BOM table
    bom_data = []
    for eq in st.session_state.components["equipment"]:
        bom_data.append({
            "Type": eq["type"], "Tag": eq["tag"], "Symbol": eq["symbol"], "Note": ""
        })
    for comp in st.session_state.components["inline"]:
        bom_data.append({
            "Type": comp["type"], "Tag": comp["tag"], "Symbol": comp["symbol"], "Note": "AI-generated" if "ai" in comp.get("symbol","").lower() else ""
        })
    if bom_data:
        df_bom = pd.DataFrame(bom_data)
        st.dataframe(df_bom)
    else:
        st.info("No components added yet.")

# --- COMPONENT TABLES, ADD/EDIT ---
st.markdown("---")
st.subheader("📝 Equipment, Pipeline & Inline Component Editor")

editor1, editor2, editor3 = st.columns(3)
with editor1:
    st.markdown("#### Equipment")
    if not equipment_df.empty:
        eq_type = st.selectbox("Type", equipment_df["type"].unique(), key="eq_type")
        row = equipment_df[equipment_df["type"] == eq_type].iloc[0]
        tag = auto_tag(row["Tag Prefix"], [e["tag"] for e in st.session_state.components["equipment"]])
        symbol = row["Symbol_Image"]
        if st.button(f"➕ Add {eq_type}"):
            st.session_state.components["equipment"].append({"type": eq_type, "tag": tag, "symbol": symbol})
            st.experimental_rerun()
        if st.button("🖼️ Generate Symbol with AI", key="ai_eq"):
            generate_symbol_stability(eq_type, symbol)
    if st.session_state.components["equipment"]:
        st.dataframe(pd.DataFrame(st.session_state.components["equipment"]))
with editor2:
    st.markdown("#### Pipelines")
    if len(st.session_state.components["equipment"]) >= 2:
        from_tag = st.selectbox("From", [e["tag"] for e in st.session_state.components["equipment"]], key="from_tag")
        to_opts = [e["tag"] for e in st.session_state.components["equipment"] if e["tag"] != from_tag]
        to_tag = st.selectbox("To", to_opts, key="to_tag")
        tag = auto_tag("P", [p["tag"] for p in st.session_state.components["pipelines"]])
        if st.button("➕ Add Pipeline"):
            st.session_state.components["pipelines"].append({"tag": tag, "from": from_tag, "to": to_tag})
            st.experimental_rerun()
    if st.session_state.components["pipelines"]:
        st.dataframe(pd.DataFrame(st.session_state.components["pipelines"]))
with editor3:
    st.markdown("#### Inline Components")
    if st.session_state.components["pipelines"] and not inline_df.empty:
        inline_type = st.selectbox("Type", inline_df["type"].unique(), key="inline_type")
        row = inline_df[inline_df["type"] == inline_type].iloc[0]
        pipe_tag = st.selectbox("Pipeline", [p["tag"] for p in st.session_state.components["pipelines"]], key="inline_pipe")
        tag = auto_tag(row["Tag Prefix"], [i["tag"] for i in st.session_state.components["inline"]])
        symbol = row["Symbol_Image"]
        if st.button(f"➕ Add {inline_type}"):
            st.session_state.components["inline"].append({"type": inline_type, "tag": tag, "pipe_tag": pipe_tag, "symbol": symbol})
            st.experimental_rerun()
        if st.button("🖼️ Generate Symbol with AI", key="ai_inline"):
            generate_symbol_stability(inline_type, symbol)
    if st.session_state.components["inline"]:
        st.dataframe(pd.DataFrame(st.session_state.components["inline"]))

# --- AI SUGGESTIONS PANEL ---
st.markdown("---")
with st.expander("🤖 Predictive Checks & Suggestions (AI)", expanded=True):
    # Compose prompt from current design
    prompt = "Equipment:\n"
    for eq in st.session_state.components["equipment"]:
        prompt += f"- {eq['type']} ({eq['tag']})\n"
    prompt += "\nPipelines:\n"
    for p in st.session_state.components["pipelines"]:
        prompt += f"- {p['tag']} from {p['from']} to {p['to']}\n"
    prompt += "\nIn-line Components:\n"
    for i in st.session_state.components["inline"]:
        prompt += f"- {i['type']} ({i['tag']}) on {i['pipe_tag']}\n"
    st.write("AI will suggest typical P&ID checks, missing features, or design errors.")
    if st.button("🧠 Get AI Suggestions"):
        suggestion = ai_predictive_suggestions(prompt)
        st.success(suggestion)
    else:
        st.info("Click to get expert P&ID checks and suggestions.")

st.markdown("---")
st.caption("EPS P&ID Generator — AI/PNG/DXF. All logic in this single app.py. For feedback or advanced features, contact EPS team.")
