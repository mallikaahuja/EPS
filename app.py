import streamlit as st
import pandas as pd
from layout_engine import compute_positions_and_routing
from drawing_engine import render_svg, svg_to_png, export_dxf
from validation import validate_pid
from control_systems import ControlSystemAnalyzer, PnIDValidator
from ai_integration import PnIDAIAssistant, SmartPnIDSuggestions
import base64
import os

# Page config
st.set_page_config(
    page_title="EPS P&ID Generator with AI",
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
    .ai-suggestion {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize AI Assistant
@st.cache_resource
def init_ai_assistant():
    # Directly retrieve keys from environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    stability_key = os.getenv("STABILITY_API_KEY")

    # Add a check to ensure keys are actually present
    if not openai_key:
        st.error("Error: OPENAI_API_KEY environment variable not found. "
                 "Please set it in your Railway project's variables.")
        st.stop() # Stop the app if a critical secret is missing
    if not stability_key:
        st.error("Error: STABILITY_API_KEY environment variable not found. "
                 "Please set it in your Railway project's variables.")
        st.stop() # Stop the app if a critical secret is missing

    return PnIDAIAssistant(
        openai_key=openai_key,
        stability_key=stability_key
    )

ai_assistant = init_ai_assistant()
smart_suggestions = SmartPnIDSuggestions(ai_assistant)

# Header
st.title("🏭 EPS Interactive P&ID Generator")
st.markdown("**Professional Process & Instrumentation Diagram Tool with AI Assistance**")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Configuration")

    # AI Features
    st.subheader("🤖 AI Features")
    enable_ai_suggestions = st.checkbox("Enable AI Suggestions", value=True)
    enable_symbol_generation = st.checkbox("Auto-generate Missing Symbols", value=True)

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
    st.subheader("Export Format", help="Choose the format for diagram export.")
    export_format = st.selectbox(
        "Export Format",
        ["PNG (High Resolution)", "DXF (AutoCAD)", "SVG (Vector)", "PDF (Document)"]
    )

    # Diagram settings
    st.subheader("Diagram Settings")
    diagram_width = st.number_input("Width (px)", 1500, 3000, 2000, 100)
    diagram_height = st.number_input("Height (px)", 800, 2000, 1100, 100)

    # Process Type for AI
    st.subheader("Process Information")
    process_type = st.selectbox(
        "Process Type",
        ["vacuum_system", "distillation", "reaction", "separation", "utilities"]
    )

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 P&ID Diagram",
    "🔧 Equipment List",
    "📋 Validation Report",
    "🔄 Control Systems",
    "🤖 AI Suggestions",
    "📖 Documentation"
])

