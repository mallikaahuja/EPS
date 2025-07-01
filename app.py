import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read and clean the Excel file
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()  # Remove extra spaces

        # Display data preview
        st.subheader("Excel Data Preview")
        st.dataframe(df)

        # Filter rows with valid X and Y coordinates
        if "X" in df.columns and "Y" in df.columns:
            filtered_df = df[df["X"].notna() & df["Y"].notna()]

            # Plot the points
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.scatter(filtered_df["X"], filtered_df["Y"], color="blue", s=10)

            # Annotate with tag names
            for _, row in filtered_df.iterrows():
                ax.annotate(str(row["Text"]), (row["X"], row["Y"]), fontsize=8)

            ax.set_title("P&ID Preview")
            ax.set_xlabel("X Coordinate")
            ax.set_ylabel("Y Coordinate")
            ax.grid(True)

            st.pyplot(fig)

            # Optional: download button
            st.download_button("Download Filtered Data", filtered_df.to_csv(index=False), file_name="filtered_pid_data.csv")

        else:
            st.error("The uploaded file must contain 'X' and 'Y' columns.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
