"""Config flow for the DEEBOT NEO 2 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_COUNTRY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.components.ecovacs.config_flow import (
    _validate_input as _ecovacs_validate_input,
)
from homeassistant.components.ecovacs.controller import EcovacsController
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import selector

from . import _patch_deebot_client
from .const import (
    CONF_DEVICE_DID,
    CONF_DEVICE_NAME,
    CONF_DEVICE_RESOURCE,
    DOMAIN,
)
from .devices import get_profile_for_device, is_supported_device, PROFILES

_LOGGER = logging.getLogger(__name__)


def _device_label(info: dict[str, Any]) -> str:
    """Return a human-readable label for the device, including model info."""
    base = str(info.get("nick") or info.get("deviceName") or info.get("name") or info["did"])
    device_class = info.get("class", "")
    profile = PROFILES.get(device_class)
    if profile is not None:
        return f"{base} ({profile.friendly_name})"
    return base


def _device_api_info(device: Any) -> dict[str, Any]:
    return device.api if hasattr(device, "api") else device


async def _find_supported_devices(
    controller: EcovacsController,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Return supported NEO 2 devices after official auth validation succeeds."""
    errors: dict[str, str] = {}
    try:
        _patch_deebot_client()
        devices = await controller._api_client.get_devices()  # noqa: SLF001
    except ConfigEntryNotReady:
        _LOGGER.debug("Cannot connect to Ecovacs during device discovery", exc_info=True)
        errors["base"] = "cannot_connect"
        return [], errors
    except ConfigEntryError:
        _LOGGER.debug("Invalid Ecovacs authentication details during discovery", exc_info=True)
        errors["base"] = "invalid_auth"
        return [], errors
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected exception during DEEBOT NEO 2 setup")
        errors["base"] = "unknown"
        return [], errors
    finally:
        await controller.teardown()

    discovered = [_device_api_info(device) for device in devices.mqtt] + devices.not_supported
    for info in discovered:
        _LOGGER.debug(
            "Ecovacs discovery saw device class=%s UILogicId=%s",
            info.get("class"),
            info.get("UILogicId"),
        )

    supported = [info for info in discovered if is_supported_device(info)]
    # Log profile assignment for each supported device (class/UI logic only, no IDs)
    for info in supported:
        profile = get_profile_for_device(info)
        _LOGGER.debug(
            "Config-flow matched device class=%s UILogicId=%s to profile=%s",
            info.get("class"),
            info.get("UILogicId"),
            profile.friendly_name if profile else "unknown",
        )

    if not supported:
        errors["base"] = "no_supported_vacuums"
    return supported, errors


class DeebotNeo2ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DEEBOT NEO 2."""

    VERSION = 1

    def __init__(self) -> None:
        self._auth_input: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Ecovacs account details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._auth_input = {}
            self._devices = []
            errors = await _ecovacs_validate_input(self.hass, user_input)
            if not errors:
                devices, errors = await _find_supported_devices(
                    EcovacsController(self.hass, user_input)
                )
            if not errors:
                self._auth_input = user_input
                self._devices = devices
                if len(devices) == 1:
                    return await self._create_entry(devices[0])
                return await self.async_step_select_device()

        defaults = dict(user_input or {CONF_COUNTRY: self.hass.config.country})
        if errors:
            defaults.pop(CONF_PASSWORD, None)
        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_COUNTRY): selector.CountrySelector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, defaults),
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose a supported DEEBOT NEO 2 vacuum."""
        if user_input is not None:
            selected = next(
                device for device in self._devices if device["did"] == user_input[CONF_DEVICE_DID]
            )
            return await self._create_entry(selected)

        options = {device["did"]: _device_label(device) for device in self._devices}
        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_DID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=value, label=label)
                                for value, label in options.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def _create_entry(self, device: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(device["did"])
        self._abort_if_unique_id_configured()
        data = dict(self._auth_input)
        data[CONF_DEVICE_DID] = device["did"]
        data[CONF_DEVICE_RESOURCE] = device.get("resource")
        data[CONF_DEVICE_NAME] = _device_label(device)
        return self.async_create_entry(title=_device_label(device), data=data)
