FROM python:3.6

MAINTAINER Mr Gao

COPY *.py /app/
COPY onethingcloud/*.py /app/onethingcloud/
COPY conf/config.ini /app/conf/
COPY requirements.txt /app/

WORKDIR /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/main.py"]
