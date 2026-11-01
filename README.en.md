# Maxxicharge for Home Assistant

[![HACS: Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/DerSpletti/ha-maxxicharge)](https://github.com/DerSpletti/ha-maxxicharge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Unofficial integration for the **Maxxisun CCU2** (Maxxicharge V2+) via MQTT. A guided setup brings the CCUs into
Home Assistant and presents the ~70 values per CCU **tidily**: main values, energy, settings and diagnostics,
with proper names, under one device per CCU.

*Deutsche Version: [README.md](README.md)*

> **Status: beta.** Developed and tested with two CCUs (firmware 2.43.21 and 2.43.53) and the built-in broker.
> Writing settings and running with an existing MQTT broker have seen little real-hardware testing so far.
> Feedback is welcome.

## Features
- **Guided setup:** the wizard explains what you need and finds the CCUs on the broker. If Home Assistant has
  **no MQTT** yet, the integration ships a small broker of its own. Nothing else has to be installed.
- **Multiple CCUs:** each CCU is its own entry. New CCUs are offered automatically as “Discovered”.
- **Tidy:** main values visible, settings under “Configuration”, diagnostics collapsed, raw values (status bits,
  timestamps, ages, converter details) disabled by default.
- **Safe writing:** max. output and charge power, charge limits, output on meter loss, charging strategy and UPS
  mode. The integration sends the value, waits up to 10 seconds for the CCU to confirm and otherwise raises an
  **error in the UI**. The entity always shows the CCU’s real value.
- **Derived values:** battery full/empty, usable energy in kWh, feed-in to house, AC draw, grid and battery balance.
- **Total overview:** a device **“Maxxicharge Gesamt”** calculates across all CCUs: state of charge (capacity
  weighted), usable energy, charge/discharge power, PV, grid, **house consumption**, **self-sufficiency**,
  **self-consumption**, remaining runtime and time to full. Per CCU there are round-trip efficiency and charge cycles.
- **Write protection:** a switch on the “Maxxicharge Gesamt” device blocks all changes to the CCUs.
- **Own dashboard card** in the style of the Maxxisun app (house with PV and storage, tiles, “household” history),
  no extra cards needed. See [Dashboard card](#dashboard-card).
- **Diagnostics:** “Connected”, “Last update”, firmware, “Writing possible”, a *Repairs* notice for firmware
  below 2.43, diagnostics download with redacted credentials.
- **No dependencies:** no extra packages, no cloud account, everything local.

## Requirements
- Home Assistant 2025.1 or newer.
- Maxxisun CCU2 with firmware **2.42.103** or newer (reading). **Changing settings requires 2.43.**
- CCU and Home Assistant on the same network.

## Installation
**HACS (recommended):**
[![Open repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DerSpletti&repository=ha-maxxicharge&category=integration)
or HACS ⋮ → *Custom repositories* → `https://github.com/DerSpletti/ha-maxxicharge`, category *Integration*.
Download *Maxxicharge* and restart Home Assistant.

**Manual:** copy `custom_components/maxxicharge` to `<config>/custom_components/` and restart.

## Setup
Settings → Devices & services → **Add integration → Maxxicharge**. The wizard walks you through:

1. **Welcome:** shows what you need (IP of Home Assistant, port, user, password).
2. **MQTT:** if you already have MQTT (e.g. Mosquitto) it is used. Otherwise choose the **built-in broker** and set
   port, user and password.
3. **Connect the CCU:** in the Maxxisun app under **Smart Home Integration** (for each CCU): MQTT connection
   **on**, broker address and port as shown, login **on**, enter user and password, **Save**. Do not leave the
   password field empty, otherwise the old password stays. (Alternatively in a browser:
   `http://<CCU-IP>/integrations/mqtt`. That page has no login, use it only in your home network.)
4. **Search and select:** the CCUs found are listed, you pick them.

Optional under the entry’s **Configure → Settings**: **disable** the CCU’s old autodiscovery entities
(nothing is deleted, reversible at any time).

### Adding CCUs later
Give the new CCU the same connection data in the app. It appears automatically under *Devices & services* as
“Discovered”. Or add the integration again.

### Looking up the connection data later
Entry → **Configure → Show connection details for the CCU** shows broker, port, user and password exactly as
they must be entered in the app. You can also **change the password** there (applies to all CCUs, then re-enter it
in the app for each CCU). With an existing MQTT broker the integration does not know the password: your broker’s
user and password apply.

## Entities
| Area | Examples |
|---|---|
| Main values | State of charge, usable energy, battery charge/discharge power, CCU AC power, grid power, PV power, operating mode, battery full/empty |
| Energy | Output/input today and total, grid import/export, PV yield, battery charged/discharged, grid and battery balance |
| Configuration | Max. output power, max. charge power, min/max charge level, output on meter loss, charging strategy, UPS mode |
| Calculated per CCU | Round-trip efficiency, charge cycles, remaining runtime, time to full |
| Total overview | State of charge total, house consumption, self-sufficiency, self-consumption, PV total, grid power, write protection |
| Diagnostics | Connected, last update, firmware, IP address, temperature, uptime, fault flags, writing possible |

Sign convention of the CCU: positive = battery discharging / CCU feeding the house / grid import, negative = the
opposite. The energy counters are **estimates** stored by the CCU roughly every 5 minutes, not for billing.
House consumption, self-sufficiency and self-consumption are **approximations** from meter and CCU values. The total
overview assumes that all CCUs share the same meter.
An example dashboard is in [`examples/dashboard.yaml`](examples/dashboard.yaml).

## Dashboard card
After setup the card **Maxxicharge** appears in the card picker (reload the browser cache once if it is missing).
Via YAML:
```yaml
type: custom:maxxicharge-card
title: Maxxicharge        # optional
hours: 3                  # history range in hours
pv_max: 4000              # bar scales in W (optional)
house_max: 3000
ccu_max: 2300
```
The card finds the entities of the total overview automatically. You can override single ones:
`entities: { pv: sensor.my_pv, grid: sensor.my_grid }`. Keys: `pv`, `charge`, `discharge`, `grid`, `house`, `soc`,
`feed`, `draw`, `runtime`, `ttf`, `autarky`, `usable`, `pvtoday`, `temp`, `fault`, `lock`, `online`.

## Changing settings: what “confirmed” means
The integration sends the value and waits until the CCU reports it back. That means *stored*, not *power changed
immediately*. There is no fixed target power (“discharge 300 W”): the CCU always regulates on its own meter. If the
CCU rejects a value or does not answer, you get an error message and the entity shows the real value again.

## Known limitations
- **Writing needs firmware 2.43+.** With older firmware the integration refuses with an error, logs a warning
  and creates a notice under *Repairs*.
- **Older firmware may not report settings back** (e.g. 2.43.21 on one tested CCU). The values stay “unknown” and a
  write cannot be confirmed. A firmware update via the Maxxisun app helps.
- The older Maxxicharge V2 CCU without MQTT is not supported.
- The **built-in broker** is deliberately small: login, publish/subscribe, retained, last will, MQTT 3.1.1 and 5,
  **no encryption**, at most 20 clients, and it only runs while a CCU is set up. If another service uses port 1883
  choose another port or use that service.
- The CCU’s MQTT connection is **unencrypted**. Use it only in a trusted home network.
- Old autodiscovery entity IDs are not migrated. Automations and dashboards must be switched to the new entities
  (`sensor.ccu_xxxx_…`).

## Troubleshooting
| Problem | Fix |
|---|---|
| The wizard finds no CCU | The dialog lists the CCUs **connected** to the broker and those **rejected**, with the reason. For “password” re-enter user and password in the app (not empty). Then “Search again”. |
| A CCU shows as “rejected” under *Repairs* | Check the credentials in the app: entry → Configure → Show connection details. |
| Values “unavailable” | The CCU has not reported for two minutes. Check Wi-Fi and broker. |
| Writing says “not applied” | Firmware 2.43 or newer? Does the CCU report the setting at all (value not “unknown”)? See log. |

Logging in `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.maxxicharge: debug
```
The **diagnostics download** (entry → ⋮ → Download diagnostics) contains topics and values. IP, CCU ID and
passwords are redacted.

## Privacy and security
- Everything runs **locally**. No cloud connection, no telemetry.
- The built-in broker password is stored in the integration’s configuration, not in entities, and redacted in the
  diagnostics download.
- The built-in broker listens on all network interfaces of Home Assistant and requires login. Do not expose it to
  the internet.

## Updates and removal
HACS announces updates (Settings → Updates). Home Assistant must be restarted after installing, as with every
integration. To remove, delete the entry and uninstall in HACS. Changes are listed in the [changelog](CHANGELOG.md).

## Reporting issues
Please open a [GitHub issue](https://github.com/DerSpletti/ha-maxxicharge/issues) with Home Assistant version, CCU firmware,
diagnostics download and a debug log excerpt (remove passwords).

## Trademarks and liability
This is an **unofficial** project and not affiliated with Maxxihandel GmbH. *Maxxisun* and *Maxxicharge* are
trademarks of the manufacturer. The icon and logo in `custom_components/maxxicharge/brand/` come from maxxisun.de and
only identify the related hardware. They will be removed on the manufacturer’s request. Use at your own risk;
changing settings on the storage is your own responsibility. License: [MIT](LICENSE) (applies to the code, not to
the trademarks).
