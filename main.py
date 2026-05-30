# main.py
from fastapi import FastAPI, Query, HTTPException
import httpx

app = FastAPI(title="Number Info API")

@app.get("/api/number-info")
async def number_info(number: str = Query(..., description="Indian mobile number")):
    upstream_url = f"https://noobster-api-5xii.onrender.com/search?mobile={number}&key=mr_noobster"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(upstream_url, timeout=17.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to fetch number details")
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Check if status is success and data exists
    if data.get("status") != "success" or not isinstance(data.get("data"), dict):
        raise HTTPException(status_code=502, detail="Invalid response from number service")
    
    # Extract the data array from the response
    data_obj = data.get("data", {})
    results_array = data_obj.get("data", [])
    
    if not results_array:
        raise HTTPException(status_code=502, detail="No number details found in response")
    
    # Build final response with all results
    result = {
        "success": True,
        "total_results": data_obj.get("found", 0),
        "results": results_array,
        "channel": "free_inf_api"
    }
    
    return result

@app.get("/")
async def root():
    return {"message": "Number Info API. Use /api/number-info?number=7439312179"}
