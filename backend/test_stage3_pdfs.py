# backend/test_stage3_pdfs.py
"""Comprehensive test script for Stage 3.3 PDF Management"""

import asyncio
import httpx
import json
import io
from datetime import datetime
from pathlib import Path
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "http://localhost:8000"

def create_test_pdf(filename: str, num_pages: int = 5) -> bytes:
    """Create a test PDF file"""
    buffer = io.BytesIO()
    
    # Create PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    
    for page_num in range(1, num_pages + 1):
        p.drawString(100, 750, f"StudySprint Test PDF - Page {page_num}")
        p.drawString(100, 700, f"This is a test PDF created for testing PDF management.")
        p.drawString(100, 650, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.drawString(100, 600, f"Filename: {filename}")
        
        # Add some content
        content_lines = [
            "This PDF contains sample content for testing:",
            "• PDF upload functionality",
            "• Metadata extraction",
            "• Reading position tracking",
            "• Exercise attachment",
            "• Bookmark management",
            "",
            "The StudySprint system should be able to:",
            "1. Upload this PDF successfully",
            "2. Extract the correct number of pages",
            "3. Store file metadata",
            "4. Track reading progress",
            "5. Manage associated exercises"
        ]
        
        y_pos = 550
        for line in content_lines:
            p.drawString(100, y_pos, line)
            y_pos -= 20
        
        p.showPage()
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

async def test_pdf_management():
    """Test the complete PDF management system"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Stage 3.3: PDF Management System")
        print("=" * 60)
        
        # 1. Health check
        print("1. Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✅ Health check passed")
        
        # 2. Register/Login user
        print("\n2. Setting up test user...")
        user_data = {
            "email": "pdftest@studysprint.com",
            "username": "pdftestuser",
            "password": "testpassword123",
            "full_name": "PDF Test User"
        }
        
        # Try to register
        response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        if response.status_code == 201:
            auth_data = response.json()
            token = auth_data["access_token"]
            print("✅ User registered successfully")
        elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
            # User exists, login
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
            print(f"❌ Auth failed: {response.status_code} - {response.text}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create test topic
        print("\n3. Creating test topic...")
        topic_data = {
            "name": "PDF Testing Topic",
            "description": "Topic for testing PDF management features",
            "color": "#e74c3c"
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/topics/", json=topic_data, headers=headers)
        assert response.status_code == 201
        topic = response.json()
        topic_id = topic["id"]
        print(f"✅ Created topic: {topic['name']}")
        
        # 4. Test PDF upload
        print("\n4. Testing PDF upload...")
        
        # Create test PDF
        pdf_content = create_test_pdf("test_document.pdf", 10)
        
        # Upload PDF
        files = {
            "file": ("test_document.pdf", pdf_content, "application/pdf")
        }
        params = {
            "topic_id": topic_id,
            "title": "Test Document for PDF Management",
            "pdf_type": "study"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/upload",
            files=files,
            params=params,
            headers=headers
        )
        
        assert response.status_code == 201
        pdf = response.json()
        pdf_id = pdf["id"]
        print(f"✅ PDF uploaded successfully")
        print(f"   📄 Title: {pdf['title']}")
        print(f"   📊 Pages: {pdf['total_pages']}")
        print(f"   📦 Size: {pdf['file_size']} bytes")
        print(f"   🔄 Status: {pdf['upload_status']}")
        
        # 5. Test PDF retrieval
        print("\n5. Testing PDF retrieval...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/{pdf_id}", headers=headers)
        assert response.status_code == 200
        retrieved_pdf = response.json()
        print(f"✅ PDF retrieved: {retrieved_pdf['title']}")
        
        # 6. Test PDF with stats
        print("\n6. Testing PDF statistics...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/{pdf_id}/stats", headers=headers)
        assert response.status_code == 200
        pdf_stats = response.json()
        print("✅ PDF statistics retrieved")
        stats = pdf_stats["statistics"]
        print(f"   📊 File size: {stats['file_size_mb']} MB")
        print(f"   📈 Reading progress: {stats['reading_progress_percentage']}%")
        print(f"   🔖 Bookmarks: {stats['bookmarks_count']}")
        print(f"   ⏱️ Estimated read time: {stats['estimated_read_time']} minutes")
        
        # 7. Test reading position update
        print("\n7. Testing reading position update...")
        position_data = {
            "page": 5,
            "scroll_y": 250.5,
            "zoom": 1.2
        }
        
        response = await client.put(
            f"{BASE_URL}/api/v1/pdfs/{pdf_id}/reading-position",
            json=position_data,
            headers=headers
        )
        assert response.status_code == 200
        updated_pdf = response.json()
        print(f"✅ Reading position updated to page {updated_pdf['current_page']}")
        
        # 8. Test bookmark creation
        print("\n8. Testing bookmark creation...")
        bookmark_data = {
            "page": 3,
            "title": "Important Section",
            "description": "This section covers key concepts"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/{pdf_id}/bookmarks",
            json=bookmark_data,
            headers=headers
        )
        assert response.status_code == 200
        print("✅ Bookmark created successfully")
        
        # Get bookmarks
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/{pdf_id}/bookmarks", headers=headers)
        assert response.status_code == 200
        bookmarks = response.json()
        print(f"✅ Retrieved {len(bookmarks['bookmarks'])} bookmarks")
        
        # 9. Test exercise set creation
        print("\n9. Testing exercise set creation...")
        exercise_set_data = {
            "main_pdf_id": pdf_id,
            "title": "Practice Problems Set 1",
            "description": "Basic exercises for testing",
            "difficulty_level": 2,
            "estimated_time_minutes": 45
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/{pdf_id}/exercise-sets",
            json=exercise_set_data,
            headers=headers
        )
        assert response.status_code == 201
        exercise_set = response.json()
        exercise_set_id = exercise_set["id"]
        print(f"✅ Exercise set created: {exercise_set['title']}")
        
        # 10. Test exercise creation
        print("\n10. Testing exercise creation...")
        exercise_data = {
            "exercise_set_id": exercise_set_id,
            "title": "Test Exercise 1",
            "description": "First test exercise",
            "difficulty_level": 2,
            "estimated_time_minutes": 15,
            "points_possible": 100
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/exercise-sets/{exercise_set_id}/exercises",
            json=exercise_data,
            headers=headers
        )
        assert response.status_code == 201
        exercise = response.json()
        exercise_id = exercise["id"]
        print(f"✅ Exercise created: {exercise['title']}")
        
        # 11. Test exercise page linking
        print("\n11. Testing exercise page linking...")
        page_links_data = [
            {
                "exercise_id": exercise_id,
                "main_pdf_id": pdf_id,
                "page_number": 2,
                "link_type": "related",
                "relevance_score": 0.9,
                "description": "Related content on page 2"
            },
            {
                "exercise_id": exercise_id,
                "main_pdf_id": pdf_id,
                "page_number": 4,
                "link_type": "prerequisite",
                "relevance_score": 0.8,
                "description": "Prerequisite knowledge on page 4"
            }
        ]
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/exercises/{exercise_id}/page-links",
            json=page_links_data,
            headers=headers
        )
        assert response.status_code == 201
        page_links = response.json()
        print(f"✅ Created {len(page_links)} page links")
        
        # 12. Test getting exercises for page
        print("\n12. Testing exercises for page retrieval...")
        response = await client.get(
            f"{BASE_URL}/api/v1/pdfs/{pdf_id}/pages/2/exercises",
            headers=headers
        )
        assert response.status_code == 200
        page_exercises = response.json()
        print(f"✅ Found {len(page_exercises)} exercises for page 2")
        
        # 13. Test exercise completion
        print("\n13. Testing exercise completion...")
        completion_data = {
            "user_score": 85,
            "notes": "Completed successfully with good understanding"
        }
        
        response = await client.put(
            f"{BASE_URL}/api/v1/pdfs/exercises/{exercise_id}/complete",
            json=completion_data,
            headers=headers
        )
        assert response.status_code == 200
        completed_exercise = response.json()
        print(f"✅ Exercise completed with score: {completed_exercise['user_score']}")
        
        # 14. Test PDF search
        print("\n14. Testing PDF search...")
        search_data = {
            "query": "test document",
            "limit": 10
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pdfs/search",
            json=search_data,
            headers=headers
        )
        assert response.status_code == 200
        search_results = response.json()
        print(f"✅ Search found {search_results['total_results']} results")
        
        # 15. Test PDF streaming
        print("\n15. Testing PDF streaming...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/stream/{pdf_id}", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        print("✅ PDF streaming working")
        
        # 16. Test PDF download
        print("\n16. Testing PDF download...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/download/{pdf_id}", headers=headers)
        assert response.status_code == 200
        print("✅ PDF download working")
        
        # 17. Test reading analytics
        print("\n17. Testing reading analytics...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/analytics/reading-stats", headers=headers)
        assert response.status_code == 200
        analytics = response.json()
        print("✅ Reading analytics generated")
        print(f"   📚 Total PDFs: {analytics['total_pdfs']}")
        print(f"   📄 Total pages: {analytics['total_pages']}")
        print(f"   📖 Pages read: {analytics['pages_read']}")
        print(f"   📊 Reading progress: {analytics['reading_progress_percentage']}%")
        
        # 18. Test enhanced topic stats (with PDF data)
        print("\n18. Testing enhanced topic statistics...")
        response = await client.get(f"{BASE_URL}/api/v1/topics/{topic_id}/stats", headers=headers)
        assert response.status_code == 200
        topic_stats = response.json()
        print("✅ Enhanced topic statistics retrieved")
        stats = topic_stats["statistics"]
        print(f"   📚 Total PDFs: {stats['total_pdfs']}")
        print(f"   📄 Total pages: {stats['total_pages']}")
        print(f"   📖 Pages read: {stats['pages_read']}")
        print(f"   🏋️ Total exercises: {stats['total_exercises']}")
        print(f"   ✅ Completed exercises: {stats['completed_exercises']}")
        
        # 19. Test PDF health check
        print("\n19. Testing PDF service health...")
        response = await client.get(f"{BASE_URL}/api/v1/pdfs/health", headers=headers)
        assert response.status_code == 200
        health = response.json()
        print("✅ PDF service health check passed")
        print(f"   📁 Upload directory: {health['upload_directory']['path']}")
        print(f"   ✅ Directory writable: {health['upload_directory']['writable']}")
        
        # 20. Test bulk delete (cleanup)
        print("\n20. Testing bulk delete (cleanup)...")
        response = await client.delete(
            f"{BASE_URL}/api/v1/pdfs/bulk-delete",
            params={"delete_files": True},
            json=[pdf_id],
            headers=headers
        )
        assert response.status_code == 200
        bulk_result = response.json()
        print(f"✅ Bulk delete completed: {bulk_result['deleted_count']} PDFs deleted")
        
        print("\n" + "=" * 60)
        print("🎉 STAGE 3.3 PDF MANAGEMENT SYSTEM - ALL TESTS PASSED!")
        print("✅ PDF upload and metadata extraction working")
        print("✅ File download and streaming working")
        print("✅ Reading position tracking working")
        print("✅ Bookmark management working")
        print("✅ Exercise creation and linking working")
        print("✅ Exercise page linking working")
        print("✅ Exercise completion tracking working")
        print("✅ PDF search functionality working")
        print("✅ Reading analytics working")
        print("✅ Enhanced topic statistics working")
        print("✅ Bulk operations working")
        print("✅ PDF service health monitoring working")
        print("\n🚀 Ready for Stage 3.4: Timer & Analytics Services!")

if __name__ == "__main__":
    asyncio.run(test_pdf_management())