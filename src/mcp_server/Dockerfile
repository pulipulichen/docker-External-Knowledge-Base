# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY *.py ./
RUN pip install --no-cache-dir -e .

# FastMCP HTTP is ASGI: use UvicornWorker, not the default sync WSGI worker.
# Gunicorn --reload with UvicornWorker is unreliable; MCP_DEV_RELOAD=1 uses uvicorn --reload (single process).
ENV MCP_DEV_RELOAD=0
EXPOSE 80
CMD ["sh", "-c", "if [ \"$MCP_DEV_RELOAD\" = 1 ]; then exec uvicorn mcp_server:http_app --host 0.0.0.0 --port 80 --reload; else exec gunicorn --bind 0.0.0.0:80 --worker-class uvicorn.workers.UvicornWorker --workers 4 --timeout 120 mcp_server:http_app; fi"]
