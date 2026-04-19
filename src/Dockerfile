FROM python 
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
WORKDIR /app
COPY . /app/
CMD ["gunicor", "--bind", "0.0.0.0:5000", "-c", "config.py", "app:app"]