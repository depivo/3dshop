import logging

import httpx

from app.config import settings
from app.models import Order

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def notify_new_order(order: Order) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    text = (
        "🆕 Новый заказ на 3D-печать\n"
        f"Имя: {order.name}\n"
        f"Телефон: {order.phone}\n"
        f"Файл: {order.original_filename} ({order.file_size / 1024:.0f} КБ)\n"
        f"Комментарий: {order.comment or '-'}\n"
        f"ID заказа: {order.id}"
    )
    url = TELEGRAM_API_URL.format(token=settings.telegram_bot_token)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url, json={"chat_id": settings.telegram_chat_id, "text": text}
            )
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send Telegram notification for order %s", order.id)
