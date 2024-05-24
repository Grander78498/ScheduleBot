FROM ubuntu:20.04

COPY src .
COPY requirements.txt .
COPY main.py .

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]