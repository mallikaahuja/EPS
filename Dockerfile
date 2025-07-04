# Use a minimal base image with Python 3.11
FROM python:3.11-slim

# Install OS dependencies required by cairosvg, graphviz, and other libraries
RUN apt-get update && apt-get install -y \
    libgtk2.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    graphviz \                  # ✅ This line installs the missing Graphviz executables
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy Python dependencies file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app code
COPY . .

# Copy symbol images explicitly
COPY symbols/ symbols/

# Expose default Streamlit port
EXPOSE 8501

# Command to run your Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
