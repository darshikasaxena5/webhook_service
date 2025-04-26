# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to the root
WORKDIR /

# Prevent Python from writing pyc files to disc and ensure output is unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Add the future /app directory to the PYTHONPATH
ENV PYTHONPATH=/

# Install system dependencies
# Add any system dependencies needed here (e.g., build-essential, libpq-dev for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
# Copy from the build context (app/) to the root of the container
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
# Install dependencies and gunicorn
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

# Copy the application code into the /app directory inside the container
# The build context is the app/ directory in the host
COPY . /app

# Expose port (informational, Railway handles the actual port via $PORT)
# EXPOSE 8000

# Command to run the application using Gunicorn
# Gunicorn will bind to 0.0.0.0:$PORT. $PORT is injected by Railway.
# The entrypoint is now app.main:app because the code is in /app
CMD gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:$PORT app.main:app
