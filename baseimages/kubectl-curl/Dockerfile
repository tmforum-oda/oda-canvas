FROM alpine/curl

ARG KUBERNETES_RELEASE=v1.30.5
ARG TARGETPLATFORM=linux/amd64

RUN apk add --no-cache jq

RUN cd /bin \
    && echo downloading kubectl from https://dl.k8s.io/release/${KUBERNETES_RELEASE}/bin/${TARGETPLATFORM}/kubectl \
    && curl -fsSLO https://dl.k8s.io/release/${KUBERNETES_RELEASE}/bin/${TARGETPLATFORM}/kubectl \
    && chmod +x kubectl

    