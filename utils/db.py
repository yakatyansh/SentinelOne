from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pymongo import ReturnDocument

load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
if not MONGO_URI:
    raise ValueError("No MONGODB_URI found in environment variables.")

client = AsyncIOMotorClient(MONGO_URI)
db = client["SentinelOne"]
users_collection = db["Users"]

async def ensure_indexes() -> None:
    """One record per (guild, user). Lets lookups use an index instead of scanning
    the whole collection, and stops concurrent first punishments from creating
    duplicate records. Fails if duplicates already exist; merge those first."""
    await users_collection.create_index(
        [("guild_id", 1), ("user_id", 1)], unique=True, name="guild_user_unique"
    )


async def add_warning(guild_id: int, user_id: int, mod_id: int, reason: Optional[str] = None) -> Tuple[int, bool]:
    """
    Add a warning to a user's record
    Returns: (warning_count, is_mutable)
    is_mutable indicates if the warning should result in a mute
    """
    warning = {
        "timestamp": datetime.utcnow(),
        "mod_id": mod_id,
        "reason": reason
    }

    # Push and read back in one atomic step, so two warnings issued at the same
    # moment get counts N and N+1 instead of both seeing N+1.
    user_data = await users_collection.find_one_and_update(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$push": {"warnings": warning},
            "$setOnInsert": {"total_points": 0, "punishments": []}
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    warning_count = len(user_data.get("warnings", []))

    # Second warning gets 5min mute, third warning converts to 1MP
    return warning_count, warning_count in [2, 3]

async def add_punishment(guild_id: int, user_id: int, reason: str, points: int, warning_count: int = 0) -> int:
    """Add punishment to the database and update total points.

    Single atomic upsert that returns the total *after* this punishment, so two
    mods punishing the same user at once each see the real running total and the
    15 MP ban vote fires exactly once."""
    new_entry = {
        "reason": reason,
        "points": points,
        "timestamp": datetime.utcnow(),
        "warning_count": warning_count
    }

    if warning_count >= 3:
        # Third warning converts to 1 MP and clears warnings
        update = {
            "$inc": {"total_points": 1},
            "$push": {"punishments": new_entry},
            "$set": {"warnings": []},
        }
    else:
        update = {
            "$inc": {"total_points": points},
            "$push": {"punishments": new_entry},
            "$setOnInsert": {"warnings": []},
        }

    user_data = await users_collection.find_one_and_update(
        {"guild_id": guild_id, "user_id": user_id},
        update,
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return user_data["total_points"]

async def get_warnings(guild_id: int, user_id: int) -> List[Dict]:
    """Get all warnings for a user"""
    user_data = await users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"warnings": 1}
    )
    return user_data.get("warnings", []) if user_data else []

async def get_warning_count(guild_id: int, user_id: int) -> int:
    """Get number of warnings for a user"""
    warnings = await get_warnings(guild_id, user_id)
    return len(warnings)

async def clear_warnings(guild_id: int, user_id: int) -> bool:
    """Clear all warnings for a user"""
    result = await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"warnings": []}}
    )
    return result.modified_count > 0

async def get_user_info(guild_id: int, user_id: int) -> Optional[Dict]:
    """Get all user information including warnings and punishments"""
    return await users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id}
    )

async def clear_points(guild_id: int, user_id: int) -> bool:
    """Clear all points and warnings for a user"""
    result = await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$set": {
                "total_points": 0,
                "warnings": [],
                "punishments": []
            }
        }
    )
    return result.modified_count > 0

async def check_expired_points(guild_id: int, user_id: int) -> int:
    """Remove expired points (older than 20 days) and return new total.

    Done as one server-side update instead of read -> filter in Python -> $set.
    The old version could overwrite a punishment that another command added
    between the read and the write (e.g. !points running during !punish)."""
    expiry_date = datetime.utcnow() - timedelta(days=20)

    as_date = {"$convert": {"input": "$$p.timestamp", "to": "date", "onError": None, "onNull": None}}
    user_data = await users_collection.find_one_and_update(
        {"guild_id": guild_id, "user_id": user_id},
        [
            {"$set": {"punishments": {"$filter": {
                "input": {"$ifNull": ["$punishments", []]},
                "as": "p",
                # entries with a missing/unparseable timestamp are dropped, as before
                "cond": {"$gt": [as_date, expiry_date]},
            }}}},
            {"$set": {"total_points": {"$sum": "$punishments.points"}}},
        ],
        return_document=ReturnDocument.AFTER,
    )
    if not user_data:
        return 0
    return user_data.get("total_points", 0)

async def deductpoints(guild_id: int, user_id: int, points_to_deduct: int) -> int:
    """
    Atomically deducts points from a user by modifying or removing their
    most recent punishment entries.
    """
    user_data = await users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id}
    )

    if not user_data or not user_data.get('punishments'):

        return 0


    punishments = sorted(user_data.get('punishments', []), key=lambda p: p['timestamp'], reverse=True)
    
    remaining_deduction = points_to_deduct
    updated_punishments = []

    for punishment in punishments:
        points = punishment.get('points', 0)
        if remaining_deduction > 0:
            if points <= remaining_deduction:

                remaining_deduction -= points

            else:

                punishment['points'] -= remaining_deduction
                remaining_deduction = 0
                updated_punishments.append(punishment)
        else:
            # No more points to deduct, just keep the record as is.
            updated_punishments.append(punishment)

    updated_punishments.sort(key=lambda p: p['timestamp'])

    new_total_points = sum(p.get('points', 0) for p in updated_punishments)

    await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$set": {
                "punishments": updated_punishments,
                "total_points": new_total_points
            }
        }
    )
    
    return new_total_points

async def get_leaderboard_users(guild_id: int) -> List[Dict]:
    """
    Gets users for the leaderboard, sorted by points accumulated in the last 20 days.
    """
    expiry_date = datetime.utcnow() - timedelta(days=20)
    

    pipeline = [

        {"$match": {"guild_id": guild_id}},
        

        {"$unwind": "$punishments"},

        {"$match": {"punishments.timestamp": {"$gte": expiry_date}}},
        

        {"$group": {
            "_id": "$user_id",
            "recent_points": {"$sum": "$punishments.points"}
        }},
        

        {"$match": {"recent_points": {"$gt": 0}}},
        

        {"$sort": {"recent_points": -1}},
        
        {"$project": {
            "user_id": "$_id",
            "total_points": "$recent_points", 
            "_id": 0
        }}
    ]
    

    cursor = users_collection.aggregate(pipeline)
    return await cursor.to_list(length=None)