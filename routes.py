from flask import jsonify, request
from api import app
from api.telethon_client import TelegramGiftsClient
import asyncio
import os

# Initialize client
client = TelegramGiftsClient(
    api_id=os.getenv('TELEGRAM_API_ID'),
    api_hash=os.getenv('TELEGRAM_API_HASH'),
    session_name='telethon_session'
)

@app.route('/api/collections')
@cache_response('collections_list', 600)  # Cache for 10 minutes
def get_collections():
    """Get all gift collections"""
    try:
        collections = asyncio.run(client.get_all_collections())
        
        # Format response
        formatted = []
        for col in collections:
            formatted.append({
                "id": col.get('id'),
                "title": col.get('title'),
                "description": col.get('description'),
                "photo_url": col.get('photo_url'),
                "items_count": col.get('count', 0),
                "price_range": col.get('price_range'),
                "category": col.get('category'),
                "created_at": col.get('date')
            })
        
        return jsonify({
            "success": True,
            "data": formatted,
            "count": len(formatted),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/collection/<int:collection_id>')
@cache_response(f'collection_{collection_id}', 300)
def get_collection(collection_id):
    """Get specific collection details"""
    try:
        collection = asyncio.run(client.get_collection(collection_id))
        
        if not collection:
            return jsonify({
                "success": False,
                "error": "Collection not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": collection
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/collection/<int:collection_id>/items')
def get_collection_items():
    """Get items in a collection with pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        sort_by = request.args.get('sort', 'newest')  # newest, cheapest, expensive
        
        items = asyncio.run(client.get_collection_items(
            collection_id=collection_id,
            page=page,
            limit=limit,
            sort_by=sort_by
        ))
        
        return jsonify({
            "success": True,
            "data": items['items'],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": items['total'],
                "pages": items['pages'],
                "has_next": page < items['pages'],
                "has_prev": page > 1
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search')
def search():
    """Search collections and items"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    
    if not query and not category:
        return jsonify({
            "success": False,
            "error": "Search query or category required"
        }), 400
    
    try:
        results = asyncio.run(client.search(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price
        ))
        
        return jsonify({
            "success": True,
            "data": results,
            "query": query,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stats')
@cache_response('stats', 1800)  # Cache for 30 minutes
def get_stats():
    """Get service statistics"""
    try:
        stats = asyncio.run(client.get_stats())
        
        return jsonify({
            "success": True,
            "data": stats,
            "server_time": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/trending')
@cache_response('trending', 900)  # Cache for 15 minutes
def get_trending():
    """Get trending gifts"""
    try:
        trending = asyncio.run(client.get_trending())
        
        return jsonify({
            "success": True,
            "data": trending
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
