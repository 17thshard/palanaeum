FROM python:3.10-buster

WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra postgresql-client

ADD ./requirements.txt /app/requirements.txt
RUN pip3 install -Ur ./requirements.txt

ADD . /app
ADD ./palanaeum/settings/docker.py /app/palanaeum/settings/local.py

ENV DJANGO_SETTINGS_MODULE palanaeum.settings.docker
CMD python3 /app/manage.py runserver_plus
