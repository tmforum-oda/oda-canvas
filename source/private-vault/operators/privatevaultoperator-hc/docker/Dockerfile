FROM python:3.11

# for debugging
RUN apt-get update && apt-get install -y vim

WORKDIR /src

ADD requirements.txt /src/
RUN pip install -r requirements.txt
RUN rm requirements.txt

ADD *.py /src/

CMD kopf run /src/privatevaultOperatorHC.py --verbose
