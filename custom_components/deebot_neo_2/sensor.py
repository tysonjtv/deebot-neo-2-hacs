"""Sensor platform for DEEBOT NEO 2."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
import logging
from typing import Any

from deebot_client.device import Device
from deebot_client.events import BatteryEvent
from deebot_client.events.base import Event

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Neo2Controller
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

BATTERY_DESCRIPTION = SensorEntityDescription(
    key="battery",
    name="Battery",
    device_class=SensorDeviceClass.BATTERY,
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DEEBOT NEO 2 sensors."""
    controller: Neo2Controller = config_entry.runtime_data
    async_add_entities([Neo2BatterySensor(device) for device in controller.devices])


class Neo2BatterySensor(SensorEntity):
    """Battery sensor that only updates when Ecovacs returns a real value."""

    entity_description = BATTERY_DESCRIPTION
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_available = True

    def __init__(self, device: Device) -> None:
        self._device = device
        self._subscribed_events: set[type[Event]] = set()
        self._attr_unique_id = f"{device.device_info['did']}_battery"

    @property
    def device_info(self) -> DeviceInfo:
        info = self._device.device_info
        return DeviceInfo(
            identifiers={(DOMAIN, info["did"])},
            manufacturer="Ecovacs",
            model=info.get("deviceName", "DEEBOT NEO 2"),
            model_id=info.get("class"),
            name=info.get("nick") or info.get("deviceName") or "DEEBOT NEO 2",
            serial_number=info.get("name") or info["did"],
            sw_version=self._device.fw_version,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to battery events."""
        await super().async_added_to_hass()

        async def on_battery(event: BatteryEvent) -> None:
            if event.value is None:
                _LOGGER.debug("Ignoring q287s6 battery event without a value")
                return
            self._attr_native_value = int(event.value)
            self.async_write_ha_state()

        self._subscribe(BatteryEvent, on_battery)
        self.async_schedule_update_ha_state(force_refresh=True)

    def _subscribe[EventT: Event](
        self,
        event_type: type[EventT],
        callback: Callable[[EventT], Coroutine[Any, Any, None]],
    ) -> None:
        self._subscribed_events.add(event_type)
        self.async_on_remove(self._device.events.subscribe(event_type, callback))

    async def async_update(self) -> None:
        """Request a best-effort refresh."""
        for event_type in self._subscribed_events:
            try:
                self._device.events.request_refresh(event_type)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("q287s6 battery refresh failed", exc_info=True)
