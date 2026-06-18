import uuid
import time
import hashlib


def generate_id(prefix: str = "") -> str:
    timestamp = int(time.time() * 1000)
    random_part = uuid.uuid4().hex[:8]
    base_id = f"{timestamp}_{random_part}"
    if prefix:
        return f"{prefix}_{base_id}"
    return base_id


def short_id() -> str:
    return uuid.uuid4().hex[:12]


def hash_id(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]
