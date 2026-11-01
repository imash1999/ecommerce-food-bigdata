FROM python:3.12-slim

WORKDIR /app

COPY wheels/ /wheels/

RUN pip install --no-cache-dir --no-index --find-links=/wheels \
    fastapi uvicorn psycopg2-binary

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
