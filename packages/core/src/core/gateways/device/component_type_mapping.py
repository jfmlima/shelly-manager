"""
Component type to API name mappings for Shelly devices.
"""

COMPONENT_TYPE_TO_API: dict[str, str] = {
    "ble": "BLE",
    "wifi": "Wifi",
    "mqtt": "Mqtt",
    "knx": "KNX",
    "ws": "WS",
    "eth": "Eth",
    "http": "HTTP",
    "sys": "Sys",
    "cloud": "Cloud",
    "shelly": "Shelly",
    "schedule": "Schedule",
    "webhook": "Webhook",
    "kvs": "KVS",
    "script": "Script",
    "switch": "Switch",
    "input": "Input",
    "cover": "Cover",
    "light": "Light",
    "rgb": "RGB",
    "rgbw": "RGBW",
    "cct": "CCT",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "voltmeter": "Voltmeter",
    "em": "EM",
    "em1": "EM1",
    "pm1": "PM1",
    "smoke": "Smoke",
    "matter": "Matter",
    "zigbee": "Zigbee",
    "bthome": "BTHome",
    "modbus": "Modbus",
    "dali": "DALI",
    "devicepower": "DevicePower",
    "ui": "UI",
}


def get_api_component_type(component_type: str) -> str:
    """Get the API component type name from the component type key.

    Args:
        component_type: Component type key (e.g., 'switch', 'sys', 'wifi')

    Returns:
        API component type name (e.g., 'Switch', 'Sys', 'Wifi')
    """
    return COMPONENT_TYPE_TO_API.get(component_type.lower(), component_type.title())
