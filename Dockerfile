# Use the official Microsoft Playwright image for Python
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Step A: Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Step B: Install the playwright package via pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright  # Extra safety: ensure the CLI is available

# Step C: Install only the chromium browser binaries
# We use the full python module path to avoid "command not found"
RUN python -m playwright install chromium --with-deps

# Step D: Copy your code and start
COPY . .

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]