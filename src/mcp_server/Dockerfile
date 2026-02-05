# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN mkdir /app

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY ./requirements.txt /app/
RUN pip install -r requirements.txt

# Command to run the application
CMD ["python3", "/app/mcp_server.py"]
