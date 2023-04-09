FROM python:3.10-alpine

RUN adduser -D trivia

WORKDIR /home/trivia

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt && pip install gunicorn

COPY app app
COPY migrations migrations
COPY trivia.py entrypoint.sh ./

RUN chmod +x entrypoint.sh

ENV FLASK_APP trivia.py

RUN chown -R trivia:trivia ./

USER trivia

EXPOSE 5000

VOLUME ["/home/trivia/config"]
VOLUME ["/home/trivia/data"]

ENTRYPOINT ["./entrypoint.sh"]
