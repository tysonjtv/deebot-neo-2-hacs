# DEEBOT NEO 2

Unofficial Home Assistant custom integration for Ecovacs DEEBOT NEO 2.0 and DEEBOT NEO 2.0 PLUS vacuums using device class `q287s6`.

This is a community integration. It is not affiliated with, endorsed by, or supported by Ecovacs or Home Assistant.

## What Works

- Add a DEEBOT NEO 2.0 / NEO 2.0 PLUS from the Home Assistant UI
- Start auto clean
- Return to dock
- Vacuum state from the q287s6 app status endpoint
- Battery level when Ecovacs returns a real battery value
- Suction power options: `quiet mode`, `standard`, `strong`, `max`

## What Is Intentionally Not Exposed

- Stop is not exposed because it has not been kept in the published UI path.
- Pause is not exposed until more users confirm it works reliably.
- Unsupported endpoints such as `getCleanInfo`, `getChargeState`, `getStats`, and `getTotalStats` are disabled or ignored in the q287s6 capability profile.
- Sensors that commonly return `None` are not exposed.

## Installation With HACS

1. Install HACS
2. Go to HACS -> three dots -> Custom repositories
3. Add this GitHub repo URL
4. Select category: Integration
5. Install "DEEBOT NEO 2"
6. Restart Home Assistant
7. Go to Settings -> Devices & services -> Add integration
8. Search for "DEEBOT NEO 2"
9. Log in with Ecovacs account details
10. Select the vacuum

## Supported Devices

This integration is for Ecovacs devices with class `q287s6`, including:

- DEEBOT NEO 2.0
- DEEBOT NEO 2.0 PLUS

Other Ecovacs models are not supported by this integration. Use Home Assistant's built-in Ecovacs integration for other models.

## Debug Logging

Add this to `configuration.yaml`, then restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.deebot_neo_2: debug
```

When opening an issue, include the relevant `custom_components.deebot_neo_2` log lines. Remove account IDs, tokens, email addresses, and home/network details before posting logs.

## Troubleshooting

### Vacuum Shows Unavailable

This integration avoids marking the vacuum unavailable just because unsupported q287s6 endpoints return `None`. If it still shows unavailable:

- Restart Home Assistant after installing or updating the integration.
- Confirm the vacuum is online in the Ecovacs app.
- Confirm your Ecovacs region/country matches the account.
- Enable debug logs and check for login, MQTT, or endpoint errors.

### Start Works But Pause Or Dock Does Not

Start clean and return-to-dock use q287s6 official-app endpoints. Pause is not exposed in the UI until it is confirmed reliable across more devices.

If return-to-dock fails:

- Confirm the robot is awake and reachable in the Ecovacs app.
- Enable debug logs.
- Open an issue with the debug log around the return-to-dock command.

### Battery Missing

Battery is only updated when Ecovacs returns a real battery value from the q287s6 status endpoint. If it is missing:

- Wait for a status refresh after restart.
- Start or dock the robot to trigger fresh status.
- Enable debug logs and check whether the status response includes `battery`.

### Region Or Login Issues

Ecovacs accounts are region-sensitive.

- Choose the same country/region you use in the Ecovacs app.
- Verify your email/phone and password by logging into the official app.
- If your Ecovacs app account uses a social login, create or set an Ecovacs password first if the app allows it.

### How To Enable Debug Logs

Use the logger configuration shown in the Debug Logging section. After reproducing the issue, download Home Assistant logs and include only the relevant sanitized lines in your GitHub issue.

## Privacy

This integration stores your Ecovacs account details in Home Assistant's config entry storage, similar to other cloud integrations. Do not post `.storage` files, tokens, passwords, or full logs in GitHub issues.

## Development Notes

The q287s6 profile disables unsupported stock status/stat/lifespan endpoints and replaces key actions with official-app endpoint calls:

- Status: APN `10001`
- Start clean: APN `40001`
- Return to dock: APN `40013`
- Suction power: APN `50011`

## License

MIT. See [LICENSE](LICENSE).
