import os
import base64
import io
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title="MySketch Proxy")
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
    image_data = await file.read()
    image_b64 = base64.b64encode(image_data).decode()

    img = Image.open(io.BytesIO(image_data))
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
    async with httpx.AsyncClient(timeout=180) as client:
        try:
            resp = await client.post(f"{FOOOCUS_URL}/v2/generate", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Fooocus error: %s", e)
            raise HTTPException(status_code=502, detail=f"Fooocus API error: {e}")

    data = resp.json()
    logger.info("Fooocus response keys: %s", list(data.keys()))

    try:
        result_b64 = data["images"][0]["base64"]
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected Fooocus response: %s", data)
        raise HTTPException(status_code=502, detail="Unexpected response from Fooocus")

    result_bytes = base64.b64decode(result_b64)
    return Response(content=result_bytes, media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
