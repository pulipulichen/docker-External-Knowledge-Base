# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && \ 
    apt-get install -y ffmpeg libreoffice && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml and install dependencies
COPY pyproject.toml pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy the current directory contents into the container at /app
# COPY . .

# Expose port 80
EXPOSE 80

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--reload", "api.api:app"]
