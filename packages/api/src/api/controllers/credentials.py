from core.use_cases.manage_credentials import (
    CredentialNotFoundError,
    ManageCredentialsUseCase,
)
from litestar import Controller, Router, delete, get, post
from litestar.exceptions import NotFoundException

from api.presentation.dto.requests import CredentialCreateRequest
from api.presentation.dto.responses import CredentialResponse


class CredentialsController(Controller):
    path = ""
    tags = ["Configuration"]

    @get()
    async def list_credentials(
        self,
        credentials_use_case: ManageCredentialsUseCase,
    ) -> list[CredentialResponse]:
        """List all stored credentials."""
        creds = await credentials_use_case.list_credentials()
        return [
            CredentialResponse(
                mac=c.mac,
                username=c.username,
                last_seen_ip=c.last_seen_ip,
            )
            for c in creds
        ]

    @post()
    async def set_credential(
        self,
        data: CredentialCreateRequest,
        credentials_use_case: ManageCredentialsUseCase,
    ) -> CredentialResponse:
        """Set or update credentials for a device."""
        credential = await credentials_use_case.set_credential(
            mac=data.mac,
            username=data.username,
            password=data.password,
        )
        return CredentialResponse(mac=credential.mac, username=credential.username)

    @delete("/{mac:str}")
    async def delete_credential(
        self,
        mac: str,
        credentials_use_case: ManageCredentialsUseCase,
    ) -> None:
        """Delete credentials for a device."""
        try:
            await credentials_use_case.delete_credential(mac)
        except CredentialNotFoundError as err:
            raise NotFoundException(
                detail=f"Credential not found for MAC: {mac}"
            ) from err


credentials_router = Router(
    path="/credentials",
    route_handlers=[CredentialsController],
)
