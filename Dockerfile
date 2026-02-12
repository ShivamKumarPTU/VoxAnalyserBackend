FROM python:3.10

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade packaging tools
RUN pip install --upgrade pip setuptools wheel

# 🔥 Install numpy FIRST (required by torch & whisper)
RUN pip install numpy

# Install CPU-only torch
RUN pip install torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install Whisper directly from GitHub
RUN pip install git+https://github.com/openai/whisper.git

# Install other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 Pre-download models during build
RUN python -c "import whisper; whisper.load_model('tiny')"
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"

# Copy application code
COPY . .

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
