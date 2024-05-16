FROM python:3.12-alpine

# workaround to handle libcrypto not found issue in alpine described here:
# https://github.com/wbond/oscrypto/tree/master?tab=readme-ov-file#dependencies
# https://github.com/python/cpython/blob/4acc140f8d2c905197362d0ffec545a412ab32a7/Lib/ctypes/util.py#L97
RUN apk update && \
    apk add --no-cache gcc && \
    ln -s /usr/lib/libcrypto.so.3 /usr/lib/libcrypto.so

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt && \
    rm requirements.txt

ADD *.py /src/

ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA

CMD kopf run --all-namespaces --verbose /src/secretsmanagementOperatorHC.py
