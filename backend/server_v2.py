"""
CI Agent Backend Server – FastAPI + MongoDB

Endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me

  GET    /api/competitors
  POST   /api/competitors
  PUT    /api/competitors/:id
  DELETE /api/competitors/:id

  POST /api/reports/run        (triggers background scan)
  GET  /api/reports            (list reports)
  GET  /api/reports/latest     (latest report JSON)
  GET  /api/dashboard/stats

  GET  /api/health
"""

import os
import json
import asyncio
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

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

MONGO_URL  = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME    = "competitive_intelligence"
JWT_SECRET = os.environ.get("JWT_SECRET", "ci_agent_2026_secret_key")

INTELLIGENCE_DATA_DIR = "intelligence_data"
REPORTS_DIR           = "reports"

client = None
db     = None


# ──────────────────────────────────────────────────────────────
# LIFESPAN
# ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await client.admin.command("ping")
        print("✅ MongoDB connected")
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print(f"❌ MongoDB failed: {e}")
    yield
    if client:
        client.close()


app = FastAPI(title="CI Agent API v2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()


# ──────────────────────────────────────────────────────────────
# MODELS
# ──────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PageMonitor(BaseModel):
    name: str = "Homepage"
    url: Optional[str] = None
    track: list[str] = ["content", "products", "pricing"]

class CompetitorCreate(BaseModel):
    name: str
    website: str
    is_baseline: bool = False
    pages_to_monitor: list[PageMonitor] = []

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    is_baseline: Optional[bool] = None
    pages_to_monitor: Optional[list[PageMonitor]] = None


# ──────────────────────────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────────────────────────

def create_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire},
        JWT_SECRET, algorithm="HS256"
    )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return {"id": payload["sub"], "email": payload["email"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ──────────────────────────────────────────────────────────────
# AUTH ROUTES
# ──────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(user: UserRegister):
    email = user.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    res = await db.users.insert_one({
        "name": user.name,
        "email": email,
        "password": pwd_context.hash(user.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    uid = str(res.inserted_id)
    return {
        "access_token": create_token(uid, email),
        "token_type": "bearer",
        "user": {"id": uid, "name": user.name, "email": email},
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    email = user.email.lower()
    u = await db.users.find_one({"email": email})
    if not u or not pwd_context.verify(user.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    uid = str(u["_id"])
    return {
        "access_token": create_token(uid, email),
        "token_type": "bearer",
        "user": {"id": uid, "name": u["name"], "email": email},
    }

@app.get("/api/auth/me")
async def get_me(cu: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(cu["id"])})
    if not u:
        raise HTTPException(404, "User not found")
    return {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}


# ──────────────────────────────────────────────────────────────
# COMPETITOR ROUTES
# ──────────────────────────────────────────────────────────────

def _ser(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@app.get("/api/competitors")
async def list_competitors(cu: dict = Depends(get_current_user)):
    docs = await db.competitors.find({"user_id": cu["id"]}).to_list(100)
    return [_ser(d) for d in docs]

@app.post("/api/competitors")
async def create_competitor(comp: CompetitorCreate, cu: dict = Depends(get_current_user)):
    if comp.is_baseline:
        await db.competitors.update_many(
            {"user_id": cu["id"]}, {"$set": {"is_baseline": False}}
        )
    doc = comp.model_dump()
    doc["user_id"] = cu["id"]
    doc["status"]  = "active"
    doc["last_checked"] = None
    res = await db.competitors.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    return doc

@app.put("/api/competitors/{comp_id}")
async def update_competitor(
    comp_id: str,
    comp: CompetitorUpdate,
    cu: dict = Depends(get_current_user),
):
    existing = await db.competitors.find_one({"_id": ObjectId(comp_id), "user_id": cu["id"]})
    if not existing:
        raise HTTPException(404, "Competitor not found")

    update = {k: v for k, v in comp.model_dump().items() if v is not None}
    if update.get("is_baseline"):
        await db.competitors.update_many(
            {"user_id": cu["id"]}, {"$set": {"is_baseline": False}}
        )
    await db.competitors.update_one({"_id": ObjectId(comp_id)}, {"$set": update})
    updated = await db.competitors.find_one({"_id": ObjectId(comp_id)})
    return _ser(updated)

@app.delete("/api/competitors/{comp_id}")
async def delete_competitor(comp_id: str, cu: dict = Depends(get_current_user)):
    res = await db.competitors.delete_one({"_id": ObjectId(comp_id), "user_id": cu["id"]})
    if res.deleted_count == 0:
        raise HTTPException(404, "Competitor not found")
    return {"deleted": True}


# ──────────────────────────────────────────────────────────────
# SCAN ENGINE
# ──────────────────────────────────────────────────────────────

async def _run_scan(user_id: str):
    """Background task: build config from DB, run orchestrator, save report."""
    print(f"\n🚀 Running scan for user {user_id}")

    comps = await db.competitors.find({"user_id": user_id}).to_list(100)
    if not comps:
        print("  ⚠️  No competitors configured")
        return

    baseline = next((c for c in comps if c.get("is_baseline")), None)
    competitors = [c for c in comps if not c.get("is_baseline")]

    if not baseline:
        print("  ⚠️  No baseline configured")
        return

    # Build config dict
    config = {
        "baseline": {
            "name": baseline["name"],
            "url": baseline["website"],
        },
        "competitors": [
            {"name": c["name"], "url": c["website"]}
            for c in competitors
        ],
    }

    # Run agent in executor to avoid blocking event loop
    loop = asyncio.get_event_loop()
    try:
        from backend.agent_core.orchestrator_v2 import CIAgentOrchestrator
        digest = await loop.run_in_executor(
            None, lambda: CIAgentOrchestrator(config).run()
        )
    except Exception as e:
        print(f"  ❌ Scan failed: {e}")
        await db.reports.insert_one({
            "user_id": user_id,
            "status": "error",
            "error": str(e),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return

    # Build summary
    total_changes = (digest.get("changes") or {}).get("total", 0)
    all_missing = sum(
        len(c.get("diff", {}).get("missing", []))
        for c in digest.get("competitors", [])
    )

    # Save to DB
    await db.reports.insert_one({
        "user_id":       user_id,
        "status":        "success",
        "report_date":   datetime.now(timezone.utc).strftime("%B %d, %Y • %H:%M"),
        "changes_count": total_changes,
        "gaps_count":    all_missing,
        "digest":        digest,
        "created_at":    datetime.now(timezone.utc).isoformat(),
    })

    # Update last_checked on all competitors
    await db.competitors.update_many(
        {"user_id": user_id},
        {"$set": {"last_checked": datetime.now(timezone.utc).strftime("%b %d, %I:%M %p")}}
    )

    print(f"  ✅ Scan saved to DB")


@app.post("/api/reports/run")
async def run_scan(
    background_tasks: BackgroundTasks,
    cu: dict = Depends(get_current_user),
):
    background_tasks.add_task(_run_scan, cu["id"])
    return {"status": "started", "message": "Scan running in background"}


@app.get("/api/reports")
async def list_reports(cu: dict = Depends(get_current_user)):
    docs = await db.reports.find(
        {"user_id": cu["id"]},
        {"digest": 0}          # exclude heavy digest field from list
    ).sort("created_at", -1).to_list(20)
    return [_ser(d) for d in docs]


@app.get("/api/reports/latest")
async def get_latest_report(cu: dict = Depends(get_current_user)):
    doc = await db.reports.find_one(
        {"user_id": cu["id"], "status": "success"},
        sort=[("created_at", -1)]
    )
    if not doc:
        raise HTTPException(404, "No reports yet")
    return _ser(doc)


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str, cu: dict = Depends(get_current_user)):
    doc = await db.reports.find_one(
        {"_id": ObjectId(report_id), "user_id": cu["id"]}
    )
    if not doc:
        raise HTTPException(404, "Report not found")
    return _ser(doc)


# ──────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
async def dashboard_stats(cu: dict = Depends(get_current_user)):
    comp_count   = await db.competitors.count_documents({"user_id": cu["id"]})
    report_count = await db.reports.count_documents({"user_id": cu["id"], "status": "success"})

    latest = await db.reports.find_one(
        {"user_id": cu["id"], "status": "success"},
        sort=[("created_at", -1)]
    )

    changes_count = latest.get("changes_count", 0) if latest else 0
    ai_insights   = ""

    if latest and latest.get("digest"):
        digest = latest["digest"]
        for comp in digest.get("competitors", []):
            insights = comp.get("insights", {})
            if isinstance(insights, dict) and insights.get("summary"):
                ai_insights += f"### {comp['name']}\n{insights['summary']}\n\n"
                for rec in (insights.get("recommendations") or [])[:2]:
                    ai_insights += f"- {rec}\n"
                ai_insights += "\n"

    return {
        "competitors":       comp_count,
        "reports":           report_count,
        "active_monitors":   comp_count,
        "changes_detected":  changes_count,
        "last_scan":         latest.get("report_date") if latest else None,
        "ai_insights":       ai_insights or "Run a scan to generate AI insights.",
    }


# ──────────────────────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "db": "connected" if db else "disconnected",
        "time": datetime.now(timezone.utc).isoformat(),
    }