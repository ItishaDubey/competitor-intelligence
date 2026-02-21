import os
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

# ---------------------------------------------------
# SAFE IMPORTS (NO LEGACY DEPENDENCY)
# ---------------------------------------------------

try:
    from backend.scraper import scrape_url_smart
except:
    async def scrape_url_smart(url):
        return {"url": url, "products": []}

# ⭐ Legacy analysis removed safely
def generate_strategic_brief(a, b):
    return "Strategic intelligence handled by CI Agent V3."


# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "competitive_intelligence"
JWT_SECRET = "agent_2026_secure_key"

client = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db

    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)

    yield

    if client:
        client.close()


app = FastAPI(title="CI Agent API", lifespan=lifespan)

# ---------------------------------------------------
# SECURITY
# ---------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# MODELS
# ---------------------------------------------------

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


# ---------------------------------------------------
# AUTH
# ---------------------------------------------------

def create_token(user_id: str, email: str):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return {"id": payload.get("sub"), "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    email = user.email.lower()

    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = pwd_context.hash(user.password)

    res = await db.users.insert_one({
        "name": user.name,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    uid = str(res.inserted_id)

    return {
        "access_token": create_token(uid, email),
        "user": {"id": uid, "name": user.name, "email": email},
    }


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    email = user.email.lower()

    u = await db.users.find_one({"email": email})

    if not u or not pwd_context.verify(user.password, u["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    uid = str(u["_id"])

    return {
        "access_token": create_token(uid, email),
        "user": {"id": uid, "name": u["name"], "email": email},
    }


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    if not u:
        return {}
    return {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}


# ---------------------------------------------------
# COMPETITORS
# ---------------------------------------------------

@app.get("/api/competitors")
async def list_competitors(current_user: dict = Depends(get_current_user)):
    comps = await db.competitors.find(
        {"user_id": current_user["id"]}
    ).to_list(100)

    for c in comps:
        c["id"] = str(c["_id"])
        del c["_id"]

    return comps


@app.post("/api/competitors")
async def create_competitor(
    comp: CompetitorCreate,
    current_user: dict = Depends(get_current_user),
):
    if comp.is_baseline:
        await db.competitors.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"is_baseline": False}},
        )

    doc = comp.dict()
    doc["user_id"] = current_user["id"]

    res = await db.competitors.insert_one(doc)

    doc["id"] = str(res.inserted_id)
    del doc["_id"]

    return doc


# ---------------------------------------------------
# SCAN ENGINE (LEGACY SAFE)
# ---------------------------------------------------

async def run_scan_task(user_id: str):

    print(f"🚀 Starting scan for user {user_id}")

    comps = await db.competitors.find(
        {"user_id": user_id}
    ).to_list(100)

    if not comps:
        return

    baseline = next((c for c in comps if c.get("is_baseline")), None)

    baseline_data = (
        await scrape_url_smart(baseline["website"]) if baseline else None
    )

    results = []

    for c in comps:
        if not c.get("is_baseline"):
            data = await scrape_url_smart(c["website"])
            results.append({**data, "name": c["name"]})

    brief = generate_strategic_brief(results, baseline_data)

    await db.reports.insert_one(
        {
            "user_id": user_id,
            "report_date": datetime.now(timezone.utc).strftime(
                "%B %d, %Y • %H:%M"
            ),
            "brief_data": brief,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    print("✅ Scan complete")


@app.post("/api/reports/run")
async def run_scan(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    background_tasks.add_task(run_scan_task, current_user["id"])
    return {"status": "started"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "db": "connected" if db else "disconnected"}
