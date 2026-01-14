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

# Copy the application code (solo bot.py, sin start.py)
COPY ./bot.py ./
COPY ./app ./app

# Expose voice port only
EXPOSE 7860

# Command to run voice server directly
CMD ["uv", "run", "python", "bot.py", "--host", "0.0.0.0"]
