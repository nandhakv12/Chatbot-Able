FROM python:3.10-slim-buster

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm


CMD ["python3", "app.py"]