FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install system dependencies (ffmpeg is often required for audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --locked --no-install-project --no-dev

# Copy the application code
COPY ./bot.py ./start.py ./
COPY ./app ./app

# Expose both ports (voice: 7860, text chat: 7861)
EXPOSE 7860 7861

# Command to run BOTH servers
CMD ["uv", "run", "python", "start.py"]
