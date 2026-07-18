from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import get_collection
from backend.auth import get_current_user
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

async def get_topic_domain_mapping():
    topics_coll = get_collection("topics")
    cursor = topics_coll.find({}, {"slug": 1, "domain_slug": 1})
    mapping = {}
    async for doc in cursor:
        mapping[doc["slug"]] = doc["domain_slug"]
    return mapping

async def get_domain_titles():
    domains_coll = get_collection("domains")
    cursor = domains_coll.find({}, {"slug": 1, "title": 1})
    mapping = {}
    async for doc in cursor:
        mapping[doc["slug"]] = doc["title"]
    return mapping

@router.get("/overview")
async def get_overview(current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    activity_coll = get_collection("activity_log")
    progress_coll = get_collection("user_progress")
    
    # 1. Total study minutes
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$minutes_spent"}}}
    ]
    total_cursor = activity_coll.aggregate(pipeline)
    total_minutes = 0
    async for result in total_cursor:
        total_minutes = result.get("total", 0)
        
    # 2. Domains Active and Problems Solved
    # Get all user progress
    progress_cursor = progress_coll.find({"user_id": user_id})
    completed_problems = 0
    active_domains = set()
    
    # Load mapping from topic to domain
    topic_to_domain = await get_topic_domain_mapping()
    
    async for doc in progress_cursor:
        status_val = doc.get("status")
        topic_slug = doc.get("topic_slug")
        
        if status_val == "completed":
            completed_problems += 1
            
        domain_slug = topic_to_domain.get(topic_slug)
        if domain_slug:
            active_domains.add(domain_slug)
            
    # 3. Consistency (percentage of days active in last 30 days)
    now = datetime.now()
    start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    
    active_days_cursor = await activity_coll.distinct("date", {
        "user_id": user_id,
        "date": {"$gte": start_date}
    })
    active_days_count = len(active_days_cursor)
    consistency_pct = round((active_days_count / 30.0) * 100)
    
    return {
        "total_minutes": total_minutes,
        "domains_active": len(active_domains),
        "problems_solved": completed_problems,
        "consistency_pct": consistency_pct
    }

@router.get("/domain-time")
async def get_domain_time(period: int = 30, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    activity_coll = get_collection("activity_log")
    
    now = datetime.now()
    start_date = (now - timedelta(days=period)).strftime("%Y-%m-%d")
    
    # Fetch mapping helpers
    topic_to_domain = await get_topic_domain_mapping()
    domain_to_title = await get_domain_titles()
    
    # Fetch all activity logs in the range
    cursor = activity_coll.find({
        "user_id": user_id,
        "date": {"$gte": start_date}
    })
    
    # We will group by date, and map categories/domains
    # Columns in chart will be dates, stacked by domain/activity title
    raw_data = []
    async for doc in cursor:
        raw_data.append(doc)
        
    # Get unique domain/activity titles to define chart series
    series_names = set(["Aptitude Test", "Programming Playground"])
    for title in domain_to_title.values():
        series_names.add(title)
        
    # Group by date
    grouped = {}
    for doc in raw_data:
        date_str = doc["date"]
        minutes = doc.get("minutes_spent", 0)
        activity_type = doc.get("activity_type")
        topic_slug = doc.get("topic_slug")
        
        # Determine category title
        category = "Programming Playground"
        if activity_type == "quiz":
            category = "Aptitude Test"
        elif topic_slug and topic_slug in topic_to_domain:
            domain_slug = topic_to_domain[topic_slug]
            category = domain_to_title.get(domain_slug, "Programming Playground")
        elif activity_type == "practice":
            category = "Programming Playground"
            
        if date_str not in grouped:
            grouped[date_str] = {s: 0 for s in series_names}
            
        grouped[date_str][category] = grouped[date_str].get(category, 0) + minutes
        
    # Sort dates
    sorted_dates = sorted(grouped.keys())
    
    # Format for chart (list of dicts, each having 'date' and the value for each domain)
    result = []
    for d in sorted_dates:
        row = {"date": d}
        row.update(grouped[d])
        result.append(row)
        
    return {
        "series": list(series_names),
        "data": result
    }

@router.get("/problems-solved")
async def get_problems_solved(period: int = 30, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    progress_coll = get_collection("user_progress")
    
    # Find all completed topics
    cursor = progress_coll.find(
        {"user_id": user_id, "status": "completed"},
        {"updated_at": 1}
    )
    
    # Parse date of completion
    date_counts = {}
    async for doc in cursor:
        updated_at = doc.get("updated_at")
        if not updated_at:
            continue
        # Convert datetime to YYYY-MM-DD
        if isinstance(updated_at, str):
            date_str = updated_at[:10]
        else:
            date_str = updated_at.strftime("%Y-%m-%d")
        date_counts[date_str] = date_counts.get(date_str, 0) + 1
        
    # Sort chronologically
    sorted_dates = sorted(date_counts.keys())
    
    # Accumulate counts for line graph
    cumulative = []
    running_total = 0
    for d in sorted_dates:
        running_total += date_counts[d]
        cumulative.append({"date": d, "count": running_total})
        
    # Filter for the last N days if needed, but cumulative list is nice as is
    return cumulative

@router.get("/skill-coverage")
async def get_skill_coverage(current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    domains_coll = get_collection("domains")
    topics_coll = get_collection("topics")
    progress_coll = get_collection("user_progress")
    
    # Fetch all domains
    domains_cursor = domains_coll.find()
    domains = []
    async for doc in domains_cursor:
        domains.append(doc)
        
    # Fetch all topics
    topics_cursor = topics_coll.find()
    topics = []
    async for doc in topics_cursor:
        topics.append(doc)
        
    # Fetch progress
    progress_cursor = progress_coll.find({"user_id": user_id, "status": "completed"})
    completed_topics = set()
    async for doc in progress_cursor:
        completed_topics.add(doc["topic_slug"])
        
    # Map topics by domain
    domain_topics = {} # {domain_slug: [topic_slugs]}
    for t in topics:
        d_slug = t.get("domain_slug")
        t_slug = t.get("slug")
        if d_slug not in domain_topics:
            domain_topics[d_slug] = []
        domain_topics[d_slug].append(t_slug)
        
    result = []
    for d in domains:
        d_slug = d["slug"]
        d_title = d["title"]
        
        topic_slugs = domain_topics.get(d_slug, [])
        total_topics = len(topic_slugs)
        
        if total_topics == 0:
            coverage = 0
        else:
            completed_in_domain = sum(1 for ts in topic_slugs if ts in completed_topics)
            coverage = round((completed_in_domain / total_topics) * 100)
            
        result.append({
            "domain": d_title,
            "domain_slug": d_slug,
            "coverage": coverage,
            "completed": sum(1 for ts in topic_slugs if ts in completed_topics),
            "total": total_topics
        })
        
    return result
