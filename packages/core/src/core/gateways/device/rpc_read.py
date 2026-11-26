"""One read of a device over RPC.

Status is gathered from several reads at once and each one is optional, so a
caller has to tell an empty answer apart from an absent one. ``body`` alone
cannot say which happened; this pairs it with whether the device answered.
"""

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..network.rpc_envelope import RpcError, rpc_result

logger = logging.getLogger(__name__)


class RpcRead(BaseModel):

    model_config = ConfigDict(frozen=True)

    body: Any = None
    answered: bool = False

    @classmethod
    def of(cls, result: Any, what: str, missing: Any = None) -> "RpcRead":
        """Read one result of a gathered call, logging what failed to answer."""
        if isinstance(result, BaseException):
            logger.error(f"Error getting {what}: {result}")
            return cls(body=missing)
        response, _ = result
        try:
            return cls(body=rpc_result(response), answered=True)
        except RpcError as e:
            logger.warning(f"Device refused {what}: {e}")
            return cls(body=missing, answered=True)
