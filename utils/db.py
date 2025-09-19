from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
if not MONGO_URI:
    raise ValueError("No MONGODB_URI found in environment variables.")

client = AsyncIOMotorClient(MONGO_URI)
db = client["SentinelOne"]
users_collection = db["Users"]

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
    
    await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$push": {"warnings": warning},
            "$setOnInsert": {"total_points": 0, "punishments": []}
        },
        upsert=True
    )
    
    user_data = await users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id}
    )
    warning_count = len(user_data.get("warnings", []))
    
    # Second warning gets 5min mute, third warning converts to 1MP
    return warning_count, warning_count in [2, 3]

async def add_punishment(guild_id: int, user_id: int, reason: str, points: int, warning_count: int = 0) -> int:
    """Add punishment to the database and update total points."""
    user_data = await users_collection.find_one({"guild_id": guild_id, "user_id": user_id})
    new_entry = {
        "reason": reason,
        "points": points,
        "timestamp": datetime.utcnow(),
        "warning_count": warning_count
    }

    if user_data:
        # Handle third warning conversion to MP
        if warning_count >= 3:
            await users_collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {"total_points": 1},  # Add 1 MP for third warning
                    "$push": {"punishments": new_entry},
                    "$set": {"warnings": []}  # Clear warnings after conversion
                }
            )
            return user_data["total_points"] + 1
        else:
            await users_collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {"total_points": points},
                    "$push": {"punishments": new_entry}
                }
            )
            return user_data["total_points"] + points
    else:
        await users_collection.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "total_points": points,
            "punishments": [new_entry],
            "warnings": []
        })
        return points

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
    """Remove expired points (older than 20 days) and return new total"""
    expiry_date = datetime.utcnow() - timedelta(days=20)
    
    user_data = await users_collection.find_one({"guild_id": guild_id, "user_id": user_id})
    if not user_data:
        return 0

    active_punishments = []
    total_points = 0
    
    for punishment in user_data.get('punishments', []):
        if punishment['timestamp'] > expiry_date:
            active_punishments.append(punishment)
            total_points += punishment['points']

    # Update database with only active punishments
    await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$set": {
                "punishments": active_punishments,
                "total_points": total_points
            }
        }
    )
    
    return total_points

async def deductpoints(guild_id: int, user_id: int, points: int) -> int:
    """Deduct points from a user atomically and return the new total."""
    user_data = await users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"total_points": 1}  # Only fetch the total_points field
    )

    if not user_data:
        return 0

    current_points = user_data.get('total_points', 0)
    
    # Ensure points don't go below zero
    points_to_deduct = min(points, current_points)
    
    if points_to_deduct <= 0:
        return current_points

    # Use $inc to atomically decrement the points
    await users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$inc": {"total_points": -points_to_deduct}}
    )
    
    return current_points - points_to_deduct