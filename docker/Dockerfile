FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt packages.txt setup.sh ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openssl \
       ffmpeg \
       libsm6 \
       libxext6 \
       libglib2.0-0 \
       build-essential \
       libssl-dev \
       libffi-dev \
       pkg-config \
       git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ../src /app

RUN mkdir -p media/recordings media/snapshots media/thumbnails cert \
    && chmod -R a+rw media cert || true

RUN if [ ! -f cert/cert.pem ] || [ ! -f cert/key.pem ]; then \
      openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -keyout cert/key.pem -out cert/cert.pem \
        -subj "/C=US/ST=Unknown/L=Unknown/O=BabyMonitor/OU=Development/CN=babymonitor.local"; \
    fi

EXPOSE 443

ENV PYTHONPATH=/app

CMD ["uvicorn","main:app_socket","--host","0.0.0.0","--port","443","--ssl-certfile","cert/cert.pem","--ssl-keyfile","cert/key.pem","--log-level","info"]
