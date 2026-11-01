FROM python:3.10-slim

WORKDIR /app

COPY wheels/ /wheels/

RUN pip install --no-cache-dir \
    --no-index \
    --find-links=/wheels \
    kafka-python==3.0.11 \
    boto3==1.43.99

COPY main.py .

CMD ["python", "-u", "main.py"]
