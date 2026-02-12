# Use a full python image (not slim)
FROM python:3.10

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \  # <--- Added git, as we'll be installing from GitHub
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CRITICAL: Force an older, known-compatible version of setuptools for stability
# And ensure pip and wheel are also up-to-date
RUN pip install --upgrade pip "setuptools<65" wheel

# Install PyTorch CPU wheels separately with the index-url.
# We'll let pip choose compatible torch/torchaudio based on the base Python 3.10 and the CPU index.
RUN pip install --no-cache-dir torch torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# CRITICAL CHANGE: Install openai-whisper directly from its GitHub repository
# This often bypasses problematic wheel building issues.
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

# Install remaining Python dependencies from requirements.txt,
# disabling build isolation for general stability.
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy app code
COPY . .

# Cloud Run expects port 8080. Uvicorn will pick this up from the environment variable.
ENV PORT 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
