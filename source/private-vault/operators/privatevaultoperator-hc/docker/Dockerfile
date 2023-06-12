FROM python:3.11

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt

ADD *.py /src/

CMD kopf run /src/privatevaultOperatorHC.py --verbose
