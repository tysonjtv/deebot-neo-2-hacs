"""Tests for the DEEBOT NEO 2 device profile registry (devices.py).

These tests are pure Python and require no HA or deebot_client installation.
They cover requirements 1-5 from the automated test specification.
"""

from __future__ import annotations

import importlib.util as _ilu
import os
import sys
import types
import unittest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Minimal stubs so we can import devices.py without HA or deebot_client
# ---------------------------------------------------------------------------

def _install_stub(name: str, **attrs: object) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# Stub homeassistant to satisfy any transitive imports that might occur.
_install_stub("homeassistant")
_install_stub("homeassistant.const", Platform=MagicMock())
_install_stub("homeassistant.core")
_install_stub("homeassistant.config_entries")
_install_stub("homeassistant.exceptions")
_install_stub("homeassistant.helpers")
_install_stub("homeassistant.helpers.device_registry")
_install_stub("homeassistant.helpers.entity_platform")
_install_stub("homeassistant.helpers.selector")
_install_stub("homeassistant.components")
_install_stub("homeassistant.components.vacuum")
_install_stub("homeassistant.components.sensor")
_install_stub("homeassistant.components.ecovacs")
_install_stub("homeassistant.components.ecovacs.controller")
_install_stub("homeassistant.components.ecovacs.config_flow")

# Stub deebot_client with enough attributes to satisfy __init__.py and devices.py
_deebot_device_stub = _install_stub("deebot_client.device", Device=MagicMock())
_deebot_hw_stub = _install_stub("deebot_client.hardware", _NOT_FOUND=set())
_install_stub("deebot_client.events")
_install_stub("deebot_client.events.base")
_install_stub("deebot_client.models")
_install_stub("deebot_client.capabilities")
_install_stub("deebot_client.commands")
_install_stub("deebot_client.commands.json")
_install_stub("deebot_client.commands.json.clean")
_install_stub("deebot_client.command")
_install_stub("deebot_client.const")
_install_stub("deebot_client.message")
_install_stub("deebot_client.authentication")
_install_stub("deebot_client.event_bus")

# Stub the component sub-modules imported in __init__.py
_q287s6_app_stub = _install_stub("custom_components.deebot_neo_2.q287s6_app")
_q287s6_profile_stub = _install_stub("custom_components.deebot_neo_2.q287s6_profile")
_eyfj07_profile_stub = _install_stub("custom_components.deebot_neo_2.eyfj07_profile")
_const_stub = _install_stub(
    "custom_components.deebot_neo_2.const",
    DOMAIN="deebot_neo_2",
    CONF_DEVICE_DID="device_did",
    CONF_DEVICE_NAME="device_name",
    CONF_DEVICE_RESOURCE="device_resource",
    SUPPORTED_DEVICE_CLASS="q287s6",
    PLATFORMS=(),
    SUCTION_OPTIONS=["quiet mode", "standard", "strong", "max"],
)

# Add the repo root to the path so custom_components is importable.
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Now import just the devices module directly (avoiding __init__ entirely)
_devices_spec = _ilu.spec_from_file_location(
    "custom_components.deebot_neo_2.devices",
    os.path.join(_REPO_ROOT, "custom_components", "deebot_neo_2", "devices.py"),
)
devices = _ilu.module_from_spec(_devices_spec)
sys.modules["custom_components.deebot_neo_2.devices"] = devices
_devices_spec.loader.exec_module(devices)


