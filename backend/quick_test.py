# backend/quick_test.py
"""Quick manual test to verify everything works"""

import asyncio
import httpx

async def quick_test():
    """Quick smoke test"""
    async with httpx.AsyncClient() as client:
        # Test health
        response = await client.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code}")
        
        # Test API docs
        response = await client.get("http://localhost:8000/docs")
        print(f"API docs: {response.status_code}")
        
        # Test auth health
        response = await client.get("http://localhost:8000/api/v1/auth/health")
        print(f"Auth health: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Quick test of Stage 3.2 endpoints...")
    asyncio.run(quick_test())
    print("✅ Basic endpoints responding!")
