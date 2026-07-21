"""Central device profile registry for DEEBOT NEO 2 integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeviceProfile:
    """Per-model profile for a supported DEEBOT NEO 2 device."""

    device_class: str
    """Ecovacs device class (e.g. q287s6, eyfj07)."""

    ui_logic_ids: frozenset[str]
    """Accepted UILogicId values reported by the Ecovacs API."""

    friendly_name: str
    """Human-readable model name shown in the UI."""

    hw_module: str
    """Python module path used to register the hardware profile in deebot_client."""

    profile_module: str
    """Local module that implements get_device_info() for this class."""

    stable: bool
    """True = stable/released; False = experimental/pending hardware validation."""


# ---------------------------------------------------------------------------
# Supported device profiles
# ---------------------------------------------------------------------------

#: DEEBOT NEO 2.0 PLUS – stable, hardware-tested
Q287S6_PROFILE = DeviceProfile(
    device_class="q287s6",
    ui_logic_ids=frozenset({"y30plus_ww_h_y30h5"}),
    friendly_name="DEEBOT NEO 2.0 PLUS",
    hw_module="deebot_client.hardware.q287s6",
    profile_module="custom_components.deebot_neo_2.q287s6_profile",
    stable=True,
)

#: DEEBOT NEO 2.0 – experimental, pending hardware validation by reporter
EYFJ07_PROFILE = DeviceProfile(
    device_class="eyfj07",
    ui_logic_ids=frozenset({"y30_ww_h_y30h5"}),
    friendly_name="DEEBOT NEO 2.0 (experimental)",
    hw_module="deebot_client.hardware.eyfj07",
    profile_module="custom_components.deebot_neo_2.eyfj07_profile",
    stable=False,
)

#: All supported profiles, keyed by device class
PROFILES: dict[str, DeviceProfile] = {
    Q287S6_PROFILE.device_class: Q287S6_PROFILE,
    EYFJ07_PROFILE.device_class: EYFJ07_PROFILE,
}

#: Set of all supported device class strings
SUPPORTED_CLASSES: frozenset[str] = frozenset(PROFILES)


def get_profile(device_class: str) -> DeviceProfile | None:
    """Return the profile for a device class, or None if unsupported."""
    return PROFILES.get(device_class)


def get_profile_for_device(device_info: dict[str, Any]) -> DeviceProfile | None:
    """Return the best matching profile for a device API info dict.

    Matches by device class first. If the class is supported but the reported
    UILogicId is not in the expected set, a warning is logged and the profile is
    still returned so the device can attempt to initialise (defensive handling).
    """
    device_class = device_info.get("class", "")
    profile = PROFILES.get(device_class)

    if profile is None:
        _LOGGER.debug(
            "Device class %s is not supported by this integration",
            device_class,
        )
        return None

    ui_logic_id = device_info.get("UILogicId", "")
    if ui_logic_id and ui_logic_id not in profile.ui_logic_ids:
        _LOGGER.warning(
            "Device class %s has unexpected UILogicId %s (expected one of %s); "
            "proceeding with %s profile defensively",
            device_class,
            ui_logic_id,
            sorted(profile.ui_logic_ids),
            profile.friendly_name,
        )
    else:
        _LOGGER.debug(
            "Matched device class=%s UILogicId=%s to profile %s (stable=%s)",
            device_class,
            ui_logic_id or "<unknown>",
            profile.friendly_name,
            profile.stable,
        )

    return profile


def is_supported_device(device_info: dict[str, Any]) -> bool:
    """Return True if the device class is recognised by this integration."""
    return device_info.get("class", "") in SUPPORTED_CLASSES
