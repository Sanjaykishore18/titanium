# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy frontend code
COPY . .

# Expose port
EXPOSE 8080

# Run Python HTTP server (serves static files)
CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0"]