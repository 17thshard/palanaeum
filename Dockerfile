FROM python:3-stretch

ADD . /app
ADD ./palanaeum/settings/docker.py /app/palanaeum/settings/local.py

WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra postgresql-client
RUN pip3 install -Ur ./requirements.txt

ENV DJANGO_SETTINGS_MODULE palanaeum.settings.docker
CMD python3 /app/manage.py runserver_plus
