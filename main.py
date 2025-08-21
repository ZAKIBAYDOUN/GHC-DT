from typing import Dict, Any, List
import os
import re
import hashlib

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv


load_dotenv()

DR_BASE_URL = os.getenv("DR_BASE_URL")
DR_API_KEY = os.getenv("DR_API_KEY")

if not DR_BASE_URL:
    raise RuntimeError("DR_BASE_URL is required in the environment")

if not DR_API_KEY:
    raise RuntimeError("DR_API_KEY is required in the environment")

ASSISTANT_IDS = {
    "boardroom": "76f94782-5f1d-4ea0-8e69-294da3e1aefb",
    "investor":  "ff7afd85-51e0-4fdd-8ec5-a14508a100f9",
    "public":    "34747e20-39db-415e-bd80-597006f71a7a",
}

HEADERS = {"x-api-key": DR_API_KEY, "content-type": "application/json"}

app = FastAPI(title="GHC-DT Proxy")
@app.get("/")
def root():
    return {
        "message": "GHC Proxy activo. Usa /docs para la documentación interactiva o POST a /board/answer, /investor/answer, /public/answer.",
        "docs": "/docs",
        "endpoints": [
            {"POST": "/board/answer"},
            {"POST": "/investor/answer"},
            {"POST": "/public/answer"}
        ]
    }


class QuestionIn(BaseModel):
    question: str


