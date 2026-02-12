# Use a full python image (not slim)
FROM python:3.10

WORKDIR /app

# System dependencies
# Install build-essential for gcc/g++ and libsndfile1 for torchaudio/soundfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch CPU wheels
# Use specific versions that are known to work together.
# Ensure these versions are compatible with your transformers and whisper versions.
RUN pip install --no-cache-dir torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Cloud Run expects port 8080. Uvicorn will pick this up from the environment variable.
# The ENV PORT 8080 is redundant if Cloud Run sets it, but harmless.
# It's better to let Uvicorn use the $PORT environment variable provided by Cloud Run.
# Uvicorn by default listens on 0.0.0.0 and uses the PORT env var if --port is not specified.
# However, explicitly passing $PORT is safer in case of different Uvicorn versions or configurations.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
