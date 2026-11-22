# 🏍️ PitStop Log

<a href="README.md"><img src="https://flagcdn.com/w40/gb.png" width="32" alt="English"></a> <a href="#français"><img src="https://flagcdn.com/w40/fr.png" width="32" alt="Français"></a>

[![GitHub release](https://img.shields.io/github/v/release/Djivouille/PitStop_Log)](https://github.com/Djivouille/PitStop_Log/releases)
[![Pre-release](https://img.shields.io/github/v/release/Djivouille/PitStop_Log/include_prereleases?label=pre-release&color=orange)](https://github.com/Djivouille/PitStop_Log/releases)
[![Licence](https://img.shields.io/badge/licence-libre%20d'utilisation-green)](#licence)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.11%2B-41bdf5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![Étoiles](https://img.shields.io/github/stars/Djivouille/PitStop_Log?style=social)](https://github.com/Djivouille/PitStop_Log/stargazers)

---

<a id="français"></a>

# 🏍️ PitStop Log (Français)

**PitStop Log** est une intégration personnalisée pour Home Assistant qui sert de
**carnet d'entretien numérique multi-véhicules** 🚗 (motos, voitures, camping-cars…).

> 💡 *Philosophie : ajoutez un véhicule à votre garage, et gérez accessoirement ses entretiens.*

## 📑 Sommaire

- [✨ Fonctionnalités](#fonctionnalites)
- [📦 Installation](#installation)
- [⚙️ Configuration](#configuration)
- [🃏 Carte Lovelace](#carte-lovelace)
- [📊 Capteurs](#capteurs)
- [🛠️ Services](#services)
- [🏷️ Marques et logos](#marques-et-logos)
- [🧰 Gabarits de natures](#gabarits-de-plans)
- [🤝 Contribuer](#contribuer)
- [💾 Stockage des données](#stockage-des-donnees)
- [🗂️ Structure du dépôt](#structure-du-depot)
- [📜 Versionnement](#versionnement)
- [📄 Licence](#licence)

<a id="fonctionnalites"></a>

## ✨ Fonctionnalités

- 🚙 **Gestion multi-véhicules** via l'interface de Home Assistant : type,
  marque (liste déroulante avec logo), modèle, année-modèle, date d'achat,
  immatriculation, kilométrage et photo du véhicule (téléversée depuis
  l'interface, stockée localement).
- 📝 **Saisie des entrées depuis la carte** : bouton « + Ajouter une entrée au carnet »
  — date, kilométrage, **natures multiples** (cases à cocher : vidange, filtres,
  pneus…), coût et **facture (photo ou PDF)** stockés localement.
- 🔄 **Carnet d'entretien modifiable** : chaque entrée du carnet peut être
  modifiée ou supprimée depuis la carte ; les relevés kilométriques issus d'un
  entretien sont identifiés et protégés.
- 📅 **Entretiens à faire** : échéances par intervalle km et/ou mois, calcul
  automatique du reste à faire et statut d'alerte à 4 niveaux — `Pas urgent` 🟢, `Urgent` 🟡, `Très urgent` 🟠, `En retard` 🔴,
  `En retard` 🔴. Un entretien réalisé **réinitialise automatiquement** les natures
  correspondants.
- 🛠️ **Édition complète via l'interface** (Options Flow) : métadonnées du
  véhicule, natures d'entretien et carnet d'entretien — sans YAML.
- 📊 **Kilométrage historisé** : chaque relevé (manuel ou issu d'un entretien)
  alimente l'historique ; clic sur la cellule → graphique natif Home Assistant.
- 🌍 **Interface bilingue** 🇫🇷/🇬🇧 — intégration **et** carte Lovelace, extensible par traduction.

<a id="installation"></a>

## 📦 Installation

> Nécessite Home Assistant **2026.11** ou plus récent (Marketplace intégré).

1. **Paramètres** → **Marketplace** → menu **⋮** → **Dépôts personnalisés**.
2. Ajoutez le dépôt :
   - URL : `https://github.com/Djivouille/PitStop_Log`
   - Catégorie : **Integration**
3. Ouvrez la fiche **PitStop Log** → **Télécharger**.
4. **Redémarrez Home Assistant**.
5. **Paramètres** → **Appareils et services** → **Ajouter une intégration** →
   recherchez **PitStop Log** et suivez l'assistant (voir [⚙️ Configuration](#configuration)).

> 🧪 Pour recevoir les versions bêta : fiche du dépôt → **⋮** → activez
> **« Inclure les pre-releases »**.

<a id="configuration"></a>

## ⚙️ Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **PitStop Log**.
2. Suivez l'assistant : *type/marque/modèle*, puis le reste
   (nom, année, achat, immatriculation, kilométrage, photo) puis la
   **définition des natures d'entretien** (contenu affiché et personnalisable à l'écran).
3. ➕ Répétez pour chaque véhicule du garage.
4. Pour gérer un véhicule : sa fiche → **Configurer** :
   - ✏️ **Modifier le véhicule** : nom, type, marque, modèle, année, achat, immatriculation, km ;
   - 📅 **Natures d'entretien** : ajout / modification / suppression ;
   - 🧰 **Gabarits de natures** : applique en un clic les natures types du type de
     véhicule (moto, voiture, camping-car), sans doublonner les natures existantes
     (contenu des gabarits consultable : `/local/pitstop_log/plan_templates.json`,
     galerie : [gabarits de natures](docs/plan_templates.md)) ;
   - 🔔 **Rappels** : seuils personnalisés Urgent / Très urgent (jours et km) — « En retard » reste toujours prioritaire ;
   - 🗂️ **Carnet d'entretien** : modification / suppression.

<a id="carte-lovelace"></a>

## 🃏 Carte Lovelace

L'intégration embarque une carte personnalisée qui affiche tout le véhicule :
logo de marque (avec icône par défaut si manquant), photo, kilométrage,
statut d'entretien, natures à faire, dernières entrées du carnet — et permet de **tout
modifier directement depuis la carte** :

- ⚙️ roue crantée de la cellule Kilométrage → relevés (ajout, ✎ modification, ✖ suppression) ;
- ⚙️ roue crantée de l'en-tête → marque, modèle, année, photo, immatriculation, date d'achat ;
- ➕ bouton « Ajouter une entrée au carnet » → formulaire complet (natures multiples, facture) ;
- ⚙️ roue crantée de la section carnet d'entretien → gestion complète du carnet ;
- ⚙️ roue crantée de la section natures à faire → ajout / ✎ modification / ✖ suppression des natures d'entretien ;
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

Les natures affichées sont traduites via `plan_names` (`locales/<langue>.json`) :
le nom stocké reste l'identifiant stable, seul l'affichage change.

<a id="capteurs"></a>

## 📊 Capteurs

| Capteur | Description |
|---|---|
| 📏 Kilométrage | Kilométrage actuel (km), avec historique des relevés en attributs. |
| 🔧 Prochain entretien | Statut le plus urgent (`Pas urgent` / `Urgent` / `Très urgent` / `En retard`), avec natures, gabarit du type (`plan_template`) et carnet d'entretien complet en attributs. |
| 📅 Un capteur par nature | Statut de la nature avec `km_remaining`, `days_remaining`, `due_km`, `due_date`. |
| 🖼️ Photo du véhicule (image) | Photo téléversée, visible sur la page de l'appareil et les tableaux de bord. |
| 🏷️ Logo de marque (image) | Logo de la marque, visible sur la page de l'appareil et les tableaux de bord. |

<a id="services"></a>

## 🛠️ Services

| Service | Rôle |
|---|---|
| `pitstop_log.update_odometer` | Met à jour le kilométrage (relevé daté optionnel). |
| `pitstop_log.delete_odometer_point` | Supprime un relevé de l'historique. |
| `pitstop_log.update_registration` | Met à jour l'immatriculation. |
| `pitstop_log.update_purchase_date` | Met à jour la date d'achat. |
| `pitstop_log.update_brand_model` | Marque, modèle, année, photo, immatriculation, achat. |
| `pitstop_log.add_maintenance_done` | Ajoute une entrée au carnet d'entretien (natures multiples, facture, réinitialisation des natures). |
| `pitstop_log.update_maintenance` | Modifie une entrée du carnet d'entretien. |
| `pitstop_log.delete_maintenance` | Supprime une entrée du carnet d'entretien. |
| `pitstop_log.add_maintenance_plan` | Ajoute une nature d'entretien périodique. |
| `pitstop_log.update_maintenance_plan` | Modifie une nature d'entretien (nom, intervalles km/mois). |
| `pitstop_log.delete_maintenance_plan` | Supprime une nature d'entretien (entrées du carnet conservées). |

Exemple — ajouter une entrée au carnet d'entretien avec facture :

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

<a id="marques-et-logos"></a>

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

<a id="gabarits-de-plans"></a>

## 🧰 Gabarits de natures

Les gabarits de natures d'entretien par type de véhicule (moto, voiture,
camping-car, autre) sont définis dans `plan_templates.json` (fichier séparé).
Ils s'appliquent en un clic à la création d'un véhicule ou depuis
**Configurer**, sans jamais écraser les natures existantes, qui restent
modifiables ensuite. La copie servie à l'exécution est consultable :
`/local/pitstop_log/plan_templates.json`.

> 🧰 **[Galerie des gabarits de natures](docs/plan_templates.md)** — visualisez tous
> les gabarits par type de véhicule : noms affichés (FR/EN), nom stocké, slug
> et intervalles (page générée automatiquement depuis `plan_templates.json`).

Pour ajouter ou modifier un gabarit : éditez `plan_templates.json` (les noms de
natures doivent rester dans `maintenance_types.json`), puis régénérez la galerie :

```bash
python3 scripts/generate_templates_page.py
```

<a id="contribuer"></a>

## 🤝 Contribuer

La plupart des ajouts se font **par simple Pull Request, sans toucher au code** :
traductions 🌍, marques + logos 🏷️, natures d'entretien 🔧.
Voir **[CONTRIBUTING.md](CONTRIBUTING.md)** pour la marche à suivre et les
scripts de vérification.

> ✅ La CI contrôle chaque PR : syntaxe Python/JS, validité JSON, cohérence des
> traductions, marques/logos, format de version, page des logos à jour.
> Une PR n'est fusionnée que si tous les jobs sont verts.

<a id="stockage-des-donnees"></a>

## 💾 Stockage des données

- 🗄️ Données (véhicules, natures, carnet d'entretien) : `.storage/pitstop_log` (JSON,
  géré par le `Store` de Home Assistant).
- 🧾 Factures : `/config/www/pitstop_log/invoices/`
- 📷 Photos des véhicules : `/config/www/pitstop_log/photos/`

<a id="structure-du-depot"></a>

## 🗂️ Structure du dépôt

```
custom_components/pitstop_log/
├── manifest.json
├── __init__.py, const.py, config_flow.py, coordinator.py, sensor.py, image.py
├── services.yaml, strings.json, icons.json
├── brands.json             ← marques + logos
├── maintenance_types.json ← natures d'entretien
├── plan_templates.json    ← gabarits de natures par type de véhicule
│                            (noms affichés traduits via `plan_names` dans translations/)
├── brands/                 ← logos SVG
├── locales/                ← traductions de la carte (fr, en)
├── translations/           ← traductions de l'intégration (fr, en)
└── lovelace/pitstop-card.js
```

<a id="versionnement"></a>

## 📜 Versionnement

Les versions suivent le **versionnement sémantique** :

- 🏷️ **`MAJOR.MINOR.PATCH`** (ex. `0.1.0`) : versions de **production** ;
- 🧪 **`MAJOR.MINOR.PATCH-beta.N`** : versions de **test** (pre-release).
  Semver strict : pas de zéro de tête (`beta.1`…`beta.9`, puis `beta.10`… —
  2 chiffres à partir de beta.10). HACS/HA rejettent un manifest avec `beta.01`.

**Cycle** : les nouveautés sont publiées en `-beta.N` ; après validation, la
version stable est publiée. La `1.0.0` arrivera lorsque l'ensemble des
fonctionnalités cibles sera atteint. Les releases GitHub sont créées
automatiquement par le workflow du dépôt à chaque changement de version.

<a id="licence"></a>

## 📄 Licence

Fourni tel quel, sans garantie. Utilisation libre.

---

☕ Vous aimez PitStop Log ? [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/C8U82AST4R)
