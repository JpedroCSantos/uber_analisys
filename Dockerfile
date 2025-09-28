ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION} as builder
WORKDIR /app
RUN pip install poetry
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY ./app .
ENV PATH="/app/.venv/bin:$PATH"
ENV ETL_MODE=DEMO

CMD ["python", "main.py"]
