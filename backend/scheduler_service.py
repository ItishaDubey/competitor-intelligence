"""
scheduler_service.py – APScheduler integration for the FastAPI backend.

Runs the CI agent every 24 hours automatically.
Import this in server_v2.py lifespan to activate.

Usage in lifespan:
    from backend.scheduler_service import start_scheduler, stop_scheduler
    start_scheduler(db)
    ...
    stop_scheduler()
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler = AsyncIOScheduler()
_db = None


async def _run_all_users_scan():
    """Scan all users' configured competitors."""
    if _db is None:
        return

    print(f"\n🕐 Scheduled scan starting at {datetime.now(timezone.utc).isoformat()}")

    # Get all unique user IDs with competitors
    cursor = _db.competitors.aggregate([
        {"$group": {"_id": "$user_id"}}
    ])
    user_ids = [doc["_id"] async for doc in cursor]

    print(f"  👥 Running scans for {len(user_ids)} user(s)")

    for user_id in user_ids:
        try:
            await _scan_user(user_id)
        except Exception as e:
            print(f"  ❌ Scan failed for user {user_id}: {e}")


async def _scan_user(user_id: str):
    comps = await _db.competitors.find({"user_id": user_id}).to_list(100)
    if not comps:
        return

    baseline = next((c for c in comps if c.get("is_baseline")), None)
    competitors = [c for c in comps if not c.get("is_baseline")]

    if not baseline:
        print(f"  ⚠️  No baseline for user {user_id}")
        return

    config = {
        "baseline": {"name": baseline["name"], "url": baseline["website"]},
        "competitors": [{"name": c["name"], "url": c["website"]} for c in competitors],
    }

    loop = asyncio.get_event_loop()

    from backend.agent_core.orchestrator_v2 import CIAgentOrchestrator
    digest = await loop.run_in_executor(
        None, lambda: CIAgentOrchestrator(config).run()
    )

    total_changes = (digest.get("changes") or {}).get("total", 0)
    all_missing = sum(
        len(c.get("diff", {}).get("missing", []))
        for c in digest.get("competitors", [])
    )

    await _db.reports.insert_one({
        "user_id":       user_id,
        "status":        "success",
        "report_date":   datetime.now(timezone.utc).strftime("%B %d, %Y • %H:%M"),
        "changes_count": total_changes,
        "gaps_count":    all_missing,
        "digest":        digest,
        "created_at":    datetime.now(timezone.utc).isoformat(),
    })

    await _db.competitors.update_many(
        {"user_id": user_id},
        {"$set": {"last_checked": datetime.now(timezone.utc).strftime("%b %d, %I:%M %p")}}
    )

    print(f"  ✅ Scan complete for user {user_id} – {total_changes} changes, {all_missing} gaps")


def start_scheduler(db_instance):
    global _db
    _db = db_instance

    # Run daily at 9 AM UTC (2:30 PM IST)
    _scheduler.add_job(
        _run_all_users_scan,
        CronTrigger(hour=9, minute=0),
        id="daily_scan",
        name="Daily Competitive Intelligence Scan",
        replace_existing=True,
    )

    _scheduler.start()
    print("⏰ Scheduler started – daily scans at 09:00 UTC")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
        print("⏰ Scheduler stopped")