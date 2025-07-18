import streamlit as st
import pandas as pd
from layout_engine import compute_positions_and_routing
from drawing_engine import render_svg, svg_to_png, export_dxf
from validation import validate_pid
from control_systems import ControlSystemAnalyzer, PnIDValidator
import base64

# Page config
st.set_page_config(
    page_title="EPS P&ID Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    .main > div {
        padding-top: 0rem;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .svg-container {
        border: 2px solid #ccc;
        border-radius: 8px;
        background: white;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .equipment-card {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #0066cc;
    }
    .validation-success {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .validation-warning {
        background-color: #fff3cd;
        border-color: #ffeeba;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .validation-error {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏭 EPS Interactive P&ID Generator")
st.markdown("**Professional Process & Instrumentation Diagram Tool**")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Configuration")

    # Display options
    st.subheader("Display Options")
    show_grid = st.checkbox("Show Grid", value=True)
    show_legend = st.checkbox("Show Legend", value=True)
    show_title = st.checkbox("Show Title Block", value=True)
    show_control_loops = st.checkbox("Show Control Loops", value=False)
    show_validation = st.checkbox("Show Validation Overlay", value=False)

    # Zoom control
    st.subheader("View Controls")
    zoom_level = st.slider("Zoom Level", 50, 200, 100, 5)

    # Export format
    st.subheader("Export Options")
    export_format = st.selectbox(
        "Export Format",
        ["PNG (High Resolution)", "DXF (AutoCAD)", "SVG (Vector)"]
    )

    # Diagram settings
    st.subheader("Diagram Settings")
    diagram_width = st.number_input("Width (px)", 1500, 3000, 2000, 100)
    diagram_height = st.number_input("Height (px)", 800, 2000, 1100, 100)

# Load data with error handling
try:
    equipment_df = pd.read_csv("equipment_list.csv")
    pipeline_df = pd.read_csv("pipeline_list.csv")
    inline_df = pd.read_csv("inline_component_list.csv")

    # Add status indicator
    st.success(f"✅ Loaded {len(equipment_df)} equipment items, {len(pipeline_df)} pipelines, {len(inline_df)} inline components")

except Exception as e:
    st.error(f"❌ Error loading data files: {str(e)}")
    st.stop()

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 P&ID Diagram", "🔧 Equipment List", "📋 Validation Report", "🔄 Control Systems", "📖 Documentation"])

with tab1:
    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        try:
            # Compute layout
            with st.spinner("🔄 Computing optimal layout..."):
                positions, pipelines, inlines = compute_positions_and_routing(
                    equipment_df, pipeline_df, inline_df
                )

            # Render SVG
            with st.spinner("🎨 Rendering P&ID..."):
                pid_svg = render_svg(
                    equipment_df, pipeline_df, inline_df,
                    positions, pipelines, inlines,
                    width=diagram_width,
                    height=diagram_height,
                    show_grid=show_grid,
                    show_legend=show_legend,
                    show_title=show_title
                )

            # Display with zoom
            zoom_scale = zoom_level / 100
            display_width = int(diagram_width * zoom_scale)
            display_height = int(diagram_height * zoom_scale)

            # Create interactive SVG display
            st.markdown(
                f"""
                <div class="svg-container" style="overflow: auto; width: 100%; height: {display_height}px;">
                    <div style="transform: scale({zoom_scale}); transform-origin: top left; width: {diagram_width}px; height: {diagram_height}px;">
                        {pid_svg}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Export buttons
            st.markdown("---")
            col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

            with col_exp1:
                if st.button("📥 Download PNG", type="primary"):
                    with st.spinner("Generating PNG..."):
                        pid_png = svg_to_png(pid_svg)
                        st.download_button(
                            "💾 Save PNG",
                            pid_png,
                            file_name="pid_diagram.png",
                            mime="image/png"
                        )

            with col_exp2:
                if st.button("📥 Download DXF"):
                    with st.spinner("Generating DXF..."):
                        dxf_data = export_dxf(positions, pipelines)
                        st.download_button(
                            "💾 Save DXF",
                            dxf_data,
                            file_name="pid_diagram.dxf",
                            mime="application/dxf"
                        )

            with col_exp3:
                if st.button("📥 Download SVG"):
                    svg_bytes = pid_svg.encode('utf-8')
                    st.download_button(
                        "💾 Save SVG",
                        svg_bytes,
                        file_name="pid_diagram.svg",
                        mime="image/svg+xml"
                    )

        except Exception as e:
            st.error(f"❌ Error generating diagram: {str(e)}")
            st.exception(e)

with tab2:
    st.header("🔧 Equipment List")

    # Equipment summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Equipment", len(equipment_df))
    with col2:
        st.metric("Total Pipelines", len(pipeline_df))
    with col3:
        st.metric("Inline Components", len(inline_df))
    with col4:
        total_cost = equipment_df['cost_usd'].sum() + inline_df['cost_usd'].sum()
        st.metric("Total Cost", f"${total_cost:,.0f}")

    # Equipment details
    st.subheader("Equipment Details")

    # Add search functionality
    search_term = st.text_input("🔍 Search equipment by ID or description")
    if search_term:
        filtered_df = equipment_df[
            equipment_df['ID'].str.contains(search_term, case=False) |
            equipment_df['Description'].str.contains(search_term, case=False)
        ]
    else:
        filtered_df = equipment_df

    # Display as cards
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['ID']} - {row['Description']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Type:** {row['type']}")
                st.write(f"**Manufacturer:** {row['manufacturer']}")
            with col2:
                st.write(f"**Cost:** ${row['cost_usd']:,.0f}")
                st.write(f"**Efficiency:** {row['efficiency_pct']}%")
            with col3:
                # Handle potential non-string values gracefully for JSON conversion
                if pd.notna(row.get('default_properties')):
                    try:
                        # Ensure the string is clean before attempting JSON load
                        prop_str = row['default_properties'].replace('""', '"') # Fix initial common error
                        st.write("**Properties:**")
                        st.json(prop_str)
                    except Exception as json_err:
                        st.warning(f"Could not display properties as JSON: {json_err}. Raw data: {row['default_properties']}")
                        st.write(f"**Properties (raw):** {row['default_properties']}")


    # Inline components
    st.subheader("Inline Components")
    st.dataframe(
        inline_df[['ID', 'Description', 'type', 'Pipeline', 'cost_usd']],
        use_container_width=True
    )

with tab3:
    st.header("📋 Validation Report")

    # Run validation
    with st.spinner("Running validation checks..."):
        # Make sure positions and pipelines are available (from tab1 computation)
        if 'positions' not in locals() or 'pipelines' not in locals():
            st.warning("Diagram not yet rendered. Please go to 'P&ID Diagram' tab first to generate layout for validation.")
            errors = ["Layout not generated."]
            validation_results = {'errors': [], 'warnings': []}
        else:
            errors = validate_pid(equipment_df, pipeline_df, positions, pipelines)

            # Create components dict for advanced validation
            components_dict = {row['ID']: row for _, row in equipment_df.iterrows()}
            pipes_list = [{'line_type': 'process', 'from_comp': p.get('src'), 'to_comp': p.get('dst')} for p in pipelines]

            validator = PnIDValidator(components_dict, pipes_list)
            validation_results = validator.validate_all()

    # Display results
    if not errors and not validation_results['errors']:
        st.markdown('<div class="validation-success">✅ All validation checks passed! P&ID is compliant.</div>', unsafe_allow_html=True)
    else:
        if errors:
            st.markdown('<div class="validation-error"><strong>Basic Validation Errors:</strong></div>', unsafe_allow_html=True)
            for error in errors:
                st.error(f"❌ {error}")

        if validation_results['errors']:
            st.markdown('<div class="validation-error"><strong>Advanced Validation Errors:</strong></div>', unsafe_allow_html=True)
            for error in validation_results['errors']:
                st.error(f"❌ {error}")

    if validation_results['warnings']:
        st.markdown('<div class="validation-warning"><strong>Warnings:</strong></div>', unsafe_allow_html=True)
        for warning in validation_results['warnings']:
            st.warning(f"⚠️ {warning}")

    # Validation statistics
    st.subheader("Validation Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Errors", len(errors) + len(validation_results['errors']))
    with col2:
        st.metric("Total Warnings", len(validation_results['warnings']))
    with col3:
        st.metric("Validation Status", "PASS" if not errors and not validation_results['errors'] else "FAIL")

with tab4:
    st.header("🔄 Control Systems Analysis")

    # Analyze control systems
    if 'components_dict' not in locals() or 'pipes_list' not in locals():
        st.warning("Control system analysis requires the layout and validation to be run first. Please visit 'P&ID Diagram' and 'Validation Report' tabs.")
    else:
        with st.spinner("Analyzing control systems..."):
            analyzer = ControlSystemAnalyzer(components_dict, pipes_list)

        st.subheader(f"Detected Control Loops: {len(analyzer.control_loops)}")

        for loop in analyzer.control_loops:
            with st.expander(f"{loop.loop_type.value} - {loop.loop_id}"):
                st.write(f"**Primary Element:** {loop.primary_element}")
                st.write(f"**Controller:** {loop.controller}")
                st.write(f"**Final Element:** {loop.final_element}")
                st.write(f"**Components:** {', '.join(loop.components)}")

        st.subheader(f"Detected Interlocks: {len(analyzer.interlocks)}")

        for interlock in analyzer.interlocks:
            st.write(f"- **{interlock['type']}:** {interlock['alarm']} → {interlock['action']}")

with tab5:
    st.header("📖 Documentation")

    st.markdown("""
### P&ID Standards Compliance

This diagram follows:
- **ISA-5.1** - Instrumentation Symbols and Identification
- **ISO 14617** - Graphical symbols for diagrams
- **ANSI/ISA-S5.1** - Standard instrument symbols

### Symbol Legend

| Symbol | Description |
|--------|-------------|
| Circle | Instrument (field mounted) |
| Circle with line | Instrument (panel mounted) |
| Rectangle | Equipment/Vessel |
| Diamond | Control valve |
| Triangle | Safety device |

### Line Types

- **Solid thick line**: Process piping
- **Dashed line**: Instrument signal
- **Dotted line**: Electrical signal
- **Double line**: Insulated piping

### Tag Format

- **XX-YYY**: XX = Function code, YYY = Loop number
- Example: PT-001 = Pressure Transmitter, Loop 001
""")

# Footer
st.markdown("---")
st.markdown("**EPS P&ID Generator v2.0** | © 2025 Economy Process Solutions Pvt. Ltd.")
