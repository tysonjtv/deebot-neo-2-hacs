"""Button platform for DEEBOT NEO 2.

No standalone buttons are exposed yet. Start clean and return-to-dock are exposed
on the vacuum entity because those paths have been tested for q287s6.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DEEBOT NEO 2 buttons."""
    _LOGGER.debug("No DEEBOT NEO 2 buttons are exposed")
