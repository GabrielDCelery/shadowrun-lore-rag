# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies for marker-pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src 

ARG USERNAME=app
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd -g ${USER_GID} ${USERNAME} && \
    useradd -m -u ${USER_UID} -g ${USER_GID} ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /app
USER ${USERNAME}
ENV HOME=/home/${USERNAME}

# Default command (can be overridden in compose)
CMD ["uv", "run", "python", "src/create_embeddings.py"]
