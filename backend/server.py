import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# --- IMPORTS ---
try:
    from backend.scraper import scrape_url_smart
    from backend.analysis import generate_strategic_brief
except ImportError:
    from scraper import scrape_url_smart
    from analysis import generate_strategic_brief

# --- CONFIG ---
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "competitive_intelligence"
JWT_SECRET = "agent_2026_secure_key"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
    yield
    if client: client.close()

app = FastAPI(title="Competitor Intelligence Agent", lifespan=lifespan)

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

class CompetitorCreate(BaseModel):
    name: str
    website: str
    is_baseline: bool = False

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    is_baseline: Optional[bool] = None

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
        return {"id": payload.get("sub"), "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# --- AUTH ROUTES ---
@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    email_clean = user.email.lower()
    if await db.users.find_one({"email": email_clean}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = pwd_context.hash(user.password)
    res = await db.users.insert_one({
        "name": user.name, "email": email_clean, "password": hashed_pw, 
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    uid = str(res.inserted_id)
    return {"access_token": create_token(uid, email_clean), "user": {"id": uid, "name": user.name, "email": email_clean}}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    u = await db.users.find_one({"email": user.email.lower()})
    if not u or not pwd_context.verify(user.password, u["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    uid = str(u["_id"])
    return {"access_token": create_token(uid, u["email"]), "user": {"id": uid, "name": u["name"], "email": u["email"]}}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    return {"id": str(u["_id"]), "name": u["name"], "email": u["email"]} if u else {}

# --- COMPETITOR ROUTES ---
@app.get("/api/competitors")
async def list_competitors(current_user: dict = Depends(get_current_user)):
    comps = await db.competitors.find({"user_id": current_user["id"]}).to_list(100)
    for c in comps: c["id"] = str(c["_id"]); del c["_id"]
    return comps

@app.post("/api/competitors")
async def create_competitor(comp: CompetitorCreate, current_user: dict = Depends(get_current_user)):
    if comp.is_baseline:
        await db.competitors.update_many({"user_id": current_user["id"]}, {"$set": {"is_baseline": False}})
    doc = comp.dict(); doc["user_id"] = current_user["id"]
    res = await db.competitors.insert_one(doc)
    doc["id"] = str(res.inserted_id); del doc["_id"]
    return doc

@app.put("/api/competitors/{comp_id}")
async def update_competitor(comp_id: str, comp: CompetitorUpdate, current_user: dict = Depends(get_current_user)):
    data = {k: v for k, v in comp.dict().items() if v is not None}
    if comp.is_baseline:
        await db.competitors.update_many({"user_id": current_user["id"]}, {"$set": {"is_baseline": False}})
    res = await db.competitors.update_one({"_id": ObjectId(comp_id), "user_id": current_user["id"]}, {"$set": data})
    if res.matched_count == 0: raise HTTPException(404, detail="Competitor not found")
    return {"status": "updated", "id": comp_id}

@app.delete("/api/competitors/{comp_id}")
async def delete_competitor(comp_id: str, current_user: dict = Depends(get_current_user)):
    res = await db.competitors.delete_one({"_id": ObjectId(comp_id), "user_id": current_user["id"]})
    if res.deleted_count == 0: raise HTTPException(404, detail="Competitor not found")
    return {"status": "deleted"}

# --- REPORT ROUTES ---
async def run_scan_task(user_id: str):
    comps = await db.competitors.find({"user_id": user_id}).to_list(100)
    if not comps: return
    baseline = next((c for c in comps if c.get("is_baseline")), None)
    baseline_data = await scrape_url_smart(baseline['website']) if baseline else None
    
    results = []
    for c in comps:
        if not c.get("is_baseline"):
            data = await scrape_url_smart(c['website'])
            results.append({**data, "name": c['name']})
    
    brief = generate_strategic_brief(results, baseline_data)
    await db.reports.insert_one({
        "user_id": user_id, "report_date": datetime.now(timezone.utc).strftime("%B %d, %Y"), 
        "brief_data": brief, "created_at": datetime.now(timezone.utc).isoformat()
    })

@app.post("/api/reports/run")
async def run_scan(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    background_tasks.add_task(run_scan_task, current_user["id"])
    return {"status": "started"}

@app.get("/api/reports")
async def get_reports(current_user: dict = Depends(get_current_user)):
    reports = await db.reports.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(20)
    for r in reports: r["id"] = str(r["_id"]); del r["_id"]
    return reports

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    return {
        "competitors_count": await db.competitors.count_documents({"user_id": current_user["id"]}),
        "reports_count": await db.reports.count_documents({"user_id": current_user["id"]}),
        "active_alerts": 0 
    }

@app.get("/api/reports/latest/summary")
async def get_latest_summary(current_user: dict = Depends(get_current_user)):
    latest = await db.reports.find_one({"user_id": current_user["id"]}, sort=[("created_at", -1)])
    return {"summary": (latest["brief_data"][:200] + "...") if latest else "No reports yet."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)