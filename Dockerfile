FROM python:3.12

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra postgresql-client

ADD ./requirements.txt /app/requirements.txt
RUN pip3 install -U pip
RUN pip3 install -Ur ./requirements.txt

ADD . /app

RUN PALA_SECRET_KEY=collectstatic-dummy-key python3 /app/manage.py collectstatic --noinput
CMD python3 /app/manage.py runserver_plus
