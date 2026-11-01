<p align="center">
  <img src="https://raw.githubusercontent.com/DerSpletti/ha-maxxicharge/main/docs/images/banner.png" alt="Maxxicharge – Maxxisun CCU V2 and V2+ in Home Assistant" width="100%">
</p>

<p align="center">
  <a href="https://hacs.xyz"><img alt="HACS: Custom" src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
  <a href="https://github.com/DerSpletti/ha-maxxicharge/releases"><img alt="Version" src="https://img.shields.io/github/v/release/DerSpletti/ha-maxxicharge"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <img alt="Home Assistant 2025.1+" src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-18bcf2.svg">
</p>

**Bring your Maxxisun storage into Home Assistant, without manual work and without clutter.** The integration guides you
through setup, tidies the ~70 values per CCU, protects you from silent failures when changing settings, and ships its own
dashboard card in the style of the Maxxisun app.

*Deutsche Version: [README.md](README.md)*

> **Version 0.9.0 (pre-release), privately maintained.** Developed and tested with two CCUs (firmware 2.43.21 and 2.43.53) on the built-in broker.
> Changing settings and running with an existing MQTT broker have seen little real-hardware testing so far. It is
> not an official release of the manufacturer (see [Trademarks and liability](#trademarks-and-liability)).

## Contents
[At a glance](#at-a-glance) · [Preview](#preview) · [How it works](#how-it-works) · [Setup](#setup-in-4-steps) ·
[Entities](#what-you-get) · [Dashboard card](#dashboard-card) · [Changing settings safely](#changing-settings-safely) ·
[FAQ](#faq) · [Limitations](#known-limitations) · [Contributing](#reporting-issues-and-contributing)

## At a glance
| | |
|---|---|
| 🧭 **Guided setup** | Welcome page, instructions for the CCU, search on the broker. New CCUs show up by themselves as “Discovered” later. |
| 📦 **Nothing extra to install** | No MQTT? The integration starts **a small broker of its own**. Already have one (e.g. Mosquitto)? It is used. |
| 🧹 **Tidy** | Main values, energy, settings and diagnostics with proper names, one device per CCU. Raw values are off by default. |
| ✅ **Safe writing** | Settings are sent, confirmed by the CCU, otherwise rejected with an **error in the UI**. No silent jumping back. |
| 🔒 **Write protection** | One switch blocks all changes on all CCUs. |
| 📊 **Total overview** | State of charge, house consumption, self-sufficiency, self-consumption, remaining runtime across all CCUs, plus efficiency and charge cycles per CCU. |
| 🏠 **Own card** | House with PV and storage, tiles and history, no extra cards needed. |
| 🔐 **All local** | No cloud, no telemetry, no extra packages. |

## Preview
<p align="center">
  <img src="https://raw.githubusercontent.com/DerSpletti/ha-maxxicharge/main/docs/images/card.png" alt="Dashboard card of the integration" width="46%">
  &nbsp;
  <img src="https://raw.githubusercontent.com/DerSpletti/ha-maxxicharge/main/docs/images/card-states.png" alt="Dashboard card in two states: discharging with grid import and charging from PV" width="50%">
</p>
<p align="center"><sub>The dashboard card, <b>preview with sample data</b>. Left: storage discharges, the house imports from the grid.
Right: PV charges the storage, surplus goes to the grid.</sub></p>

## How it works
<p align="center">
  <img src="https://raw.githubusercontent.com/DerSpletti/ha-maxxicharge/main/docs/images/architecture.png" alt="Architecture: CCUs, MQTT broker, Maxxicharge, devices and dashboard" width="100%">
</p>

The CCUs connect to a broker via MQTT and describe their values (discovery). Maxxicharge reads that description, builds
tidy entities, calculates totals and verifies every change to the settings. There are no hard-coded topic names: everything
comes from the CCU’s discovery.

## Requirements
- Home Assistant **2025.1** or newer
- Maxxisun **CCU V2 or V2+** with firmware **2.42.103** or newer for reading, **2.43** or newer to change settings
- CCU and Home Assistant on the same network

### Supported devices
| Model | Status |
|---|---|
| **Maxxicharge CCU V2+** | ✅ supported: reading from firmware 2.42.103, changing settings from 2.43 |
| **Maxxicharge CCU V2** | ✅ supported as soon as the CCU has the MQTT interface (firmware 2.42.103 or newer). A CCU with older firmware without MQTT cannot be added. |

Both models report a serial number like `CCU2-XXXX-XXXX-XXXX` and can run side by side on the same meter.

**Model detection:** The integration queries `http://<IP>/api/info` on each CCU (read-only, local network addresses only) and shows the
result as the device model and as the diagnostic sensor **Model**. The rule: if the CCU reports `CCU2_PLUS` it is a **CCU V2+**.
Any other answer (one tested CCU says `UNKNOWN`) is a regular **CCU V2**. Only if the CCU does not answer at all it says “Unknown”.
If the detection is ever wrong, set the model by hand under entry → Configure → Settings.

## Setup in 4 steps
<p align="center">
  <img src="https://raw.githubusercontent.com/DerSpletti/ha-maxxicharge/main/docs/images/setup-steps.png" alt="Setup in four steps" width="100%">
</p>

### 1. Install
[![Open repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DerSpletti&repository=ha-maxxicharge&category=integration)

Or HACS ⋮ → *Custom repositories* → `https://github.com/DerSpletti/ha-maxxicharge`, category *Integration*. Download
*Maxxicharge* and **restart** Home Assistant. Manual: copy `custom_components/maxxicharge` to `<config>/custom_components/`.

### 2. Add the integration
Settings → Devices & services → **Add integration → Maxxicharge**. The welcome page shows what you need: the IP of Home
Assistant, the port, user and password for MQTT.

If you **already have MQTT** (e.g. Mosquitto) the integration uses it. Otherwise choose the **built-in broker** and set port,
user and password (suggestion: port 1883, a random password without look-alike characters).

### 3. Connect the CCU
In the **Maxxisun app** under **Smart Home Integration**, for each CCU:

1. Switch **MQTT connection** on
2. **Broker address** and **port** as shown by the wizard
3. Switch **Login** on, enter **user name** and **password**
4. **Save**

> ⚠️ **Do not leave the password field empty**, otherwise the CCU keeps its old password.
> Alternatively use a browser: `http://<CCU-IP>/integrations/mqtt`. That page has **no login**, use it only in your home network.

### 4. Select the CCUs
The wizard lists the CCUs found. Pick them, done. You get one device **per CCU** and the device **“Maxxicharge Gesamt”**.

<details>
<summary><b>Adding CCUs later, looking up connection data, changing the password</b></summary>

- **New CCU:** give it the same connection data in the app. It appears by itself under *Devices & services* as “Discovered”
  and can be set up with one click. Or add the integration again.
- **Look up connection data:** entry → **Configure → Show connection details for the CCU**. Broker, port, user and password
  are listed exactly as they must be entered in the app.
- **Change password** (built-in broker only): entry → Configure → *Change password*. It applies to all CCUs; afterwards enter
  it in the app for every CCU.
- **With an existing MQTT broker** the integration does not know the password. Your broker’s user and password apply
  (Settings → People → Users or the broker configuration).
- **Old autodiscovery entities** of the CCU can be **disabled** under Configure → Settings (nothing is deleted).
</details>

## What you get
| Area | Examples |
|---|---|
| **Main values** | State of charge, usable energy, battery charge/discharge power, CCU AC power, grid power, PV power, operating mode, battery full/empty |
| **Energy** | Output/input today and total, grid import/export, PV yield, battery charged/discharged, grid and battery balance |
| **Configuration** | Max. output power, max. charge power, min/max charge level, output on meter loss, charging strategy, UPS mode |
| **Calculated per CCU** | Round-trip efficiency, charge cycles, remaining runtime, time to full |
| **Total overview** | State of charge total, house consumption, self-sufficiency, self-consumption, PV total, grid power, **write protection** |
| **Diagnostics** | Connected, last update, firmware, IP address, temperature, uptime, fault flags, writing possible |

Sign convention of the CCU: positive = battery discharging / CCU feeding the house / grid import, negative = the opposite.
The energy counters are **estimates** stored by the CCU roughly every 5 minutes, not for billing. House consumption,
self-sufficiency and self-consumption are **approximations** from meter and CCU values. The total overview assumes that all
CCUs share the same meter.

## Dashboard card
The card **Maxxicharge** appears in the card picker after setup (reload the browser cache once if it is missing). It works for the
**total overview** and for **each single CCU** and is **modular**: in the card editor you choose the **device**, the **modules**
(house graphic, tiles, “household” history, statistics) and the **tiles** (PV, consumption, grid, CCU output, storage). Via YAML:
```yaml
type: custom:maxxicharge-card
device: <device id>                       # start device; empty = Maxxicharge Gesamt (picked in the editor)
switcher: true                            # switch between total / CCUs inside the card (default: on if no device is fixed)
modules: [scene, tiles, chart, stats]     # house graphic, tiles, history, statistics
tiles: [pv, house, grid, ccu, store]      # which tiles
title: Maxxicharge                        # empty = device name
hours: 3                                  # history range in hours
pv_max: 4000                              # bar scales in W (optional)
house_max: 3000
ccu_max: 2300
```
With the **switcher** on, the card shows tabs for “Maxxicharge Gesamt” and every CCU at the top. A click switches the view right inside the
card (the choice is remembered in the browser). If you fix a device, the switcher is off by default; `switcher: true` turns it on anyway.
Without the house graphic the tiles form a grid, e.g. for a compact card with only storage and CCU output. You can override
single entities: `entities: { pv: sensor.my_pv, grid: sensor.my_grid }` (keys: `pv`, `charge`, `discharge`, `grid`, `house`,
`soc`, `feed`, `draw`, `runtime`, `ttf`, `autarky`, `usable`, `pvtoday`, `temp`, `fault`, `lock`, `online`). A single CCU has
no self-sufficiency value. Consumption is only calculated if that CCU has a meter value.

### Maxxicharge page and “Device info”
Home Assistant does not let integrations embed cards directly in the device page. So there is a page of its own,
**Maxxicharge** (sidebar, address `/maxxicharge`), with tabs for the total overview, each CCU and “All”. On the device page of
each CCU and of the total overview the **Visit** button in the **Device info** box leads straight to the matching card. The CCU’s web
interface is reachable from there via the “CCU web interface” button.

## Changing settings safely
The integration sends the value and waits up to 10 seconds for the CCU to report it back. Then it is **stored**, which does not
mean the power changes immediately. If the CCU rejects it or does not answer, you get an **error message** and the entity shows
the real value again. There is no fixed target power (“discharge 300 W”): the CCU always regulates on its own meter. The
**write protection switch** on the “Maxxicharge Gesamt” device blocks all changes at once.

## FAQ
<details>
<summary><b>Do I need Mosquitto or another MQTT broker?</b></summary>
No. Without MQTT in Home Assistant the wizard offers the built-in broker. It runs as long as at least one CCU is set up. With
Mosquitto it works the same way, the integration detects it by itself.
</details>

<details>
<summary><b>The wizard does not find my CCU</b></summary>
The dialog lists the CCUs <b>connected</b> to the broker and those <b>rejected</b>, with the reason. If it says “password”, enter
user and password in the app again (not empty) and choose “Search again”. If the CCU is listed as connected but not offered, it
has not announced its entities yet. Wait a moment and search again.
</details>

<details>
<summary><b>A CCU is listed under “Repairs” as rejected</b></summary>
The credentials at the CCU do not match. Look them up under entry → Configure → Show connection details and enter them in the
app again. The notice disappears as soon as the CCU can log in.
</details>

<details>
<summary><b>Values are “unavailable”</b></summary>
The CCU has not reported for two minutes. Check the CCU’s Wi-Fi and the broker.
</details>

<details>
<summary><b>Writing says “not applied”</b></summary>
Firmware 2.43 or newer? Does the CCU report the setting back at all (value not “unknown”)? Is write protection off? See the log.
</details>

<details>
<summary><b>How do I get logs and diagnostics?</b></summary>

```yaml
logger:
  default: warning
  logs:
    custom_components.maxxicharge: debug
```
The **diagnostics download** (entry → ⋮ → Download diagnostics) contains topics and values. IP, CCU ID and passwords are redacted.
</details>

## Known limitations
- **Writing needs firmware 2.43+.** With older firmware the integration refuses with an error, logs a warning and creates a
  notice under *Repairs*.
- **Older firmware may not report settings back** (e.g. 2.43.21 on one tested CCU). The values stay “unknown” and a write
  cannot be confirmed. A firmware update via the Maxxisun app helps.
- A CCU without an MQTT interface (firmware before 2.42.103) is not supported. See [Supported devices](#supported-devices).
- The **built-in broker** is deliberately small: login, publish/subscribe, retained, last will, MQTT 3.1.1 and 5, **no
  encryption**, at most 20 clients. If another service uses port 1883, choose another port.
- The CCU’s MQTT connection is **unencrypted**. Use it only in a trusted home network.
- Old autodiscovery entity IDs are not migrated. Automations and dashboards must be switched to the new entities
  (`sensor.ccu_xxxx_…`).

## Privacy and security
- Everything runs **locally**. No cloud connection, no telemetry.
- The built-in broker password is stored in the integration’s configuration, in no entity and not in the diagnostics download.
- The built-in broker listens on all network interfaces of Home Assistant and requires login. Do not expose it to the internet.

## Updates and removal
HACS announces updates (Settings → Updates). Home Assistant must be restarted after installing, as with every integration. To
remove, delete the entry and uninstall in HACS. Changes are listed in the [changelog](CHANGELOG.md).

## Reporting issues and contributing
Issues and ideas are welcome as [GitHub issues](https://github.com/DerSpletti/ha-maxxicharge/issues), with Home Assistant version,
CCU firmware, diagnostics download and a debug log excerpt (remove passwords).

For developers: the entity catalog is in `custom_components/maxxicharge/const.py`; translations are generated from it with
`python3 scripts/generate_translations.py`. The diagrams in this README come from `scripts/make_docs_images.py` (Pillow). The tests
under `tests/` run without Home Assistant (`paho-mqtt` for the broker tests).

## Trademarks and liability
This is a privately maintained project and not an official release of Maxxihandel GmbH. *Maxxisun* and *Maxxicharge* are trademarks of the
manufacturer. The icon and logo in `custom_components/maxxicharge/brand/` and in the banner are used **with the manufacturer’s permission** and
identify the related hardware (see [NOTICE.md](NOTICE.md)). Use at your own risk; changing settings on the storage is your own responsibility.
License: [MIT](LICENSE) (applies to the code, not to the trademarks).
