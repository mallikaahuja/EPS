import streamlit as st

st.set_page_config(layout="wide")

st.title("Barebones Application Test")

st.header("Deployment Environment Check")
st.success("If you can see this message, the Streamlit application is successfully running on Railway.")

st.info("The Dockerfile and requirements.txt are working.")

st.balloons()
