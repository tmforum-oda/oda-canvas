FROM python:3.11

# for debugging
RUN apt-get update && apt-get install -y vim

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt
RUN rm requirements.txt

ADD *.py /src/

ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

CMD kopf run /src/componentvaultOperatorHC.py --verbose
