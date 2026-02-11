FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python packages with optimizations
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    torch \
    torchvision \
    torchaudio \
    && pip install --no-cache-dir -r requirements.txt

# Pre-download models with progress indication
RUN python -c "import whisper; print('Downloading Whisper model...'); whisper.load_model('base'); print('Whisper model downloaded')"
RUN python -c "from transformers import pipeline; print('Downloading emotion model...'); pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base'); print('Emotion model downloaded')"

COPY . .

# Create necessary directories
RUN mkdir -p /tmp/whisper-cache

# Use environment variable for port
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --limit-concurrency 1