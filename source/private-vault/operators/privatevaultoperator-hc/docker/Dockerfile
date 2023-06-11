FROM python:3.10

WORKDIR /src
ADD *.py /src
ADD requirements.txt /src

RUN pip install -r requirements.txt

CMD kopf run /src/privatevaultOperatorHC.py --verbose
