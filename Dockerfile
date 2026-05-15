FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && poetry install --without dev,test --no-root

COPY . .

FROM python:3.13-slim AS final

WORKDIR /app

RUN useradd -m appuser

COPY --chown=appuser --from=builder /app/.venv .venv

COPY --chown=appuser . .

ENV PATH=$PATH:/app/.venv/bin

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