def _contains_sensitive_tokens(text: str) -> bool:
    if not text:
        return False
    # simple heuristics: presence of 'SHA' or 'financial' (case-insensitive)
    return bool(re.search(r"\b(SHA|sha|financial)\b", text))


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _extract_answer_and_citations(run_resp: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to normalize different possible run response shapes into {answer, citations}.

    The DigitalRoots response may vary; look for sensible places: 'output', 'result', 'answers', 'items', 'text', or any 'content' fields.
    Citations are expected as lists of dicts or strings in 'citations' or 'sources'.
    """
    answer = None
    citations: List[Any] = []

    # Common shapes
    # 1) run_resp['output']['text'] or run_resp['output']['answer']
    out = run_resp.get("output") if isinstance(run_resp, dict) else None
    if out:
        if isinstance(out, dict):
            for key in ("answer", "text", "content"):
                if key in out and isinstance(out[key], str):
                    answer = out[key]
                    break
        elif isinstance(out, str):
            answer = out

    # 2) direct fields
    if not answer:
        for key in ("answer", "text", "result"):
            v = run_resp.get(key) if isinstance(run_resp, dict) else None
            if isinstance(v, str):
                answer = v
                break

    # 3) nested items that may contain blocks with 'text' keys
    if not answer and isinstance(run_resp, dict):
        # look for 'items' or 'outputs'
        for list_key in ("items", "outputs", "blocks"):
            lst = run_resp.get(list_key)
            if isinstance(lst, list) and lst:
                for it in lst:
                    if isinstance(it, dict):
                        for key in ("text", "content", "answer"):
                            if key in it and isinstance(it[key], str):
                                answer = it[key]
                                break
                    if answer:
                        break
            if answer:
                break

    # Citations
    if isinstance(run_resp, dict):
        for cit_key in ("citations", "sources", "references"):
            c = run_resp.get(cit_key)
            if isinstance(c, list):
                citations = c
                break

    # final fallback: coerce to strings
    if not answer:
        # try to stringify plausible textual parts
        try:
            answer = str(run_resp)
        except Exception:
            answer = ""

    return {"answer": answer or "", "citations": citations}


async def _call_runs_wait(assistant_id: str, question: str) -> Dict[str, Any]:
    url = DR_BASE_URL.rstrip("/") + "/runs/wait"
    payload = {"assistant_id": assistant_id, "input": {"question": question}}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=HEADERS, json=payload)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Upstream error: {resp.status_code}: {resp.text}")
        return resp.json()


@app.post("/board/answer")
async def board_answer(q: QuestionIn):
    run = await _call_runs_wait(ASSISTANT_IDS["boardroom"], q.question)
    norm = _extract_answer_and_citations(run)
    return norm


@app.post("/investor/answer")
async def investor_answer(q: QuestionIn):
    run = await _call_runs_wait(ASSISTANT_IDS["investor"], q.question)
    norm = _extract_answer_and_citations(run)
    # investor requires citations
    if not norm.get("citations"):
        raise HTTPException(status_code=422, detail="Investor answers must include citations.")
    # append disclaimer
    ans = norm.get("answer", "")
    if ans and not ans.endswith("."):
        ans = ans + "."
    ans = ans + " — Information only; not investment advice."
    norm["answer"] = ans
    return norm


@app.post("/public/answer")
async def public_answer(q: QuestionIn):
    run = await _call_runs_wait(ASSISTANT_IDS["public"], q.question)
    norm = _extract_answer_and_citations(run)
    ans = norm.get("answer", "")
    # sensitive check
    if _contains_sensitive_tokens(q.question):
        return {"answer": "This question appears to request sensitive financial or hashed information; cannot provide publicly.", "citations": []}
    # truncate
    if len(ans) > 800:
        norm["answer"] = _truncate(ans, 800)
    return norm


@app.get("/internal/assistants")
def internal_assistants():
    return {"base_url": DR_BASE_URL, "assistant_ids": ASSISTANT_IDS}
from fastapi import FastAPI, Request, HTTPException
import httpx
import os
from dotenv import load_dotenv
from typing import Any, Dict, List

load_dotenv()

app = FastAPI()

# Config from env
DR_BASE_URL = os.getenv("DR_BASE_URL", "https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app")
DR_API_KEY = os.getenv("DR_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))

HEADERS = {"x-api-key": DR_API_KEY} if DR_API_KEY else {}

# Hardcoded assistant IDs provided by user
ASSISTANT_IDS: Dict[str, str] = {
    "boardroom": "76f94782-5f1d-4ea0-8e69-294da3e1aefb",
    "investor":  "ff7afd85-51e0-4fdd-8ec5-a14508a100f9",
    "public":    "34747e20-39db-415e-bd80-597006f71a7a",
}


def _extract_answer_and_citations(resp: Any) -> Dict[str, Any]:
    """Normalize backend response into {answer: str, citations: [..]}"""
    answer = ""
    citations: List[Dict[str, str]] = []

    if isinstance(resp, dict):
        # common text fields
        for k in ("answer", "text", "output", "result", "content"):
            if k in resp and isinstance(resp[k], str) and resp[k].strip():
                answer = resp[k].strip()
                break

        # nested structures
        if not answer:
            for k in ("output", "results", "data", "response"):
                v = resp.get(k)
                if isinstance(v, str) and v.strip():
                    answer = v.strip()
                    break
                if isinstance(v, dict):
                    nested = _extract_answer_and_citations(v)
                    if nested.get("answer"):
                        answer = nested.get("answer")
                        citations = nested.get("citations", [])
                        break
                if isinstance(v, list) and v:
                    for item in v:
                        if isinstance(item, str) and item.strip():
                            answer = item.strip()
                            break
                        if isinstance(item, dict):
                            nested = _extract_answer_and_citations(item)
                            if nested.get("answer"):
                                answer = nested.get("answer")
                                citations = nested.get("citations", [])
                                break
                    if answer:
                        break

        # extract citations if present
        for key in ("citations", "references", "sources", "refs"):
            if key in resp and isinstance(resp[key], list):
                for c in resp[key]:
                    if isinstance(c, dict):
                        citations.append({
                            "source": c.get("source", ""),
                            "section": c.get("section", ""),
                            "clause": c.get("clause", ""),
                            "url": c.get("url", ""),
                        })
                if citations:
                    break

    # defaults
    return {"answer": answer or "", "citations": citations}


async def _call_runs_wait(assistant_id: str, question: str) -> Any:
    url = f"{DR_BASE_URL.rstrip('/')}/runs/wait"
    payload = {"assistant_id": assistant_id, "input": {"question": question}}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=HEADERS, json=payload)
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "text": resp.text}


@app.post("/board/answer")
async def board_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")
    assistant_id = ASSISTANT_IDS.get("boardroom")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Boardroom assistant_id not configured")
    resp = await _call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    return normalized


@app.post("/investor/answer")
async def investor_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")
    assistant_id = ASSISTANT_IDS.get("investor")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Investor assistant_id not configured")
    resp = await _call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    # investor rule: require citations
    if not normalized.get("citations"):
        raise HTTPException(status_code=422, detail="Response did not include citations/references")
    # append disclaimer
    if normalized.get("answer"):
        normalized["answer"] = normalized["answer"] + "\n\n— Information only; not investment advice."
    else:
        normalized["disclaimer"] = "— Information only; not investment advice."
    return normalized


@app.post("/public/answer")
async def public_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")

    # sensitive check
    qlow = question.lower()
    sensitive_keywords = ["sha", "financial", "financials", "balance sheet", "income statement", "cashflow"]
    if any(k in qlow for k in sensitive_keywords):
        return {"answer": "This information is restricted. Please contact Investor Relations.", "citations": []}

    assistant_id = ASSISTANT_IDS.get("public")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Public assistant_id not configured")
    resp = await _call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    ans = normalized.get("answer", "")
    if len(ans) > 800:
        normalized["answer"] = ans[:800] + "…"
    return normalized


@app.get("/internal/assistants")
async def internal_assistants():
    return {"DR_BASE_URL": DR_BASE_URL, "ASSISTANT_IDS": ASSISTANT_IDS}
from fastapi import FastAPI, Request, HTTPException
import httpx
import os
import subprocess
import json
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Config
DR_BASE_URL = os.getenv("DR_BASE_URL", "https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app")
DEFAULT_GRAPH_ID = os.getenv("DEFAULT_GRAPH_ID", "ghc")
DR_API_KEY = os.getenv("DR_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))

HEADERS = {"x-api-key": DR_API_KEY} if DR_API_KEY else {}

# Will be set at startup by running fetch_assistants.py
ASSISTANT_IDS: Dict[str, str] = {"boardroom": "", "investor": "", "public": ""}


def run_fetch_assistants() -> Dict[str, str]:
    """Run fetch_assistants.py as a subprocess and return the JSON mapping."""
    try:
        res = subprocess.run(["python3", "fetch_assistants.py"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print("fetch_assistants.py failed:", e.stderr or e.stdout)
        raise
    out = res.stdout.strip()
    try:
        data = json.loads(out)
    except Exception as e:
        print("Failed to parse JSON from fetch_assistants.py output:", out)
        raise
    return data


def _extract_answer_and_citations(resp: Any) -> Dict[str, Any]:
    # Safe mapping to {answer, citations}
    answer = ""
    citations: List[Dict[str, str]] = []

    if isinstance(resp, dict):
        # common textual fields
        for k in ("answer", "text", "output", "result"):
            if k in resp and isinstance(resp[k], str):
                answer = resp[k]
                break

        # sometimes nested
        if not answer:
            for k in ("output", "results", "data", "response"):
                v = resp.get(k)
                if isinstance(v, str):
                    answer = v
                    break
                if isinstance(v, dict):
                    nested = _extract_answer_and_citations(v)
                    if nested.get("answer"):
                        answer = nested["answer"]
                        citations = nested.get("citations", [])
                        break
                if isinstance(v, list) and v:
                    for item in v:
                        if isinstance(item, str) and not answer:
                            answer = item
                            break

        # citations search
        for key in ("citations", "references", "sources", "refs"):
            if key in resp and isinstance(resp[key], list):
                for c in resp[key]:
                    if isinstance(c, dict):
                        citations.append({
                            "source": c.get("source", ""),
                            "section": c.get("section", ""),
                            "clause": c.get("clause", ""),
                            "url": c.get("url", ""),
                        })
                if citations:
                    break

    # ensure defaults
    return {"answer": answer or "", "citations": citations}


@app.on_event("startup")
def startup_event():
    # fetch assistant ids by running fetch_assistants.py
    if not DR_API_KEY:
        print("Missing DR_API_KEY in environment; fetch_assistants will fail until DR_API_KEY is set in .env")
        return
    try:
        data = run_fetch_assistants()
    except Exception:
        print("Failed to retrieve assistant IDs at startup.")
        raise
    for k in ("boardroom", "investor", "public"):
        ASSISTANT_IDS[k] = data.get(k, "")
    missing = [k for k, v in ASSISTANT_IDS.items() if not v]
    if missing:
        raise RuntimeError(f"Missing assistant ids for: {missing}")
    print("Loaded ASSISTANT_IDS:", ASSISTANT_IDS)


async def call_runs_wait(assistant_id: str, question: str) -> Dict[str, Any]:
    url = f"{DR_BASE_URL.rstrip('/')}/runs/wait"
    payload = {"assistant_id": assistant_id, "input": {"question": question}}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json=payload, timeout=60.0)
        try:
            data = resp.json()
        except Exception:
            data = {"status_code": resp.status_code, "text": resp.text}
        return data


@app.post("/board/answer")
async def board_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")
    assistant_id = ASSISTANT_IDS.get("boardroom")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Boardroom assistant_id not configured")
    resp = await call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    return normalized


@app.post("/investor/answer")
async def investor_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")
    assistant_id = ASSISTANT_IDS.get("investor")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Investor assistant_id not configured")
    resp = await call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    if not normalized.get("citations"):
        raise HTTPException(status_code=422, detail="Response did not include citations/references")
    # append disclaimer
    if normalized.get("answer"):
        normalized["answer"] = normalized["answer"] + "\n\n— Information only; not investment advice."
    else:
        normalized["disclaimer"] = "— Information only; not investment advice."
    return normalized


@app.post("/public/answer")
async def public_answer(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")
    # sensitive check
    qlow = question.lower()
    sensitive = ["sha", "financial", "financials", "balance sheet", "income statement", "cashflow", "ssn", "secret", "salary"]
    if any(k in qlow for k in sensitive):
        return {"answer": "This information is restricted. Please contact Investor Relations.", "citations": []}
    assistant_id = ASSISTANT_IDS.get("public")
    if not assistant_id:
        raise HTTPException(status_code=500, detail="Public assistant_id not configured")
    resp = await call_runs_wait(assistant_id, question)
    normalized = _extract_answer_and_citations(resp)
    ans = normalized.get("answer", "")
    if len(ans) > 800:
        normalized["answer"] = ans[:800] + "…"
    return normalized



@app.get("/internal/assistants")
async def internal_assistants():
    return {"DR_BASE_URL": DR_BASE_URL, "ASSISTANT_IDS": ASSISTANT_IDS}

