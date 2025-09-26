#!/usr/bin/env python3
"""
Simple Redis Connection Test
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

import redis.asyncio as redis
from src.config.settings import settings

async def test_redis_connection():
    """Test basic Redis connection"""
    print("Testing Redis connection...")
    print(f"Redis URL: {settings.redis_url}")
    
    try:
        # Create Redis connection
        client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Test ping
        result = await client.ping()
        print(f"Ping result: {result}")
        
        # Test set/get
        test_key = "test_key"
        test_value = "hello_world"
        
        await client.set(test_key, test_value)
        retrieved = await client.get(test_key)
        
        print(f"Set: {test_value}")
        print(f"Get: {retrieved}")
        
        if retrieved == test_value:
            print("SUCCESS: Redis operations working!")
        else:
            print("ERROR: Value mismatch")
            
        # Cleanup
        await client.delete(test_key)
        await client.close()
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_redis_connection())
    if success:
        print("\nReady to run full test suite!")
    else:
        print("\nFix Redis connection before proceeding.")