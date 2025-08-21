import os
import sys
import json
import requests
from dotenv import load_dotenv

ASSISTANT_IDS = {
    "boardroom": "76f94782-5f1d-4ea0-8e69-294da3e1aefb",
    "investor":  "ff7afd85-51e0-4fdd-8ec5-a14508a100f9",
    "public":    "34747e20-39db-415e-bd80-597006f71a7a"
}

def usage():
    print("Usage: python3 call_dr.py [public|investor|boardroom] 'your question'")
    sys.exit(1)

def main():
    load_dotenv()
    dr_api_key = os.getenv("DR_API_KEY")
    dr_base_url = os.getenv("DR_BASE_URL")
    if not dr_api_key or not dr_base_url:
        print("Error: DR_API_KEY and DR_BASE_URL must be set in .env", file=sys.stderr)
        sys.exit(2)
    if len(sys.argv) < 3:
        usage()
    role = sys.argv[1].strip().lower()
    question = " ".join(sys.argv[2:]).strip()
    if role not in ASSISTANT_IDS:
        print(f"Unknown role: {role}")
        usage()
    assistant_id = ASSISTANT_IDS[role]
    url = dr_base_url.rstrip("/") + "/runs/wait"
    headers = {"x-api-key": dr_api_key, "Content-Type": "application/json"}
    body = {"assistant_id": assistant_id, "input": {"question": question}}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(3)
    if resp.status_code >= 400:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(resp.status_code)
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)

if __name__ == "__main__":
    main()