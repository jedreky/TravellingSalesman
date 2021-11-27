#FROM python:3.8-alpine
FROM czentye/matplotlib-minimal

COPY requirements.txt /app/

RUN pip install -r app/requirements.txt

WORKDIR /app
COPY TravellingSalesman.py /app/
COPY webapp.py /app/
COPY static/background.png /app/static/
COPY static/readPos.js /app/static/
COPY templates/main.html /app/templates/

CMD [ "python3", "./webapp.py" ]
