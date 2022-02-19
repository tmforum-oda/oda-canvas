FROM docker:dind as tmf-canvas-in-a-bottle

RUN apk add --no-cache \
    bash \
    curl \
    docker \
    git \
    jq \
    openssl \
    shadow \
    vim \
    wget \
    coreutils \
    openrc

RUN rc-update add docker boot

# Add Limited user
RUN groupadd -r canvas \
             -g 777 && \
    useradd -c "canvas runner account" \
            -g canvas \
            -u 777 \
            -m \
            -r \
            canvas && \
    usermod -aG docker canvas


# Install kubectl
RUN curl -LO https://dl.k8s.io/release/v1.23.1/bin/linux/amd64/kubectl && \
    chmod +x ./kubectl && \
    mv ./kubectl /usr/local/bin/kubectl

# Install Kubernetes in Docker (kind)
RUN curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/v0.11.1/kind-linux-amd64 && \
    chmod +x ./kind && \
    mv ./kind /usr/local/bin/kind

# Install helm
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh

# Install Grafana helm charts
RUN cd /root && \
    git clone https://github.com/pivotal-cf/charts-grafana

# Install Istio
RUN cd /root && \
    wget -O downloadIstio.sh https://raw.githubusercontent.com/istio/istio/master/release/downloadIstioCandidate.sh && \
    chmod 700 downloadIstio.sh && \
    ./downloadIstio.sh && \
    mv /root/istio-1.13.0/bin/istioctl /usr/local/bin/istioctl

# Clone Canvas Repository
# TODO: clone just the necessary scripts
RUN cd /root && \
    git clone https://github.com/tmforum-oda/oda-canvas-charts.git


RUN dockerd &


COPY canvas_demo.sh /root/canvas_demo.sh
COPY scripts/get_dashboard_token /root/get_dashboard_token
COPY scripts/get_grafana_credentials /root/get_grafana_credentials

#Add Graphical user interface
#COPY ../ciab-gui /root/ciab-gui

ENV PATH="${PATH}:/root"

ENTRYPOINT ["/bin/bash"]
