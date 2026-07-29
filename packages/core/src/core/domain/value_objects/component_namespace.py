"""The RPC namespaces a component type answers to.

Shelly addresses actions as ``Namespace.Method``, and the namespace is not the
component key: the ``emdata`` component answers to ``EMData``, ``sys`` answers to
both ``Sys`` and ``Shelly``. This table is the single place that correspondence
is written down; nothing else should derive a namespace from a component key.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict


class ComponentNamespace(BaseModel):
    """Which RPC methods one component type owns.

    ``discovers`` defines ownership. An entry ending in a dot is a namespace
    prefix; anything else is one exact method name, which is how the zigbee
    component owns ``Shelly.ZigbeeClear`` without owning the rest of ``Shelly``.
    ``namespaces`` are the ones a bare method may be qualified into, in
    preference order; ``sys`` answers to both ``Sys`` and ``Shelly``.

    Ownership is the boundary for execution as well as discovery. Naming a
    method the component does not own must not reach the device, or addressing
    the wifi component would be enough to send ``Shelly.FactoryReset``.
    """

    model_config = ConfigDict(frozen=True)

    namespaces: tuple[str, ...]
    discovers: tuple[str, ...]

    @classmethod
    def for_component_type(cls, component_type: str) -> "ComponentNamespace":
        """The namespaces of a component type, or a title-cased guess when the
        type is one this table does not know."""
        known = _NAMESPACES.get(component_type.lower())
        if known is not None:
            return known
        return _namespace(component_type.title())

    @property
    def qualifies_as(self) -> str:
        return self.namespaces[0]

    def actions_in(self, available_methods: Sequence[str]) -> list[str]:
        """Select this component's methods, leaving the device's spelling intact."""
        prefixes = tuple(p.lower() for p in self.discovers if p.endswith("."))
        exact = {p.lower() for p in self.discovers if not p.endswith(".")}
        if not prefixes and not exact:
            return []
        return [
            m
            for m in available_methods
            if (prefixes and m.lower().startswith(prefixes)) or m.lower() in exact
        ]

    def owns(self, method: str) -> bool:
        """Whether a fully qualified method name belongs to this component."""
        return bool(self.actions_in([method]))


def _namespace(
    *namespaces: str, discovers: tuple[str, ...] | None = None
) -> ComponentNamespace:
    return ComponentNamespace(
        namespaces=namespaces,
        discovers=(
            discovers
            if discovers is not None
            else tuple(f"{name}." for name in namespaces)
        ),
    )


_NAMESPACES: dict[str, ComponentNamespace] = {
    "ble": _namespace("BLE"),
    "boolean": _namespace("Boolean"),
    "bthome": _namespace("BTHome"),
    "button": _namespace("Button"),
    "cct": _namespace("CCT"),
    "cloud": _namespace("Cloud"),
    "enum": _namespace("Enum"),
    "cover": _namespace("Cover"),
    "dali": _namespace("DALI"),
    "devicepower": _namespace("DevicePower"),
    "em": _namespace("EM"),
    "em1": _namespace("EM1"),
    "em1data": _namespace("EM1Data"),
    "emdata": _namespace("EMData"),
    "eth": _namespace("Eth"),
    "group": _namespace("Group"),
    "http": _namespace("HTTP"),
    "humidity": _namespace("Humidity"),
    "input": _namespace("Input"),
    "knx": _namespace("KNX"),
    "kvs": _namespace("KVS"),
    "light": _namespace("Light"),
    "matter": _namespace("Matter"),
    "modbus": _namespace("Modbus"),
    "mqtt": _namespace("Mqtt"),
    "number": _namespace("Number"),
    "pm1": _namespace("PM1"),
    "rgb": _namespace("RGB"),
    "rgbw": _namespace("RGBW"),
    "schedule": _namespace("Schedule"),
    "script": _namespace("Script"),
    "shelly": _namespace("Shelly"),
    "smoke": _namespace("Smoke"),
    "switch": _namespace("Switch"),
    "sys": _namespace("Sys", "Shelly"),
    "temperature": _namespace("Temperature"),
    "text": _namespace("Text"),
    "ui": _namespace("UI"),
    "voltmeter": _namespace("Voltmeter"),
    "webhook": _namespace("Webhook"),
    "wifi": _namespace("Wifi"),
    "ws": _namespace("WS"),
    "zigbee": _namespace("Zigbee", discovers=("Zigbee.", "Shelly.ZigbeeClear")),
}
