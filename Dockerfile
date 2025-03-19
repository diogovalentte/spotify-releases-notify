FROM python:3.10.0-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt update && apt install -y --no-install-recommends \ 
    supervisor \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV TZ=UTC

EXPOSE 8000

RUN mkdir -p /config

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD sh -c 'curl -f http://localhost:8000/health | grep OK || exit 1'

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
