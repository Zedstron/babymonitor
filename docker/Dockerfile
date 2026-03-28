FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openssl \
       ffmpeg \
       libsm6 \
       libxext6 \
       libglib2.0-0 \
       portaudio19-dev \
       libasound-dev \
       libjack-jackd2-dev \
       build-essential \
       libssl-dev \
       libffi-dev \
       pkg-config \
       python3-pyaudio \
       vlc \
       python3-gi \
       openresolv \
       wireguard \
       gir1.2-gstreamer-1.0 \
       gstreamer1.0-plugins-base \
       gstreamer1.0-plugins-good \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p media/recordings media/snapshots media/thumbnails cert && chmod -R a+rw media cert || true

RUN if [ ! -f cert/cert.pem ] || [ ! -f cert/key.pem ]; then \
      openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -keyout cert/key.pem -out cert/cert.pem \
        -subj "/C=US/ST=Unknown/L=Unknown/O=BabyMonitor/OU=Development/CN=babymonitor.local"; \
    fi

EXPOSE 443

ENV PYTHONPATH=/app

CMD ["uvicorn","main:app_socket","--host","0.0.0.0","--port","443","--ssl-certfile","cert/cert.pem","--ssl-keyfile","cert/key.pem","--log-level","info"]
