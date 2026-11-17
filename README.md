# 🏍️ PitStop Log

**[🇬🇧 English](#english)** | **[🇫🇷 Français](#français)**

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

<a id="français"></a>

# 🏍️ PitStop Log (Français)

**PitStop Log** est une intégration personnalisée pour Home Assistant qui sert de
**carnet d'entretien numérique multi-véhicules** 🚗 (motos, voitures, camping-cars…).

> 💡 *Philosophie : ajoutez un véhicule à votre garage, et gérez accessoirement ses entretiens.*

## 📑 Sommaire

- [✨ Fonctionnalités](#-fonctionnalités)
- [📦 Installation](#-installation-1)
- [⚙️ Configuration](#️-configuration-1)
- [🃏 Carte Lovelace](#-carte-lovelace)
- [📊 Capteurs](#-capteurs)
- [🛠️ Services](#️-services-1)
- [🏷️ Marques et logos](#️-marques-et-logos)
- [💾 Stockage des données](#-stockage-des-données)
- [🗂️ Structure du dépôt](#️-structure-du-dépôt)
- [🤝 Contribuer](#-contribuer)
- [📜 Versionnement](#-versionnement)
- [📄 Licence](#-licence)

## ✨ Fonctionnalités

- 🚙 **Gestion multi-véhicules** via l'interface de Home Assistant : type,
  marque (liste déroulante avec logo), modèle, année-modèle, date d'achat,
  immatriculation, kilométrage et photo du véhicule (téléversée depuis
  l'interface, stockée localement).
- 📝 **Saisie des entretiens depuis la carte** : bouton « + Ajouter un entretien »
  — date, kilométrage, **natures multiples** (cases à cocher : vidange, filtres,
  pneus…), coût et **facture (photo ou PDF)** stockés localement.
- 🔄 **Historique complet modifiable** : chaque entretien réalisé peut être
  modifié ou supprimé depuis la carte ; les relevés kilométriques issus d'un
  entretien sont identifiés et protégés.
- 📅 **Entretiens à faire** : échéances par intervalle km et/ou mois, calcul
  automatique du reste à faire et statut d'alerte — `OK` 🟢, `Bientôt dû` 🟡,
  `En retard` 🔴. Un entretien réalisé **réinitialise automatiquement** les plans
  correspondants.
- 🛠️ **Édition complète via l'interface** (Options Flow) : métadonnées du
  véhicule, plans d'entretien et historique — sans YAML.
- 📊 **Kilométrage historisé** : chaque relevé (manuel ou issu d'un entretien)
  alimente l'historique ; clic sur la cellule → graphique natif Home Assistant.
- 🌍 **Interface bilingue** 🇫🇷/🇬🇧 — intégration **et** carte Lovelace, extensible par traduction.

## 📦 Installation

> Nécessite Home Assistant **2026.11** ou plus récent (Marketplace intégré).

1. **Paramètres** → **Marketplace** → menu **⋮** → **Dépôts personnalisés**.
2. Ajoutez le dépôt :
   - URL : `https://github.com/Djivouille/PitStop_Log`
   - Catégorie : **Integration**
3. Ouvrez la fiche **PitStop Log** → **Télécharger**.
4. **Redémarrez Home Assistant**.
5. **Paramètres** → **Appareils et services** → **Ajouter une intégration** →
   recherchez **PitStop Log** et suivez l'assistant (voir [⚙️ Configuration](#️-configuration-1)).

> 🧪 Pour recevoir les versions bêta : fiche du dépôt → **⋮** → activez
> **« Inclure les pre-releases »**.

## ⚙️ Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **PitStop Log**.
2. Suivez l'assistant en deux étapes : *type/marque/modèle*, puis le reste
   (nom, année, achat, immatriculation, kilométrage, photo).
3. ➕ Répétez pour chaque véhicule du garage.
4. Pour gérer un véhicule : sa fiche → **Configurer** :
   - ✏️ **Modifier le véhicule** : nom, type, marque, modèle, année, achat, immatriculation, km ;
   - 📅 **Plans d'entretien** : ajout / modification / suppression ;
   - 🗂️ **Historique des entretiens** : modification / suppression.

## 🃏 Carte Lovelace

L'intégration embarque une carte personnalisée qui affiche tout le véhicule :
logo de marque (avec icône par défaut si manquant), photo, kilométrage,
statut d'entretien, plans à faire, derniers entretiens — et permet de **tout
modifier directement depuis la carte** :

- ⚙️ roue crantée de la cellule Kilométrage → relevés (ajout, ✎ modification, ✖ suppression) ;
- ⚙️ roue crantée de l'en-tête → marque, modèle, année, photo, immatriculation, date d'achat ;
- ➕ bouton « Ajouter un entretien » → formulaire complet (natures multiples, facture) ;
- ⚙️ roue crantée de la section historique → gestion complète des entretiens ;
- 🖱️ clic sur la cellule Kilométrage → graphique natif Home Assistant.

**Installation (une seule fois)** :

1. Paramètres → Tableaux de bord → menu **⋮** → **Ressources** → **Ajouter** :
   - URL : `/local/pitstop_log/lovelace/pitstop-card.js`
   - Type : **Module JavaScript**
2. Rechargez la page (F5).

**Utilisation** : Modifier → ajouter carte → **« PitStop Log »**. L'éditeur
visuel propose un menu déroulant listant les véhicules (noms des appareils) et
un titre optionnel — **aucun YAML**. Le fichier JS est copié automatiquement
dans `/config/www/pitstop_log/lovelace/` au démarrage.

## 📊 Capteurs

| Capteur | Description |
|---|---|
| 📏 Kilométrage | Kilométrage actuel (km), avec historique des relevés en attributs. |
| 🔧 Prochain entretien | Statut le plus urgent (`OK` / `Bientôt dû` / `En retard`), avec plans et historique complet en attributs. |
| 📅 Un capteur par plan | Statut du plan avec `km_remaining`, `days_remaining`, `due_km`, `due_date`. |
| 🖼️ Photo du véhicule (image) | Photo téléversée, visible sur la page de l'appareil et les tableaux de bord. |
| 🏷️ Logo de marque (image) | Logo de la marque, visible sur la page de l'appareil et les tableaux de bord. |

## 🛠️ Services

| Service | Rôle |
|---|---|
| `pitstop_log.update_odometer` | Met à jour le kilométrage (relevé daté optionnel). |
| `pitstop_log.delete_odometer_point` | Supprime un relevé de l'historique. |
| `pitstop_log.update_registration` | Met à jour l'immatriculation. |
| `pitstop_log.update_purchase_date` | Met à jour la date d'achat. |
| `pitstop_log.update_brand_model` | Marque, modèle, année, photo, immatriculation, achat. |
| `pitstop_log.add_maintenance_done` | Enregistre un entretien (natures multiples, facture, réinitialisation des plans). |
| `pitstop_log.update_maintenance` | Modifie un entretien réalisé. |
| `pitstop_log.delete_maintenance` | Supprime un entretien réalisé. |
| `pitstop_log.add_maintenance_plan` | Ajoute un plan d'entretien périodique. |

Exemple — enregistrer un entretien avec facture :

```yaml
service: pitstop_log.add_maintenance_done
data:
  vehicle_id: "yamaha_mt07"
  date: "2025-05-01"
  km: 15432
  actions: ["Vidange", "Filtre à huile"]
  cost: 89.5
```

> 💡 Une facture peut être fournie en base64 via `invoice_base64` (photo ou PDF) :
> elle est sauvegardée dans `/config/www/pitstop_log/invoices/`.

## 🏷️ Marques et logos

La liste des marques est définie dans `brands.json` (fichier séparé) :
motos, voitures et camping-cars courants, chacun associé à son logo SVG stocké
**localement** (aucun CDN externe). Les logos sont copiés automatiquement vers
`/config/www/pitstop_log/brands/` au démarrage.

> 🖼️ **[Galerie des logos de marques](docs/logos.md)** — visualisez toutes les
> marques et celles en attente de logo (page générée automatiquement depuis `brands.json`).

Pour ajouter une marque : déposez son SVG dans `brands/` et éditez `brands.json` :

```json
"Ma Marque": {"logo": "/local/pitstop_log/brands/mamarque.svg", "category": "moto", "label": "Ma Marque"}
```

## 💾 Stockage des données

- 🗄️ Données (véhicules, plans, historique) : `.storage/pitstop_log` (JSON,
  géré par le `Store` de Home Assistant).
- 🧾 Factures : `/config/www/pitstop_log/invoices/`
- 📷 Photos des véhicules : `/config/www/pitstop_log/photos/`

## 🗂️ Structure du dépôt

```
custom_components/pitstop_log/
├── manifest.json
├── __init__.py, const.py, config_flow.py, coordinator.py, sensor.py, image.py
├── services.yaml, strings.json, icons.json
├── brands.json             ← marques + logos
├── maintenance_types.json ← natures d'entretien
├── brands/                 ← logos SVG
├── locales/                ← traductions de la carte (fr, en)
├── translations/           ← traductions de l'intégration (fr, en)
└── lovelace/pitstop-card.js
```

## 🤝 Contribuer

La plupart des ajouts se font **par simple Pull Request, sans toucher au code** :
traductions 🌍, marques + logos 🏷️, natures d'entretien 🔧.
Voir **[CONTRIBUTING.md](CONTRIBUTING.md)** pour la marche à suivre et les
scripts de vérification.

> ✅ La CI contrôle chaque PR : syntaxe Python/JS, validité JSON, cohérence des
> traductions, marques/logos, format de version, page des logos à jour.
> Une PR n'est fusionnée que si tous les jobs sont verts.

## 📜 Versionnement

Les versions suivent le **versionnement sémantique** :

- 🏷️ **`MAJOR.MINOR.PATCH`** (ex. `0.1.0`) : versions de **production** ;
- 🧪 **`MAJOR.MINOR.PATCH-beta.NN`** : versions de **test** (pre-release),
  numéros de bêta sur 2 chiffres.

**Cycle** : les nouveautés sont publiées en `-beta.NN` ; après validation, la
version stable est publiée. La `1.0.0` arrivera lorsque l'ensemble des
fonctionnalités cibles sera atteint. Les releases GitHub sont créées
automatiquement par le workflow du dépôt à chaque changement de version.

## 📄 Licence

Fourni tel quel, sans garantie. Utilisation libre.

---

☕ Vous aimez PitStop Log ? [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/C8U82AST4R)
