import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# Cargar variables de entorno (root y local)
load_dotenv("../.env")
load_dotenv()
DR_BASE_URL = os.getenv("DR_BASE_URL")
DR_API_KEY = os.getenv("DR_API_KEY")

if not DR_BASE_URL or not DR_API_KEY:
    raise RuntimeError("DR_BASE_URL y DR_API_KEY deben estar configurados en .env")

ASSISTANT_IDS = {
    "boardroom": "76f94782-5f1d-4ea0-8e69-294da3e1aefb",
    "investor": "ff7afd85-51e0-4fdd-8ec5-a14508a100f9",
    "public": "34747e20-39db-415e-bd80-597006f71a7a",
}

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskBody(BaseModel):
    audience: str
    question: str

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/history")
def history():
    # Placeholder de historial (puedes conectarlo a DR si hay endpoint específico)
    return {"history": []}

@app.post("/api/ask")
def ask(body: AskBody):
    audience = body.audience.lower()
    if audience not in ASSISTANT_IDS:
        raise HTTPException(status_code=400, detail="Invalid audience")
    url = f"{DR_BASE_URL}/runs/wait"
    headers = {"x-api-key": DR_API_KEY, "Content-Type": "application/json"}
    payload = {
        "assistant_id": ASSISTANT_IDS[audience],
        "input": {"question": body.question},
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json(), response.status_code

@app.post("/api/ingest")
def ingest():
    return {"status": "not_implemented"}