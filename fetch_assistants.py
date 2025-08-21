import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

DR_BASE_URL = os.getenv("DR_BASE_URL")
DR_API_KEY = os.getenv("DR_API_KEY")
DEFAULT_GRAPH_ID = os.getenv("DEFAULT_GRAPH_ID", "ghc")

if not DR_API_KEY:
    print("Missing DR_API_KEY in .env. Aborting.", file=sys.stderr)
    sys.exit(1)

HEADERS = {"x-api-key": DR_API_KEY}

def pick_id(items, audience, name_kw):
    for it in items:
        meta = it.get("metadata") or {}
        name = (it.get("name") or "").lower()
        if meta.get("audience", "").lower() == audience:
            return it.get("assistant_id") or it.get("id")
        if name_kw in name:
            return it.get("assistant_id") or it.get("id")
    return None

async def main():
    url = f"{DR_BASE_URL.rstrip('/')}/assistants/search"
    payload = {"graph_id": DEFAULT_GRAPH_ID, "limit": 50}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json=payload)
        try:
            data = resp.json()
        except Exception:
            print(json.dumps({"error": "Non-json response", "text": resp.text}), file=sys.stderr)
            sys.exit(2)
    items = None
    if isinstance(data, dict):
        for k in ("assistants", "data", "results", "items"):
            if k in data and isinstance(data[k], list):
                items = data[k]
                break
        if items is None and any(isinstance(v, list) for v in data.values()):
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
    if items is None and isinstance(data, list):
        items = data
    if not items:
        print(json.dumps({"error": "No assistants found", "response": data}), file=sys.stderr)
        sys.exit(3)

    boardroom = pick_id(items, "board", "board")
    investor  = pick_id(items, "investor", "investor")
    public    = pick_id(items, "public", "public")

    ids = {"boardroom": boardroom, "investor": investor, "public": public}

    # Fallback: asigna por orden si no hay coincidencias
    if not ids["boardroom"] or not ids["investor"] or not ids["public"]:
        ordered = [a.get("assistant_id") or a.get("id") for a in items][:3]
        if len(ordered) < 3:
            print(json.dumps({"error":"Missing audience(s)", "missing":["boardroom","investor","public"], "available_assistants":items}))
            sys.exit(1)
        ids["boardroom"], ids["investor"], ids["public"] = ordered

    print(json.dumps(ids))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
