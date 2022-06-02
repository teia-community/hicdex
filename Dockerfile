FROM dipdup/dipdup:5.1
COPY . .
RUN inject_pyproject
