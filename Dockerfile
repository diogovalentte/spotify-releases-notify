FROM python:3.10.0-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt update && apt install git curl -y && pip install -r requirements.txt
RUN pip install gunicorn
COPY . .

ENV TZ=UTC

EXPOSE 8000

RUN mkdir -p /config

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD sh -c 'curl -f http://localhost:8000/health | grep OK || exit 1'

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "src.api:app"]
