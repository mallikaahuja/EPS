# app.py - Updated to handle 3 sheets

import streamlit as st
import pandas as pd
from pid_drawer import generate_pid

st.title("EPS Detailed P&ID Generator")
st.write("Upload an Excel file with 'Equipment', 'Piping', and 'In-Line_Components' sheets.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read all THREE sheets
        df_equipment = pd.read_excel(uploaded_file, sheet_name='Equipment')
        df_piping = pd.read_excel(uploaded_file, sheet_name='Piping')
        df_inline = pd.read_excel(uploaded_file, sheet_name='In-Line_Components')

        st.success("File loaded!")
        
        # Display data (optional, but good for debugging)
        st.subheader("Equipment")
        st.dataframe(df_equipment)
        st.subheader("Piping")
        st.dataframe(df_piping)
        st.subheader("In-Line Components")
        st.dataframe(df_inline)

        if st.button("Generate Detailed P&ID"):
            with st.spinner("Drawing detailed P&ID... This may take a moment."):
                
                # Pass all three DataFrames to the drawing function
                pid_diagram = generate_pid(df_equipment, df_piping, df_inline)
                
                st.subheader("Generated P&ID")
                st.graphviz_chart(pid_diagram)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.warning("Please ensure your Excel file has the required three sheets and columns.")
