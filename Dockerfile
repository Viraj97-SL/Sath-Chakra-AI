FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install all requirements from the list above
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the browser for your "THE ASCENDANT" identity cards
RUN python -m playwright install chromium --with-deps

COPY . .

# Railway default port
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]