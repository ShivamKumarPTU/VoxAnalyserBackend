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

# Upgrade pip tools FIRST
RUN pip install --upgrade pip setuptools wheel

# Install CPU-only torch FIRST
RUN pip install --no-cache-dir torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# 🔥 Install openai-whisper separately WITHOUT build isolation
RUN pip install --no-cache-dir --no-build-isolation openai-whisper==20231117

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models
RUN python -c "import whisper; whisper.load_model('tiny')"
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
