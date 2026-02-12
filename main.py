import os
import tempfile
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
import whisper
import shutil
from transformers import pipeline
from pathlib import Path

app = FastAPI()

whisper_model = None
emotion_classifier = None

@app.on_event("startup")
def load_models():
    global whisper_model, emotion_classifier

    print("🚀 Loading models...")
    start = time.time()

    whisper_model = whisper.load_model("tiny")
    print(f"Whisper loaded in {time.time()-start:.2f}s")

    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True
    )
    print(f"Emotion model loaded in {time.time()-start:.2f}s")
    print("✅ Models ready")


@app.get("/")
def home():
    return {"status": "running on cloud run"}


@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):
    temp_path = None

    try:
        valid_extensions = (".wav", ".mp3", ".m4a", ".webm", ".ogg")
        if not file.filename.lower().endswith(valid_extensions):
            raise HTTPException(400, "Invalid file type")

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix
        ) as tmp:
            temp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        result = whisper_model.transcribe(
            temp_path,
            language="en",
            fp16=False
        )

        segments_data = []

        for segment in result.get("segments", []):
            text = segment.get("text", "").strip()
            if not text:
                continue

            scores = emotion_classifier(text)[0]
            top = max(scores, key=lambda x: x["score"])

            segments_data.append({
                "start": round(segment["start"], 2),
                "end": round(segment["end"], 2),
                "text": text,
                "emotion": top["label"],
                "confidence": round(top["score"], 3)
            })

        return {"segments": segments_data}

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
