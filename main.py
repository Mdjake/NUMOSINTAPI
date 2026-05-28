# main.py
from fastapi import FastAPI, Query, HTTPException
import httpx
import re
from typing import Set, Dict, Any, List

app = FastAPI(title="Number Info API - Deep Search")

def normalize_number(number: str) -> str:
    """Convert any phone number format to standard 10-digit Indian number"""
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', str(number))
    
    # Handle different formats:
    # 917980750651 -> 7980750651 (remove 91 prefix)
    # 07980750651 -> 7980750651 (remove leading 0)
    # 7980750651 -> 7980750651 (keep as is)
    # +917980750651 -> 7980750651 (remove +91)
    
    if len(digits) == 12 and digits.startswith('91'):
        return digits[2:]  # Remove 91 prefix
    elif len(digits) == 11 and digits.startswith('0'):
        return digits[1:]  # Remove leading 0
    elif len(digits) == 10:
        return digits  # Perfect 10-digit number
    else:
        return digits  # Return as is (unlikely to match)

async def deep_search(
    client: httpx.AsyncClient, 
    number: str, 
    visited: Set[str], 
    all_results: List[Dict],
    depth: int = 0,
    max_depth: int = 5
) -> None:
    """
    Recursively search for number details and follow alt numbers
    """
    # Normalize the number
    normalized = normalize_number(number)
    
    # Stop if already visited or max depth reached
    if normalized in visited or depth > max_depth:
        return
    
    # Mark as visited
    visited.add(normalized)
    
    # Fetch data for this number
    upstream_url = f"https://wasifali-indian-number-info.vercel.app/api?number={normalized}"
    
    try:
        resp = await client.get(upstream_url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return  # Silently fail for this number
    
    # Check if valid response
    if not data.get("success") or not isinstance(data.get("number_detail"), dict):
        return
    
    result_obj = data["result"]
    
    # Extract all numbered entries for this number
    current_results = []
    alt_numbers = set()
    
    for key, value in result_obj.items():
        if key.isdigit():
            # Remove developer field
            value.pop("developer", None)
            
            # Extract alt number if exists and normalize it
            if "alt" in value and value["alt"]:
                alt_normalized = normalize_number(value["alt"])
                if alt_normalized and alt_normalized != normalized:
                    alt_numbers.add(alt_normalized)
            
            # Add to current results (as tuple for deduplication)
            current_results.append(value)
    
    # Add unique results to master list (based on all fields combined)
    for result in current_results:
        # Create a unique key for deduplication (using all fields)
        unique_key = tuple(sorted(result.items()))
        if not any(tuple(sorted(r.items())) == unique_key for r in all_results):
            all_results.append(result)
    
    # Recursively search alt numbers
    for alt_num in alt_numbers:
        await deep_search(client, alt_num, visited, all_results, depth + 1, max_depth)

@app.get("/api/number-info")
async def number_info(
    number: str = Query(..., description="Indian mobile number"),
    max_depth: int = Query(5, description="Maximum recursion depth", ge=1, le=10)
):
    """
    Deep search API - recursively follows alt numbers to find core results
    """
    visited_numbers: Set[str] = set()
    all_results: List[Dict] = []
    
    async with httpx.AsyncClient() as client:
        await deep_search(client, number, visited_numbers, all_results, 0, max_depth)
    
    if not all_results:
        raise HTTPException(status_code=404, detail="No information found for this number")
    
    # Build final response
    result = {
        "success": True,
        "searched_numbers": list(visited_numbers),  # All numbers that were searched
        "total_unique_records": len(all_results),
        "results": all_results,
        "channel": "free_inf_api"
    }
    
    return result

@app.get("/")
async def root():
    return {"message": "Number Info API - Deep Search. Use /api/number-info?number=7439312179&max_depth=5"}
