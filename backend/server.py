"""
Competitive Intelligence Agent - FastAPI Backend
"""
import os
import re
import json
import hashlib
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

# Database
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "competitive_intelligence")
JWT_SECRET = os.environ.get("JWT_SECRET", "competitive_intel_secret")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB client
client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.competitors.create_index("user_id")
    await db.reports.create_index([("user_id", 1), ("created_at", -1)])
    yield
    client.close()

app = FastAPI(title="Competitive Intelligence Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Pydantic Models ==============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

class PageConfig(BaseModel):
    name: str
    url: str
    track: List[str] = ["content", "products", "pricing"]

class CompetitorCreate(BaseModel):
    name: str
    website: str
    is_baseline: bool = False
    pages_to_monitor: List[PageConfig] = []

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    is_baseline: Optional[bool] = None
    pages_to_monitor: Optional[List[PageConfig]] = None

class CompetitorResponse(BaseModel):
    id: str
    name: str
    website: str
    is_baseline: bool
    pages_to_monitor: List[dict]
    last_checked: Optional[str]
    status: str
    created_at: str

class ReportResponse(BaseModel):
    id: str
    report_date: str
    summary: dict
    detailed_results: List[dict]
    ai_insights: Optional[str]
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============== Auth Helpers ==============

def create_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": user_id, "email": email, "exp": expire}, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== Auth Endpoints ==============

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = pwd_context.hash(user.password)
    user_doc = {
        "email": user.email,
        "password": hashed,
        "name": user.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    token = create_token(user_id, user.email)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user.email, name=user.name, created_at=user_doc["created_at"])
    )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(db_user["_id"])
    token = create_token(user_id, user.email)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, 
            email=db_user["email"], 
            name=db_user["name"], 
            created_at=db_user["created_at"]
        )
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    return UserResponse(
        id=current_user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"]
    )

# ============== Competitor Endpoints ==============

