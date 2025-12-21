FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/*.py ./
#
# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python3", "kc_setup_compreg.py"]
