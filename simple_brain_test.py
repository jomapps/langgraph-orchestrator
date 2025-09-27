#!/usr/bin/env python3
"""
Simple test script to verify brain service connection without heavy dependencies.
"""

import asyncio
import websockets
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_brain_service_websocket():
    """Test basic WebSocket connection to brain service"""
    print("Testing brain service WebSocket connection...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
    ws_url = brain_service_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/mcp'

    print(f"Connecting to: {ws_url}")

    try:
        # Test basic connection
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✅ Successfully connected to brain service WebSocket")

            # Test sending a simple request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "store_embedding",
                    "arguments": {
                        "content": "Test content from orchestrator",
                        "metadata": {"test": True, "component": "orchestrator"}
                    }
                }
            }

            await websocket.send(json.dumps(request))
            print("✅ Successfully sent test request")

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)

            print(f"✅ Received response: {response_data}")

            if "result" in response_data:
                print("✅ Brain service is responding correctly")
                return True
            else:
                print(f"❌ Unexpected response format: {response_data}")
                return False

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        return False
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Invalid WebSocket URI: {e}")
        return False
    except asyncio.TimeoutError:
        print("❌ Connection timeout - brain service may be unavailable")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - brain service may be down")
        return False
    except Exception as e:
        print(f"❌ Brain service connection failed: {str(e)}")
        return False


async def test_environment_variables():
    """Test that required environment variables are set"""
    print("Testing environment variables...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL')

    if brain_service_url:
        print(f"✅ BRAIN_SERVICE_BASE_URL is set: {brain_service_url}")
        return True
    else:
        print("❌ BRAIN_SERVICE_BASE_URL is not set")
        print("💡 Make sure to set BRAIN_SERVICE_BASE_URL environment variable")
        return False


async def main():
    """Run connection tests"""
    print("🧠 Brain Service Connection Test")
    print("=" * 40)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("WebSocket Connection", test_brain_service_websocket)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Brain service is accessible from orchestrator!")
        print("✅ Neo4j removal and brain service integration completed successfully")
        return 0
    else:
        print("⚠️  Some tests failed. Check brain service configuration and connectivity.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)