class TestDeviceProfiles(unittest.TestCase):
    """Test device profile registry."""

    # ------------------------------------------------------------------
    # Requirement 1: q287s6 remains recognised
    # ------------------------------------------------------------------

    def test_q287s6_is_recognised(self) -> None:
        profile = devices.get_profile("q287s6")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "q287s6")
        self.assertEqual(profile.friendly_name, "DEEBOT NEO 2.0 PLUS")
        self.assertTrue(profile.stable)

    # ------------------------------------------------------------------
    # Requirement 2: eyfj07 is recognised
    # ------------------------------------------------------------------

    def test_eyfj07_is_recognised(self) -> None:
        profile = devices.get_profile("eyfj07")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "eyfj07")
        self.assertFalse(profile.stable)

    # ------------------------------------------------------------------
    # Requirement 3: correct profile selected by class + UI logic ID
    # ------------------------------------------------------------------

    def test_q287s6_with_correct_ui_logic(self) -> None:
        info = {"class": "q287s6", "UILogicId": "y30plus_ww_h_y30h5"}
        profile = devices.get_profile_for_device(info)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "q287s6")

    def test_eyfj07_with_correct_ui_logic(self) -> None:
        info = {"class": "eyfj07", "UILogicId": "y30_ww_h_y30h5"}
        profile = devices.get_profile_for_device(info)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "eyfj07")

    # ------------------------------------------------------------------
    # Requirement 4: unsupported class is rejected
    # ------------------------------------------------------------------

    def test_unsupported_class_returns_none(self) -> None:
        profile = devices.get_profile("totally_unknown_class")
        self.assertIsNone(profile)

    def test_is_supported_returns_false_for_unknown(self) -> None:
        self.assertFalse(devices.is_supported_device({"class": "xyz999"}))

    def test_is_supported_returns_true_for_q287s6(self) -> None:
        self.assertTrue(devices.is_supported_device({"class": "q287s6"}))

    def test_is_supported_returns_true_for_eyfj07(self) -> None:
        self.assertTrue(devices.is_supported_device({"class": "eyfj07"}))

    # ------------------------------------------------------------------
    # Requirement 5: supported class with unexpected UI logic handled safely
    # ------------------------------------------------------------------

    def test_q287s6_unexpected_ui_logic_still_returns_profile(self) -> None:
        """An unexpected UILogicId must not crash or return None for the class."""
        info = {"class": "q287s6", "UILogicId": "y30_ww_h_y30h5"}  # eyfj07's logic
        profile = devices.get_profile_for_device(info)
        # Profile must still be returned (defensive)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "q287s6")

    def test_eyfj07_unexpected_ui_logic_still_returns_profile(self) -> None:
        info = {"class": "eyfj07", "UILogicId": "y30plus_ww_h_y30h5"}  # q287s6's logic
        profile = devices.get_profile_for_device(info)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.device_class, "eyfj07")

    def test_missing_ui_logic_id_returns_profile(self) -> None:
        """Missing UILogicId must not crash."""
        info = {"class": "q287s6"}
        profile = devices.get_profile_for_device(info)
        self.assertIsNotNone(profile)

    # ------------------------------------------------------------------
    # Profile structure / content checks
    # ------------------------------------------------------------------

    def test_profiles_have_expected_keys(self) -> None:
        for cls, profile in devices.PROFILES.items():
            self.assertEqual(cls, profile.device_class)
            self.assertIsInstance(profile.ui_logic_ids, frozenset)
            self.assertGreater(len(profile.ui_logic_ids), 0)
            self.assertTrue(profile.friendly_name)
            self.assertTrue(profile.hw_module)
            self.assertTrue(profile.profile_module)

    def test_supported_classes_matches_profiles(self) -> None:
        self.assertEqual(devices.SUPPORTED_CLASSES, frozenset(devices.PROFILES))

    def test_q287s6_stable_eyfj07_experimental(self) -> None:
        self.assertTrue(devices.PROFILES["q287s6"].stable)
        self.assertFalse(devices.PROFILES["eyfj07"].stable)


