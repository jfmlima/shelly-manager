from dataclasses import dataclass

from core.utils.validation import normalize_mac


@dataclass
class Credential:
    mac: str
    username: str
    password: str
    last_seen_ip: str | None = None
    created_at: int | None = None
    rotated_at: int | None = None

    def __post_init__(self) -> None:
        self.mac = normalize_mac(self.mac)
