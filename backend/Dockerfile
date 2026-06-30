FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (leverages Docker caching layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source code
COPY . .

# Expose the internal port (purely documentation, overridden by runtime)
EXPOSE 8000

# Run the data cleanup script, then launch Uvicorn using the dynamic cloud PORT
CMD ["sh", "-c", "python scripts/clean_dataset.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]