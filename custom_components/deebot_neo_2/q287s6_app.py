"""q287s6 official-app command support."""

from __future__ import annotations

import logging
import random
import string
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from deebot_client.command import Command
from deebot_client.const import PATH_API_APPSVR_APP, REALM, REQUEST_HEADERS, DataType
from deebot_client.events import BatteryEvent, FanSpeedEvent, FanSpeedLevel, StateEvent
from deebot_client.message import HandlingResult, HandlingState
from deebot_client.models import CleanAction, CleanMode, State

if TYPE_CHECKING:
    from deebot_client.authentication import Authenticator
    from deebot_client.event_bus import EventBus
    from deebot_client.models import ApiDeviceInfo

_LOGGER = logging.getLogger(__name__)


def _nonce(length: int = 16) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def _ngiot_host(device_info: ApiDeviceInfo) -> str:
    service = device_info.get("service")
    if isinstance(service, dict) and service.get("mqs"):
        return str(service["mqs"])
    return f"api-ngiot.dc-{REALM}.ww.ecouser.net"


class Q287s6RobotControlClean(Command):
    """q287s6 clean action using the official Ecovacs app RobotControl envelope."""

    DATA_TYPE = DataType.JSON
    NAME = "Q287s6RobotControlClean"

    def __init__(self, action: CleanAction) -> None:
        super().__init__({"action": action})
        self._action = action

    def _get_payload(self) -> dict[str, Any]:
        return {}

    async def _execute_api_request(
        self, authenticator: Authenticator, device_info: ApiDeviceInfo
    ) -> dict[str, Any]:
        if self._action in (
            CleanAction.START,
            CleanAction.STOP,
            CleanAction.PAUSE,
            CleanAction.RESUME,
        ):
            return await self._post_robot_control(authenticator, device_info)
        return {"ret": "fail", "error": f"Unsupported q287s6 clean action: {self._action}"}

    async def _post_robot_control(
        self, authenticator: Authenticator, device_info: ApiDeviceInfo
    ) -> dict[str, Any]:
        clean_data = {
            "act": self._action.xml_value,
            "type": CleanMode.AUTO.value,
            "tri": "app",
        }
        payload = {
            "todo": "RobotControl",
            "did": device_info["did"],
            "mid": device_info["class"],
            "res": device_info["resource"],
            "app": {"id": "ecovacs", "ts": int(time.time() * 1000)},
            "data": {
                "ctl": {
                    "Clean": {
                        "cmd": "Clean",
                        "type": "p2p",
                        "did": device_info["did"],
                        "mid": device_info["class"],
                        "res": device_info["resource"],
                        "all": False,
                        "data": clean_data,
                    }
                }
            },
        }
        _LOGGER.debug("q287s6 RobotControl Clean request: %s", clean_data)
        try:
            response = await authenticator.post_authenticated(
                PATH_API_APPSVR_APP,
                payload,
                headers=REQUEST_HEADERS,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("q287s6 RobotControl Clean request failed")
            return {"ret": "fail", "error": str(err)}
        _LOGGER.debug(
            "q287s6 RobotControl Clean response received ret=%s code=%s",
            response.get("ret"),
            response.get("code"),
        )
        return response

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        if response.get("ret") == "ok" and response.get("code") == 0:
            clean = response.get("data", {}).get("Clean", {})
            if clean.get("ret") == "ok":
                if self._action in (CleanAction.STOP, CleanAction.PAUSE):
                    event_bus.notify(StateEvent(State.PAUSED))
                else:
                    event_bus.notify(StateEvent(State.CLEANING))
                return HandlingResult.success()
        if response.get("body", {}).get("code") == 0:
            return HandlingResult.success()
        return HandlingResult(HandlingState.ANALYSE)


class Q287s6EndpointCommand(Command):
    """q287s6 field-style api-ngiot endpoint command."""

    DATA_TYPE = DataType.JSON
    NAME = "Q287s6EndpointCommand"
    APN: str | None = None

    def __init__(
        self, data: dict[str, Any] | list[Any] | None = None, apn: str | None = None
    ) -> None:
        super().__init__(data or {})
        self._apn = apn or self.APN

    def _get_payload(self) -> dict[str, Any]:
        return {}

    async def _execute_api_request(
        self, authenticator: Authenticator, device_info: ApiDeviceInfo
    ) -> dict[str, Any]:
        if self._apn is None:
            return {"body": {"code": 1, "msg": "missing apn"}}
        return await self._post_endpoint(authenticator, device_info, self._apn, self._args)

    async def _post_endpoint(
        self,
        authenticator: Authenticator,
        device_info: ApiDeviceInfo,
        apn: str,
        data: dict[str, Any] | list[Any],
    ) -> dict[str, Any]:
        credentials = await authenticator.authenticate()
        auth_client = authenticator._auth_client  # noqa: SLF001
        config = auth_client._config  # noqa: SLF001
        url = urljoin(f"https://{_ngiot_host(device_info)}", "api/iot/endpoint/control")
        request_id = _nonce()
        query_params = {
            "si": request_id,
            "ct": "q",
            "eid": device_info["did"],
            "et": device_info["class"],
            "er": device_info["resource"],
            "apn": apn,
            "fmt": self.DATA_TYPE.value,
        }
        payload = {
            "header": {
                "channel": "iOS",
                "m": "request",
                "pri": 1,
                "reqid": _nonce(6),
                "ts": str(int(time.time() * 1000)),
                "tzc": "UTC",
                "tzm": 0,
                "ver": "0.0.50",
            },
            "body": {"data": data},
        }
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {credentials.token}",
            "content-type": "application/octet-stream",
            "user-agent": "EcovacsHome/287541 CFNetwork Darwin",
            "x-eco-request-id": request_id,
        }
        _LOGGER.debug("q287s6 endpoint request apn=%s data=%s", apn, data)
        try:
            async with config.session.post(
                url,
                json=payload,
                params=query_params,
                headers=headers,
            ) as response:
                response.raise_for_status()
                result: dict[str, Any] = await response.json(content_type=None)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("q287s6 endpoint request failed apn=%s", apn)
            return {"body": {"code": 1, "msg": str(err)}}
        body = result.get("body", {})
        _LOGGER.debug(
            "q287s6 endpoint response apn=%s code=%s", apn, body.get("code")
        )
        return result

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        body = response.get("body", {})
        if body.get("code") == 0:
            return HandlingResult.success()
        return HandlingResult(HandlingState.ANALYSE)


