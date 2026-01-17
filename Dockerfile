# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /project_root

# Install system dependencies needed for psycopg2 (PostgreSQL driver)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY backend/requirements.txt backend/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r backend/requirements.txt

# Copy the app directory into the container
COPY backend/ ./backend/


# We switch into 'backend' directory so uvicorn runs 'app.main' correctly
WORKDIR /project_root/backend

ENV PYTHONPATH=/project_root/backend
ENV PYTHONUNBUFFERED=1

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the application
# We use 0.0.0.0 to allow external connections to the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]