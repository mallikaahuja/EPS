# Use the official Streamlit image as the base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files to working directory
COPY . .

# Streamlit-specific port binding for Railway
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=$PORT", "--server.enableCORS=false"]
