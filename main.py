# main.py
from fastapi import FastAPI, Query
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Number Info API")

# Get API keys from environment variable and convert to list
VALID_API_KEYS_RAW = os.getenv("VALID_API_KEYS", "")
VALID_API_KEYS = [key.strip() for key in VALID_API_KEYS_RAW.split(",") if key.strip()]

print(f"Loaded API keys: {VALID_API_KEYS}")

# Internal API configuration
INTERNAL_PRIMARY_API = "https://number-to-api-team-only.vercel.app/api/index.js"
INTERNAL_PRIMARY_KEY = "team6months"
INTERNAL_BACKUP_API = "https://noobster-api-5xii.onrender.com/search"
INTERNAL_BACKUP_KEY = "mr_noobster"

def transform_to_unified_format(data: dict, number: str, source: str) -> dict:
    """Transform any API response to unified @helper_man format"""
    
    if source == "primary":
        # Extract results from primary API
        results = data.get("results", [])
        return {
            "status": "success",
            "developer": "@helper_man",  # Override original developer
            "queried_number": number,
            "timestamp": datetime.now().isoformat() + "Z",
            "results": results
        }
    
    elif source == "backup":
        # Extract from backup API's nested structure
        data_obj = data.get("data", {})
        results = data_obj.get("data", [])
        return {
            "status": "success",
            "developer": "@helper_man",
            "queried_number": number,
            "timestamp": datetime.now().isoformat() + "Z",
            "results": results
        }
    
    return None

async def fetch_from_internal_primary(number: str):
    """Internal: Fetch from primary data source"""
    url = f"{INTERNAL_PRIMARY_API}?api_key={INTERNAL_PRIMARY_KEY}&number={number}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") == "success" and data.get("results"):
                # Transform primary response to unified format
                unified = transform_to_unified_format(data, number, "primary")
                return {"success": True, "data": unified}
            return {"success": False}
        except Exception:
            return {"success": False}

async def fetch_from_internal_backup(number: str):
    """Internal: Fetch from backup data source"""
    url = f"{INTERNAL_BACKUP_API}?mobile={number}&key={INTERNAL_BACKUP_KEY}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=17.0)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") == "success" and isinstance(data.get("data"), dict):
                data_obj = data.get("data", {})
                results_array = data_obj.get("data", [])
                
                if results_array:
                    # Transform backup response to unified format
                    unified = transform_to_unified_format(data, number, "backup")
                    return {"success": True, "data": unified}
            return {"success": False}
        except Exception:
            return {"success": False}

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
    
    # Try primary internal source first
    result = await fetch_from_internal_primary(number)
    
    # If primary fails, try backup
    if not result["success"]:
        result = await fetch_from_internal_backup(number)
    
    # If both fail
    if not result["success"]:
        return {
            "status": "error",
            "success": False,
            "developer": "@helper_man",
            "message": "We are working on fixing the API. It will be fixed soon.",
            "error": "Service temporarily unavailable",
            "queried_number": number,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    # Return unified response
    return result["data"]

@app.get("/")
async def root():
    return {
        "message": "Number Info API",
        "developer": "@helper_man",
        "usage": "/api/number-info?number=7439312179&apikey=YOUR_API_KEY",
        "get_api_key": "Contact @helper_man on Telegram for a free api key",
        "status": "active"
    }
