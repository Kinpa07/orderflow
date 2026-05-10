from dataclasses import dataclass
from typing import Any


@dataclass
class AppError:
    message: str
    code: int | None = None
    details: list[Any] | None = None
