FROM python:3.12-slim

WORKDIR /app

# Systemafhængigheder til at bygge nogle Python-pakker (pandas/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Mappen hvor SQLite-databasen gemmes (mountes som volume i docker-compose)
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
