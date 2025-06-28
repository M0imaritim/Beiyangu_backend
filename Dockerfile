FROM python:3.11-slim

# environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

ENV DJANGO_SETTINGS_MODULE=beiyangu.settings.production

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "beiyangu.wsgi:application"]
