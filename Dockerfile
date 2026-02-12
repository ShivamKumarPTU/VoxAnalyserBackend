# Use a full python image (not slim)
FROM python:3.10

WORKDIR /app

# System dependencies
# Install ffmpeg, build-essential, libsndfile1, and CRITICALLY 'git'
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt early
COPY requirements.txt .

# CRITICAL STEP: Upgrade pip, and explicitly install/pin setuptools and wheel.
# Pinning setuptools<65 is a common workaround for pkg_resources errors.
RUN pip install --upgrade pip "setuptools<65" wheel

# Install PyTorch CPU wheels separately.
# This ensures you get CPU-only versions and avoids conflicts with other packages.
RUN pip install --no-cache-dir torch torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# CRITICAL STEP: Install openai-whisper directly from its GitHub repository.
# This often bypasses problematic metadata generation issues with pip's build isolation.
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

# Install remaining Python dependencies from requirements.txt.
# Use --no-build-isolation to prevent similar pkg_resources issues with other packages.
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy your application code into the container
COPY . .

# Cloud Run expects port 8080. Uvicorn will pick this up from the environment variable.
ENV PORT 8080

# Command to run your FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
