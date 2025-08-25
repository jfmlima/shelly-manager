from abc import ABC, abstractmethod


class MDNSGateway(ABC):
    @abstractmethod
    async def discover_device_ips(
        self, timeout: float = 10.0, service_types: list[str] | None = None
    ) -> list[str]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
