# Use the official Python 3.11 slim image to match your local setup
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file first (this makes building faster)
COPY requirements.txt .

# Install your dependencies (grpcio, pika, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files into the container
COPY . .