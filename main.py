from fastapi import FastAPI, File, UploadFile
import whisper
import shutil
import os
from transformers import pipeline
import traceback
import uvicorn
app = FastAPI()

whisper_model = whisper.load_model("base")

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)

@app.get("/")
def home():
    return {"status": "Backend running"}

@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):

    try:
        if not file.filename.endswith((".wav", ".mp3", ".m4a",".3gp")):
            return {"error": "Invalid file type"}

        file_path = f"temp_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = whisper_model.transcribe(file_path)

        segments_data = []

        for segment in result.get("segments", []):
            text = segment.get("text", "")
            start = segment.get("start", 0)
            end = segment.get("end", 0)

            if text.strip() == "":
                continue

            emotion_outputs = emotion_classifier(text)

            # Handle both possible return formats
            if isinstance(emotion_outputs, list):
                if isinstance(emotion_outputs[0], list):
                    scores = emotion_outputs[0]
                elif isinstance(emotion_outputs[0], dict):
                    scores = emotion_outputs
                else:
                    continue
            else:
                continue

            top_emotion = max(scores, key=lambda x: x["score"])

            segments_data.append({
                "start": start,
                "end": end,
                "text": text,
                "emotion": top_emotion["label"],
                "confidence": float(top_emotion["score"])
            })

        os.remove(file_path)

        return {"segments": segments_data}

    except Exception as e:
        print("FULL ERROR TRACE:")
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
