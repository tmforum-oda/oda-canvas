# Dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy operator code from src/ directory
COPY ./src/ /carbonOperator/

CMD kopf run --namespace=components --verbose /carbonOperator/main.py
