# DEEBOT NEO 2

Unofficial Home Assistant custom integration for Ecovacs DEEBOT NEO 2 vacuums.

This is a community integration. It is not affiliated with, endorsed by, or supported by Ecovacs or Home Assistant.

## Supported Devices

| Model | Device Class | UI Logic ID | Status |
|---|---|---|---|
| DEEBOT NEO 2.0 PLUS | `q287s6` | `y30plus_ww_h_y30h5` | ✅ Stable |
| DEEBOT NEO 2.0 | `eyfj07` | `y30_ww_h_y30h5` | ⚠️ Experimental (awaiting hardware validation — see [issue #1](https://github.com/tysonjtv/deebot-neo-2-hacs/issues/1)) |

The `q287s6` (NEO 2.0 PLUS) path is stable and hardware-tested. The `eyfj07` (NEO 2.0) path uses the same command family but has not yet been confirmed on real hardware by the maintainer.

## What Works

- Add a DEEBOT NEO 2 from the Home Assistant UI
- Start auto clean
- Return to dock
- Vacuum state from the status endpoint
- Battery level when Ecovacs returns a real battery value
- Suction power options: `quiet mode`, `standard`, `strong`, `max`

## What Is Intentionally Not Exposed

- Stop is not exposed because it has not been kept in the published UI path.
- Pause is not exposed until more users confirm it works reliably.
- Unsupported endpoints such as `getCleanInfo`, `getChargeState`, `getStats`, and `getTotalStats` are disabled or ignored.
- Sensors that commonly return `None` are not exposed.

## Installation With HACS (Stable — q287s6 NEO 2.0 PLUS)

1. Install HACS
2. Go to HACS → three dots → Custom repositories
3. Add this GitHub repo URL: `https://github.com/tysonjtv/deebot-neo-2-hacs`
4. Select category: Integration
5. Install "DEEBOT NEO 2"
6. Restart Home Assistant
7. Go to Settings → Devices & services → Add integration
8. Search for "DEEBOT NEO 2"
9. Log in with Ecovacs account details
10. Select the vacuum

## Installation for Experimental Testing (eyfj07 NEO 2.0)

See [TESTING_EYFJ07.md](TESTING_EYFJ07.md) for step-by-step instructions to install and test the experimental `eyfj07` branch.

## Debug Logging

Add this to `configuration.yaml`, then restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.deebot_neo_2: debug
```

After reproducing an issue, look for log lines containing `custom_components.deebot_neo_2` in your Home Assistant logs. The following sanitized log lines are most useful for diagnosing problems:

```
Matched device class=<class> UILogicId=<logic_id> to profile <profile> (stable=<true/false>)
Config-flow matched device class=<class> UILogicId=<logic_id> to profile=<profile>
Accepted device class=<class> profile=<profile> stable=<true/false>
Initialized N supported DEEBOT NEO 2 device(s)
```

**⚠️ Before posting logs:** Remove all passwords, tokens, email addresses, full device IDs, resource IDs, and home IDs. Only share the log lines that contain `class=`, `UILogicId=`, `profile=`, or command/response status. Never share tokens, email addresses, full DIDs, resource IDs, or home IDs.

Issues: <https://github.com/tysonjtv/deebot-neo-2-hacs/issues>

## Troubleshooting

### Vacuum Shows Unavailable

This integration avoids marking the vacuum unavailable just because unsupported endpoints return `None`. If it still shows unavailable:

- Restart Home Assistant after installing or updating the integration.
- Confirm the vacuum is online in the Ecovacs app.
- Confirm your Ecovacs region/country matches the account.
- Enable debug logs and check for login, MQTT, or endpoint errors.

### Start Works But Pause Or Dock Does Not

Start clean and return-to-dock use official-app endpoints. Pause is not exposed in the UI until it is confirmed reliable across more devices.

If return-to-dock fails:

- Confirm the robot is awake and reachable in the Ecovacs app.
- Enable debug logs.
- Open an issue with the debug log around the return-to-dock command.

### Battery Missing

Battery is only updated when Ecovacs returns a real battery value from the status endpoint. If it is missing:

- Wait for a status refresh after restart.
- Start or dock the robot to trigger fresh status.
- Enable debug logs and check whether the status response includes `battery`.

### Region Or Login Issues

Ecovacs accounts are region-sensitive.

- Choose the same country/region you use in the Ecovacs app.
- Your Ecovacs email may be case sensitive. Enter the same email address you use in the Ecovacs Home app.
- Verify your email and password by logging into the Ecovacs Home app.
- If your Ecovacs app account uses a social login, create or set an Ecovacs password first if the app allows it.

## Privacy

This integration stores your Ecovacs account details in Home Assistant's config entry storage, similar to other cloud integrations. Do not post `.storage` files, tokens, passwords, or full logs in GitHub issues.

## Development Notes

Both models use the same official-app endpoint command family:

- Status: APN `10001`
- Start clean: APN `40001`
- Return to dock: APN `40013`
- Suction power: APN `50011`

The central device profile registry (`devices.py`) maps each device class to its capability profile and whether support is stable or experimental.

## License

MIT. See [LICENSE](LICENSE).
