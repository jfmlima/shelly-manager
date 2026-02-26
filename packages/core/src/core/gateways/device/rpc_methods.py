class RpcMethods:
    """RPC method names used by Shelly Gen2+ devices."""

    GET_DEVICE_INFO = "Shelly.GetDeviceInfo"
    GET_COMPONENTS = "Shelly.GetComponents"
    GET_STATUS = "Shelly.GetStatus"
    LIST_METHODS = "Shelly.ListMethods"
    CHECK_FOR_UPDATE = "Shelly.CheckForUpdate"
    UPDATE = "Shelly.Update"
    REBOOT = "Shelly.Reboot"
    FACTORY_RESET = "Shelly.FactoryReset"
    SET_AUTH = "Shelly.SetAuth"

    # Component-level config methods
    SYS_SET_CONFIG = "Sys.SetConfig"
    WIFI_SET_CONFIG = "WiFi.SetConfig"
    MQTT_SET_CONFIG = "MQTT.SetConfig"
    CLOUD_SET_CONFIG = "Cloud.SetConfig"
