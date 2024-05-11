#FROM codercom/code-server:4.22.0
FROM dockerhub.devops.telekom.de/codercom/code-server:4.22.0

USER 0

ARG KCVERSION=v1.27.11
ARG KCSHA256=7ae327978a1edb43700070c86f5fd77215792c6b58a7ea70192647e0da848e29

ARG HELMVERSION=v3.14.2
ARG HELMSHA256=0885a501d586c1e949e9b113bf3fb3290b0bbf74db9444a1d8c2723a143006a5

# ----- INSTALL "kubectl" ----- (see https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/ )
RUN curl -Lo /usr/local/bin/kubectl https://dl.k8s.io/release/$KCVERSION/bin/linux/amd64/kubectl \
    && echo "$KCSHA256  /usr/local/bin/kubectl" | sha256sum -c \
    && chmod a+x /usr/local/bin/kubectl

# ----- INSTALL "helm" ----- (see https://github.com/helm/helm/releases )
RUN cd /tmp \
    && curl -Lo helm.tar.gz https://get.helm.sh/helm-${HELMVERSION}-linux-amd64.tar.gz \
    && echo "$HELMSHA256  helm.tar.gz" | sha256sum -c \
    && tar xvzf helm.tar.gz \
    && cp linux-amd64/helm /usr/local/bin/ \
    && chmod a+x /usr/local/bin/helm \
    && rm -rf /tmp/linux-amd64 \
    && rm /tmp/*


# ----- INSTALL "node" ----- (see https://joshtronic.com/2023/11/12/how-to-install-node-js-21-on-ubuntu/ )
RUN apt update \
    && apt install -y ca-certificates curl gnupg jq \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_21.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list \
    && apt update \
    && apt install nodejs -y \
    && node -v \
    && npm -v

USER 1000:1000