_FAN_SPEED_TO_FAN_MODE = {
    FanSpeedLevel.QUIET: "quiet",
    FanSpeedLevel.NORMAL: "auto",
    FanSpeedLevel.MAX: "strong",
    FanSpeedLevel.MAX_PLUS: "max",
}
_FAN_MODE_TO_FAN_SPEED = {value: key for key, value in _FAN_SPEED_TO_FAN_MODE.items()}
_FAN_SPEED_NAME_TO_FAN_MODE = {
    "quiet": "quiet",
    "quiet mode": "quiet",
    "normal": "auto",
    "standard": "auto",
    "auto": "auto",
    "strong": "strong",
    "max": "max",
    "max_plus": "max",
}


class Q287s6EndpointFanSpeed(Q287s6EndpointCommand):
    """Set q287s6 suction using the official app fanMode endpoint."""

    NAME = "Q287s6EndpointFanSpeed"
    APN = "50011"

    def __init__(self, speed: FanSpeedLevel | str) -> None:
        if isinstance(speed, FanSpeedLevel):
            fan_mode = _FAN_SPEED_TO_FAN_MODE[speed]
        else:
            fan_mode = _FAN_SPEED_NAME_TO_FAN_MODE[speed]
        super().__init__({"fanMode": fan_mode})
        self._speed = _FAN_MODE_TO_FAN_SPEED[fan_mode]

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        result = super()._handle_response(event_bus, response)
        if result.state == HandlingState.SUCCESS:
            event_bus.notify(FanSpeedEvent(self._speed))
        return result


class Q287s6EndpointFanSpeedStatus(Q287s6EndpointCommand):
    """Read q287s6 suction from the official app status endpoint."""

    NAME = "Q287s6EndpointFanSpeedStatus"
    APN = "10001"

    def __init__(self) -> None:
        super().__init__({"fields": ["fanMode"]})

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        body = response.get("body", {})
        if body.get("code") != 0:
            return HandlingResult(HandlingState.ANALYSE)

        fan_mode = body.get("data", {}).get("fanMode")
        speed = _FAN_MODE_TO_FAN_SPEED.get(fan_mode)
        if speed is None:
            return HandlingResult(HandlingState.ANALYSE)
        event_bus.notify(FanSpeedEvent(speed))
        return HandlingResult.success()


