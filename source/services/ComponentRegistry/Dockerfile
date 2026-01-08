FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY openapi/ ./openapi/
#
RUN rm -f /app/app/.env

# Expose port
EXPOSE 8080

ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH $SOURCE_DATE_EPOCH
ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8080

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
