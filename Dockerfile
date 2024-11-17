FROM python:3.12

WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

COPY bot .
COPY django_queue .
COPY queue_api .
COPY entrypoint.sh /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]