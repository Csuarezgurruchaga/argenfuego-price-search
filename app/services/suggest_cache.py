from cachetools import TTLCache


suggest_cache = TTLCache(maxsize=1024, ttl=60)  # 60s cache for suggest

def cache_key(q: str) -> str:
    return q.strip().lower()


