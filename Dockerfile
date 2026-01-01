FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install the massive list of requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install nest-asyncio as a safety measure
RUN pip install nest-asyncio

# Install the Chromium browser for your identity cards
RUN python -m playwright install chromium --with-deps

COPY . .

# Match the port in your Railway settings
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]