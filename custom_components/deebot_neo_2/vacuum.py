"""Vacuum platform for DEEBOT NEO 2."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
import logging
from typing import Any

from deebot_client.device import Device
from deebot_client.events import BatteryEvent, FanSpeedEvent, FanSpeedLevel, StateEvent
from deebot_client.events.base import Event
from deebot_client.models import CleanAction, State

from homeassistant.components.vacuum import StateVacuumEntity, VacuumActivity, VacuumEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Neo2Controller
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_STATE_TO_ACTIVITY = {
    State.IDLE: VacuumActivity.IDLE,
    State.CLEANING: VacuumActivity.CLEANING,
    State.RETURNING: VacuumActivity.RETURNING,
    State.DOCKED: VacuumActivity.DOCKED,
    State.ERROR: VacuumActivity.ERROR,
    State.PAUSED: VacuumActivity.PAUSED,
}

_SUCTION_LABELS = {
    FanSpeedLevel.QUIET: "quiet mode",
    FanSpeedLevel.NORMAL: "standard",
    FanSpeedLevel.MAX: "strong",
    FanSpeedLevel.MAX_PLUS: "max",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DEEBOT NEO 2 vacuums."""
    controller: Neo2Controller = config_entry.runtime_data
    async_add_entities([Neo2VacuumEntity(device) for device in controller.devices])


class Neo2VacuumEntity(StateVacuumEntity):
    """DEEBOT NEO 2 vacuum entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.FAN_SPEED
    )

    def __init__(self, device: Device) -> None:
        self._device = device
        self._subscribed_events: set[type[Event]] = set()
        self._attr_unique_id = f"{device.device_info['did']}_vacuum"
        self._attr_activity = VacuumActivity.IDLE
        self._attr_available = True
        self._attr_fan_speed_list = list(_SUCTION_LABELS.values())

    @property
    def device_info(self) -> DeviceInfo:
        info = self._device.device_info
        device_info = DeviceInfo(
            identifiers={(DOMAIN, info["did"])},
            manufacturer="Ecovacs",
            model=info.get("deviceName", "DEEBOT NEO 2"),
            model_id=info.get("class"),
            name=info.get("nick") or info.get("deviceName") or "DEEBOT NEO 2",
            serial_number=info.get("name") or info["did"],
            sw_version=self._device.fw_version,
        )
        if mac := self._device.mac:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, mac)}
        return device_info

    async def async_added_to_hass(self) -> None:
        """Subscribe to device events."""
        await super().async_added_to_hass()

        async def on_state(event: StateEvent) -> None:
            self._attr_available = True
            self._attr_activity = _STATE_TO_ACTIVITY.get(event.state, VacuumActivity.IDLE)
            self.async_write_ha_state()

        async def on_fan_speed(event: FanSpeedEvent) -> None:
            self._attr_available = True
            self._attr_fan_speed = _SUCTION_LABELS.get(event.speed)
            self.async_write_ha_state()

        async def on_battery(event: BatteryEvent) -> None:
            if event.value is not None:
                self._attr_battery_level = int(event.value)
                self.async_write_ha_state()

        self._subscribe(StateEvent, on_state)
        self._subscribe(FanSpeedEvent, on_fan_speed)
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
        """Request a best-effort refresh without marking the entity unavailable."""
        for event_type in self._subscribed_events:
            try:
                self._device.events.request_refresh(event_type)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("q287s6 refresh failed for %s", event_type, exc_info=True)

    async def async_start(self) -> None:
        """Start an auto clean."""
        await self._execute("start", self._device.capabilities.clean.action.command(CleanAction.START))

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return the vacuum to the dock."""
        await self._execute("return_to_base", self._device.capabilities.charge.execute())

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set suction power."""
        if fan_speed not in self._attr_fan_speed_list:
            raise HomeAssistantError(f"Unsupported suction power: {fan_speed}")
        await self._execute("set_suction_power", self._device.capabilities.fan_speed.set(fan_speed))

    async def _execute(self, action: str, command: Any) -> None:
        try:
            _LOGGER.debug("q287s6 command requested: %s", action)
            await self._device.execute_command(command)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("q287s6 command failed: %s", action)
            raise HomeAssistantError(f"DEEBOT NEO 2 command failed: {action}") from err
