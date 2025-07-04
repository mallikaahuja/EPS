# Use an official Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Graphviz, DXF, and PDF/PNG generation
RUN apt-get update && apt-get install -y \
    graphviz-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's source code
COPY . .

# Command to run your Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]
