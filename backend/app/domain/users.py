from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass(slots=True)
class User:
    id: str
    email: str
    hashed_password: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, email: str, hashed_password: str) -> "User":
        return cls(id=str(uuid.uuid4()), email=email, hashed_password=hashed_password)
