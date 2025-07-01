import streamlit as st
import pandas as pd
# REMOVE: matplotlib and unicodedata are no longer needed
# import matplotlib.pyplot as plt
# import unicodedata

# IMPORT our new drawing function from the other file
from pid_drawer import generate_pid

st.title("EPS Auto P&ID Generator")
st.write("Upload an Excel file with 'Equipment' and 'Piping' sheets to generate a P&ID.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # --- THIS IS THE BIG CHANGE ---
        # We now read TWO sheets from the one Excel file.
        # This is much cleaner than dealing with X/Y coordinates.
        df_equipment = pd.read_excel(uploaded_file, sheet_name='Equipment')
        df_piping = pd.read_excel(uploaded_file, sheet_name='Piping')

        # Clean up any extra whitespace from column names
        df_equipment.columns = df_equipment.columns.str.strip()
        df_piping.columns = df_piping.columns.str.strip()

        st.success("Excel file loaded successfully! Here's the data:")

        # Show the data we just read
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

                # Optional: Add a download button for the image
                pid_diagram.render('output/generated_pid', format='png', cleanup=True)
                with open("output/generated_pid.png", "rb") as file:
                    btn = st.download_button(
                        label="Download P&ID as PNG",
                        data=file,
                        file_name="generated_pid.png",
                        mime="image/png"
                    )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.warning("Please ensure your Excel file has two sheets named 'Equipment' and 'Piping' with the correct columns (e.g., 'Tag', 'Type', 'From', 'To').")
