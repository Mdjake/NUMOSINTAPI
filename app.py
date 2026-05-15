from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# Read API_KEY from environment variable (REQUIRED)
API_KEY = os.getenv('API_KEY')
BASE_URL = "https://numapi-production.up.railway.app/search"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'GHOST PROXY API',
        'status': 'active',
        'endpoints': {
            '/api/lookup': 'GET - Pass ?mobile=10digitnumber&apikey=yourapikey (apikey parameter required)'
        }
    })

@app.route('/api/lookup', methods=['GET', 'OPTIONS'])
def lookup():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    mobile = request.args.get('mobile', '')
    # API key from query parameter - REQUIRED
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
    
    # Validate API key is provided
    if not provided_apikey:
        return jsonify({
            'success': False,
            'error': 'API key is required - pass ?apikey=yourapikey'
        }), 401
    
    # Validate API key matches environment variable
    if provided_apikey != API_KEY:
        return jsonify({
            'success': False,
            'error': 'Invalid API key'
        }), 403
    
    try:
        # Call the original API with the correct key
        target_url = f"{BASE_URL}?api_key={API_KEY}&mobile={mobile}"
        print(f"[LOG] Calling: {target_url}")
        
        response = requests.get(target_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Wrap the response with proxy info
        result = {
            'proxy_status': 'active',
            'proxy_service': 'GHOST-PROXY v1.0',
            'proxy_timestamp': datetime.now().isoformat(),
            'target_mobile': mobile,
            'api_response': data
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
            'error': f'API returned error: {str(e)}'
        }), response.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
