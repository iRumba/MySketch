import base64
import os
import logging
import argparse
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mysketch")

# === CONFIG ===
def get_fooocus_url() -> str:
    """Get Gradio/Colab API URL.

    Precedence: --fooocus-url CLI arg > FOOOCUS_URL env var > default
    """
    return os.environ.get("FOOOCUS_URL", "http://localhost:8888")

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
    """
    Принимает рисунок пользователя (PNG),
    отправляет в Gradio API на Colab (через /api/predict),
    возвращает готовое изображение.
    """
    image_data = await file.read()
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    # Gradio API принимает base64 в JSON
    image_b64 = base64.b64encode(image_data).decode()

    payload = {
        "data": [
            {
                "background": None,
                "layers": [],
                "composite": image_b64
            },
            ""  # prompt (пустой → будет default)
        ]
    }

    url = get_fooocus_url()
    logger.info("Sending to Gradio API: %s", url)

    try:
        resp = await http_client.post(
            f"{url}/api/predict",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Gradio API error: %s", e.response.text)
        raise HTTPException(status_code=502, detail=f"Colab API error: {e.response.text}")
    except httpx.RequestError as e:
        logger.error("Connection error: %s", e)
        raise HTTPException(status_code=502, detail=f"Cannot connect to Colab: {e}")

    data = resp.json()
    try:
        # Gradio возвращает список результатов, первый — изображение
        result_b64 = data["data"][0]
        # Если это строка вида "data:image/png;base64,..." — обрезаем префикс
        if result_b64.startswith("data:"):
            result_b64 = result_b64.split(",", 1)[1]
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected Gradio response: %s", data)
        raise HTTPException(status_code=502, detail="Unexpected response from Gradio")

    result_bytes = base64.b64decode(result_b64)
    return Response(content=result_bytes, media_type="image/png")


# === Serve client static files ===
CLIENT_DIR = os.path.join(os.path.dirname(__file__), "..", "client")
if os.path.isdir(CLIENT_DIR):
    app.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="client")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MySketch - AI sketch completion proxy")
    parser.add_argument(
        "-u", "--fooocus-url",
        help="Gradio/Colab API URL (e.g. https://xxxx.gradio.live)"
    )
    args = parser.parse_args()

    if args.fooocus_url:
        os.environ["FOOOCUS_URL"] = args.fooocus_url

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
