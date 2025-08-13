FROM python:3.12-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
    
RUN pip install --upgrade pip


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .