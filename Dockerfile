FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directories
RUN mkdir -p data/recommendations data/proposals data/processed

# Environment variables (set at runtime)
ENV SAM_API_KEY=""
ENV OPENAI_API_KEY=""
ENV PYTHONUNBUFFERED=1

# Default: run full pipeline
CMD ["python3", "main.py"]
