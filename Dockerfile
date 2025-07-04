# Use an official, slim Python base image for faster builds and smaller size
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install only the essential system dependencies for Graphviz
# This is the most critical step for stability on cloud platforms.
RUN apt-get update && apt-get install -y \
    graphviz-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker's layer caching.
# The following steps will only re-run if this file changes.
COPY requirements.txt .

# Install all Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's source code into the container.
# This includes app.py, the 'symbols' folder, etc.
COPY . .

# The command to run your Streamlit application using the "shell form"
# This allows Railway to correctly substitute the ${PORT} variable.
CMD streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0
