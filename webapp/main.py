from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from PIL import Image, ImageDraw
import io
import base64
import torch
from ultralytics import YOLO
import os
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CORSMiddlewareStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

# Serve static files (frontend)
app.mount("/static", CORSMiddlewareStaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Lazy-init YOLO model to reduce cold start during app import
model = None

def get_model():
    global model
    if model is None:
        model = YOLO('yolov8n.pt')
    return model

class DetectionRequest(BaseModel):
    image_url: str
    threshold: float = 0.3

@app.post("/detect")
async def detect_objects(req: DetectionRequest):
    try:
        resp = requests.get(req.image_url, stream=True, timeout=8)
        image = Image.open(resp.raw).convert('RGB')
        with torch.no_grad():
            results = get_model()(image)
        object_info = []
        draw = ImageDraw.Draw(image)
        car_count = 0
        person_count = 0
        for r in results[0].boxes:
            conf = r.conf.item()
            if conf < req.threshold:
                continue
            cls = int(r.cls.item())
            class_name = get_model().names[cls]
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

@app.post("/detect_counts")
async def detect_counts(req: DetectionRequest):
    """Lightweight endpoint that returns only counts and objects without drawing image.
    Useful for heatmap density to save bandwidth.
    """
    try:
        resp = requests.get(req.image_url, stream=True, timeout=8)
        image = Image.open(resp.raw).convert('RGB')
        with torch.no_grad():
            results = get_model()(image)
        object_info = []
        car_count = 0
        person_count = 0
        for r in results[0].boxes:
            conf = r.conf.item()
            if conf < req.threshold:
                continue
            cls = int(r.cls.item())
            class_name = get_model().names[cls]
            box = r.xyxy[0].tolist()
            object_info.append({'class': class_name, 'confidence': conf, 'box': box})
            if class_name == 'car':
                car_count += 1
            if class_name == 'person':
                person_count += 1
        return JSONResponse({
            'objects': object_info,
            'traffic_assessment': {'cars': car_count, 'people': person_count}
        })
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Serve index.html at root
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/live")
def live():
    return FileResponse(os.path.join(STATIC_DIR, "live.html"))

@app.get("/density")
def density():
    return FileResponse(os.path.join(STATIC_DIR, "density.html"))

@app.get("/tracker")
def tracker():
    return FileResponse(os.path.join(STATIC_DIR, "tracker.html"))

@app.get("/proxy_image")
def proxy_image(url: str):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        content_type = r.headers.get('content-type', 'image/jpeg')
        return StreamingResponse(BytesIO(r.content), media_type=content_type, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return Response(content=f"Image fetch failed: {e}", status_code=400)

@app.post("/search_similar")
def search_similar(image_url: str = Form(...), target_image: UploadFile = File(...)):
    # Placeholder: always returns no match
    # You can implement feature matching or embedding comparison here
    return {"found": False}
