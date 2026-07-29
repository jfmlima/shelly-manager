"""Device generation as one domain value.

Shelly generations reach the code in three raw shapes: the integer ``gen``
devices report (1 legacy, 2/3/4 RPC), the ``gen1``/``gen2`` labels stored on
backups, and a ``/shelly`` identification response whose ``gen`` field Gen1
firmware omits entirely. This value object is the single place those shapes
are reconciled; nothing else should compare raw ``gen`` ints or labels.

``GEN2`` covers the whole RPC family: Gen2+ devices share one RPC surface, so
gen 3 and 4 devices are ``GEN2`` here. Code that needs the literal device
generation (provisioning reports gen 2 vs 3) keeps the raw int.
"""

from enum import Enum
from typing import Any


class Generation(str, Enum):
    """The two protocol families a device can speak."""

    GEN1 = "gen1"
    GEN2 = "gen2"

    @classmethod
    def from_device_gen(cls, gen: int | None) -> "Generation | None":
        """From the ``gen`` a device status reports (Gen2+ RPC field or the
        legacy gateway's gen=1 stamp). ``None`` when the generation could not
        be determined; callers decide whether that is an error."""
        if gen == 1:
            return cls.GEN1
        if gen is not None and gen >= 2:
            return cls.GEN2
        return None

    @classmethod
    def from_label(cls, label: str) -> "Generation | None":
        """From a stored backup label; ``None`` for an unknown label."""
        try:
            return cls(label)
        except ValueError:
            return None

    @classmethod
    def from_shelly_payload(cls, payload: dict[str, Any]) -> "Generation":
        """From a raw ``/shelly`` identification response.

        Gen1 firmware has no ``gen`` field there (it identifies via ``type``),
        so a missing field means Gen1, unlike a device status where a missing
        generation means undetermined.
        """
        return cls.GEN1 if payload.get("gen") is None else cls.GEN2
