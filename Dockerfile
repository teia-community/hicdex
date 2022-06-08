FROM dipdup/dipdup:5.1.6
# Uncomment if you have an additional dependencies in pyproject.toml
# COPY pyproject.toml poetry.lock ./
# RUN inject_pyproject
COPY --chown=dipdup src/hicdex hicdex
