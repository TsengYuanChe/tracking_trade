FROM python:3.10-slim

# Install gcc for some dependencies
RUN apt-get update && apt-get install -y gcc

WORKDIR /app

# Copy only requirements first for better docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Cloud Run needs the container to listen on port 8080
EXPOSE 8080

# Start FastAPI Webhook server
CMD ["uvicorn", "webhook.webhook_server:app", "--host", "0.0.0.0", "--port", "8080"]