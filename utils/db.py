from utils.mongo import users
from datetime import datetime

def add_punishment(user_id, points, reason):
    now = datetime.now()
    user = users.update_one(
        {"_id": user_id},
        {
            "$inc": {"points": points},
            "$push": {
                "history": {
                    "points": points,
                    "reason": reason,
                    "timestamp": now
                }
            },
            "$setOnInsert": {"last_decay": now}
        },
        upsert=True
    )
        