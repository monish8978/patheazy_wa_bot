# Use lightweight python base image
FROM python:3.11-slim-bookworm

# Prevent python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /workspace



# Copy and install python dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /workspace/

# Expose port for FastAPI application
EXPOSE 9103

# Default command to run the FastAPI app (using python runner to read port from env/.env)
CMD ["python", "-m", "app.main"]
