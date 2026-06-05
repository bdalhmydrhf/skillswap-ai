FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

COPY requirements-light.txt .
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements-light.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

CMD gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 8
