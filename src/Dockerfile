FROM python 

COPY requirements.txt .

RUN python -m pip install -r requirements.txt

WORKDIR /app

COPY . /app/

RUN python manage.py collectstatic --noinput

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "core.wsgi:application"]