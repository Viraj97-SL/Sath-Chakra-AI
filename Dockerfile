# Use a Python base image that supports Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium)
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]