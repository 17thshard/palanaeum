FROM python:3.12-slim
LABEL org.opencontainers.image.source = "https://github.com/17thshard/palanaeum"
ARG PALA_VERSION_TAG=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PALA_VERSION_TAG=${PALA_VERSION_TAG}

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install -U pip && \
    pip3 install -r /app/requirements.txt

COPY . /app

RUN mkdir -p /app/media /app/backups /app/logs && \
    PALA_SECRET_KEY=collectstatic-dummy-key python3 /app/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "palanaeum.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