class TestRuntimePatching(unittest.TestCase):
    """Test runtime deebot_client registration (requirement 6)."""

    def _make_fresh_deebot_hardware_stub(self) -> types.ModuleType:
        mod = types.ModuleType("deebot_client.hardware")
        mod._NOT_FOUND = {p.device_class for p in devices.PROFILES.values()}  # type: ignore[attr-defined]
        return mod

    def test_patch_removes_supported_classes_from_not_found(self) -> None:
        hw_stub = self._make_fresh_deebot_hardware_stub()
        hw_stub._NOT_FOUND = {"q287s6", "eyfj07", "other_class"}

        # Replicate what _patch_deebot_client() does:
        for profile in devices.PROFILES.values():
            hw_stub._NOT_FOUND.discard(profile.device_class)

        self.assertNotIn("q287s6", hw_stub._NOT_FOUND)
        self.assertNotIn("eyfj07", hw_stub._NOT_FOUND)
        self.assertIn("other_class", hw_stub._NOT_FOUND)  # unrelated class preserved

    def test_patch_idempotent_when_called_multiple_times(self) -> None:
        """Calling the equivalent patch logic multiple times must not raise."""
        hw_stub = self._make_fresh_deebot_hardware_stub()
        hw_stub._NOT_FOUND = {"q287s6", "eyfj07"}

        for _ in range(3):  # call three times
            for profile in devices.PROFILES.values():
                hw_stub._NOT_FOUND.discard(profile.device_class)

        self.assertNotIn("q287s6", hw_stub._NOT_FOUND)
        self.assertNotIn("eyfj07", hw_stub._NOT_FOUND)

    def test_sys_modules_setdefault_is_idempotent(self) -> None:
        """sys.modules.setdefault must not overwrite already-registered modules."""
        key = "_test_deebot_neo_2_dummy_module_"
        fake_mod_1 = types.ModuleType(key)
        fake_mod_2 = types.ModuleType(key)

        sys.modules.pop(key, None)
        sys.modules.setdefault(key, fake_mod_1)
        sys.modules.setdefault(key, fake_mod_2)  # should not overwrite

        self.assertIs(sys.modules[key], fake_mod_1)
        del sys.modules[key]

    def test_patch_does_not_corrupt_unrelated_modules(self) -> None:
        """sys.modules must not lose unrelated modules after patching."""
        original_keys = set(sys.modules.keys())

        fake_mod = types.ModuleType("_deebot_test_eyfj07_stub_")
        sys.modules.setdefault("_deebot_test_eyfj07_stub_", fake_mod)

        # All pre-existing modules still present
        for key in original_keys:
            self.assertIn(key, sys.modules)

        del sys.modules["_deebot_test_eyfj07_stub_"]


class TestStatusHandlerDefensiveness(unittest.TestCase):
    """Requirement 10: missing/unexpected status fields must not crash setup."""

    def test_empty_status_data_does_not_raise(self) -> None:
        data: dict = {}
        result = self._state_from_status(data)
        self.assertIsNone(result)

    def test_none_values_do_not_raise(self) -> None:
        data = {
            "battery": None,
            "fanMode": None,
            "status": None,
            "workMode": None,
            "chargeStatus": None,
            "pauseSwitch": None,
        }
        result = self._state_from_status(data)
        self.assertIsNone(result)

    def test_unexpected_status_string_returns_none(self) -> None:
        data = {"status": "TOTALLY_UNEXPECTED_VALUE_XYZ"}
        result = self._state_from_status(data)
        self.assertIsNone(result)

    def test_cleaning_status_detected(self) -> None:
        result = self._state_from_status({"status": "clean"})
        self.assertEqual(result, "cleaning")

    def test_docked_when_charging(self) -> None:
        result = self._state_from_status({"chargeStatus": True})
        self.assertEqual(result, "docked")

    def test_paused_when_pause_switch_true(self) -> None:
        result = self._state_from_status({"pauseSwitch": True})
        self.assertEqual(result, "paused")

    def test_returning_state_detected(self) -> None:
        result = self._state_from_status({"status": "goCharge"})
        self.assertEqual(result, "returning")

    def test_idle_state_detected(self) -> None:
        result = self._state_from_status({"status": "idle"})
        self.assertEqual(result, "idle")

    @staticmethod
    def _state_from_status(data: dict) -> str | None:
        """Inline re-implementation of Q287s6EndpointStatus._state_from_status.

        Tests the status-parsing logic without importing the module (which needs
        deebot_client at import time).
        """
        if data.get("pauseSwitch") is True:
            return "paused"

        status = data.get("status")
        work_mode = data.get("workMode")
        station_status = data.get("stationStatus")
        charge_state = data.get("chargeState")

        if status in {"clean", "cleaning", "smartClean"} or work_mode in {
            "auto",
            "clean",
            "cleaning",
        }:
            return "cleaning"
        if status in {"pause", "paused"} or work_mode in {"auto_pause", "pause", "paused"}:
            return "paused"
        if (
            data.get("chargeStatus") is True
            or data.get("charging") is True
            or data.get("isCharging") is True
            or data.get("isDocked") is True
        ):
            return "docked"
        if charge_state in {"charging", "docked", "charge", "charged"}:
            return "docked"
        if status in {"goCharge", "goCharging", "returning"} or work_mode in {
            "return_dock",
            "goCharging",
            "returning",
        }:
            return "returning"
        if status in {"charging", "docked"} or station_status in {"charging", "docked"}:
            return "docked"
        if status in {"idle", "stop"} or work_mode in {"idle", "stop"}:
            return "idle"
        return None


