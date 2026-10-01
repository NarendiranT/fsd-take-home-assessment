import json
from pathlib import Path

SOURCE_FILES = ("crm_events.json", "calendar_events.json")


def load_sources(data_dir: Path) -> tuple[list[dict], list[dict]]:
    return tuple(json.loads(_read(data_dir, name)) for name in SOURCE_FILES)


def source_token(data_dir: Path) -> tuple[str, str] | None:
    try:
        texts = tuple(_read(data_dir, name) for name in SOURCE_FILES)
    except OSError:
        return None
    for text in texts:
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return None
    return texts


def _read(data_dir: Path, name: str) -> str:
    return (data_dir / name).read_text(encoding="utf-8")
