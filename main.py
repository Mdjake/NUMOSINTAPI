# main.py
from fastapi import FastAPI, Query, HTTPException
import httpx

app = FastAPI(title="Number Info API")

@app.get("/api/number-info")
async def number_info(number: str = Query(..., description="Indian mobile number")):
    upstream_url = f"https://wasifali-indian-number-info.vercel.app/api?number={number}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(upstream_url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to fetch number details")
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Check if status is true and result exists
    if not data.get("status") or not isinstance(data.get("result"), dict):
        raise HTTPException(status_code=502, detail="Invalid response from number service")
    
    result_obj = data["result"]
    
    # Extract all numbered entries into a list
    all_results = []
    for key, value in result_obj.items():
        if key.isdigit():  # Only take numeric keys like "0", "1", "2", etc.
            # Remove 'developer' field from each result if it exists
            value.pop("developer", None)
            all_results.append(value)
    
    if not all_results:
        raise HTTPException(status_code=502, detail="No number details found in response")
    
    # Build final response with all results
    result = {
        "success": data["status"],      # rename status → success
        "total_results": len(all_results),
        "results": all_results,         # array of all number details
        "channel": "free_inf_api"
    }
    
    return result

@app.get("/")
async def root():
    return {"message": "Number Info API. Use /api/number-info?number=7439312179"}