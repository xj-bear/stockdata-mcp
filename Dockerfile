FROM python:3.10-slim

WORKDIR /app

# Install dependencies
# We copy pyproject.toml but since we don't have a full build system in this simple dockerfile,
# we can just install via pip.
# Ideally we use `pip install .` if pyproject.toml is valid.
COPY pyproject.toml .
COPY server.py .
COPY data_source.py .

# Install dependencies
RUN pip install --no-cache-dir mcp akshare pandas starlette uvicorn httpx

# Expose port for SSE
EXPOSE 8000

# Set mode to SSE by default for Docker
ENV MCP_MODE=sse

# Run the server
CMD ["python", "server.py"]
