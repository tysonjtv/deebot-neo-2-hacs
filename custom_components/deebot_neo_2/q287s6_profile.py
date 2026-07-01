"""DEEBOT NEO 2 / NEO 2 PLUS q287s6 capability profile."""

from __future__ import annotations

from dataclasses import replace

from deebot_client.capabilities import CapabilityEvent, CapabilityExecute, CapabilitySetTypes
from deebot_client.commands.json.clean import CleanArea
from deebot_client.events import BatteryEvent, FanSpeedEvent, FanSpeedLevel, StateEvent
from deebot_client.hardware.qhe2o2 import get_device_info as _base_get_device_info

from .q287s6_app import (
    Q287s6EndpointCharge,
    Q287s6EndpointClean,
    Q287s6EndpointFanSpeed,
    Q287s6EndpointFanSpeedStatus,
    Q287s6EndpointStatus,
)


def get_device_info():
    """Return adjusted capabilities for q287s6."""
    info = _base_get_device_info()

    availability = replace(info.capabilities.availability, get=[])
    battery = CapabilityEvent(BatteryEvent, [Q287s6EndpointStatus()])
    error = replace(info.capabilities.error, get=[])
    life_span = replace(info.capabilities.life_span, get=[])
    network = replace(info.capabilities.network, get=[])
    state = CapabilityEvent(StateEvent, [Q287s6EndpointStatus()])
    stats = replace(
        info.capabilities.stats,
        clean=replace(info.capabilities.stats.clean, get=[]),
        report=replace(info.capabilities.stats.report, get=[]),
        total=replace(info.capabilities.stats.total, get=[]),
    )

    clean_action = replace(
        info.capabilities.clean.action,
        command=Q287s6EndpointClean,
        area=CleanArea,
    )
    clean = replace(
        info.capabilities.clean,
        action=clean_action,
        continuous=None,
        count=None,
        log=None,
    )

    caps = replace(
        info.capabilities,
        availability=availability,
        battery=battery,
        error=error,
        charge=CapabilityExecute(Q287s6EndpointCharge),
        fan_speed=CapabilitySetTypes(
            event=FanSpeedEvent,
            get=[Q287s6EndpointFanSpeedStatus()],
            set=Q287s6EndpointFanSpeed,
            types=(
                FanSpeedLevel.QUIET,
                FanSpeedLevel.NORMAL,
                FanSpeedLevel.MAX,
                FanSpeedLevel.MAX_PLUS,
            ),
        ),
        life_span=life_span,
        map=None,
        network=network,
        play_sound=None,
        settings=replace(
            info.capabilities.settings,
            carpet_auto_fan_boost=None,
            child_lock=None,
            volume=None,
        ),
        station=None,
        stats=stats,
        water=None,
        clean=clean,
        state=state,
    )
    return replace(info, capabilities=caps)
