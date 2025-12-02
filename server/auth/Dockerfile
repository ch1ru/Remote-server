# Use a small, efficient Python base image
FROM python:3.11-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY verify.py .

# Expose port for FastAPI
EXPOSE 8000

# Healthcheck (optional)
HEALTHCHECK CMD curl --fail http://localhost:8000/verify || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "verify:app", "--host", "0.0.0.0", "--port", "8000"]
