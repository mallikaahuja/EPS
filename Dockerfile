# Use a slim base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    graphviz \
    graphviz-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the Streamlit app using port forwarding for Railway
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]
