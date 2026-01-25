# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN mkdir /app

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY ./requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables
ENV MCP_API_KEY=${MCP_API_KEY}

# Command to run the application
CMD ["python3", "/app/rps_mpc_server.py"]
