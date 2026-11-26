FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm tar gzip \
    && ARCH="$(dpkg --print-architecture)" \
    && case "${ARCH}" in \
        amd64) HELM_ARCH="amd64" ;; \
        arm64) HELM_ARCH="arm64" ;; \
        *) echo "Unsupported architecture: ${ARCH}" && exit 1 ;; \
      esac \
    && curl -fsSL "https://get.helm.sh/helm-v3.15.4-linux-${HELM_ARCH}.tar.gz" -o /tmp/helm.tgz \
    && tar -xzf /tmp/helm.tgz -C /tmp \
    && mv "/tmp/linux-${HELM_ARCH}/helm" /usr/local/bin/helm \
    && chmod +x /usr/local/bin/helm \
    && rm -rf /var/lib/apt/lists/* /tmp/helm.tgz "/tmp/linux-${HELM_ARCH}" \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
