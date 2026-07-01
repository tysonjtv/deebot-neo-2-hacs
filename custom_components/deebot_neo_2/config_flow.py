"""Config flow for the DEEBOT NEO 2 integration."""

from __future__ import annotations

from functools import partial
import logging
import random
import string
from typing import Any

from aiohttp import ClientError
from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.exceptions import InvalidAuthenticationError, MqttError
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.util import md5
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_COUNTRY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, selector

from . import _patch_deebot_client
from .const import (
    CONF_DEVICE_DID,
    CONF_DEVICE_NAME,
    CONF_DEVICE_RESOURCE,
    DOMAIN,
    SUPPORTED_DEVICE_CLASS,
)

_LOGGER = logging.getLogger(__name__)


def _client_device_id() -> str:
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def _device_label(info: dict[str, Any]) -> str:
    return str(info.get("nick") or info.get("deviceName") or info.get("name") or info["did"])


async def _find_supported_devices(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Validate login and return q287s6 devices."""
    errors: dict[str, str] = {}
    device_id = _client_device_id()
    authenticator = Authenticator(
        create_rest_config(
            aiohttp_client.async_get_clientsession(hass),
            device_id=device_id,
            alpha_2_country=user_input[CONF_COUNTRY],
        ),
        user_input[CONF_USERNAME],
        md5(user_input[CONF_PASSWORD]),
    )

    try:
        _patch_deebot_client()
        await authenticator.authenticate()
        mqtt_config = await hass.async_add_executor_job(
            partial(create_mqtt_config, device_id=device_id, country=user_input[CONF_COUNTRY])
        )
        mqtt_client = MqttClient(mqtt_config, authenticator)
        await mqtt_client.verify_config()
        await mqtt_client.disconnect()
        devices = await ApiClient(authenticator).get_devices()
    except ClientError:
        _LOGGER.debug("Cannot connect to Ecovacs", exc_info=True)
        errors["base"] = "cannot_connect"
        return [], errors
    except InvalidAuthenticationError:
        errors["base"] = "invalid_auth"
        return [], errors
    except MqttError:
        _LOGGER.debug("Cannot connect to Ecovacs MQTT", exc_info=True)
        errors["base"] = "cannot_connect"
        return [], errors
    except Exception:
        _LOGGER.exception("Unexpected exception during DEEBOT NEO 2 setup")
        errors["base"] = "unknown"
        return [], errors
    finally:
        await authenticator.teardown()

    supported = [info for info in devices.mqtt if info.get("class") == SUPPORTED_DEVICE_CLASS]
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
            devices, errors = await _find_supported_devices(self.hass, user_input)
            if not errors:
                self._auth_input = user_input
                self._devices = devices
                if len(devices) == 1:
                    return await self._create_entry(devices[0])
                return await self.async_step_select_device()

        defaults = user_input or {CONF_COUNTRY: self.hass.config.country}
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
        """Let the user choose a q287s6 vacuum."""
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
