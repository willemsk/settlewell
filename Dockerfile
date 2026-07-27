# Production Dockerfile for SettleWell Solara Web GUI

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libegl1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency specifications
COPY pyproject.toml uv.lock README.md /app/

# Install dependencies using uv
RUN uv sync --frozen --extra web --no-dev

# Copy source code
COPY src /app/src

# Expose default Solara port
EXPOSE 8765

ENV SOLARA_APP=settlewell.solara_app.app
ENV PORT=8765
ENV HOST=0.0.0.0

# Run Solara web application
CMD ["uv", "run", "--extra", "web", "solara", "run", "settlewell.solara_app.app", "--host", "0.0.0.0", "--port", "8765"]
