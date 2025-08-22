import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import tools  # Importación corregida

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
    # Placeholder de historial
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        # Levantar una excepción HTTP si la respuesta es un error (4xx o 5xx)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # Intentar devolver el detalle del error del servicio externo si es posible
        error_detail = response.json() if response.content else str(http_err)
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    except requests.exceptions.RequestException as req_err:
        # Para errores de conexión, timeouts, etc.
        raise HTTPException(status_code=503, detail=f"Service unavailable: {req_err}")

@app.post("/api/ingest")
def ingest():
    return {"status": "not_implemented"}

# --- Endpoints para Herramientas ---

@app.get("/api/tools")
def get_tools():
    """Devuelve la lista de definiciones de herramientas."""
    return tools.get_tool_definitions()

class ToolExecutionBody(BaseModel):
    name: str
    args: dict

@app.post("/api/tools/execute")
def execute_tool_endpoint(body: ToolExecutionBody):
    """Ejecuta una herramienta y devuelve el resultado."""
    result = tools.execute_tool(body.name, body.args)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result
