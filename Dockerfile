FROM python:latest
EXPOSE 8000
WORKDIR /source

COPY requirements.txt /source

RUN pip install -U pip
RUN pip install -r requirements.txt

COPY . /source
CMD ["uvicorn","wall.main:app", "--host", "0.0.0.0", "--port", "8000"]
