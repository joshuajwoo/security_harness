FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies only (skip building the project wheel — code is COPY'd next)
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY agents/ agents/
COPY harness/ harness/
COPY scenarios/ scenarios/

# Default command (overridden by DockerSandbox)
CMD ["python", "-m", "harness.agent_wrapper", "--help"]
