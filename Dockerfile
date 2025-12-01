FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install system dependencies (ffmpeg is often required for audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the application code
COPY ./bot.py bot.py
COPY ./app app

# Command to run the bot
CMD ["uv", "run", "bot.py", "--host", "0.0.0.0", "--port", "8765"]
