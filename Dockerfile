FROM python:3.10

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Install CPU-only PyTorch first (important)
RUN pip install --no-cache-dir torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# 🔥 Pre-download models during build (VERY IMPORTANT)
RUN python -c "import whisper; whisper.load_model('tiny')"
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"

COPY . .

# Cloud Run requires this
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
