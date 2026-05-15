from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# ========== CONFIGURATION ==========
# Your PROXY API key (for clients to use YOUR API)
# Set this via environment variable: export PROXY_API_KEY="your-secret-key-here"
PROXY_API_KEY = os.getenv('PROXY_API_KEY', 'GHOST-PROXY-KEY-2024')  # Default for testing

# Main NUM-API key (hardcoded as you provided)
MAIN_API_KEY = "Newapiofnum567unlimyXy52vG7vF6aM8cny74Vz8jfe6Hs"
MAIN_API_URL = "http://numapi-production.up.railway.app/search"

print(f"[INFO] Proxy API Key: {PROXY_API_KEY}")
print(f"[INFO] Main API URL: {MAIN_API_URL}")
# ===================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'GHOST PROXY API',
        'status': 'active',
        'version': '2.0',
        'endpoints': {
            '/api/lookup': 'GET - Pass ?mobile=10digitnumber&apikey=YOUR_PROXY_KEY'
        },
        'auth_required': 'Use your own proxy API key (not the main NUM-API key)'
    })

@app.route('/api/lookup', methods=['GET', 'OPTIONS'])
def lookup():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Get parameters
    mobile = request.args.get('mobile', '')
    provided_apikey = request.args.get('apikey', '')
    
    # Clean mobile number - keep only digits
    mobile = re.sub(r'\D', '', mobile)
    
    # Validate 10 digit number
    if not mobile or len(mobile) != 10:
        return jsonify({
            'success': False,
            'error': 'Valid 10-digit mobile number required',
            'provided': request.args.get('mobile', '')
        }), 400
    
    # Validate YOUR proxy API key
    if not provided_apikey:
        return jsonify({
            'success': False,
            'error': 'Your proxy API key is required - pass ?apikey=YOUR_PROXY_KEY',
            'note': 'This is your key for my proxy API, not the main NUM-API key'
        }), 401
    
    if provided_apikey != PROXY_API_KEY:
        return jsonify({
            'success': False,
            'error': 'Invalid proxy API key',
            'hint': 'Contact admin to get valid proxy API key'
        }), 403
    
    try:
        # Call the main NUM-API with THEIR key (hardcoded above)
        target_url = f"{MAIN_API_URL}?api_key={MAIN_API_KEY}&mobile={mobile}"
        print(f"[LOG] Proxying request for mobile: {mobile}")
        print(f"[LOG] Calling: {MAIN_API_URL}?api_key=***&mobile={mobile}")
        
        response = requests.get(target_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Wrap the response with proxy info
        result = {
            'success': True,
            'proxy_status': 'active',
            'proxy_service': 'GHOST-PROXY v2.0',
            'proxy_timestamp': datetime.now().isoformat(),
            'target_mobile': mobile,
            'data': data  # Changed from 'api_response' to 'data' for cleaner response
        }
        
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'API request timeout - server took too long to respond'
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Connection failed - cannot reach NUM-API server'
        }), 502
    except requests.exceptions.HTTPError as e:
        return jsonify({
            'success': False,
            'error': f'Main API returned error: {str(e)}'
        }), response.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)