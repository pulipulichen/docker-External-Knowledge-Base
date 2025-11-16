# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and install dependencies
COPY pyproject.toml pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8080
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
