# Use an official lightweight Python runtime as the base engine
FROM python:3.12-slim

# Set systemic environment configurations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establish isolated internal application directory
WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching optimization
COPY requirements.txt /app/

# Install application dependencies via pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application assets into the container image space
COPY gateway.py gateway_config.json /app/

# The gateway reads configuration files and connects to networks dynamically.
# Command to launch the data gateway loop automatically on container spin-up
CMD ["python", "gateway.py"]
