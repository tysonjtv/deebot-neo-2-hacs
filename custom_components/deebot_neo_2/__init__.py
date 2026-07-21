"""DEEBOT NEO 2 custom integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
import sys
from typing import Any

import deebot_client.hardware as deebot_hardware
from deebot_client.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.ecovacs.controller import EcovacsController
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import q287s6_app, q287s6_profile, eyfj07_profile
from .const import CONF_DEVICE_DID, PLATFORMS
from .devices import PROFILES, get_profile

_LOGGER = logging.getLogger(__name__)


def _patch_deebot_client() -> None:
    """Register all supported device classes with deebot_client (idempotent)."""
    # Mapping from deebot_client hardware module path to local profile module.
    _modules = {
        "deebot_client.commands.json.q287s6_app": q287s6_app,
        "deebot_client.hardware.q287s6": q287s6_profile,
        "deebot_client.hardware.eyfj07": eyfj07_profile,
    }

    for module_path, module_obj in _modules.items():
        if module_path not in sys.modules:
            sys.modules[module_path] = module_obj
            _LOGGER.debug("Registered deebot_client module: %s", module_path)
        else:
            _LOGGER.debug("deebot_client module already registered: %s", module_path)

    # Remove all supported classes from the "not found" cache so deebot_client
    # will call get_device_info() for them instead of raising.
    if not_found := getattr(deebot_hardware, "_NOT_FOUND", None):
        for profile in PROFILES.values():
            device_class = profile.device_class
            if device_class in not_found:
                not_found.discard(device_class)
                _LOGGER.debug(
                    "Removed %s from deebot_client _NOT_FOUND cache", device_class
                )


class Neo2Controller(EcovacsController):
    """Official Ecovacs controller with multi-model registration and filtering."""

    def __init__(self, hass: HomeAssistant, config: Mapping[str, Any]) -> None:
        super().__init__(hass, config)
        self._config = config

    async def initialize(self) -> None:
        """Register all supported models, then run the official Ecovacs controller setup."""
        _patch_deebot_client()
        await super().initialize()

        selected_did = self._config.get(CONF_DEVICE_DID)
        selected_devices: list[Device] = []
        for device in self._devices:
            device_class = device.device_info.get("class", "")
            profile = get_profile(device_class)
            if profile is not None and (
                selected_did is None or device.device_info.get("did") == selected_did
            ):
                _LOGGER.debug(
                    "Accepted device class=%s profile=%s stable=%s",
                    device_class,
                    profile.friendly_name,
                    profile.stable,
                )
                if not profile.stable:
                    _LOGGER.warning(
                        "Device class %s (%s) is experimental and has not been "
                        "hardware-validated by the maintainer. Please report results "
                        "to https://github.com/tysonjtv/deebot-neo-2-hacs/issues/1",
                        device_class,
                        profile.friendly_name,
                    )
                selected_devices.append(device)
            else:
                await device.teardown()

        self._devices = selected_devices
        if not self._devices:
            raise ConfigEntryNotReady("No supported DEEBOT NEO 2 device found")

        _LOGGER.debug("Initialized %d supported DEEBOT NEO 2 device(s)", len(self._devices))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DEEBOT NEO 2 from a config entry."""
    controller = Neo2Controller(hass, entry.data)
    await controller.initialize()
    entry.runtime_data = controller
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    controller: Neo2Controller = entry.runtime_data
    await controller.teardown()
    return unload_ok
