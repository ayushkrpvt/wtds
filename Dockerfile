# Use the official Python image with a specific version tag to ensure reproducibility  
FROM python:3.12
  
# Set environment variables to prevent Python from writing pyc files to disc and buffering stdout and stderr  
ENV PYTHONDONTWRITEBYTECODE 1  
ENV PYTHONUNBUFFERED 1  
  
# Set the working directory in the Docker container  
WORKDIR /code  
  
# Install system dependencies  
RUN apt-get update \  
    && apt-get install -y --no-install-recommends gcc libc-dev \  
    && rm -rf /var/lib/apt/lists/*  
  
# Install Python dependencies  
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt  
  
# Copy project files to the working directory  
COPY . .  
  
# Expose the port the app runs on  
EXPOSE 8000  
  
# Run Uvicorn without reloading (for production)  
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]  
