FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

# استخدام الملف الخفيف للمتطلبات
COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

COPY . .

# جمع الملفات الثابتة بشكل آمن (تجاهلي الأخطاء)
RUN python manage.py collectstatic --noinput || true

CMD gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 8
