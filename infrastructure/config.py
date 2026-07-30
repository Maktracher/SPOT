import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class APIKeys:
    api_key: str
    api_secret: str
    telegram_bot_token: str | None = None


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def load_api_keys(file_path: Path = Path("api_folder/API.txt")) -> APIKeys:
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found at path: {file_path.absolute()}")

    with file_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        raise ValueError("API key file must contain at least API_KEY and API_SECRET on separate lines.")

    telegram_token = lines[3] if len(lines) >= 4 else None

    return APIKeys(
        api_key=lines[0],
        api_secret=lines[1],
        telegram_bot_token=telegram_token,
    )