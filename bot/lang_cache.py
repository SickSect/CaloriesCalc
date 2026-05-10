import aioredis

from log.log_writer import log

class LangCache:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis = aioredis.from_url(redis_url, decode_responses=True, encoding="utf-8")

    async def get_lang(self, user_id):
        lang = await self.redis.lang(user_id)
        return lang or "en"

    async def set_lang(self, lang, user_id):
        await self.redis.set(f"user:{user_id}:lang", lang, ex=86400)