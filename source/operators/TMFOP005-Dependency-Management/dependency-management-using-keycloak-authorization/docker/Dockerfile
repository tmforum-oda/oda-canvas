FROM python:3.12-alpine

WORKDIR /src

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

ADD src .
ADD templates ./templates/

ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME=$CICD_BUILD_TIME

ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA

CMD ["/bin/sh", "-c", "kopf run -n $POD_NAMESPACE --verbose /src/dependencyManagementKeycloakAuthzOperator.py"]
