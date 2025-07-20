import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING

import asyncio


MONGODB_URL = os.getenv('MONGO_URI')
DATABASE_NAME = os.getenv("DATABASE_NAME", "discord_moderation")

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.punishments = None
        self.guild_settings = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client[DATABASE_NAME]
        self.punishments = self.db.punishments
        self.guild_settings = self.db.guild_settings
        
        await self._create_indexes()
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        await self.punishments.create_index([("guild_id", 1), ("user_id", 1)])
        await self.punishments.create_index([("guild_id", 1), ("timestamp", -1)])
        await self.punishments.create_index([("user_id", 1)])
        await self.punishments.create_index([("timestamp", -1)])
        
        await self.guild_settings.create_index([("guild_id", 1)], unique=True)
    
    async def close(self):
        if self.client:
            self.client.close()

db_manager = DatabaseManager()

async def init_database():
    await db_manager.connect()

async def close_database():
    await db_manager.close()

async def insert_punishment(guild_id: int, user_id: int, mod_id: int, reason: str, timestamp: str, points: int) -> int:
    print("insert_punishment called")
    
    punishment_doc = {
        "guild_id": guild_id,
        "user_id": user_id,
        "mod_id": mod_id,
        "reason": reason,
        "timestamp": timestamp,
        "points": points,
        "created_at": datetime.utcnow()
    }
    
    await db_manager.punishments.insert_one(punishment_doc)
    
    total_points = await get_user_total_points(guild_id, user_id)
    
    return total_points

async def get_punishments(guild_id: Optional[int] = None, user_id: Optional[int] = None) -> List[Dict]:
    query = {}
    
    if guild_id:
        query["guild_id"] = guild_id
    if user_id:
        query["user_id"] = user_id
    
    cursor = db_manager.punishments.find(query)
    results = []
    
    async for document in cursor:
        document["_id"] = str(document["_id"])
        results.append(document)
    
    return results

async def get_user_total_points(guild_id: int, user_id: int) -> int:
    pipeline = [
        {
            "$match": {
                "guild_id": guild_id,
                "user_id": user_id
            }
        },
        {
            "$group": {
                "_id": None,
                "total_points": {"$sum": "$points"}
            }
        }
    ]
    
    result = await db_manager.punishments.aggregate(pipeline).to_list(1)
    
    if result:
        return result[0]["total_points"]
    return 0

async def get_user_punishments(guild_id: int, user_id: int, limit: int = 10) -> List[Dict]:
    query = {
        "guild_id": guild_id,
        "user_id": user_id
    }
    
    cursor = db_manager.punishments.find(query).sort("timestamp", DESCENDING).limit(limit)
    results = []
    
    async for document in cursor:
        document["_id"] = str(document["_id"])
        results.append(document)
    
    return results

async def get_recent_punishments(guild_id: int, hours: int = 24) -> List[Dict]:
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_iso = cutoff_time.isoformat()
    
    query = {
        "guild_id": guild_id,
        "timestamp": {"$gte": cutoff_iso}
    }
    
    cursor = db_manager.punishments.find(query).sort("timestamp", DESCENDING)
    results = []
    
    async for document in cursor:
        document["_id"] = str(document["_id"])
        results.append(document)
    
    return results

async def cleanup_old_punishments(guild_id: int, days_old: int = 30) -> int:
    cutoff_time = datetime.now() - timedelta(days=days_old)
    cutoff_iso = cutoff_time.isoformat()
    
    query = {
        "guild_id": guild_id,
        "timestamp": {"$lt": cutoff_iso}
    }
    
    result = await db_manager.punishments.delete_many(query)
    removed_count = result.deleted_count
    
    if removed_count > 0:
        print(f"Cleaned up {removed_count} old punishments")
    
    return removed_count

