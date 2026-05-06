import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def blacklist_token(token_jti: str, expires_in_seconds: int) -> None:
    """
    Blacklist a token by its JTI (Unique Identifier).
    """
    await redis_client.setex(
        f"blacklist:{token_jti}",
        expires_in_seconds,
        "true"
    )

async def is_token_blacklisted(token_jti: str) -> bool:
    """
    Check if a token JTI is in the blacklist.
    """
    return await redis_client.exists(f"blacklist:{token_jti}") > 0
