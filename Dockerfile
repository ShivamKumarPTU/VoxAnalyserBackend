# Use a full python image (not slim)
FROM python:3.10

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt early
COPY requirements.txt .

# CRITICAL: Force an older, known-compatible version of setuptools for stability
# And ensure pip and wheel are also up-to-date
RUN pip install --upgrade pip "setuptools<65" wheel

# Install PyTorch CPU wheels separately with the index-url.
# This prevents pip from trying to install GPU versions and ensures specific versions.
# We'll let pip choose compatible torch/torchaudio based on the base Python 3.10 and the CPU index.
# We're removing explicit version numbers here as per your request,
# but know that specific versions (like torch==2.1.2+cpu) are often more stable.
# If this fails, you might need to re-introduce specific versions here.
RUN pip install --no-cache-dir torch torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the Python dependencies from requirements.txt,
# disabling build isolation to prevent pkg_resources errors.
# This includes openai-whisper.
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy app code
COPY . .

# Cloud Run expects port 8080. Uvicorn will pick this up from the environment variable.
ENV PORT 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
