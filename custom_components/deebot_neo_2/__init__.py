"""DEEBOT NEO 2 custom integration."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from functools import partial
import logging
import random
import string
import sys
from typing import Any

from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.device import Device
from deebot_client.exceptions import DeebotError, InvalidAuthenticationError, MqttError
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.util import md5

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_COUNTRY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from . import q287s6_app, q287s6_profile
from .const import CONF_DEVICE_DID, DOMAIN, PLATFORMS, SUPPORTED_DEVICE_CLASS

_LOGGER = logging.getLogger(__name__)


def _patch_deebot_client() -> None:
    """Expose q287s6 support to deebot_client before devices initialize."""
    sys.modules.setdefault("deebot_client.commands.json.q287s6_app", q287s6_app)
    sys.modules.setdefault("deebot_client.hardware.q287s6", q287s6_profile)


def _client_device_id() -> str:
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


class Neo2Controller:
    """Small deebot_client controller scoped to q287s6 devices."""

    def __init__(self, hass: HomeAssistant, config: Mapping[str, Any]) -> None:
        self._hass = hass
        self._config = config
        self._device_id = _client_device_id()
        self._devices: list[Device] = []
        self._mqtt_client: MqttClient | None = None
        self._authenticator: Authenticator | None = None

    @property
    def devices(self) -> list[Device]:
        """Return initialized q287s6 devices."""
        return self._devices

    async def initialize(self) -> None:
        """Authenticate, initialize MQTT, and load the selected q287s6 device."""
        _patch_deebot_client()
        country = self._config[CONF_COUNTRY]
        authenticator = Authenticator(
            create_rest_config(
                aiohttp_client.async_get_clientsession(self._hass),
                device_id=self._device_id,
                alpha_2_country=country,
            ),
            self._config[CONF_USERNAME],
            md5(self._config[CONF_PASSWORD]),
        )
        self._authenticator = authenticator
        api_client = ApiClient(authenticator)

        try:
            device_list = await api_client.get_devices()
            selected_did = self._config.get(CONF_DEVICE_DID)
            mqtt_devices = [
                info
                for info in device_list.mqtt
                if info.get("class") == SUPPORTED_DEVICE_CLASS
                and (selected_did is None or info.get("did") == selected_did)
            ]
            if not mqtt_devices:
                raise ConfigEntryNotReady("No selected q287s6 device found")

            mqtt_config = await self._hass.async_add_executor_job(
                partial(create_mqtt_config, device_id=self._device_id, country=country)
            )
            mqtt = MqttClient(mqtt_config, authenticator)
            await mqtt.verify_config()
            self._mqtt_client = mqtt

            async with asyncio.TaskGroup() as task_group:
                for info in mqtt_devices:
                    device = Device(info, authenticator)
                    task_group.create_task(self._initialize_device(device, mqtt))
        except InvalidAuthenticationError as err:
            raise ConfigEntryAuthFailed("Invalid Ecovacs credentials") from err
        except (DeebotError, MqttError) as err:
            raise ConfigEntryNotReady("Ecovacs setup failed") from err

        _LOGGER.debug("Initialized %s q287s6 device(s)", len(self._devices))

    async def _initialize_device(self, device: Device, mqtt: MqttClient) -> None:
        await device.initialize(mqtt)
        self._devices.append(device)

    async def teardown(self) -> None:
        """Disconnect devices and clients."""
        for device in self._devices:
            await device.teardown()
        self._devices.clear()
        if self._mqtt_client is not None:
            await self._mqtt_client.disconnect()
            self._mqtt_client = None
        if self._authenticator is not None:
            await self._authenticator.teardown()
            self._authenticator = None


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
