import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
import whisper
import shutil
from transformers import pipeline
import traceback
import time
import asyncio
from contextlib import asynccontextmanager

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting server with 4GB RAM, 2 CPUs...")
    print("📦 Loading Whisper model (base)...")
    start = time.time()
    app.state.whisper_model = whisper.load_model("base")
    print(f"✅ Whisper model loaded in {time.time() - start:.2f}s")
    
    print("📦 Loading emotion model...")
    start = time.time()
    app.state.emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True
    )
    print(f"✅ Emotion model loaded in {time.time() - start:.2f}s")
    print("🎯 Server ready to accept requests!")
    yield
    # Cleanup
    print("👋 Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {
        "status": "Backend running in India region (asia-south1)",
        "memory": "4GB",
        "cpu": "2",
        "concurrency": "1"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):
    temp_path = None
    try:
        # Validate file type
        valid_extensions = (".wav", ".mp3", ".m4a", ".3gp", ".webm", ".ogg")
        if not file.filename.lower().endswith(valid_extensions):
            raise HTTPException(400, f"Invalid file type. Supported: {valid_extensions}")

        print(f"📁 Processing file: {file.filename}")
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            temp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        # Transcribe with Whisper
        print("🎤 Transcribing audio...")
        result = app.state.whisper_model.transcribe(
            temp_path,
            language="en",
            task="transcribe",
            fp16=False
        )
        
        segments_data = []
        print(f"📝 Processing {len(result.get('segments', []))} segments...")

        for segment in result.get("segments", []):
            text = segment.get("text", "").strip()
            if not text or len(text) < 2:  # Skip very short segments
                continue

            # Get emotion
            emotion_outputs = app.state.emotion_classifier(text)
            scores = emotion_outputs[0] if isinstance(emotion_outputs[0], list) else emotion_outputs
            
            if scores and isinstance(scores, list):
                top_emotion = max(scores, key=lambda x: x["score"])
                segments_data.append({
                    "start": round(segment.get("start", 0), 2),
                    "end": round(segment.get("end", 0), 2),
                    "text": text,
                    "emotion": top_emotion["label"],
                    "confidence": round(float(top_emotion["score"]), 3),
                    "all_emotions": {e["label"]: round(e["score"], 3) for e in scores[:3]}
                })

        print(f"✅ Processed {len(segments_data)} segments")
        return {
            "segments": segments_data,
            "total_segments": len(segments_data),
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR:")
        traceback.print_exc()
        raise HTTPException(500, str(e))
    
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
            print("🧹 Cleaned up temp file")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,  # Single worker for 1 concurrency
        limit_concurrency=1  # Match your concurrency setting
    )