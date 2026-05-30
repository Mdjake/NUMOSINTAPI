# main.py
from fastapi import FastAPI, Query
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Number Info API")

# Get API keys from environment variable and convert to list
VALID_API_KEYS_RAW = os.getenv("VALID_API_KEYS", "")
# Split by comma and remove any whitespace
VALID_API_KEYS = [key.strip() for key in VALID_API_KEYS_RAW.split(",") if key.strip()]

print(f"Loaded API keys: {VALID_API_KEYS}")  # Debug: see what keys are loaded

@app.get("/api/number-info")
async def number_info(
    number: str = Query(..., description="Indian mobile number"),
    apikey: str = Query(None, description="API key for authentication")
):
    # Check if API key is missing or invalid
    if not apikey or apikey not in VALID_API_KEYS:
        return {
            "success": False,
            "message": "Contact @helper_man on Telegram to get your free API key",
            "error": "Invalid or missing API key"
        }
    
    upstream_url = f"https://noobster-api-5xii.onrender.com/search?mobile={number}&key=mr_noobster"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(upstream_url, timeout=17.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError:
            return {
                "success": False,
                "message": "Contact @helper_man for support",
                "error": "Failed to fetch number details"
            }
        except Exception:
            return {
                "success": False,
                "message": "Contact @helper_man for support", 
                "error": "Internal server error"
            }
    
    # Check if status is success and data exists
    if data.get("status") != "success" or not isinstance(data.get("data"), dict):
        return {
            "success": False,
            "message": "Contact @helper_man for support",
            "error": "please give some time api is in maintainance will be fixed soon"
        }
    
    # Extract the data array from the response
    data_obj = data.get("data", {})
    results_array = data_obj.get("data", [])
    
    if not results_array:
        return {
            "success": False,
            "message": "Contact @helper_man for support",
            "error": "No number details found in response"
        }
    
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
    return {
        "message": "Number Info API",
        "usage": "/api/number-info?number=7439312179&apikey=YOUR_API_KEY",
        "get_api_key": "Contact @helper_man on Telegram for a free api key",
        "api_keys_loaded": len(VALID_API_KEYS)  # Shows how many keys are loaded
    }
