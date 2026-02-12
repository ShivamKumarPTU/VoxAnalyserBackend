FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

# Install torch CPU first
RUN pip install --no-cache-dir torch==2.1.2+cpu torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install rest
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/audio && chmod 777 /tmp/audio

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
