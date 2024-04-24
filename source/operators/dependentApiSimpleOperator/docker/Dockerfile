FROM python:3.12-alpine

ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

RUN apk update && \
    apk add --no-cache git

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt
RUN rm requirements.txt

ADD *.py /src/

CMD kopf run /src/dependentApiSimpleOperator.py --verbose
