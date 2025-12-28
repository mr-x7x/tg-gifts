from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import json
from datetime import datetime
import os
from functools import wraps
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

# Cache setup (using file cache for Vercel compatibility)
cache_dir = "/tmp/telegram_gifts_cache"
os.makedirs(cache_dir, exist_ok=True)

def cache_response(key, duration=300):
    """Simple file-based cache decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_file = os.path.join(cache_dir, f"{key}.json")
            
            # Check cache
            if os.path.exists(cache_file):
                mtime = os.path.getmtime(cache_file)
                if time.time() - mtime < duration:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # Call function
            result = f(*args, **kwargs)
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
            
            return result
        return decorated_function
    return decorator

# Import routes
from api.routes import *

@app.route('/')
def home():
    return {
        "service": "Telegram Star Gifts API",
        "version": "1.0.0",
        "endpoints": {
            "/api/collections": "Get all gift collections",
            "/api/collections/<id>": "Get specific collection",
            "/api/collection/<id>/items": "Get items in collection",
            "/api/search?q=<query>": "Search collections",
            "/api/stats": "Get statistics"
        }
    }

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded", "retry_after": e.description}), 429

if __name__ == "__main__":
    app.run(debug=True)
