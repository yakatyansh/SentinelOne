import json
import os
import aiofiles

DB_PATH = "db.json"

def _read_data():
    if not os.path.exists(DB_PATH):
        return {"users": []}
    with open(DB_PATH, "r") as f:
        return json.load(f)

async def _write_data(data):
    async with aiofiles.open("db.json", "w") as f:
        await f.write(json.dumps(data, indent=4))


async def insert_punishment(guild_id, user_id, mod_id, reason, timestamp, points):
    print("insert_punishment called")
    data = _read_data()
    data["users"].append({
        "guild_id": guild_id,
        "user_id": user_id,
        "mod_id": mod_id,
        "reason": reason,
        "timestamp": timestamp,
        "points": points 
    })
    await _write_data(data)
    total_points = 0
    for p in data["users"]:
        if p["user_id"] == user_id and p["guild_id"] == guild_id:
                total_points += int(p["points"])
    return total_points

# Replace your Mongo fetch function
async def get_punishments(guild_id=None, user_id=None):
    data = _read_data()
    results = data["users"]
    if guild_id:
        results = [p for p in results if p["guild_id"] == guild_id]
    if user_id:
        results = [p for p in results if p["user_id"] == user_id]
    return results
