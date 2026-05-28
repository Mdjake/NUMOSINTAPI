# main.py
from fastapi import FastAPI, Query, HTTPException
import httpx
from typing import Dict, Any

app = FastAPI(title="Number Info API", description="Get Indian mobile number details")

@app.get("/api/number-info")
async def number_info(number: str = Query(..., description="Indian mobile number")):
    upstream_url = f"https://vsnshika-info-number.deeshantjatav90.workers.dev/?key=LOVEBxROTHER&num={number}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(upstream_url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="Failed to fetch number details")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")
    
    number_detail = data.get("result")
    if not number_detail:
        raise HTTPException(status_code=502, detail="Invalid response from number service")
    
    # Build response: success + all number_detail fields + channel
    result = {
        "success": data.get("status", True),   # keep original success (default True)
        **number_detail,                        # flatten all fields from number_detail
        "channel": "free_inf_api"
    }
    return result

@app.get("/")
async def root():
    return {"message": "Number Info API. Use /api/number-info?number=7439312179"}
