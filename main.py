import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
import whisper
import shutil
from transformers import pipeline
import traceback
import time
from pathlib import Path

app = FastAPI()

# Load models at startup with timing
print("🚀 Loading models...")
start_time = time.time()

print("📦 Loading Whisper model (tiny)...")
whisper_model = whisper.load_model("tiny")
print(f"✓ Whisper loaded in {time.time() - start_time:.2f}s")

print("📦 Loading emotion model...")
emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)
print(f"✓ Emotion model loaded in {time.time() - start_time:.2f}s")
print("✅ Server ready!")

@app.get("/")
def home():
    return {
        "status": "Emotion Analyzer Running",
        "region": "asia-south1 (Mumbai)",
        "model": "whisper-tiny"
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
            raise HTTPException(400, f"Invalid file type: {file.filename}")

        print(f"📁 Processing: {file.filename}")
        
        # Windows-safe temp file handling
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(file.filename).suffix,
            dir='/tmp/audio'  # Explicit temp directory
        ) as tmp:
            temp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        # Transcribe with tiny model (fast!)
        result = whisper_model.transcribe(
            temp_path,
            language="en",
            fp16=False,
            task="transcribe"
        )
        
        segments_data = []
        
        for segment in result.get("segments", []):
            text = segment.get("text", "").strip()
            if not text or len(text) < 2:
                continue

            # Get emotions
            emotion_outputs = emotion_classifier(text)
            scores = emotion_outputs[0] if isinstance(emotion_outputs[0], list) else emotion_outputs
            
            if scores:
                top_emotion = max(scores, key=lambda x: x["score"])
                segments_data.append({
                    "start": round(segment.get("start", 0), 2),
                    "end": round(segment.get("end", 0), 2),
                    "text": text,
                    "emotion": top_emotion["label"],
                    "confidence": round(top_emotion["score"], 3)
                })

        print(f"✓ Processed {len(segments_data)} segments")
        return {"segments": segments_data}

    except Exception as e:
        print("❌ Error:", str(e))
        traceback.print_exc()
        raise HTTPException(500, str(e))
    
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1
    )