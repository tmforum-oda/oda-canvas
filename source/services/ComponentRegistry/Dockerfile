FROM python:3.12-alpine

WORKDIR /src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA
ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME=$CICD_BUILD_TIME

COPY ./src/app /src/app

EXPOSE 8080

CMD ["fastapi", "run", "app/main.py", "--port", "8080"]