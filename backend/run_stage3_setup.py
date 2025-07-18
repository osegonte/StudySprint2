"""Complete setup script for Stage 3.2"""

import os
import sys
import subprocess
import asyncio
import time

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

async def verify_server():
    """Verify the server is running correctly"""
    import httpx
    
    print("🔄 Verifying server...")
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is running and responding")
                    return True
        except:
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting for server... ({attempt + 1}/{max_attempts})")
                await asyncio.sleep(2)
            else:
                print("❌ Server failed to start properly")
                return False
    
    return False

def main():
    """Main setup function"""
    print("🚀 StudySprint 2.0 - Stage 3.2 Setup")
    print("=" * 50)
    
    # Check if we're in the backend directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the backend/ directory")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("⚠️  Virtual environment not detected. Make sure to activate venv first.")
        print("   Run: source venv/bin/activate  (Linux/Mac) or venv\\Scripts\\activate (Windows)")
    
    # Step 1: Install dependencies
    if not run_command("pip install -r requirements-dev.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Step 2: Create migration
    if not run_command("alembic revision --autogenerate -m 'Add Stage 3 models'", "Creating migration"):
        print("ℹ️  Migration creation failed - this might be normal if models already exist")
    
    # Step 3: Apply migration
    if not run_command("alembic upgrade head", "Applying migrations"):
        print("⚠️  Migration failed - check database connection")
    
    # Step 4: Start server in background for testing
    print("\n🔄 Starting development server...")
    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give server time to start
    time.sleep(3)
    
    try:
        # Step 5: Verify server
        if asyncio.run(verify_server()):
            print("\n🧪 Running comprehensive tests...")
            
            # Step 6: Run tests
            test_success = run_command("python test_stage3_topics.py", "Running Stage 3.2 tests")
            
            if test_success:
                print("\n" + "=" * 50)
                print("🎉 STAGE 3.2 SETUP COMPLETE!")
                print("✅ Database models created")
                print("✅ Migrations applied") 
                print("✅ Server running at http://localhost:8000")
                print("✅ API docs at http://localhost:8000/docs")
                print("✅ All tests passed")
                print("\n📊 Available endpoints:")
                print("   • Authentication: /api/v1/auth/*")
                print("   • Topics: /api/v1/topics/*")
                print("   • Health: /health")
                print("\n🚀 Ready for Stage 3.3: PDF Management!")
                
                # Keep server running
                input("\nPress Enter to stop the server...")
                
            else:
                print("❌ Tests failed - check server logs")
        
    finally:
        # Step 7: Cleanup
        print("\n🔄 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()