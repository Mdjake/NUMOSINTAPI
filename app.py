
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import requests
import re
from datetime import datetime
import os

app = FastAPI()

# ENABLE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIG
PROXY_API_KEY = os.getenv(
    "PROXY_API_KEY",
    "GHOST-PROXY-KEY-2024"
)

MAIN_API_KEY = os.getenv("MAIN_API_KEY")

MAIN_API_URL = (
    "http://numapi-production.up.railway.app/search"
)

# HOME ROUTE
@app.get("/")
async def home():

    return {
        "service": "GHOST PROXY API",
        "status": "active",
        "version": "2.0"
    }

# LOOKUP ROUTE
@app.get("/api/lookup")
async def lookup(

    mobile: str = Query(""),
    apikey: str = Query("")

):

    # CLEAN MOBILE
    mobile = re.sub(r"\D", "", mobile)

    # VALIDATE MOBILE
    if len(mobile) != 10:

        raise HTTPException(
            status_code=400,
            detail="Valid 10-digit mobile required"
        )

    # VALIDATE API KEY
    if apikey != PROXY_API_KEY:

        raise HTTPException(
            status_code=403,
            detail="Invalid proxy API key"
        )

    try:

        # BUILD URL
        target_url = (
            f"{MAIN_API_URL}"
            f"?api_key={MAIN_API_KEY}"
            f"&mobile={mobile}"
        )

        print(f"[LOG] Calling: {target_url}")

        # CALL MAIN API
        response = requests.get(
            target_url,
            timeout=30
        )

        response.raise_for_status()

        # JSON RESPONSE
        data = response.json()

        # CUSTOM RESULT
        result = {
            "success": True,
            "proxy_status": "active",
            "proxy_service": "GHOST-PROXY v2.0",
            "proxy_timestamp":
                datetime.now().isoformat(),
            "target_mobile": mobile,
            "data": data
        }

        return result

    except requests.exceptions.Timeout:

        raise HTTPException(
            status_code=504,
            detail="API timeout"
        )

    except requests.exceptions.ConnectionError:

        raise HTTPException(
            status_code=502,
            detail="Connection failed"
        )

    except requests.exceptions.HTTPError as e:

        raise HTTPException(
            status_code=response.status_code,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )