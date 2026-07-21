"""Constants for the DEEBOT NEO 2 integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "deebot_neo_2"
NAME = "DEEBOT NEO 2"
VERSION = "0.1.3"

# Kept for backwards-compatibility with any existing config-entry data that
# stores the device class.  New code should use devices.PROFILES / SUPPORTED_CLASSES.
SUPPORTED_DEVICE_CLASS = "q287s6"

CONF_DEVICE_DID = "device_did"
CONF_DEVICE_NAME = "device_name"
CONF_DEVICE_RESOURCE = "device_resource"

PLATFORMS: tuple[Platform, ...] = (
    Platform.VACUUM,
    Platform.SENSOR,
    Platform.BUTTON,
)

SUCTION_OPTIONS = ["quiet mode", "standard", "strong", "max"]
