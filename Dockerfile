FROM dipdup/dipdup:5.1

COPY pyproject.toml poetry.lock ./
RUN inject_pyproject
