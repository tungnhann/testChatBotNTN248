FROM python:3.11-slim

WORKDIR /app

# Setup timezone
ENV TZ=UTC

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the job
CMD ["python", "main.py"]
