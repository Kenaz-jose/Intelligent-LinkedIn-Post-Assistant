import json
import os
import threading
from pathlib import Path

from src.schemas.perspective import UserMemory

_PATH = Path(os.getenv("MEMORY_STORE", "data/user_memory.json"))
_LOCK = threading.Lock()


def _read_all() -> dict:
    """
    Load the whole store.

    Returns {} rather than raising when the file is missing or
    corrupt. A broken memory file should never stop someone from
    writing a post — the worst case is that the interview asks
    questions it has asked before.
    """
    if not _PATH.exists():
        return {}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        print(f"[memory_store] {_PATH} is corrupt, starting fresh")
        return {}


def get_memory(user_id: str) -> UserMemory:
    """
    Load one user's memory. Always returns a UserMemory.

    A user with no history gets an empty object with
    interviews_done = 0, which makes to_prompt_block() emit
    "(First interview with this person — nothing known yet)".
    Callers never need to check for None.
    """
    data = _read_all().get(user_id)
    return UserMemory.model_validate(data) if data else UserMemory(user_id=user_id)


def save_memory(memory: UserMemory) -> None:
    """
    Persist one user's memory, leaving every other user untouched.

    Read-modify-write under a lock. Two Streamlit sessions finishing
    an interview at the same moment would otherwise overwrite each
    other, because the whole store lives in one file.
    """
    with _LOCK:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        data = _read_all()
        data[memory.user_id] = json.loads(memory.model_dump_json())
        _PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def reset_memory(user_id: str) -> None:
    """Clear one user's memory. Useful when testing fills it with junk."""
    with _LOCK:
        data = _read_all()
        data.pop(user_id, None)
        _PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")