import aiohttp
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EasyRoutesClient:
    """Client for EasyRoutes API integration"""
    
    def __init__(self):
        self.client_id = os.getenv('EASYROUTES_CLIENT_ID')
        self.client_secret = os.getenv('EASYROUTES_CLIENT_SECRET')
        self.base_url = "https://easyroutes.roundtrip.ai/api/2024-07"
        self.access_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("EasyRoutes credentials not configured")
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            await self.authenticate()
    
    async def authenticate(self):
        """Authenticate and obtain access token"""
        auth_data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/authenticate", json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["accessToken"]
                    expires_in = data.get("expiresInSeconds", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
                else:
                    error_text = await response.text()
                    raise Exception(f"EasyRoutes authentication failed: {response.status} - {error_text}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated request to EasyRoutes API"""
        await self._ensure_authenticated()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, f"{self.base_url}{endpoint}", headers=headers, **kwargs) as response:
                if response.status == 401:
                    # Token might be expired, try to re-authenticate once
                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    async with session.request(method, f"{self.base_url}{endpoint}", headers=headers, **kwargs) as retry_response:
                        if retry_response.status >= 400:
                            error_text = await retry_response.text()
                            raise Exception(f"EasyRoutes API error: {retry_response.status} - {error_text}")
                        return await retry_response.json()
                elif response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"EasyRoutes API error: {response.status} - {error_text}")
                
                return await response.json()
    
    async def get_routes(self, include_archived: bool = False, limit: int = 100) -> Dict:
        """Retrieve routes with pagination support"""
        params = {
            "query.limit": limit,
            "query.includeArchived": include_archived
        }
        
        return await self._make_request("GET", "/routes", params=params)
    
    async def get_route_by_id(self, route_id: str) -> Optional[Dict]:
        """Get specific route by ID"""
        try:
            return await self._make_request("GET", f"/routes/{route_id}")
        except Exception as e:
            if "404" in str(e):
                return None
            raise
    
    async def get_route_by_number(self, route_number: str) -> Optional[Dict]:
        """Find route by route number/name"""
        try:
            # Get all routes and search for matching route number
            routes_response = await self.get_routes()
            routes = routes_response.get("routes", [])
            
            for route in routes:
                # Check if route name/number matches
                if (route.get("name", "").upper() == route_number.upper() or 
                    route.get("id", "").upper() == route_number.upper()):
                    # Get full route details
                    return await self.get_route_by_id(route["id"])
            
            return None
            
        except Exception as e:
            raise Exception(f"Error searching for route {route_number}: {str(e)}")
    
    async def get_incomplete_stops(self, route_id: str) -> List[Dict]:
        """Get stops that are not delivered for a specific route"""
        try:
            route = await self.get_route_by_id(route_id)
            if not route:
                return []
            
            incomplete_stops = []
            stops = route.get("stops", [])
            
            for stop in stops:
                delivery_status = stop.get("deliveryStatus", "UNKNOWN")
                # Consider any status other than "DELIVERED" as incomplete
                if delivery_status != "DELIVERED":
                    incomplete_stops.append(stop)
            
            return incomplete_stops
            
        except Exception as e:
            raise Exception(f"Error getting incomplete stops for route {route_id}: {str(e)}")
    
    async def get_route_summary(self, route_id: str) -> Dict:
        """Get summary information about a route"""
        try:
            route = await self.get_route_by_id(route_id)
            if not route:
                return {}
            
            stops = route.get("stops", [])
            total_stops = len(stops)
            
            status_counts = {}
            incomplete_count = 0
            
            for stop in stops:
                status = stop.get("deliveryStatus", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
                if status != "DELIVERED":
                    incomplete_count += 1
            
            return {
                "route_id": route_id,
                "route_name": route.get("name", ""),
                "total_stops": total_stops,
                "incomplete_stops": incomplete_count,
                "delivered_stops": status_counts.get("DELIVERED", 0),
                "status_breakdown": status_counts,
                "driver": route.get("driver", {}),
                "scheduled_for": route.get("scheduledFor", "")
            }
            
        except Exception as e:
            raise Exception(f"Error getting route summary for {route_id}: {str(e)}")

# Utility function to run async functions in sync context
def run_async(coro):
    """Helper function to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

