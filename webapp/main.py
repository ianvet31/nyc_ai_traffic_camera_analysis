
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from PIL import Image, ImageDraw
import io
import base64
import torch
from ultralytics import YOLO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load lightweight model (YOLOv8n)
model = YOLO('yolov8n.pt')

class DetectionRequest(BaseModel):
    image_url: str
    threshold: float = 0.3

@app.post("/detect")
async def detect_objects(req: DetectionRequest):
    try:
        image = Image.open(requests.get(req.image_url, stream=True).raw).convert('RGB')
        results = model(image)
        object_info = []
        draw = ImageDraw.Draw(image)
        car_count = 0
        person_count = 0
        for r in results[0].boxes:
            conf = r.conf.item()
            if conf < req.threshold:
                continue
            cls = int(r.cls.item())
            class_name = model.names[cls]
            box = r.xyxy[0].tolist()
            draw.rectangle(box, outline='red', width=2)
            object_info.append({'class': class_name, 'confidence': conf, 'box': box})
            if class_name == 'car':
                car_count += 1
            if class_name == 'person':
                person_count += 1
        # Encode image to base64
        buf = io.BytesIO()
        image.save(buf, format='JPEG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return JSONResponse({
            'image': img_b64,
            'objects': object_info,
            'traffic_assessment': {
                'cars': car_count,
                'people': person_count
            }
        })
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse("static/index.html")
