import asyncio
import websockets
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class BrainServiceClient:
    def __init__(self, brain_service_url: str):
        self.base_url = brain_service_url
        self.ws_url = brain_service_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/mcp'
        self.websocket = None
        self.request_id = 0
        self.pending_requests = {}
        
    async def connect(self):
        """Establish WebSocket connection to brain service"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"Connected to brain service at {self.ws_url}")
            
            # Start listening for responses
            asyncio.create_task(self._listen_for_responses())
            
        except Exception as e:
            logger.error(f"Failed to connect to brain service: {str(e)}")
            raise
    
    async def _listen_for_responses(self):
        """Listen for WebSocket responses"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                request_id = data.get("id")
                
                if request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if not future.cancelled():
                        future.set_result(data)
                        
        except Exception as e:
            logger.error(f"WebSocket listener error: {str(e)}")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP request and wait for response"""
        if not self.websocket:
            await self.connect()
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": f"tools/call",
            "params": {
                "name": method,
                "arguments": params
            }
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[self.request_id] = future
        
        try:
            await self.websocket.send(json.dumps(request))

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            return response.get("result", {})

        except asyncio.TimeoutError:
            logger.error(f"Request {self.request_id} timed out")
            self.pending_requests.pop(self.request_id, None)
            raise
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            self.pending_requests.pop(self.request_id, None)
            raise

    async def store_embedding(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store content embedding in brain service"""
        params = {
            "content": content,
            "metadata": metadata or {}
        }
        result = await self._send_request("store_embedding", params)
        return result.get("id", "")

    async def search_embeddings(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        params = {
            "query": query,
            "limit": limit
        }
        result = await self._send_request("search_embeddings", params)
        return result.get("results", [])

    async def store_knowledge(self, knowledge_type: str, content: Dict[str, Any]) -> str:
        """Store structured knowledge in brain service"""
        params = {
            "knowledge_type": knowledge_type,
            "content": content
        }
        result = await self._send_request("store_knowledge", params)
        return result.get("id", "")

    async def get_knowledge(self, knowledge_type: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge from brain service"""
        params = {
            "knowledge_type": knowledge_type,
            "query": query or {}
        }
        result = await self._send_request("get_knowledge", params)
        return result.get("results", [])

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from brain service")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()