FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY hydra/ hydra/
COPY config/ config/
COPY scripts/ scripts/
COPY DISCLAIMER.md .

RUN useradd -m hydra && chown -R hydra:hydra /app
USER hydra

EXPOSE 8000
CMD ["uvicorn", "hydra.main:app", "--host", "127.0.0.1", "--port", "8000"]
