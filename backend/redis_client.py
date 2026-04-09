import uuid
import json
import redis.asyncio as redis
from config import REDIS_URL

client = redis.from_url(REDIS_URL, decode_responses=True)

SESSION_TTL = 60 * 60 * 24 * 7  # 7 days

async def create_session(data: dict) -> str:
    session_id = str(uuid.uuid4())
    await client.setex(f"session:{session_id}", SESSION_TTL, json.dumps(data))
    return session_id

async def get_session(session_id: str) -> dict | None:
    raw = await client.get(f"session:{session_id}")
    if not raw:
        return None
    return json.loads(raw)

async def update_session(session_id: str, data: dict):
    await client.setex(f"session:{session_id}", SESSION_TTL, json.dumps(data))

async def delete_session(session_id: str):
    await client.delete(f"session:{session_id}") 

async def rate_limit_check(ip: str) -> bool:
    key = f"rate:{ip}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, 60)
    return count > 60