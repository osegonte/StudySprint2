# backend/stage3_status.py
"""Status checker for Stage 3 implementation"""

import asyncio
import httpx
import json
from datetime import datetime

async def check_stage3_status():
    """Check the status of Stage 3 implementation"""
    
    print("📊 StudySprint 2.0 - Stage 3 Status Check")
    print("=" * 50)
    
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "server_running": False,
        "database_connected": False,
        "auth_working": False,
        "topics_working": False,
        "models_registered": False,
        "endpoints_available": []
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            
            # Check server health
            try:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    status["server_running"] = True
                    health_data = response.json()
                    status["database_connected"] = health_data.get("database") == "connected"
                    print("✅ Server running and database connected")
                else:
                    print("❌ Server health check failed")
            except:
                print("❌ Server not responding")
                return status
            
            # Check database health
            try:
                response = await client.get("http://localhost:8000/health/db")
                if response.status_code == 200:
                    print("✅ Database health check passed")
                else:
                    print("❌ Database health check failed")
            except:
                print("❌ Database health endpoint not available")
            
            # Check auth endpoints
            try:
                response = await client.get("http://localhost:8000/api/v1/auth/health")
                if response.status_code == 200:
                    status["auth_working"] = True
                    print("✅ Authentication system working")
                    status["endpoints_available"].append("/api/v1/auth/*")
            except:
                print("❌ Authentication endpoints not available")
            
            # Check topics endpoints
            try:
                # This should fail with 401 (unauthorized) which means endpoint exists
                response = await client.get("http://localhost:8000/api/v1/topics/")
                if response.status_code == 401:
                    status["topics_working"] = True
                    print("✅ Topics endpoints available (requires auth)")
                    status["endpoints_available"].append("/api/v1/topics/*")
                elif response.status_code == 200:
                    status["topics_working"] = True
                    print("✅ Topics endpoints working")
                    status["endpoints_available"].append("/api/v1/topics/*")
            except:
                print("❌ Topics endpoints not available")
            
            # Check API documentation
            try:
                response = await client.get("http://localhost:8000/docs")
                if response.status_code == 200:
                    print("✅ API documentation available at /docs")
                    status["endpoints_available"].append("/docs")
            except:
                print("❌ API documentation not available")
            
            # Test model registration by checking OpenAPI schema
            try:
                response = await client.get("http://localhost:8000/openapi.json")
                if response.status_code == 200:
                    openapi_data = response.json()
                    schemas = openapi_data.get("components", {}).get("schemas", {})
                    
                    # Check for our schemas
                    required_schemas = ["TopicCreate", "TopicResponse", "UserResponse"]
                    found_schemas = [schema for schema in required_schemas if schema in schemas]
                    
                    if len(found_schemas) == len(required_schemas):
                        status["models_registered"] = True
                        print(f"✅ All models registered ({len(schemas)} total schemas)")
                    else:
                        print(f"⚠️  Some models missing: {set(required_schemas) - set(found_schemas)}")
            except:
                print("❌ Could not check model registration")
    
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    # Print summary
    print("\n📋 Summary:")
    print(f"   Server: {'✅' if status['server_running'] else '❌'}")
    print(f"   Database: {'✅' if status['database_connected'] else '❌'}")
    print(f"   Authentication: {'✅' if status['auth_working'] else '❌'}")
    print(f"   Topics: {'✅' if status['topics_working'] else '❌'}")
    print(f"   Models: {'✅' if status['models_registered'] else '❌'}")
    
    if status["endpoints_available"]:
        print(f"\n🔗 Available endpoints:")
        for endpoint in status["endpoints_available"]:
            print(f"   • {endpoint}")
    
    # Overall status
    components_working = sum([
        status['server_running'],
        status['database_connected'], 
        status['auth_working'],
        status['topics_working'],
        status['models_registered']
    ])
    
    total_components = 5
    percentage = (components_working / total_components) * 100
    
    print(f"\n🎯 Stage 3.2 Progress: {components_working}/{total_components} ({percentage:.0f}%)")
    
    if percentage == 100:
        print("🎉 Stage 3.2 COMPLETE - Ready for Stage 3.3!")
    elif percentage >= 80:
        print("🚧 Stage 3.2 Nearly Complete - Minor issues to resolve")
    elif percentage >= 60:
        print("⚠️  Stage 3.2 Partially Working - Some components need attention")
    else:
        print("❌ Stage 3.2 Major Issues - Requires debugging")
    
    return status

if __name__ == "__main__":
    asyncio.run(check_stage3_status())
