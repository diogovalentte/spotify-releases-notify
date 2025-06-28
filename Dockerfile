FROM python:3.11.0-slim AS build

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt update && apt install -y --no-install-recommends \ 
    git \
    curl \
    && pip install --upgrade pip \
    && pip install --no-cache-dir --target=/app/deps -r requirements.txt gunicorn supervisor 

RUN mkdir -p /config

FROM gcr.io/distroless/python3:nonroot

WORKDIR /app
COPY --from=build /app/deps /app/deps
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./init_db.py /app/init_db.py
COPY ./app.py /app/app.py
COPY ./src /app/src
COPY --from=build /config /config

ENV TZ=UTC
ENV PYTHONPATH="/app/deps"
ENV PATH="/app/deps/bin:$PATH"

EXPOSE 8000

CMD ["/app/deps/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
