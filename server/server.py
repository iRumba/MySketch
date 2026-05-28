import os
import base64
import io
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mysketch")

# === CONFIG ===
FOOOCUS_URL = os.getenv("FOOOCUS_URL", "http://localhost:8888")
PROMPT = os.getenv(
    "PROMPT",
    "finish this sketch, make it a complete cute illustration, "
    "add creative details, harmonious colors, professional digital art"
)
NEGATIVE_PROMPT = os.getenv("NEGATIVE_PROMPT", "ugly, deformed, blurry, low quality, bad anatomy")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()

app = FastAPI(title="MySketch Proxy", lifespan=lifespan)
# Shared HTTP client for Fooocus API calls
http_client = httpx.AsyncClient(timeout=180)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/dorisuy")
async def dorisuy(file: UploadFile = File(...)):
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    image_data = await file.read()
    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    image_b64 = base64.b64encode(image_data).decode()

    try:
        img = Image.open(io.BytesIO(image_data))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
    if img.size != (512, 512):
        img = img.resize((512, 512), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_b64 = base64.b64encode(buf.getvalue()).decode()

    payload = {
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "style_selections": ["Fooocus V2", "Fooocus Enhance"],
        "performance_selection": "Speed",
        "image_number": 1,
        "input_image": image_b64,
        "controlnet_image": image_b64,
        "controlnet_type": "ImagePrompt",
    }

    logger.info("Sending to Fooocus: %s", FOOOCUS_URL)
    try:
        resp = await http_client.post(f"{FOOOCUS_URL}/v2/generate", json=payload)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("Fooocus error: %s", e)
        raise HTTPException(status_code=502, detail=f"Fooocus API error: {e}")

    data = resp.json()
    logger.info("Fooocus response keys: %s", list(data.keys()))

    try:
        result_b64 = data["images"][0]["base64"]
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected Fooocus response keys: %s", list(data.keys()))
        raise HTTPException(status_code=502, detail="Unexpected response from Fooocus")

    result_bytes = base64.b64decode(result_b64)
    return Response(content=result_bytes, media_type="image/png")


# === Serve client static files ===
CLIENT_DIR = os.path.join(os.path.dirname(__file__), "..", "client")
if os.path.isdir(CLIENT_DIR):
    app.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="client")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
