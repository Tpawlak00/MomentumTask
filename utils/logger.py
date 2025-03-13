import logging
import time
from fastapi import Request

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def log_request(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    log_message = (
        f"Request: {request.method} {request.url} "
        f"from {request.client.host} | Status: {response.status_code} "
        f"| Time: {process_time:.3f}s"
    )

    logger.info(log_message)

    return response
