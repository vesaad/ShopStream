FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Start both consumer and API
CMD ["sh", "-c", "python app/consumer.py & uvicorn app.main:app --host 0.0.0.0 --port 8004"]
