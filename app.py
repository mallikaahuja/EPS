# app.py - The FINAL Correct Version

import streamlit as st
import pandas as pd

# Import our new drawing function from the other file
from pid_drawer import generate_pid

st.title("EPS Auto P&ID Generator")
st.write("Upload an Excel file with 'Equipment' and 'Piping' sheets to generate a P&ID.")

# File uploader widget
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # We read the TWO required sheets from the one Excel file.
        df_equipment = pd.read_excel(uploaded_file, sheet_name='Equipment')
        df_piping = pd.read_excel(uploaded_file, sheet_name='Piping')

        # Clean up any extra whitespace from column names, just in case
        df_equipment.columns = df_equipment.columns.str.strip()
        df_piping.columns = df_piping.columns.str.strip()

        st.success("Excel file loaded successfully! Here's the data:")

        # Show the dataframes in two columns for a nice layout
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Equipment Data")
            st.dataframe(df_equipment)
        with col2:
            st.subheader("Piping Data")
            st.dataframe(df_piping)

        # Add a button to trigger the P&ID generation
        if st.button("Generate P&ID"):
            with st.spinner("Drawing P&ID..."):
                
                # Call the drawing function from pid_drawer.py
                pid_diagram = generate_pid(df_equipment, df_piping)
                
                st.subheader("Generated P&ID")
                
                # Display the finished diagram in Streamlit!
                st.graphviz_chart(pid_diagram)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.warning("Please check your Excel file. It must contain two sheets named 'Equipment' and 'Piping'.")
        st.warning("Required columns for 'Equipment': Tag, Type. For 'Piping': From, To, PipeTag.")
