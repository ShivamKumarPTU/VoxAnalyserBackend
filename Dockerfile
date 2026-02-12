FROM python:3.10

WORKDIR /app

# Install system packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and stable setuptools
RUN pip install --upgrade pip setuptools==65.5.1 wheel

# Install torch CPU wheels first
RUN pip install --no-cache-dir torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Copy requirements
COPY requirements.txt .

# Install remaining dependencies
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy application
COPY . .

# Set port
ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
