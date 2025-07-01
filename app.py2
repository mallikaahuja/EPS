import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import unicodedata

st.title("EPS Auto P&ID Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        # Strip weird unicode characters and cast coordinates to numeric
        def clean_text(val):
            try:
                return unicodedata.normalize("NFKD", str(val)).encode("ascii", "ignore").decode("ascii")
            except:
                return str(val)

        df["Text"] = df["Text"].apply(clean_text)
        df["X"] = pd.to_numeric(df["X"], errors="coerce")
        df["Y"] = pd.to_numeric(df["Y"], errors="coerce")

        # Drop rows with missing coordinates
        filtered_df = df.dropna(subset=["X", "Y"])

        st.subheader("Excel Data Preview")
        st.dataframe(filtered_df)

        if filtered_df.empty:
            st.warning("No valid data points to plot.")
        else:
            # Plot
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.scatter(filtered_df["X"], filtered_df["Y"], color="blue", s=10)

            for _, row in filtered_df.iterrows():
                ax.annotate(str(row["Text"]), (row["X"], row["Y"]), fontsize=8)

            ax.set_title("P&ID Preview")
            ax.set_xlabel("X Coordinate")
            ax.set_ylabel("Y Coordinate")
            ax.grid(True)

            st.pyplot(fig)

            # Optional: download cleaned data
            st.download_button("Download Cleaned Data", filtered_df.to_csv(index=False), file_name="filtered_pid_data.csv")

    except Exception as e:
        st.error(f"An error occurred: {e}")
