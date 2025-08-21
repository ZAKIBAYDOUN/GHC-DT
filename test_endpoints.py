import httpx
import asyncio

URL = "http://127.0.0.1:8000"

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Boardroom
        resp1 = await client.post(f"{URL}/board/answer", json={"question": "Summarize veto rights & board composition with clause refs."})
        print("/board/answer:", resp1.status_code, resp1.json())

        # Investor
        resp2 = await client.post(f"{URL}/investor/answer", json={"question": "Capital required + CAPEX/working capital/contingency, with citations."})
        print("/investor/answer:", resp2.status_code, resp2.json())

        # Public
        resp3 = await client.post(f"{URL}/public/answer", json={"question": "What is live-dried flower and why does it matter?"})
        print("/public/answer:", resp3.status_code, resp3.json())

if __name__ == "__main__":
    asyncio.run(test_endpoints())
