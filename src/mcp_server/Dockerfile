# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY pyproject.toml pyproject.toml
RUN pip install --no-cache-dir -e .

COPY *.py ./

# Command to run the application
CMD ["python3", "/app/mcp_server.py"]
