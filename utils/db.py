from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

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
