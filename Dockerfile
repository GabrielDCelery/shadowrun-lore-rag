# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies for marker-pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
ARG USERNAME=app
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd -g ${USER_GID} ${USERNAME} && \
    useradd -m -u ${USER_UID} -g ${USER_GID} ${USERNAME}

USER ${USERNAME}
ENV HOME=/home/${USERNAME}

WORKDIR /app

# Copy dependency files and install as app user
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/home/${USERNAME}/.cache/uv,uid=${USER_UID},gid=${USER_GID} \
    uv sync --frozen

# Copy source code
COPY --chown=${USERNAME}:${USERNAME} src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Default command (can be overridden in compose)
CMD ["uv", "run", "python", "src/create_embeddings.py"]
