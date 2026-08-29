FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# shell form so $PORT expands — Cloud Run injects this at runtime
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
