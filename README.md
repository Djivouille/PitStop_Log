# 🏍️ PitStop Log

**[🇬🇧 English](#english)** | **[🇫🇷 Français](README.fr.md)**

---

<a id="english"></a>

# 🏍️ PitStop Log (English)

**PitStop Log** is a custom Home Assistant integration that acts as a
**digital multi-vehicle maintenance logbook** 🚗 (motorcycles, cars, campervans…).

> 💡 *Philosophy: add a vehicle to your garage, and incidentally manage its maintenance.*

## 📑 Table of contents

- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🃏 Lovelace card](#-lovelace-card)
- [📊 Sensors](#-sensors)
- [🛠️ Services](#️-services)
- [🏷️ Brands and logos](#️-brands-and-logos)
- [💾 Data storage](#-data-storage)
- [🗂️ Repository structure](#️-repository-structure)
- [🤝 Contributing](#-contributing)
- [📜 Versioning](#-versioning)
- [📄 License](#-license)

## ✨ Features

- 🚙 **Multi-vehicle management** from the Home Assistant UI: type,
  brand (dropdown with logo), model, model year, purchase date,
  registration, odometer and vehicle photo (uploaded from the UI,
  stored locally).
- 📝 **Maintenance entry from the card**: “+ Add maintenance” button —
  date, odometer, **multiple natures** (checkboxes: oil change, filters,
  tires…), cost and **invoice (photo or PDF)** stored locally.
- 🔄 **Fully editable history**: every completed maintenance can be
  edited or deleted from the card; odometer readings created by a
  maintenance entry are identified and protected.
- 📅 **Upcoming maintenance**: due by km and/or months interval, automatic
  remaining calculation and alert status — `OK` 🟢, `Due soon` 🟡,
  `Overdue` 🔴. Recording a maintenance **automatically resets** the
  matching plans.
- 🛠️ **Full editing from the UI** (Options Flow): vehicle metadata,
  maintenance plans and history — no YAML.
- 📊 **Odometer history**: every reading (manual or from a maintenance)
  feeds the history; click the cell → native Home Assistant chart.
- 🌍 **Bilingual UI** 🇫🇷/🇬🇧 — integration **and** Lovelace card, extensible by translation.

## 📦 Installation

> Requires Home Assistant **2026.11** or newer (built-in Marketplace).

1. **Settings** → **Marketplace** → **⋮** menu → **Custom repositories**.
2. Add the repository:
   - URL: `https://github.com/Djivouille/PitStop_Log`
   - Category: **Integration**
3. Open the **PitStop Log** page → **Download**.
4. **Restart Home Assistant**.
5. **Settings** → **Devices & services** → **Add integration** →
   search for **PitStop Log** and follow the wizard (see [⚙️ Configuration](#️-configuration)).

> 🧪 To receive beta versions: repository page → **⋮** → enable
> **“Include pre-releases”**.

## ⚙️ Configuration

1. **Settings** → **Devices & services** → **Add integration** → **PitStop Log**.
2. Follow the two-step wizard: *type/brand/model*, then the rest
   (name, year, purchase, registration, odometer, photo).
3. ➕ Repeat for each vehicle in your garage.
4. To manage a vehicle: its page → **Configure**:
   - ✏️ **Edit vehicle**: name, type, brand, model, year, purchase, registration, odometer;
   - 📅 **Maintenance plans**: add / edit / delete;
   - 🗂️ **Maintenance history**: edit / delete.

## 🃏 Lovelace card

The integration ships a custom card showing the whole vehicle: brand
logo (with a default icon when missing), photo, odometer, maintenance
status, upcoming plans, recent maintenance — and lets you **edit
everything directly from the card**:

- ⚙️ gear icon on the Odometer cell → readings (add, ✎ edit, ✖ delete);
- ⚙️ gear icon in the header → brand, model, year, photo, registration, purchase date;
- ➕ “Add maintenance” button → full form (multiple natures, invoice);
- ⚙️ gear icon on the history section → full maintenance management;
- 🖱️ click the Odometer cell → native Home Assistant chart.

**Setup (once)**:

1. Settings → Dashboards → **⋮** menu → **Resources** → **Add**:
   - URL: `/local/pitstop_log/lovelace/pitstop-card.js`
   - Type: **JavaScript module**
2. Reload the page (F5).

**Usage**: Edit → add card → **“PitStop Log”**. The visual editor offers a
dropdown listing your vehicles (device names) and an optional title —
**no YAML**. The JS file is copied automatically to
`/config/www/pitstop_log/lovelace/` at startup.

## 📊 Sensors

| Sensor | Description |
|---|---|
| 📏 Odometer | Current odometer (km), with reading history in attributes. |
| 🔧 Next maintenance | Most urgent status (`OK` / `Due soon` / `Overdue`), with plans and full history in attributes. |
| 📅 One per plan | Plan status with `km_remaining`, `days_remaining`, `due_km`, `due_date`. |
| 🖼️ Vehicle photo (image) | Uploaded photo, visible on the device page and dashboards. |
| 🏷️ Brand logo (image) | Brand logo, visible on the device page and dashboards. |

## 🛠️ Services

| Service | Purpose |
|---|---|
| `pitstop_log.update_odometer` | Update the odometer (optional dated reading). |
| `pitstop_log.delete_odometer_point` | Delete a reading from the history. |
| `pitstop_log.update_registration` | Update the registration. |
| `pitstop_log.update_purchase_date` | Update the purchase date. |
| `pitstop_log.update_brand_model` | Brand, model, year, photo, registration, purchase. |
| `pitstop_log.add_maintenance_done` | Record a maintenance (multiple natures, invoice, plan reset). |
| `pitstop_log.update_maintenance` | Edit a completed maintenance. |
| `pitstop_log.delete_maintenance` | Delete a completed maintenance. |
| `pitstop_log.add_maintenance_plan` | Add a periodic maintenance plan. |

Example — record a maintenance with an invoice:

```yaml
service: pitstop_log.add_maintenance_done
data:
  vehicle_id: "yamaha_mt07"
  date: "2025-05-01"
  km: 15432
  actions: ["Oil change", "Oil filter"]
  cost: 89.5
```

> 💡 An invoice can be provided as base64 via `invoice_base64` (photo or
> PDF): it is saved to `/config/www/pitstop_log/invoices/`.

## 🏷️ Brands and logos

The brand list is defined in `brands.json` (separate file): common
motorcycles, cars and campervans, each with its SVG logo stored
**locally** (no external CDN). Logos are copied automatically to
`/config/www/pitstop_log/brands/` at startup.

> 🖼️ **[Brand logo gallery](docs/logos.md)** — browse all brands and the
> ones still missing a logo (page generated automatically from `brands.json`).

To add a brand: drop its SVG in `brands/` and edit `brands.json`:

```json
"My Brand": {"logo": "/local/pitstop_log/brands/mybrand.svg", "category": "moto", "label": "My Brand"}
```

## 💾 Data storage

- 🗄️ Data (vehicles, plans, history): `.storage/pitstop_log` (JSON,
  managed by Home Assistant's `Store`).
- 🧾 Invoices: `/config/www/pitstop_log/invoices/`
- 📷 Vehicle photos: `/config/www/pitstop_log/photos/`

## 🗂️ Repository structure

```
custom_components/pitstop_log/
├── manifest.json
├── __init__.py, const.py, config_flow.py, coordinator.py, sensor.py, image.py
├── services.yaml, strings.json, icons.json
├── brands.json             ← brands + logos
├── maintenance_types.json  ← maintenance natures
├── brands/                 ← SVG logos
├── locales/                ← card translations (fr, en)
├── translations/           ← integration translations (fr, en)
└── lovelace/pitstop-card.js
```

## 🤝 Contributing

Most additions are made **by simple Pull Request, without touching code**:
translations 🌍, brands + logos 🏷️, maintenance natures 🔧.
See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the process and the
verification scripts.

> ✅ CI checks every PR: Python/JS syntax, JSON validity, translation
> consistency, brands/logos, version format, logos page up to date.
> A PR is only merged when all jobs are green.

## 📜 Versioning

Versions follow **semantic versioning**:

- 🏷️ **`MAJOR.MINOR.PATCH`** (e.g. `0.1.0`): **production** releases;
- 🧪 **`MAJOR.MINOR.PATCH-beta.NN`**: **test** releases (pre-releases),
  beta numbers on two digits.

**Cycle**: new features are released as `-beta.NN`; after validation, the
stable version is published. `1.0.0` will come when the target feature set
is reached. GitHub releases are created automatically by the repository
workflow on every version change.

## 📄 License

Provided as-is, without warranty. Free to use.

---

☕ Do you like PitStop Log? [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/C8U82AST4R)

---