async def get_guild_settings(guild_id: int) -> Dict:
    """Get guild-specific settings"""
    document = await db_manager.guild_settings.find_one({"guild_id": guild_id})
    
    if not document:
        # Create default settings
        default_settings = {
            "guild_id": guild_id,
            "mute_role_id": None,
            "mod_log_channel": None,
            "automod_enabled": True,
            "point_decay_days": 30,
            "ban_vote_threshold": 10,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db_manager.guild_settings.insert_one(default_settings)
        
        # Return without MongoDB-specific fields
        settings = default_settings.copy()
        del settings["created_at"]
        del settings["updated_at"]
        del settings["guild_id"]
        
        return settings
    
    # Remove MongoDB-specific fields from response
    settings = document.copy()
    if "_id" in settings:
        del settings["_id"]
    if "created_at" in settings:
        del settings["created_at"]
    if "updated_at" in settings:
        del settings["updated_at"]
    if "guild_id" in settings:
        del settings["guild_id"]
    
    return settings

async def update_guild_setting(guild_id: int, setting_name: str, value) -> bool:
    """Update a specific guild setting"""
    try:
        update_doc = {
            "$set": {
                setting_name: value,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await db_manager.guild_settings.update_one(
            {"guild_id": guild_id},
            update_doc,
            upsert=True
        )
        
        return True
    except Exception as e:
        print(f"Error updating guild setting: {e}")
        return False


async def get_top_offenders(guild_id: int, limit: int = 10) -> List[Dict]:
    """Get users with the most punishment points"""
    pipeline = [
        {"$match": {"guild_id": guild_id}},
        {
            "$group": {
                "_id": "$user_id",
                "total_points": {"$sum": "$points"},
                "punishment_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_points": DESCENDING}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "user_id": "$_id",
                "total_points": 1,
                "punishment_count": 1
            }
        }
    ]
    
    result = await db_manager.punishments.aggregate(pipeline).to_list(limit)
    return result

async def backup_database(backup_path: Optional[str] = None) -> str:
    """Create a backup of the database (export to JSON)"""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"db_backup_{timestamp}.json"
    
    import json
    import aiofiles
    
    # Export punishments
    punishments_cursor = db_manager.punishments.find({})
    punishments = []
    async for doc in punishments_cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        punishments.append(doc)
    
    # Export guild settings
    settings_cursor = db_manager.guild_settings.find({})
    guild_settings = {}
    async for doc in settings_cursor:
        guild_id = str(doc["guild_id"])
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].isoformat()
        guild_settings[guild_id] = doc
    
    backup_data = {
        "users": punishments,  # Keep original field name for compatibility
        "guild_settings": guild_settings
    }
    
    async with aiofiles.open(backup_path, "w") as f:
        await f.write(json.dumps(backup_data, indent=4))
    
    return backup_path

async def get_database_info() -> Dict:
    """Get information about the database"""
    # Count documents in collections
    punishment_count = await db_manager.punishments.count_documents({})
    guild_settings_count = await db_manager.guild_settings.count_documents({})
    
    # Get unique guilds and users from punishments
    guilds_pipeline = [{"$group": {"_id": "$guild_id"}}]
    guild_results = await db_manager.punishments.aggregate(guilds_pipeline).to_list(None)
    total_guilds = len(guild_results)
    
    users_pipeline = [{"$group": {"_id": "$user_id"}}]
    user_results = await db_manager.punishments.aggregate(users_pipeline).to_list(None)
    total_users = len(user_results)
    
    # Get database stats (approximate size)
    db_stats = await db_manager.db.command("dbStats")
    database_size_kb = round(db_stats.get("dataSize", 0) / 1024, 2)
    
    return {
        "total_punishments": punishment_count,
        "total_guilds": total_guilds,
        "total_users": total_users,
        "guild_settings_count": guild_settings_count,
        "database_size_kb": database_size_kb
    }

class DatabaseContext:
    """Context manager for database operations"""
    
    async def __aenter__(self):
        await init_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await close_database()