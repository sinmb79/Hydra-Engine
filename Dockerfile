FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY hydra/ hydra/
RUN pip install --no-cache-dir .

COPY config/ config/
COPY scripts/ scripts/
COPY DISCLAIMER.md .

RUN useradd -m hydra && chown -R hydra:hydra /app
USER hydra

EXPOSE 8000
CMD ["uvicorn", "hydra.main:app", "--host", "0.0.0.0", "--port", "8000"]
