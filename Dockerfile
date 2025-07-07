FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv export --no-hashes --format requirements-txt > requirements.txt
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libmagic1

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY . .

ENV PATH="/opt/venv/bin:$PATH"