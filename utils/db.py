from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, List

load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
if not MONGO_URI:
    raise ValueError("No MONGODB_URI found in environment variables.")

client = MongoClient(MONGO_URI)
db = client["SentinelOne"]
users_collection = db["Users"]

def add_punishment(guild_id: int, user_id: int, reason: str, points: int) -> int:
    user_data = users_collection.find_one({"guild_id": guild_id, "user_id": user_id})
    new_entry = {
        "reason": reason,
        "points": points,
        "timestamp": datetime.utcnow()
    }

    if user_data:
        users_collection.update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$inc": {"total_points": points},
                "$push": {"punishments": new_entry}
            }
        )
        return user_data["total_points"] + points
    else:
        users_collection.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "total_points": points,
            "punishments": [new_entry]
        })
        return points

def clear_points(guild_id, user_id):
    users_collection.delete_one({"guild_id": guild_id, "user_id": user_id})

def get_points(guild_id, user_id):
    user = users_collection.find_one({"guild_id": guild_id, "user_id": user_id})
    return user["total_points"] if user else 0

def add_warning(guild_id: int, user_id: int, mod_id: int, reason: Optional[str] = None) -> int:
    """
    Add a warning to a user's record
    Returns: Number of current warnings
    """
    warning = {
        "timestamp": datetime.utcnow(),
        "mod_id": mod_id,
        "reason": reason
    }
    
    result = users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {
            "$push": {"warnings": warning},
            "$setOnInsert": {"total_points": 0, "punishments": []}
        },
        upsert=True
    )
    
    user_data = users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id}
    )
    return len(user_data.get("warnings", []))

def get_warnings(guild_id: int, user_id: int) -> List[Dict]:
    """Get all warnings for a user"""
    user_data = users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"warnings": 1}
    )
    return user_data.get("warnings", []) if user_data else []

def get_warning_count(guild_id: int, user_id: int) -> int:
    """Get number of warnings for a user"""
    warnings = get_warnings(guild_id, user_id)
    return len(warnings)

def clear_warnings(guild_id: int, user_id: int) -> bool:
    """
    Clear all warnings for a user
    Returns: True if warnings were cleared, False if user not found
    """
    result = users_collection.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"warnings": []}}
    )
    return result.modified_count > 0

def get_user_info(guild_id: int, user_id: int) -> Optional[Dict]:
    """Get all user information including warnings and punishments"""
    return users_collection.find_one(
        {"guild_id": guild_id, "user_id": user_id}
    )

# Modify existing add_punishment to handle warning conversion
def add_punishment(guild_id: int, user_id: int, reason: str, points: int, mod_id: Optional[int] = None) -> int:
    user_data = users_collection.find_one({"guild_id": guild_id, "user_id": user_id})
    new_entry = {
        "reason": reason,
        "points": points,
        "timestamp": datetime.utcnow(),
        "mod_id": mod_id
    }

    if user_data:
        # Clear warnings if converting to MP
        if "warning_conversion" in reason.lower():
            users_collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {"total_points": points},
                    "$push": {"punishments": new_entry},
                    "$set": {"warnings": []}
                }
            )
        else:
            users_collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {"total_points": points},
                    "$push": {"punishments": new_entry}
                }
            )
        return user_data["total_points"] + points
    else:
        users_collection.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "total_points": points,
            "punishments": [new_entry],
            "warnings": []
        })
        return points