with tab1:
    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        try:
            # Compute layout
            with st.spinner("🔄 Computing optimal layout..."):
                positions, pipelines, inlines = compute_positions_and_routing(
                    equipment_df, pipeline_df, inline_df
                )
                
                # AI Layout Optimization
                if enable_ai_suggestions:
                    with st.spinner("🤖 Optimizing layout with AI..."):
                        positions = ai_assistant.optimize_layout(positions, pipelines)
            
            # Check for missing symbols and generate if needed
            if enable_symbol_generation:
                missing_symbols = []
                # Placeholder: In a real app, you'd check a database or local asset folder
                # to see if symbols for equipment_df['ID'] already exist.
                # For demonstration, let's assume some are always missing if enabled:
                # if enable_symbol_generation:
                #     for _, row in equipment_df.iterrows():
                #         # Example condition: if symbol file for row['ID'] does not exist
                #         # if not os.path.exists(f"symbols/{row['ID']}.svg"): 
                #         missing_symbols.append({'name': row['ID'], 'type': row['type']})
                
                if missing_symbols: # This block will only execute if missing_symbols has items
                    with st.spinner(f"🎨 Generating {len(missing_symbols)} missing symbols with AI..."):
                        for symbol in missing_symbols:
                            ai_assistant.generate_missing_symbol(
                                symbol['name'], 
                                symbol['type']
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
            col_exp1, col_exp2, col_exp3, col_exp4, col_exp5 = st.columns(5)
            
            with col_exp1:
                if st.button("📥 Download PNG", type="primary"):
                    with st.spinner("Generating PNG..."):
                        pid_png = svg_to_png(pid_svg, scale=2.0)
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
            
            with col_exp4:
                if st.button("📄 Generate Report"):
                    # AI-powered report generation
                    st.info("Generating comprehensive P&ID report...")
                    # Implementation for PDF report
            
            with col_exp5:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
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

    # Equipment details with AI datasheets
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

    # Display as cards with AI datasheet generation
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
                if pd.notna(row.get('default_properties')):
                    st.write("**Properties:**")
                    st.json(row['default_properties'])
            
            # AI Datasheet Generation
            if st.button(f"📄 Generate Datasheet", key=f"datasheet_{row['ID']}"):
                with st.spinner("Generating datasheet..."):
                    datasheet = ai_assistant.generate_equipment_datasheet(
                        row['ID'], 
                        row.to_dict()
                    )
                    st.json(datasheet)

with tab3:
    st.header("📋 Validation Report")

    # Run validation
    with st.spinner("Running validation checks..."):
        errors = validate_pid(equipment_df, pipeline_df, positions, pipelines)
        
        # Create components dict for advanced validation
        components_dict = {row['ID']: row.to_dict() for _, row in equipment_df.iterrows()}
        pipes_list = []
        for p in pipelines:
            pipes_list.append({
                'line_type': p.get('line_type', 'process'),
                'from_comp': p.get('src'),
                'to_comp': p.get('dst')
            })
        
        validator = PnIDValidator(components_dict, pipes_list)
        validation_results = validator.validate_all()
        
        # AI Compliance Check
        if enable_ai_suggestions:
            compliance_check = ai_assistant.check_compliance({
                'equipment': equipment_df['ID'].tolist(),
                'line_sizes': pipeline_df['Min_Diameter_DN'].tolist(),
                'instruments': inline_df[inline_df['type'] == 'instrument']['ID'].tolist()
            })

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

with tab4:
    st.header("🔄 Control Systems Analysis")

    # Analyze control systems
    with st.spinner("Analyzing control systems..."):
        analyzer = ControlSystemAnalyzer(components_dict, pipes_list)

    st.subheader(f"Detected Control Loops: {len(analyzer.control_loops)}")

    for loop in analyzer.control_loops:
        with st.expander(f"{loop.loop_type.value} - {loop.loop_id}"):
            st.write(f"**Primary Element:** {loop.primary_element}")
            st.write(f"**Controller:** {loop.controller}")
            st.write(f"**Final Element:** {loop.final_element}")
            st.write(f"**Components:** {', '.join(loop.components)}")

with tab5:
    st.header("🤖 AI-Powered Suggestions")

    # Process Flow Validation
    st.subheader("Process Flow Analysis")
    if st.button("🔍 Analyze Process Flow"):
        with st.spinner("Analyzing process flow with AI..."):
            sequence = equipment_df.sort_values('sequence')['ID'].tolist()
            connections = [f"{p['src']} → {p['dst']}" for p in pipelines]
            
            flow_validation = ai_assistant.validate_process_flow(sequence, connections)
            
            if flow_validation['valid']:
                st.success("✅ Process flow is logically correct!")
            else:
                st.error("❌ Issues found in process flow:")
                for issue in flow_validation['issues']:
                    st.warning(f"• {issue}")
            
            if 'recommendations' in flow_validation:
                st.info("💡 Recommendations:")
                for rec in flow_validation['recommendations']:
                    st.write(f"• {rec}")

    # Missing Components
    st.subheader("Missing Components Analysis")
    missing = smart_suggestions.suggest_missing_components(
        process_type,
        equipment_df['type'].tolist()
    )

    if missing:
        st.markdown('<div class="ai-suggestion"><strong>🤖 AI suggests adding these components:</strong></div>', unsafe_allow_html=True)
        for item in missing:
            category_emoji = {
                'safety': '🛡️',
                'instrumentation': '📊',
                'utilities': '🔧',
                'environmental': '🌱'
            }
            emoji = category_emoji.get(item['category'], '📌')
            st.write(f"{emoji} **{item['component']}** - {item['reason']} (Priority: {item['priority']})")

    # Energy Efficiency
    st.subheader("Energy Efficiency Analysis")
    efficiency_suggestions = smart_suggestions.analyze_energy_efficiency(equipment_df, pipeline_df)

    if efficiency_suggestions:
        for suggestion in efficiency_suggestions:
            st.markdown(f"""
            <div class="ai-suggestion">
                <strong>💡 {suggestion.get('equipment', suggestion.get('system', 'System'))}</strong><br>
                {suggestion['suggestion']}<br>
                <em>Potential Savings: {suggestion['savings']}</em><br>
                <em>Estimated Cost: {suggestion['cost']}</em>
            </div>
            """, unsafe_allow_html=True)

    # Get General Suggestions
    st.subheader("General Process Improvements")
    if st.button("🧠 Get AI Suggestions"):
        with st.spinner("Consulting AI for process improvements..."):
            suggestions = ai_assistant.get_process_suggestions(
                equipment_df,
                pipeline_df,
                "Vacuum system for solvent recovery with KDP-330 dry screw pump"
            )
            
            if 'error' not in suggestions:
                for category, items in suggestions.items():
                    st.write(f"**{category}:**")
                    if isinstance(items, list):
                        for item in items:
                            st.write(f"• {item}")
                    else:
                        st.write(f"• {items}")
            else:
                st.error(f"Failed to get suggestions: {suggestions['error']}")

with tab6:
    st.header("📖 Documentation")

    st.markdown("""
    ### Process Flow Sequence

    The vacuum system follows this sequence:

    1. **Expansion Bellows** - Thermal expansion compensation
    2. **Electrically Heated Panel Box** - Prevents condensation
    3. **Flame Arrestor** - Safety device
    4. **Vapor Condenser with Catchpot** - Primary condensation
    5. **ACG Filter** - Chemical contaminant removal
    6. **Suction Filter** - Physical filtration
    7. **KDP-330 Dry Screw Vacuum Pump** - Main vacuum generation
    8. **Discharge Silencer** - Noise reduction
    9. **Post-Pump Condenser** - Secondary condensation
    10. **Discharge Scrubber** - Final treatment

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
st.markdown("**EPS P&ID Generator v2.0 with AI** | © 2025 Economy Process Solutions Pvt. Ltd. | Powered by OpenAI & Stability AI")
