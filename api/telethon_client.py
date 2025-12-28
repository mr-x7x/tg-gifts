import asyncio
from telethon import TelegramClient, functions
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class TelegramGiftsClient:
    def __init__(self, api_id: int, api_hash: str, session_name: str = 'session'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        
    async def connect(self):
        """Connect to Telegram"""
        if not self.client:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()
    
    async def get_all_collections(self) -> List[Dict]:
        """Get all gift collections"""
        await self.connect()
        
        try:
            result = await self.client(functions.payments.GetStarGiftsRequest(hash=0))
            collections = result.gifts if hasattr(result, 'gifts') else []
            
            formatted_collections = []
            for col in collections:
                col_dict = col.to_dict()
                
                # Format for frontend
                formatted = {
                    'id': col_dict.get('id'),
                    'title': col_dict.get('title'),
                    'description': col_dict.get('description', ''),
                    'photo_url': self._get_photo_url(col_dict),
                    'cover_url': self._get_cover_url(col_dict),
                    'count': col_dict.get('count', 0),
                    'price_range': {
                        'min': col_dict.get('min_price'),
                        'max': col_dict.get('max_price')
                    },
                    'category': col_dict.get('category', 'general'),
                    'date': col_dict.get('date'),
                    'stats': {
                        'total_items': col_dict.get('count', 0),
                        'average_price': col_dict.get('average_price'),
                        'popularity': col_dict.get('popularity', 0)
                    }
                }
                formatted_collections.append(formatted)
            
            return formatted_collections
            
        except Exception as e:
            print(f"Error getting collections: {e}")
            return []
    
    async def get_collection_items(self, collection_id: int, page: int = 1, limit: int = 20, sort_by: str = 'newest') -> Dict:
        """Get items in a collection with pagination"""
        await self.connect()
        
        try:
            all_items = []
            offset = ""
            items_per_page = 100
            
            # Get all items first (with pagination)
            while True:
                result = await self.client(functions.payments.GetResaleStarGiftsRequest(
                    gift_id=collection_id,
                    offset=offset,
                    limit=items_per_page
                ))
                
                items = result.gifts if hasattr(result, 'gifts') else []
                all_items.extend(items)
                
                if len(items) < items_per_page:
                    break
                
                if items:
                    offset = str(items[-1].id)
                
                await asyncio.sleep(0.1)
            
            # Convert to dict
            items_dicts = []
            for item in all_items:
                item_dict = item.to_dict()
                
                # Convert bytes and datetime
                item_dict = self._format_item(item_dict)
                
                # Add additional fields for frontend
                item_dict['formatted_price'] = self._format_price(item_dict.get('price'))
                item_dict['image_url'] = self._get_item_image_url(item_dict)
                item_dict['animation_url'] = self._get_item_animation_url(item_dict)
                
                items_dicts.append(item_dict)
            
            # Apply sorting
            if sort_by == 'cheapest':
                items_dicts.sort(key=lambda x: x.get('price', 0))
            elif sort_by == 'expensive':
                items_dicts.sort(key=lambda x: x.get('price', 0), reverse=True)
            elif sort_by == 'newest':
                items_dicts.sort(key=lambda x: x.get('date', 0), reverse=True)
            
            # Apply pagination
            total_items = len(items_dicts)
            total_pages = (total_items + limit - 1) // limit
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_items = items_dicts[start_idx:end_idx]
            
            return {
                'items': paginated_items,
                'total': total_items,
                'pages': total_pages
            }
            
        except Exception as e:
            print(f"Error getting collection items: {e}")
            return {'items': [], 'total': 0, 'pages': 0}
    
    async def search(self, query: str = "", category: str = "", min_price: int = None, max_price: int = None) -> List[Dict]:
        """Search across collections and items"""
        collections = await self.get_all_collections()
        
        results = []
        for collection in collections:
            # Filter by category
            if category and collection.get('category') != category:
                continue
            
            # Filter by query in title/description
            if query:
                title_match = query.lower() in collection.get('title', '').lower()
                desc_match = query.lower() in collection.get('description', '').lower()
                if not title_match and not desc_match:
                    continue
            
            # Get items for this collection
            items_data = await self.get_collection_items(collection['id'], page=1, limit=50)
            
            # Filter items by price
            filtered_items = []
            for item in items_data['items']:
                price = item.get('price', 0)
                
                if min_price and price < min_price:
                    continue
                if max_price and price > max_price:
                    continue
                
                filtered_items.append(item)
            
            if filtered_items:
                results.append({
                    'collection': collection,
                    'items': filtered_items[:10],  # Limit to 10 items per collection
                    'matching_items': len(filtered_items)
                })
        
        return results
    
    async def get_stats(self) -> Dict:
        """Get service statistics"""
        collections = await self.get_all_collections()
        
        total_items = 0
        price_sum = 0
        price_count = 0
        
        for collection in collections:
            items_data = await self.get_collection_items(collection['id'], page=1, limit=10)
            
            for item in items_data['items']:
                price = item.get('price')
                if price:
                    price_sum += price
                    price_count += 1
            
            total_items += collection.get('count', 0)
        
        avg_price = price_sum / price_count if price_count > 0 else 0
        
        return {
            'total_collections': len(collections),
            'total_items': total_items,
            'average_price': round(avg_price, 2),
            'price_range': {
                'min': 0,  # You would track this
                'max': 0   # You would track this
            },
            'categories': len(set(c.get('category') for c in collections))
        }
    
    def _format_item(self, item_dict: Dict) -> Dict:
        """Format item for JSON serialization"""
        import binascii
        
        def convert(obj):
            if isinstance(obj, bytes):
                return binascii.hexlify(obj).decode('utf-8')
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            else:
                return obj
        
        return convert(item_dict)
    
    def _get_photo_url(self, collection_dict: Dict) -> str:
        """Extract photo URL from collection"""
        # This is simplified - you'd extract actual file reference
        photos = collection_dict.get('photos', [])
        if photos:
            # Telegram file reference logic here
            return f"/api/collection/{collection_dict.get('id')}/photo"
        return ""
    
    def _get_item_image_url(self, item_dict: Dict) -> str:
        """Get item image URL"""
        # Implementation depends on Telegram API
        return f"/api/item/{item_dict.get('id')}/image"
    
    def _format_price(self, price: int) -> str:
        """Format price for display"""
        if not price:
            return "N/A"
        return f"${price / 100:.2f}"
