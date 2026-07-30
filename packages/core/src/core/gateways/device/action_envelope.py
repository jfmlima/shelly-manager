"""The answer shape of a component action.

Every execute path answers with an ``ActionResult``, whether the action ran,
was refused before reaching the device, or failed on the wire. Which device and
which action are being reported is fixed for the whole call, so they are bound
once here and each exit says only what happened.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

from ...domain.value_objects.action_result import ActionResult


class ActionEnvelope(BaseModel):

    model_config = ConfigDict(frozen=True)

    device_ip: str
    action_type: str

    def succeeded(
        self, message: str, data: dict[str, Any] | None = None
    ) -> ActionResult:
        return ActionResult(
            device_ip=self.device_ip,
            action_type=self.action_type,
            success=True,
            message=message,
            data=data,
        )

    def failed(self, message: str, error: str) -> ActionResult:
        return ActionResult(
            device_ip=self.device_ip,
            action_type=self.action_type,
            success=False,
            message=message,
            error=error,
        )
