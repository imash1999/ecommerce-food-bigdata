FROM python:3.10-slim

WORKDIR /app

COPY wheels/*.whl ./
RUN pip install --no-index --find-links=. *.whl

COPY main.py .

CMD ["python", "-u", "main.py"]
