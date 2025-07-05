import streamlit as st
import pandas as pd
from PIL import Image
import os
import io
import openai
import ezdxf

st.set_page_config(page_title="EPS Interactive P&ID Generator", layout="wide")

# Load component data
equipment_df = pd.read_csv("equipment_list.csv")
pipeline_df = pd.read_csv("pipeline_list.csv")
inline_df = pd.read_csv("inline_component_list.csv")

# Session state init
for key in ["equipment", "pipelines", "inline"]:
    if key not in st.session_state:
        st.session_state[key] = []

# Utilities
def auto_generate_tag(prefix, existing_tags):
    count = sum(1 for tag in existing_tags if tag.startswith(prefix))
    return f"{prefix}-{count + 1:03}"

def get_image(component_type, symbol_col="Symbol_Image", source_df=None):
    if source_df is not None and symbol_col in source_df.columns:
        match = source_df[source_df["type"] == component_type]
        if not match.empty:
            filename = match[symbol_col].values[0]
            path = os.path.join("symbols", filename)
            if os.path.exists(path):
                return Image.open(path)
    return None

# Sidebar
st.sidebar.title("➕ Add Components")

# Equipment
with st.sidebar.expander("Add Equipment", expanded=True):
    eq_type = st.selectbox("Equipment Type", equipment_df["type"])
    eq_prefix = equipment_df[equipment_df["type"] == eq_type]["Tag Prefix"].values[0]
    eq_tag = auto_generate_tag(eq_prefix, [e["tag"] for e in st.session_state.equipment])
    if st.button("Add Equipment"):
        st.session_state.equipment.append({"type": eq_type, "tag": eq_tag})

# Pipelines
with st.sidebar.expander("Add Pipeline"):
    if len(st.session_state.equipment) >= 2:
        from_eq = st.selectbox("From", [e["tag"] for e in st.session_state.equipment], key="from_pipe")
        to_eq = st.selectbox("To", [e["tag"] for e in st.session_state.equipment], key="to_pipe")
        pipe_prefix = pipeline_df["Tag Prefix"].iloc[0]  # e.g., "P"
        pipe_tag = auto_generate_tag(pipe_prefix, [p["tag"] for p in st.session_state.pipelines])
        if st.button("Add Pipeline"):
            st.session_state.pipelines.append({"tag": pipe_tag, "from": from_eq, "to": to_eq})
    else:
        st.info("Add at least 2 equipment to create a pipeline.")

# In-line components
with st.sidebar.expander("Add In-Line Component"):
    if len(st.session_state.pipelines) > 0:
        inline_type = st.selectbox("In-line Type", inline_df["type"])
        pipe_tag = st.selectbox("On Pipeline", [p["tag"] for p in st.session_state.pipelines])
        inline_prefix = inline_df[inline_df["type"] == inline_type]["Tag Prefix"].values[0]
        inline_tag = auto_generate_tag(inline_prefix, [c["tag"] for c in st.session_state.inline])
        if st.button("Add In-Line Component"):
            st.session_state.inline.append({"tag": inline_tag, "type": inline_type, "pipe_tag": pipe_tag})
    else:
        st.info("Add a pipeline first.")

# Reset
if st.sidebar.button("Reset All"):
    st.session_state.equipment.clear()
    st.session_state.pipelines.clear()
    st.session_state.inline.clear()
    st.rerun()

# MAIN UI
st.title("🧠 EPS Interactive P&ID Generator")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Equipment")
    st.dataframe(pd.DataFrame(st.session_state.equipment))

with col2:
    st.subheader("Pipelines")
    st.dataframe(pd.DataFrame(st.session_state.pipelines))

with col3:
    st.subheader("In-Line Components")
    st.dataframe(pd.DataFrame(st.session_state.inline))

# Image mockup
st.markdown("### 🖼️ P&ID Diagram Preview (Mockup Layout)")
preview_cols = st.columns(len(st.session_state.equipment) or 1)

for idx, eq in enumerate(st.session_state.equipment):
    image = get_image(eq["type"], source_df=equipment_df)
    if image:
        preview_cols[idx].image(image, caption=eq["tag"], width=150)
    else:
        preview_cols[idx].markdown(f"❌ Missing: `{eq['type']}`")

# AI Suggestions
st.markdown("### 🤖 AI Engineer Suggestions")

def get_ai_suggestions():
    try:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            return "**Missing OpenAI API key**"
        openai.api_key = key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Suggest P&ID design improvements."}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI failed: {e}"

if st.button("Get Suggestions"):
    st.markdown(get_ai_suggestions())

# Export Functions
def generate_dxf():
    try:
        doc = ezdxf.new()
        msp = doc.modelspace()
        x = 0
        for eq in st.session_state.equipment:
            msp.add_circle(center=(x, 0), radius=1)
            msp.add_text(eq["tag"], dxfattribs={"height": 0.2}).set_placement((x, -1))
            x += 3
        buffer = io.StringIO()
        doc.write(buffer)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"DXF Export failed: {e}")
        return None

def generate_png_mockup():
    width = max(400, 180 * len(st.session_state.equipment))
    height = 200
    image = Image.new("RGB", (width, height), color="white")
    return image

st.markdown("### 📤 Export P&ID")

png_image = generate_png_mockup()
st.image(png_image, caption="Preview", use_column_width=True)

col_download1, col_download2 = st.columns(2)
with col_download1:
    buf = io.BytesIO()
    png_image.save(buf, format="PNG")
    st.download_button("Download PNG", data=buf.getvalue(), file_name="pid_mockup.png")

with col_download2:
    dxf_data = generate_dxf()
    if dxf_data:
        st.download_button("Download DXF", data=dxf_data, file_name="pid.dxf")
