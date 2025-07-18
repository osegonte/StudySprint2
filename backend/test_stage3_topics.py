# backend/test_stage3_topics.py
"""Quick test script for Stage 3.2 Topic Management"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_topic_endpoints():
    """Test the complete topic management system"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Stage 3.2: Topic Management System")
        print("=" * 50)
        
        # 1. Health check
        print("1. Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✅ Health check passed")
        
        # 2. Register a test user
        print("\n2. Registering test user...")
        user_data = {
            "email": "test@studysprint.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        if response.status_code == 201:
            auth_data = response.json()
            token = auth_data["access_token"]
            print("✅ User registered successfully")
        elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
            # User exists, try to login
            print("ℹ️ User already exists, logging in...")
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            response = await client.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
            assert response.status_code == 200
            auth_data = response.json()
            token = auth_data["access_token"]
            print("✅ User logged in successfully")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Test topic creation
        print("\n3. Testing topic creation...")
        topics_to_create = [
            {
                "name": "Machine Learning Fundamentals",
                "description": "Core concepts of ML including supervised and unsupervised learning",
                "color": "#3498db"
            },
            {
                "name": "Python Programming",
                "description": "Advanced Python techniques and best practices",
                "color": "#e74c3c"
            },
            {
                "name": "Data Structures & Algorithms",
                "description": "Essential CS concepts for problem solving",
                "color": "#2ecc71"
            }
        ]
        
        created_topics = []
        for topic_data in topics_to_create:
            response = await client.post(
                f"{BASE_URL}/api/v1/topics/",
                json=topic_data,
                headers=headers
            )
            if response.status_code == 201:
                topic = response.json()
                created_topics.append(topic)
                print(f"✅ Created topic: {topic['name']}")
            else:
                print(f"❌ Failed to create topic: {response.status_code} - {response.text}")
        
        # 4. Test getting all topics
        print("\n4. Testing topic retrieval...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/", headers=headers)
        assert response.status_code == 200
        topics = response.json()
        print(f"✅ Retrieved {len(topics)} topics")
        
        # 5. Test getting topics with stats
        print("\n5. Testing topics with statistics...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/with-stats", headers=headers)
        assert response.status_code == 200
        topics_with_stats = response.json()
        print(f"✅ Retrieved {len(topics_with_stats)} topics with statistics")
        
        for topic in topics_with_stats:
            stats = topic.get("statistics", {})
            print(f"   📊 {topic['name']}: {stats.get('total_pdfs', 0)} PDFs, {stats.get('total_study_time_minutes', 0)} min studied")
        
        # 6. Test individual topic with stats
        if created_topics:
            topic_id = created_topics[0]["id"]
            print(f"\n6. Testing individual topic stats for {created_topics[0]['name']}...")
            response = await client.get(f"{BASE_URL}/api/v1/topics/{topic_id}/stats", headers=headers)
            assert response.status_code == 200
            topic_stats = response.json()
            print("✅ Retrieved detailed topic statistics")
            print(f"   📈 Statistics: {json.dumps(topic_stats['statistics'], indent=2)}")
        
        # 7. Test topic search
        print("\n7. Testing topic search...")
        search_data = {
            "query": "python",
            "limit": 10
        }
        response = await client.post(f"{BASE_URL}/api/v1/topics/search", json=search_data, headers=headers)
        assert response.status_code == 200
        search_results = response.json()
        print(f"✅ Search found {search_results['total_results']} results in {search_results['search_time_ms']}ms")
        
        # 8. Test topic update
        if created_topics:
            topic_id = created_topics[0]["id"]
            print(f"\n8. Testing topic update...")
            update_data = {
                "description": "Updated: Core ML concepts with practical examples",
                "color": "#9b59b6"
            }
            response = await client.put(f"{BASE_URL}/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert response.status_code == 200
            updated_topic = response.json()
            print(f"✅ Updated topic: {updated_topic['name']}")
            print(f"   🎨 New color: {updated_topic['color']}")
        
        # 9. Test topic duplication
        if created_topics:
            topic_id = created_topics[0]["id"]
            print(f"\n9. Testing topic duplication...")
            response = await client.post(f"{BASE_URL}/api/v1/topics/{topic_id}/duplicate", headers=headers)
            assert response.status_code == 200
            duplicate_topic = response.json()
            print(f"✅ Duplicated topic: {duplicate_topic['name']}")
        
        # 10. Test popular topics
        print("\n10. Testing popular topics...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/popular?limit=5", headers=headers)
        assert response.status_code == 200
        popular_topics = response.json()
        print(f"✅ Retrieved {len(popular_topics)} popular topics")
        
        # 11. Test color suggestions
        print("\n11. Testing color suggestions...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/colors/suggestions", headers=headers)
        assert response.status_code == 200
        color_suggestions = response.json()
        print(f"✅ Retrieved {len(color_suggestions['primary_colors'])} primary colors")
        
        # 12. Test analytics (will show empty data since no study sessions yet)
        if created_topics:
            topic_id = created_topics[0]["id"]
            print(f"\n12. Testing topic analytics...")
            response = await client.get(f"{BASE_URL}/api/v1/topics/{topic_id}/analytics?days=30", headers=headers)
            assert response.status_code == 200
            analytics = response.json()
            print("✅ Retrieved topic analytics")
            print(f"   📊 Analytics keys: {list(analytics.keys())}")
        
        # 13. Test batch operations
        if len(created_topics) >= 2:
            print("\n13. Testing batch update...")
            batch_update_data = {
                "ids": [created_topics[0]["id"], created_topics[1]["id"]],
                "updates": {"color": "#34495e"}
            }
            response = await client.put(f"{BASE_URL}/api/v1/topics/batch-update", json=batch_update_data, headers=headers)
            assert response.status_code == 200
            batch_result = response.json()
            print(f"✅ Batch updated {batch_result['updated_count']} topics")
        
        # 14. Test topic deletion (delete the duplicate)
        print("\n14. Testing topic deletion...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/", headers=headers)
        current_topics = response.json()
        
        # Find a topic to delete (preferably a duplicate)
        topic_to_delete = None
        for topic in current_topics:
            if "(Copy)" in topic["name"]:
                topic_to_delete = topic
                break
        
        if topic_to_delete:
            response = await client.delete(f"{BASE_URL}/api/v1/topics/{topic_to_delete['id']}", headers=headers)
            assert response.status_code == 200
            print(f"✅ Deleted topic: {topic_to_delete['name']}")
        
        # 15. Final verification
        print("\n15. Final verification...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/count/total", headers=headers)
        assert response.status_code == 200
        count_data = response.json()
        print(f"✅ Final topic count: {count_data['total']}")
        
        print("\n" + "=" * 50)
        print("🎉 Stage 3.2 Topic Management System - ALL TESTS PASSED!")
        print("✅ CRUD operations working")
        print("✅ Statistics calculation working") 
        print("✅ Search functionality working")
        print("✅ Analytics framework ready")
        print("✅ Batch operations working")
        print("✅ Authentication integration working")
        print("\n🚀 Ready for Stage 3.3: PDF Management!")

if __name__ == "__main__":
    asyncio.run(test_topic_endpoints())