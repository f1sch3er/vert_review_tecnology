FROM python 

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SETTINGS_MODULE=core.settings \
    DATABASE_URL=postgres://none:none@none:5432/none \
    python manage.py collectstatic --noinput --clear

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "core.wsgi:application"]