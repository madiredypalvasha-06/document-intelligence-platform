FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
