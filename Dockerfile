FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the backend requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into /app
COPY backend/ .

# Hugging Face Spaces route web traffic to port 7860
EXPOSE 7860

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
