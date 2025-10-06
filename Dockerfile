FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:8000 --workers 3 --timeout 60"
CMD ["gunicorn", "wsgi:app"]
