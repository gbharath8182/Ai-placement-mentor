from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import get_collection
from backend.models import ActivityLogCreate, StreakResponse
from backend.auth import get_current_user
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from typing import List, Optional

router = APIRouter(prefix="/activity", tags=["activity"])

def get_today_and_yesterday_str():
    # Use system local time
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    return today_str, yesterday_str

@router.post("/log")
async def log_activity(req: ActivityLogCreate, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    activity_coll = get_collection("activity_log")
    streaks_coll = get_collection("streaks")
    
    today_str, yesterday_str = get_today_and_yesterday_str()
    
    # 1. Log or update activity
    # Find if there is already an activity log for this user, date, and activity_type
    # We will increment minutes_spent
    await activity_coll.update_one(
        {
            "user_id": user_id,
            "date": today_str,
            "activity_type": req.activity_type
        },
        {
            "$inc": {"minutes_spent": req.minutes_spent},
            "$set": {
                "updated_at": datetime.now(timezone.utc),
                "topic_slug": req.topic_slug
            }
        },
        upsert=True
    )
    
    # 2. Update Streak
    streak_doc = await streaks_coll.find_one({"user_id": user_id})
    
    if not streak_doc:
        # First activity ever
        new_streak = {
            "user_id": user_id,
            "current_streak": 1,
            "longest_streak": 1,
            "last_active_date": today_str,
            "updated_at": datetime.now(timezone.utc)
        }
        await streaks_coll.insert_one(new_streak)
        current_streak = 1
    else:
        last_active = streak_doc.get("last_active_date")
        current_streak = streak_doc.get("current_streak", 0)
        longest_streak = streak_doc.get("longest_streak", 0)
        
        if last_active == today_str:
            # Already active today, streak doesn't change
            pass
        elif last_active == yesterday_str:
            # Active yesterday, increment streak
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
            await streaks_coll.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "current_streak": current_streak,
                        "longest_streak": longest_streak,
                        "last_active_date": today_str,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        else:
            # Streak broken, reset to 1
            current_streak = 1
            await streaks_coll.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "current_streak": current_streak,
                        "last_active_date": today_str,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
    return {
        "message": "Activity logged successfully",
        "date": today_str,
        "minutes_spent": req.minutes_spent,
        "current_streak": current_streak
    }

@router.get("/heatmap")
async def get_heatmap(year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    activity_coll = get_collection("activity_log")
    
    # If year is not specified, use current year
    if not year:
        year = datetime.now().year
        
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Query all activities for the year
    cursor = activity_coll.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    })
    
    # Aggregate by date (since we log multiple activity types per date)
    date_map = {}
    async for doc in cursor:
        dt = doc["date"]
        mins = doc.get("minutes_spent", 0)
        date_map[dt] = date_map.get(dt, 0) + mins
        
    result = [{"date": k, "minutes_spent": v} for k, v in date_map.items()]
    return result

@router.get("/streak", response_model=StreakResponse)
async def get_streak(current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    streaks_coll = get_collection("streaks")
    
    streak_doc = await streaks_coll.find_one({"user_id": user_id})
    if not streak_doc:
        return StreakResponse(current_streak=0, longest_streak=0, last_active_date=None)
        
    # Check if the streak is broken (i.e. last active date was before yesterday)
    today_str, yesterday_str = get_today_and_yesterday_str()
    last_active = streak_doc.get("last_active_date")
    current_streak = streak_doc.get("current_streak", 0)
    
    if last_active and last_active != today_str and last_active != yesterday_str:
        # Streak broken, reset current streak to 0 in response and DB
        current_streak = 0
        await streaks_coll.update_one(
            {"user_id": user_id},
            {"$set": {"current_streak": 0}}
        )
        
    return StreakResponse(
        current_streak=current_streak,
        longest_streak=streak_doc.get("longest_streak", 0),
        last_active_date=last_active
    )

@router.get("/time-spent")
async def get_time_spent(
    period: int = 30, 
    aggregation: str = "daily", 
    current_user: dict = Depends(get_current_user)
):
    user_id = ObjectId(current_user["id"])
    activity_coll = get_collection("activity_log")
    
    # Calculate start date
    now = datetime.now()
    start_date = (now - timedelta(days=period)).strftime("%Y-%m-%d")
    
    cursor = activity_coll.find({
        "user_id": user_id,
        "date": {"$gte": start_date}
    })
    
    # Parse and aggregate
    data = []
    async for doc in cursor:
        data.append({
            "date": doc["date"],
            "minutes_spent": doc.get("minutes_spent", 0),
            "activity_type": doc.get("activity_type", "lesson")
        })
        
    # Standard group by daily/weekly/monthly
    if aggregation == "daily":
        # Group by date
        grouped = {}
        for d in data:
            dt = d["date"]
            grouped[dt] = grouped.get(dt, 0) + d["minutes_spent"]
        # Sort by date
        sorted_keys = sorted(grouped.keys())
        return [{"label": k, "minutes_spent": grouped[k]} for k in sorted_keys]
        
    elif aggregation == "weekly":
        # Group by week (e.g. "Year - WkNo")
        grouped = {}
        for d in data:
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            # Get week number
            wk = dt.strftime("%Y-W%U")
            grouped[wk] = grouped.get(wk, 0) + d["minutes_spent"]
        sorted_keys = sorted(grouped.keys())
        return [{"label": k, "minutes_spent": grouped[k]} for k in sorted_keys]
        
    elif aggregation == "monthly":
        # Group by month (e.g. "YYYY-MM")
        grouped = {}
        for d in data:
            dt = d["date"][:7] # YYYY-MM
            grouped[dt] = grouped.get(dt, 0) + d["minutes_spent"]
        sorted_keys = sorted(grouped.keys())
        return [{"label": k, "minutes_spent": grouped[k]} for k in sorted_keys]
        
    return []
