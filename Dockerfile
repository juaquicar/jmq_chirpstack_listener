FROM python:3.12-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY --from=builder /install /usr/local
COPY app/ctx /app/ctx
COPY . .
RUN chmod +x entrypoint-prod.sh
RUN mkdir -p /var/log && touch /var/log/api.err.log /var/log/mqtt.err.log
EXPOSE 8999
CMD ["./entrypoint-prod.sh"]