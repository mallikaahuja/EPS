# Use an official, slim Python base image for faster builds
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for Graphviz and its Python libraries
# This single command replaces the need for packages.txt on Railway
RUN apt-get update && apt-get install -y \
    graphviz-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container first
# This allows Docker to cache the installed packages if the file doesn't change
COPY requirements.txt .

# Install all Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's source code into the container
# This includes app.py, the 'symbols' folder, etc.
COPY . .

# The command to run your Streamlit application
# Railway provides the ${PORT} environment variable automatically
CMD ["streamlit", "run", "app.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]
