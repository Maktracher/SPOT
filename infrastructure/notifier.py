import logging
from typing import Protocol, Sequence
import requests

logger = logging.getLogger(__name__)


class NotifierProtocol(Protocol):
    def send_message(self, message: str) -> None: ...


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str | None,
        chat_id: str | int | Sequence[str | int] | None = None,
    ) -> None:
        self._token = bot_token

        # Уніфікуємо chat_id: підтримуємо int, str, list/tuple або дефолтний 378059841
        if chat_id is None:
            self._chat_ids: list[str] = ["378059841"]
        elif isinstance(chat_id, (str, int)):
            self._chat_ids = [str(chat_id)]
        else:
            self._chat_ids = [str(cid) for cid in chat_id]

    def send_message(self, message: str) -> None:
        if not self._token or not self._chat_ids:
            logger.debug("Telegram token or chat_ids missing. Notification skipped.")
            return

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"

        for cid in self._chat_ids:
            try:
                payload = {
                    "chat_id": cid,
                    "text": message,
                    "parse_mode": "HTML",
                }
                response = requests.post(url, json=payload, timeout=5)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error("❌ Не вдалося надіслати повідомлення до %s: %s", cid, e)


class NullNotifier:
    def send_message(self, message: str) -> None:
        pass