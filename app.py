import streamlit as st
import os

st.set_page_config(page_title="EPS P&ID Generator", layout="wide")

# Try to access the OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")

st.title("🚀 EPS P&ID Generator")
if openai_key:
    st.success("✅ OpenAI Key Loaded")
else:
    st.error("❌ OpenAI Key not found!")

# Simple dropdown test
component = st.selectbox("Choose Component", ["Pump", "Condenser", "Receiver"])
st.write(f"You selected: {component}")
