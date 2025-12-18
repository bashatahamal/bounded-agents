FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------
# 1. Copy ONLY dependency metadata
# -----------------------
COPY pyproject.toml README.md langgraph.json ./

# Install build tooling once
RUN pip install --upgrade pip setuptools wheel

# Install runtime deps (cached unless pyproject.toml changes)
RUN pip install .

# Install LangGraph CLI (rarely changes)
RUN pip install "langgraph-cli[inmem]>=0.1.71"

# -----------------------
# 2. Copy application code LAST
# -----------------------
COPY src ./src

EXPOSE 1024

CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "1024"]