@app.post("/api/competitors", response_model=CompetitorResponse)
async def create_competitor(competitor: CompetitorCreate, current_user: dict = Depends(get_current_user)):
    # If setting as baseline, unset other baselines
    if competitor.is_baseline:
        await db.competitors.update_many(
            {"user_id": current_user["id"], "is_baseline": True},
            {"$set": {"is_baseline": False}}
        )
    
    comp_doc = {
        "user_id": current_user["id"],
        "name": competitor.name,
        "website": competitor.website,
        "is_baseline": competitor.is_baseline,
        "pages_to_monitor": [p.model_dump() for p in competitor.pages_to_monitor],
        "last_checked": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.competitors.insert_one(comp_doc)
    comp_doc["id"] = str(result.inserted_id)
    return CompetitorResponse(
        id=comp_doc["id"],
        name=comp_doc["name"],
        website=comp_doc["website"],
        is_baseline=comp_doc["is_baseline"],
        pages_to_monitor=comp_doc["pages_to_monitor"],
        last_checked=comp_doc["last_checked"],
        status=comp_doc["status"],
        created_at=comp_doc["created_at"]
    )

@app.get("/api/competitors", response_model=List[CompetitorResponse])
async def list_competitors(current_user: dict = Depends(get_current_user)):
    competitors = await db.competitors.find({"user_id": current_user["id"]}).to_list(100)
    return [
        CompetitorResponse(
            id=str(c["_id"]),
            name=c["name"],
            website=c["website"],
            is_baseline=c.get("is_baseline", False),
            pages_to_monitor=c.get("pages_to_monitor", []),
            last_checked=c.get("last_checked"),
            status=c.get("status", "pending"),
            created_at=c["created_at"]
        )
        for c in competitors
    ]

@app.get("/api/competitors/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(competitor_id: str, current_user: dict = Depends(get_current_user)):
    competitor = await db.competitors.find_one({"_id": ObjectId(competitor_id), "user_id": current_user["id"]})
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return CompetitorResponse(
        id=str(competitor["_id"]),
        name=competitor["name"],
        website=competitor["website"],
        is_baseline=competitor.get("is_baseline", False),
        pages_to_monitor=competitor.get("pages_to_monitor", []),
        last_checked=competitor.get("last_checked"),
        status=competitor.get("status", "pending"),
        created_at=competitor["created_at"]
    )

@app.put("/api/competitors/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(competitor_id: str, update: CompetitorUpdate, current_user: dict = Depends(get_current_user)):
    competitor = await db.competitors.find_one({"_id": ObjectId(competitor_id), "user_id": current_user["id"]})
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if "pages_to_monitor" in update_data:
        update_data["pages_to_monitor"] = [p if isinstance(p, dict) else p.model_dump() for p in update_data["pages_to_monitor"]]
    
    # If setting as baseline, unset other baselines
    if update_data.get("is_baseline"):
        await db.competitors.update_many(
            {"user_id": current_user["id"], "is_baseline": True, "_id": {"$ne": ObjectId(competitor_id)}},
            {"$set": {"is_baseline": False}}
        )
    
    if update_data:
        await db.competitors.update_one({"_id": ObjectId(competitor_id)}, {"$set": update_data})
    
    updated = await db.competitors.find_one({"_id": ObjectId(competitor_id)})
    return CompetitorResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        website=updated["website"],
        is_baseline=updated.get("is_baseline", False),
        pages_to_monitor=updated.get("pages_to_monitor", []),
        last_checked=updated.get("last_checked"),
        status=updated.get("status", "pending"),
        created_at=updated["created_at"]
    )

@app.delete("/api/competitors/{competitor_id}")
async def delete_competitor(competitor_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.competitors.delete_one({"_id": ObjectId(competitor_id), "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "deleted"}

# ============== Intelligence Agent ==============

class IntelligenceAgent:
    def __init__(self):
        self.junk_keywords = ['about', 'terms', 'privacy', 'legal', 'cookie', 'contact', 'support', 'faq', 'career', 'press']
    
    def clean_soup(self, soup):
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'nav', 'header', 'footer']):
            tag.decompose()
        return soup
    
    def extract_prices(self, text):
        prices = []
        patterns = [r'\$(\d+(?:\.\d{2})?)', r'₹(\d+)', r'Rs\.?\s*(\d+)']
        for pattern in patterns:
            for match in re.findall(pattern, text):
                try:
                    price = float(match)
                    if 0.1 <= price <= 999999:
                        prices.append(price)
                except:
                    pass
        return sorted(list(set(prices)))
    
    def extract_products(self, soup, url):
        products = []
        all_divs = soup.find_all('div', recursive=True)
        seen_names = set()
        
        for div in all_divs:
            if len(str(div)) > 5000:
                continue
            text_content = div.get_text(strip=True)
            if not text_content or len(text_content) < 5 or len(text_content) > 500:
                continue
            if any(kw in text_content.lower() for kw in self.junk_keywords):
                continue
            
            has_image = div.find('img') is not None
            has_link = div.find('a') is not None
            
            if (has_image or has_link) and len(text_content) < 200:
                title = None
                for tag in div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'span', 'p', 'div']):
                    t = tag.get_text(strip=True)
                    if t and 5 < len(t) < 100 and not any(kw in t.lower() for kw in self.junk_keywords):
                        title = t
                        break
                
                if not title:
                    lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                    if lines:
                        title = lines[0]
                
                if title and 3 < len(title) < 150 and title not in seen_names:
                    seen_names.add(title)
                    discount = None
                    match = re.search(r'([\d.]+)%\s*[Oo]ff', text_content)
                    if match:
                        discount = f"{match.group(1)}% off"
                    
                    price = None
                    for pattern in [r'\$(\d+(?:\.\d{2})?)', r'₹(\d+)', r'Rs\.?\s*(\d+)']:
                        m = re.search(pattern, text_content)
                        if m:
                            price = f"${m.group(1)}"
                            break
                    
                    products.append({
                        'name': title,
                        'discount': discount,
                        'price': price
                    })
        
        return products[:30]
    
    def analyze_page(self, url, track_options):
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = self.clean_soup(soup)
            
            analysis = {
                'url': url,
                'checked_at': datetime.now(timezone.utc).isoformat(),
                'products': [],
                'content_hash': hashlib.md5(soup.get_text()[:5000].encode()).hexdigest()
            }
            
            if 'products' in track_options or 'content' in track_options:
                products = self.extract_products(soup, url)
                analysis['products'] = products
            
            if 'pricing' in track_options or 'prices' in track_options:
                text = soup.get_text()
                prices = self.extract_prices(text)
                if prices:
                    analysis['price_range'] = {
                        'min': min(prices),
                        'max': max(prices),
                        'avg': round(sum(prices) / len(prices), 2),
                        'count': len(prices)
                    }
            
            return analysis
        except Exception as e:
            return {'url': url, 'error': str(e), 'checked_at': datetime.now(timezone.utc).isoformat()}
    
    def compare_data(self, current, previous):
        if not previous:
            return {'is_first_run': True}
        
        changes = {}
        curr_products = current.get('products', [])
        prev_products = previous.get('products', [])
        
        curr_names = {p.get('name') for p in curr_products if p.get('name')}
        prev_names = {p.get('name') for p in prev_products if p.get('name')}
        
        added = list(curr_names - prev_names)[:10]
        removed = list(prev_names - curr_names)[:10]
        
        if added:
            changes['new_products'] = added
        if removed:
            changes['removed_products'] = removed
        
        if current.get('content_hash') != previous.get('content_hash'):
            changes['content_changed'] = True
        
        if 'price_range' in current and 'price_range' in previous:
            curr_avg = current['price_range']['avg']
            prev_avg = previous['price_range']['avg']
            diff_pct = ((curr_avg - prev_avg) / prev_avg) * 100 if prev_avg else 0
            if abs(diff_pct) > 5:
                changes['avg_price_change'] = {
                    'old_avg': prev_avg,
                    'new_avg': curr_avg,
                    'change_pct': round(diff_pct, 1)
                }
        
        return changes if changes else None

agent = IntelligenceAgent()

# ============== AI Insights ==============

async def generate_ai_insights(report_data: dict) -> str:
    if not EMERGENT_LLM_KEY:
        return "AI insights unavailable - API key not configured"
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ci-insights-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            system_message="You are a competitive intelligence analyst. Analyze the competitor data and provide strategic insights, trends, and actionable recommendations. Be concise but insightful."
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        summary = report_data.get('summary', {})
        results = report_data.get('detailed_results', [])
        
        prompt = f"""Analyze this competitive intelligence report:

Summary:
- Companies monitored: {summary.get('companies_monitored', 0)}
- Total products tracked: {summary.get('total_products_tracked', 0)}
- Changes detected: {summary.get('changes_detected', 0)}

Detailed findings:
"""
        for r in results[:5]:
            prompt += f"\n{r.get('company', 'Unknown')}:"
            prompt += f"\n  - Products found: {r.get('products_found', 0)}"
            if r.get('price_range'):
                pr = r['price_range']
                prompt += f"\n  - Price range: ${pr.get('min', 0):.2f} - ${pr.get('max', 0):.2f}"
            if r.get('changes'):
                prompt += f"\n  - Changes: {json.dumps(r['changes'])}"
            if r.get('sample_products'):
                prompt += f"\n  - Sample products: {[p.get('name') for p in r['sample_products'][:3]]}"
        
        prompt += "\n\nProvide 3-5 key strategic insights and recommendations based on this data."
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        return f"Error generating insights: {str(e)}"

# ============== Report Endpoints ==============

@app.post("/api/reports/run")
async def run_intelligence_scan(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Trigger a new intelligence scan"""
    competitors = await db.competitors.find({"user_id": current_user["id"]}).to_list(100)
    
    if not competitors:
        raise HTTPException(status_code=400, detail="No competitors configured. Add at least one competitor first.")
    
    background_tasks.add_task(run_scan_task, current_user["id"], competitors)
    return {"status": "started", "message": "Intelligence scan started in background"}

async def run_scan_task(user_id: str, competitors: list):
    """Background task to run the scan"""
    results = []
    baseline_data = None
    
    # Find baseline
    baseline = next((c for c in competitors if c.get("is_baseline")), None)
    
    if baseline:
        for page in baseline.get("pages_to_monitor", []):
            data = agent.analyze_page(page["url"], page.get("track", ["products"]))
            if data and not data.get("error"):
                baseline_data = data
                
                # Get previous data for comparison
                prev_report = await db.reports.find_one(
                    {"user_id": user_id},
                    sort=[("created_at", -1)]
                )
                prev_data = None
                if prev_report:
                    for r in prev_report.get("detailed_results", []):
                        if r.get("company") == baseline["name"]:
                            prev_data = r.get("raw_data")
                            break
                
                changes = agent.compare_data(data, prev_data)
                
                result = {
                    "company": baseline["name"],
                    "is_baseline": True,
                    "url": page["url"],
                    "products_found": len(data.get("products", [])),
                    "price_range": data.get("price_range"),
                    "sample_products": data.get("products", [])[:5],
                    "raw_data": data
                }
                if changes and not changes.get("is_first_run"):
                    result["changes"] = changes
                results.append(result)
        
        await db.competitors.update_one(
            {"_id": baseline["_id"]},
            {"$set": {"last_checked": datetime.now(timezone.utc).isoformat(), "status": "active"}}
        )
    
    # Process competitors
    for comp in competitors:
        if comp.get("is_baseline"):
            continue
        
        for page in comp.get("pages_to_monitor", []):
            data = agent.analyze_page(page["url"], page.get("track", ["products"]))
            if data and not data.get("error"):
                # Get previous data for comparison
                prev_report = await db.reports.find_one(
                    {"user_id": user_id},
                    sort=[("created_at", -1)]
                )
                prev_data = None
                if prev_report:
                    for r in prev_report.get("detailed_results", []):
                        if r.get("company") == comp["name"]:
                            prev_data = r.get("raw_data")
                            break
                
                changes = agent.compare_data(data, prev_data)
                
                result = {
                    "company": comp["name"],
                    "is_baseline": False,
                    "url": page["url"],
                    "products_found": len(data.get("products", [])),
                    "price_range": data.get("price_range"),
                    "sample_products": data.get("products", [])[:5],
                    "raw_data": data
                }
                if changes and not changes.get("is_first_run"):
                    result["changes"] = changes
                
                # Compare with baseline if available
                if baseline_data:
                    base_count = len(baseline_data.get('products', []))
                    comp_count = len(data.get('products', []))
                    insights = []
                    
                    if base_count > 0 and comp_count > 0:
                        if comp_count > base_count * 1.3:
                            insights.append({
                                'type': 'product_range',
                                'priority': 'medium',
                                'message': f"{comp['name']} offers {comp_count} products vs your {base_count}",
                                'recommendation': 'Consider expanding product range'
                            })
                    
                    base_prices = baseline_data.get('price_range')
                    comp_prices = data.get('price_range')
                    
                    if base_prices and comp_prices:
                        base_avg = base_prices.get('avg', 0)
                        comp_avg = comp_prices.get('avg', 0)
                        if base_avg:
                            diff_pct = ((comp_avg - base_avg) / base_avg) * 100
                            if abs(diff_pct) > 10:
                                insights.append({
                                    'type': 'pricing',
                                    'priority': 'high' if abs(diff_pct) > 20 else 'medium',
                                    'message': f"{comp['name']} avg price is {diff_pct:+.1f}% vs yours",
                                    'recommendation': 'Review pricing' if diff_pct < 0 else 'Maintain pricing'
                                })
                    
                    if insights:
                        result['insights'] = insights
                
                results.append(result)
        
        await db.competitors.update_one(
            {"_id": comp["_id"]},
            {"$set": {"last_checked": datetime.now(timezone.utc).isoformat(), "status": "active"}}
        )
    
    # Generate digest
    total_products = sum(r.get('products_found', 0) for r in results)
    has_changes = sum(1 for r in results if r.get('changes'))
    has_insights = sum(1 for r in results if r.get('insights'))
    
    report_data = {
        "report_date": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "companies_monitored": len(results),
            "total_products_tracked": total_products,
            "changes_detected": has_changes,
            "insights_generated": has_insights
        },
        "detailed_results": results
    }
    
    # Generate AI insights
    ai_insights = await generate_ai_insights(report_data)
    
    # Save report
    report_doc = {
        "user_id": user_id,
        "report_date": report_data["report_date"],
        "summary": report_data["summary"],
        "detailed_results": results,
        "ai_insights": ai_insights,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reports.insert_one(report_doc)

@app.get("/api/reports", response_model=List[ReportResponse])
async def list_reports(limit: int = 10, current_user: dict = Depends(get_current_user)):
    reports = await db.reports.find(
        {"user_id": current_user["id"]}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [
        ReportResponse(
            id=str(r["_id"]),
            report_date=r["report_date"],
            summary=r["summary"],
            detailed_results=[{k: v for k, v in res.items() if k != "raw_data"} for res in r.get("detailed_results", [])],
            ai_insights=r.get("ai_insights"),
            created_at=r["created_at"]
        )
        for r in reports
    ]

@app.get("/api/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    report = await db.reports.find_one({"_id": ObjectId(report_id), "user_id": current_user["id"]})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        id=str(report["_id"]),
        report_date=report["report_date"],
        summary=report["summary"],
        detailed_results=[{k: v for k, v in res.items() if k != "raw_data"} for res in report.get("detailed_results", [])],
        ai_insights=report.get("ai_insights"),
        created_at=report["created_at"]
    )

@app.get("/api/reports/latest/summary")
async def get_latest_summary(current_user: dict = Depends(get_current_user)):
    report = await db.reports.find_one(
        {"user_id": current_user["id"]},
        sort=[("created_at", -1)]
    )
    
    if not report:
        return {
            "has_report": False,
            "summary": None,
            "last_scan": None
        }
    
    return {
        "has_report": True,
        "summary": report["summary"],
        "last_scan": report["created_at"],
        "ai_insights": report.get("ai_insights")
    }

# ============== Dashboard Stats ==============

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    competitors_count = await db.competitors.count_documents({"user_id": current_user["id"]})
    reports_count = await db.reports.count_documents({"user_id": current_user["id"]})
    
    latest_report = await db.reports.find_one(
        {"user_id": current_user["id"]},
        sort=[("created_at", -1)]
    )
    
    active_count = await db.competitors.count_documents({"user_id": current_user["id"], "status": "active"})
    
    return {
        "competitors_tracked": competitors_count,
        "total_reports": reports_count,
        "active_monitors": active_count,
        "last_scan": latest_report["created_at"] if latest_report else None,
        "latest_summary": latest_report["summary"] if latest_report else None,
        "changes_this_week": latest_report["summary"].get("changes_detected", 0) if latest_report else 0
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