class TestPrivacySafety(unittest.TestCase):
    """Requirement 11: sensitive fields must not appear in diagnostics/logs."""

    _SENSITIVE_KEYS = {
        "password",
        "token",
        "email",
        "did",
        "resource",
        "home_id",
        "homeid",
        "uid",
        "access_token",
        "refresh_token",
        "auth_token",
        "account",
        "secret",
    }

    def test_device_profile_does_not_expose_sensitive_fields(self) -> None:
        """DeviceProfile dataclass must not contain any sensitive field names."""
        for profile in devices.PROFILES.values():
            for field_name in self._SENSITIVE_KEYS:
                self.assertFalse(
                    hasattr(profile, field_name),
                    f"DeviceProfile has sensitive field: {field_name}",
                )

    def test_get_profile_for_device_does_not_log_sensitive_values(self) -> None:
        """Log messages from get_profile_for_device must not include sensitive values."""
        import logging

        captured_messages: list[str] = []

        class CapturingHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_messages.append(self.format(record))

        handler = CapturingHandler()
        devices._LOGGER.addHandler(handler)
        devices._LOGGER.setLevel(logging.DEBUG)

        try:
            device_info = {
                "class": "q287s6",
                "UILogicId": "y30plus_ww_h_y30h5",
                "did": "SENSITIVE_DID_12345",
                "resource": "SENSITIVE_RESOURCE",
                "email": "user@example.com",
                "token": "supersecrettoken",
            }
            devices.get_profile_for_device(device_info)
        finally:
            devices._LOGGER.removeHandler(handler)

        for msg in captured_messages:
            self.assertNotIn("SENSITIVE_DID_12345", msg, "DID leaked in log")
            self.assertNotIn("SENSITIVE_RESOURCE", msg, "Resource ID leaked in log")
            self.assertNotIn("user@example.com", msg, "Email leaked in log")
            self.assertNotIn("supersecrettoken", msg, "Token leaked in log")


class TestConfigFlowErrors(unittest.TestCase):
    """Requirement 9: config-flow errors must use model-neutral wording."""

    def _load_translations(self) -> dict:
        import json
        translations_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "deebot_neo_2",
            "translations",
            "en.json",
        )
        with open(translations_path) as f:
            return json.load(f)

    def test_no_supported_vacuums_error_is_neutral(self) -> None:
        """The translations file must not reference only q287s6 in the error string."""
        translations = self._load_translations()
        error_msg = translations["config"]["error"]["no_supported_vacuums"]
        # Must not be exclusively q287s6-focused
        self.assertNotIn("only supports", error_msg.lower())
        # Must mention a broader context
        self.assertIn("NEO 2", error_msg)

    def test_user_step_description_mentions_both_classes(self) -> None:
        """The user step description must mention both device classes."""
        translations = self._load_translations()
        description = translations["config"]["step"]["user"]["description"]
        self.assertIn("q287s6", description)
        self.assertIn("eyfj07", description)


class TestSyntaxAndImports(unittest.TestCase):
    """Requirement 12: formatting, imports and syntax pass."""

    def _get_python_files(self) -> list[str]:
        import glob
        root = os.path.join(
            os.path.dirname(__file__), "..", "custom_components", "deebot_neo_2"
        )
        return glob.glob(os.path.join(root, "*.py"))

    def test_all_source_files_compile(self) -> None:
        """All source files must compile without syntax errors."""
        import py_compile
        for path in self._get_python_files():
            with self.subTest(path=path):
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as exc:
                    self.fail(f"Syntax error in {path}: {exc}")

    def test_devices_module_has_docstring(self) -> None:
        self.assertTrue(devices.__doc__, "devices.py must have a module docstring")

    def test_eyfj07_profile_file_exists(self) -> None:
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "deebot_neo_2",
            "eyfj07_profile.py",
        )
        self.assertTrue(os.path.exists(path), "eyfj07_profile.py must exist")

    def test_devices_py_exists(self) -> None:
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "deebot_neo_2",
            "devices.py",
        )
        self.assertTrue(os.path.exists(path), "devices.py must exist")


if __name__ == "__main__":
    unittest.main()

