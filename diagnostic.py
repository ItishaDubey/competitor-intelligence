import sys
import os
import asyncio
import importlib.util

# 1. ADD LOCAL PATHS
sys.path.append(os.getcwd())

def print_status(component, status, message=""):
    icon = "✅" if status else "❌"
    print(f"{icon} [{component}]: {message}")

async def check_mongo():
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        # Default Mac Homebrew MongoDB URL
        url = "mongodb://localhost:27017"
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        print_status("MongoDB", True, "Connection successful")
        return True
    except ImportError:
        print_status("MongoDB", False, "Motor library missing (pip install motor)")
    except Exception as e:
        print_status("MongoDB", False, f"Connection failed: {str(e)}")
        print("   -> Run: brew services start mongodb-community")
    return False

def check_dependencies():
    required = [
        "fastapi", "uvicorn", "motor", "pydantic", 
        "email_validator", "passlib", "jose", "multipart"
    ]
    all_good = True
    for package in required:
        if importlib.util.find_spec(package) is None:
            # Handle package name differences
            if package == "email_validator" and importlib.util.find_spec("email_validator"): continue
            if package == "multipart" and importlib.util.find_spec("python_multipart"): continue
            if package == "jose" and importlib.util.find_spec("jose"): continue
            
            print_status("Dependency", False, f"Missing {package}")
            all_good = False
    
    if all_good:
        print_status("Dependencies", True, "All required packages installed")
    else:
        print("   -> Run: pip install fastapi uvicorn motor email-validator passlib[bcrypt] python-jose[cryptography] python-multipart")

def check_imports():
    try:
        # Simulate how Uvicorn imports the app
        from backend.server import app
        print_status("Backend Code", True, "backend/server.py compiles successfully")
    except ImportError as e:
        print_status("Backend Code", False, f"Import Error: {e}")
        if "scraper" in str(e):
            print("   -> Issue: 'scraper.py' not found in backend folder or circular import.")
        if "analysis" in str(e):
            print("   -> Issue: 'analysis.py' not found in backend folder.")
    except Exception as e:
        print_status("Backend Code", False, f"Crash on startup: {e}")

async def main():
    print("="*40)
    print("🛠  COMPETITOR INTELLIGENCE DIAGNOSTIC")
    print("="*40)
    
    check_dependencies()
    await check_mongo()
    check_imports()
    
    print("="*40)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    