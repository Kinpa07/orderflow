from dataclasses import dataclass

@dataclass
class AppError:
    message: str
    code: int | None = None
    details: list | None = None