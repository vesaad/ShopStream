FROM python:3.11-slim

WORKDIR /app

# 🔧 Required for pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends unixodbc unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
