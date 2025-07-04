# Use an official, slim Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies. Ensure no spaces exist after the backslashes `\`
RUN apt-get update && apt-get install -y \
    graphviz-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's source code into the container
COPY . .

# Command to run your Streamlit app
# Railway provides the ${PORT} environment variable automatically
CMD ["streamlit", "run", "app.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]
