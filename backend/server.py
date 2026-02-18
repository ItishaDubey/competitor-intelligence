import os
import re
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# --- NEW MODULE IMPORTS ---
# Ensure backend/scraper.py and backend/analysis.py exist!
from .scraper import scrape_url_smart
from .analysis import generate_strategic_brief

# --- CONFIG ---
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "competitive_intelligence"
JWT_SECRET = os.environ.get("JWT_SECRET", "super_secret_key_change_me")

# --- AUTH SETUP ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# --- DATABASE SETUP ---
client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        # Verify connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
        
        # Create indexes
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
    yield
    if client:
        client.close()

app = FastAPI(title="Competitive Intelligence API", lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PageConfig(BaseModel):
    url: str
    name: Optional[str] = None

class CompetitorCreate(BaseModel):
    name: str
    website: str
    is_baseline: bool = False
    pages_to_monitor: List[PageConfig] = []

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# --- HELPERS ---
def create_token(user_id: str, email: str):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id: raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- AUTH ENDPOINTS ---

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    if not db: raise HTTPException(status_code=500, detail="Database not connected")
    
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = pwd_context.hash(user.password)
    user_doc = {
        "name": user.name,
        "email": user.email,
        "password": hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    token = create_token(user_id, user.email)
    return {
        "access_token": token,
        "user": {"id": user_id, "name": user.name, "email": user.email}
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    if not db: raise HTTPException(status_code=500, detail="Database not connected")

    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(str(db_user["_id"]), db_user["email"])
    return {
        "access_token": token,
        "user": {"id": str(db_user["_id"]), "name": db_user["name"], "email": db_user["email"]}
    }

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    if not user: raise HTTPException(status_code=404)
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}

# --- COMPETITOR ENDPOINTS ---

@app.get("/api/competitors")
async def list_competitors(current_user: dict = Depends(get_current_user)):
    comps = await db.competitors.find({"user_id": current_user["id"]}).to_list(100)
    for c in comps: c["id"] = str(c["_id"]); del c["_id"]
    return comps

@app.post("/api/competitors")
async def create_competitor(comp: CompetitorCreate, current_user: dict = Depends(get_current_user)):
    # Unset other baselines if this is one
    if comp.is_baseline:
        await db.competitors.update_many(
            {"user_id": current_user["id"], "is_baseline": True},
            {"$set": {"is_baseline": False}}
        )

    doc = comp.dict()
    doc["user_id"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    
    res = await db.competitors.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    del doc["_id"]
    return doc

# --- REPORT & SCAN ENDPOINTS (THE NEW LOGIC) ---

async def run_scan_task(user_id: str):
    """Background task: Scrapes sites & generates the Strategic Brief"""
    print(f"🚀 Starting scan for user {user_id}")
    
    # 1. Fetch competitors
    competitors = await db.competitors.find({"user_id": user_id}).to_list(100)
    if not competitors:
        print("⚠️ No competitors found for scan.")
        return

    scraped_results = []
    baseline_result = None
    
    # 2. Scrape Baseline
    baseline = next((c for c in competitors if c.get("is_baseline")), None)
    if baseline:
        # Get first monitored page
        pages = baseline.get("pages_to_monitor", [])
        url = pages[0].get("url") if pages else baseline.get("website")
        
        if url:
            print(f"  🏠 Scraping Baseline: {baseline['name']} ({url})")
            data = await scrape_url_smart(url)
            baseline_result = {**data, "name": baseline["name"]}

    # 3. Scrape Competitors
    for comp in competitors:
        if comp.get("is_baseline"): continue
        
        pages = comp.get("pages_to_monitor", [])
        url = pages[0].get("url") if pages else comp.get("website")
        
        if url:
            print(f"  🎯 Scraping Competitor: {comp['name']} ({url})")
            data = await scrape_url_smart(url)
            scraped_results.append({**data, "name": comp["name"]})

    # 4. Generate Strategic Brief
    brief = generate_strategic_brief(scraped_results, baseline_result)
    
    # 5. Save Report
    report_doc = {
        "user_id": user_id,
        "report_date": datetime.now(timezone.utc).strftime("%B %d, %Y • %H:%M"),
        "brief_data": brief,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reports.insert_one(report_doc)
    print("✅ Scan Complete. Report Saved.")

@app.post("/api/reports/run")
async def run_scan(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    background_tasks.add_task(run_scan_task, current_user["id"])
    return {"status": "started", "message": "Intelligence scan started in background"}

@app.get("/api/reports")
async def get_reports(current_user: dict = Depends(get_current_user)):
    # Return latest reports first
    reports = await db.reports.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(20)
    for r in reports: r["id"] = str(r["_id"]); del r["_id"]
    return reports

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)