"""Background retry loop for webhook deliveries.

Runs inside the same FastAPI process on a plain poll loop -- no separate
worker service or message broker. That keeps this repo's "one process,
one SQLite file" deployment story intact (see README > Known limitations
for when a real task queue like Celery/RQ would be worth the extra
infrastructure instead: many concurrent writers, or delivery volume high
enough that a 15s poll interval isn't tight enough).
"""
import asyncio
import logging

from api import webhooks

logger = logging.getLogger("webhooks.worker")

POLL_INTERVAL_SECONDS = 15


async def run_forever() -> None:
    while True:
        try:
            processed = await asyncio.to_thread(webhooks.run_due_retries)
            if processed:
                logger.info("Webhook retry worker processed %d due deliveries", processed)
        except Exception:
            logger.exception("Webhook retry worker iteration failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
