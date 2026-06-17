# Dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy operator code
COPY ./main.py /carbonOperator/
COPY ./models.py /carbonOperator/
COPY ./carbon_forecast_fetcher.py /carbonOperator/
COPY ./carbon_tmf628_fetcher.py /carbonOperator/
COPY ./max_replica_getter.py /carbonOperator/
COPY ./scaled_object_manager.py /carbonOperator/
COPY ./metrics.py /carbonOperator/
COPY ./utils.py /carbonOperator/

CMD kopf run --namespace=components --verbose /carbonOperator/main.py
