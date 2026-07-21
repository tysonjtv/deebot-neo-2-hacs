"""DEEBOT NEO 2.0 eyfj07 capability profile.

The eyfj07 (DEEBOT NEO 2.0) uses the same official-app endpoint commands as the
q287s6 (DEEBOT NEO 2.0 PLUS). This module reuses the q287s6 profile implementation
so both classes share the same command family.

Status: EXPERIMENTAL – pending hardware validation by reporter (issue #1).
"""

from __future__ import annotations

from .q287s6_profile import get_device_info as _q287s6_get_device_info

# eyfj07 uses the same capability profile as q287s6 since both models share the
# NEO 2 command family (APNs 10001 / 40001 / 40013 / 50011).
# If hardware testing reveals differences, this module can be extended independently.
get_device_info = _q287s6_get_device_info
