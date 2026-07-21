# Testing the DEEBOT NEO 2.0 (eyfj07) Experimental Branch

This guide is for non-developers who want to help test the experimental
`eyfj07` support for the **DEEBOT NEO 2.0** (not the PLUS).

If you own a NEO 2.0 PLUS (class `q287s6`), you do not need this guide —
the stable release already supports your device.

---

## ⚠️ Important Warnings

- This branch is **experimental**. It has not been validated on real `eyfj07` hardware by the maintainer.
- Back up your Home Assistant config before testing.
- Do **not** post tokens, email addresses, full device IDs, resource IDs, or home IDs in issue comments.
- If anything goes wrong, follow the [Rollback](#rollback) steps at the bottom.

---

## Step 1 – Install the Experimental Branch

### Option A: ZIP download (no Git required, recommended)

1. Go to the pull request for this branch on GitHub.
2. Click the branch name in the PR header to open the branch page.
3. Click the green **Code** button → **Download ZIP**.
4. Unzip the file on your computer.
5. Inside the ZIP, find the folder `custom_components/deebot_neo_2/`.
6. Copy that folder into your Home Assistant `config/custom_components/` directory, replacing the existing `deebot_neo_2` folder.
   - You can use the Home Assistant File Editor or Samba/SSH to transfer the files.
7. Continue to Step 2.

### Option B: HACS custom repository with a specific branch

> HACS currently only supports installing a custom repository from its default branch.
> To test a PR branch, use Option A (ZIP download) instead.

---

## Step 2 – Enable Debug Logging

Add the following to your `configuration.yaml` before restarting:

```yaml
logger:
  default: info
  logs:
    custom_components.deebot_neo_2: debug
```

---

## Step 3 – Restart Home Assistant

Restart Home Assistant fully (not just reload).

---

## Step 4 – Add or Reload the Integration

1. Go to **Settings → Devices & services**.
2. If "DEEBOT NEO 2" is already configured: click it → three-dot menu → **Reload**.
3. If not yet configured: click **+ Add integration** → search for "DEEBOT NEO 2" → log in.

---

## Step 5 – Confirm Discovery

After the integration loads:

- The DEEBOT NEO 2 device should appear under **Settings → Devices & services → DEEBOT NEO 2**.
- In debug logs, look for a line like:

  ```
  Matched device class=eyfj07 UILogicId=y30_ww_h_y30h5 to profile DEEBOT NEO 2.0 (experimental) (stable=False)
  ```

  ✅ If you see this line, the device was correctly identified.
  ❌ If you see `Device class eyfj07 not recognized` or similar, please post the relevant sanitized log lines in [issue #1](https://github.com/tysonjtv/deebot-neo-2-hacs/issues/1).

---

## Step 6 – Record Initial State

Note down:

- **Vacuum state** shown in the entity card (Idle, Docked, etc.)
- **Battery level** shown in the battery sensor

---

## Step 7 – Test Start Auto Clean

1. On the vacuum entity card, press **Start**.
2. Wait a few seconds.
3. Confirm the state changes to **Cleaning**.

---

## Step 8 – Test Return to Dock

1. While the vacuum is cleaning, press **Return to dock**.
2. Confirm the state changes to **Returning**.
3. Wait for the robot to dock.
4. Confirm the state changes to **Docked**.

---

## Step 9 – Test Suction Options

1. Open the vacuum entity details.
2. Change the **Suction** fan speed to each option in turn: `quiet mode`, `standard`, `strong`, `max`.
3. Confirm each setting applies without errors.

---

## Step 10 – Restart and Reconnect Test

1. Restart Home Assistant fully.
2. After restart, confirm:
   - The DEEBOT NEO 2 device is still shown.
   - The battery and state values are populated.
   - In logs, look for `Initialized 1 supported DEEBOT NEO 2 device(s)`.

---

## Step 11 – Report Results

Go to [issue #1](https://github.com/tysonjtv/deebot-neo-2-hacs/issues/1) and post:

1. Which steps passed ✅ and which failed ❌.
2. The relevant sanitized log lines (see below).
3. Your HA version and integration version.

### Which log lines to share

Only share log lines that contain these patterns:
- `class=`
- `UILogicId=`
- `profile=`
- `command requested`
- `command succeeded` or `command failed`
- `Initialized N supported`

### ⚠️ What NOT to share

Never share:
- Tokens or passwords
- Email addresses
- Full device IDs (`did=` values)
- Resource IDs
- Home IDs
- Network addresses

---

## Rollback

To restore the stable release:

1. Remove the `custom_components/deebot_neo_2/` folder.
2. Reinstall via HACS from the main branch.
3. Restart Home Assistant.
4. The integration will work as before using the stable `q287s6` code.
