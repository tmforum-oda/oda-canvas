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

ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH $SOURCE_DATE_EPOCH
ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

# Run the application
CMD ["python3", "-u", "kc_setup_compreg.py"]