class Q287s6EndpointClean(Q287s6EndpointCommand):
    """q287s6 clean actions using official app endpoint commands."""

    NAME = "Q287s6EndpointClean"

    def __init__(self, action: CleanAction) -> None:
        super().__init__({"action": action})
        self._action = action

    async def _execute_api_request(
        self, authenticator: Authenticator, device_info: ApiDeviceInfo
    ) -> dict[str, Any]:
        if self._action == CleanAction.START:
            status = await self._post_endpoint(
                authenticator,
                device_info,
                "10001",
                {"fields": ["pauseSwitch", "status", "workMode"]},
            )
            data = status.get("body", {}).get("data", {})
            if data.get("pauseSwitch") is True or data.get("status") in {"pause", "paused"}:
                return await self._post_endpoint(
                    authenticator, device_info, "40011", {"pauseSwitch": False}
                )
            return await self._post_endpoint(
                authenticator,
                device_info,
                "40001",
                {"cleanMode": "smart", "cleanSwitch": True},
            )

        if self._action == CleanAction.RESUME:
            return await self._post_endpoint(
                authenticator, device_info, "40011", {"pauseSwitch": False}
            )

        if self._action == CleanAction.PAUSE:
            return await self._post_endpoint(
                authenticator, device_info, "40009", {"pauseSwitch": True}
            )

        return await Q287s6RobotControlClean(self._action)._execute_api_request(
            authenticator, device_info
        )

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        result = super()._handle_response(event_bus, response)
        if result.state == HandlingState.SUCCESS:
            if self._action == CleanAction.PAUSE:
                event_bus.notify(StateEvent(State.PAUSED))
            elif self._action in (CleanAction.START, CleanAction.RESUME):
                event_bus.notify(StateEvent(State.CLEANING))
        return result


class Q287s6EndpointStatus(Q287s6EndpointCommand):
    """q287s6 app-style status reader."""

    NAME = "Q287s6EndpointStatus"
    APN = "10001"

    def __init__(self) -> None:
        super().__init__(
            {
                "fields": [
                    "battery",
                    "chargeStatus",
                    "chargeState",
                    "charging",
                    "isCharging",
                    "isDocked",
                    "pauseSwitch",
                    "status",
                    "workMode",
                    "stationStatus",
                    "stationType",
                    "fanMode",
                    "cleanTime",
                    "cleanArea",
                    "error",
                ]
            }
        )

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        body = response.get("body", {})
        if body.get("code") != 0:
            return HandlingResult(HandlingState.ANALYSE)

        data = body.get("data", {})
        battery = data.get("battery")
        if battery is not None:
            event_bus.notify(BatteryEvent(int(battery)))

        speed = _FAN_MODE_TO_FAN_SPEED.get(data.get("fanMode"))
        if speed is not None:
            event_bus.notify(FanSpeedEvent(speed))

        state = self._state_from_status(data)
        if state is not None:
            event_bus.notify(StateEvent(state))
            return HandlingResult.success()
        if battery is not None or speed is not None:
            return HandlingResult.success()
        return HandlingResult(HandlingState.ANALYSE)

    @staticmethod
    def _state_from_status(data: dict[str, Any]) -> State | None:
        if data.get("pauseSwitch") is True:
            return State.PAUSED

        status = data.get("status")
        work_mode = data.get("workMode")
        station_status = data.get("stationStatus")
        charge_state = data.get("chargeState")

        if status in {"clean", "cleaning", "smartClean"} or work_mode in {
            "auto",
            "clean",
            "cleaning",
        }:
            return State.CLEANING
        if status in {"pause", "paused"} or work_mode in {"auto_pause", "pause", "paused"}:
            return State.PAUSED
        if (
            data.get("chargeStatus") is True
            or data.get("charging") is True
            or data.get("isCharging") is True
            or data.get("isDocked") is True
        ):
            return State.DOCKED
        if charge_state in {"charging", "docked", "charge", "charged"}:
            return State.DOCKED
        if status in {"goCharge", "goCharging", "returning"} or work_mode in {
            "return_dock",
            "goCharging",
            "returning",
        }:
            return State.RETURNING
        if status in {"charging", "docked"} or station_status in {"charging", "docked"}:
            return State.DOCKED
        if status in {"idle", "stop"} or work_mode in {"idle", "stop"}:
            return State.IDLE
        return None


class Q287s6EndpointCharge(Q287s6EndpointCommand):
    """Return q287s6 to dock using official app chargeSwitch endpoint."""

    NAME = "Q287s6EndpointCharge"
    APN = "40013"

    def __init__(self) -> None:
        super().__init__({"chargeSwitch": True})

    def _handle_response(
        self, event_bus: EventBus, response: dict[str, Any]
    ) -> HandlingResult:
        result = super()._handle_response(event_bus, response)
        if result.state == HandlingState.SUCCESS:
            event_bus.notify(StateEvent(State.RETURNING))
        return result
