FROM python:3.12-alpine

ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

# some workaround to handle libcrypto not found issue in alpine described here:
# https://stackoverflow.com/questions/73977158/libcrypto-not-found-using-oscrypto-library-in-alpine-based-docker-image
RUN apk update && \
    apk add --no-cache \
    build-base openssl-dev

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt && \
    rm requirements.txt

ADD *.py /src/

CMD kopf run /src/dependentApiSimpleOperator.py --verbose
