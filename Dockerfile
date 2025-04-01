FROM python:3.10-slim-buster

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 5000
RUN python -m spacy download en_core_web_sm

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]