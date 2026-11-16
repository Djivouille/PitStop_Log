# PitStop Log

**PitStop Log** est une intégration personnalisée pour Home Assistant qui sert de
carnet d'entretien numérique multi-véhicules (motos, voitures, camping-cars, etc.).

## Versionnement

## Versionnement

Les versions suivent le **versionnement sémantique** :

- **`MAJOR.MINOR.PATCH`** (ex. `0.1.0`) : versions de **production**, stables — le `0.x` indique que l'intégration n'a pas encore atteint l'ensemble des fonctionnalités prévues pour une `1.0.0` ;
- **`MAJOR.MINOR.PATCH-beta.N`** (ex. `0.2.0-beta.1`) : versions de **test** (pre-release), destinées à la validation des nouveautés avant leur publication en production.

**Cycle d'une version** : les nouvelles fonctionnalités sont développées et publiées en `-beta.N` ; après validation, la version stable `MAJOR.MINOR.PATCH` est publiée. La `1.0.0` sera publiée lorsque l'intégration atteindra son ensemble de fonctionnalités cible. Les releases bêta sont marquées « pre-release » sur GitHub : le Marketplace ne les propose qu'aux utilisateurs qui activent **« Afficher les versions bêta »** dans les paramètres du dépôt.

Une release GitHub du même nom que la version du `manifest.json` est publiée automatiquement par le workflow du dépôt à chaque changement de version ; les versions contenant `beta` ou `rc` sont automatiquement marquées pre-release.

## Fonctionnalités

- **Gestion multi-véhicules** via l'interface de Home Assistant (Config Flow) :
  type, marque (liste déroulante issue de `brands.json`, avec logo associé), modèle,
  année-modèle, date d'achat, immatriculation (carte grise), kilométrage actuel
  et photo du véhicule (téléversement depuis l'interface, stockée dans
  `/config/www/pitstop_log/photos/`, servie via `/local/pitstop_log/photos/...`).
- **Édition complète via l'interface** (Options Flow) : métadonnées du véhicule,
  plans d'entretien (ajout/modification/suppression) et historique des entretiens
  (modification/suppression) — sans passer par les services YAML.
- **Saisie des entretiens depuis la carte** : bouton « + Ajouter un entretien » (date, kilométrage, nature via liste déroulante issue de `maintenance_types.json`, coût, facture photo ou PDF stockée localement) ; historique complet modifiable et supprimable depuis la carte.
- **Entretiens à faire** : échéances basées sur un intervalle en kilomètres
  et/ou en mois, avec calcul automatique du reste à faire (km restants, jours
  restants) et statut d'alerte : `OK`, `Bientôt dû`, `En retard` (états traduits
  dans l'interface via `translation_key` + sélecteur de texte).
- **Entretiens réalisés** : historique daté avec kilométrage, description des
  actions, coût et photo de facture (stockée dans `/config/www/pitstop_log/invoices/`,
  accessible via `/local/pitstop_log/invoices/...`).
- **Persistance** : toutes les données sont sauvegardées via le `Store` de
  Home Assistant dans `.storage/pitstop_log`.
- **Interface bilingue** français / anglais.

## **Installation**

### **Via HACS (recommandé)**

Prérequis : [**HACS**](https://hacs.xyz/installation/prerequisites/) déjà installé.

1. Dans Home Assistant, ouvrez **HACS** dans le menu latéral.

2. Cliquez sur les **trois points** en haut à droite, puis **Dépôts personnalisés** (*Custom repositories*).

3. Collez l'URL du dépôt et choisissez la catégorie **Integration** :

   * URL : `https://github.com/Djivouille/PitStop_Log`

   * Catégorie : `Integration`

4. Cliquez sur **Ajouter**, puis fermez la fenêtre.

5. Recherchez **PitStop Log** dans HACS, ouvrez la fiche et cliquez sur **Télécharger** (*Download*).

6. **Redémarrez Home Assistant** (Paramètres > Système > Redémarrer).

7. Ajoutez l'intégration : **Paramètres > Appareils et services > Ajouter une intégration**, recherchez **PitStop Log** et suivez l'assistant (voir [**Configuration**](#configuration)).

## Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**.
2. Recherchez **PitStop Log** et suivez l'assistant pour créer un véhicule.
3. Répétez pour chaque véhicule du parc.
4. Pour gérer un véhicule : roulez sa carte → **Configurer** (Options Flow). Le menu permet de :
   - **Modifier le véhicule** : nom, type, marque, modèle, année-modèle, date d'achat, immatriculation, kilométrage ;
   - **Plans d'entretien** : ajouter, modifier ou supprimer les entretiens périodiques (intervalle km/mois, dernière réalisation) ;
   - **Historique des entretiens** : modifier ou supprimer chaque entretien réalisé (date, kilométrage, actions, coût, facture) ;
   - **Terminé** pour fermer.

## Capteurs créés par véhicule

| Capteur | Description |
|---|---|
| Kilométrage | Kilométrage actuel du véhicule (km). |
| Prochain entretien | Statut le plus urgent (`OK` / `Bientôt dû` / `En retard`, traduit dans l'interface), avec en attributs le détail des plans et l'historique complet (dates, km, actions, coûts, liens vers les factures). |
| Un capteur par plan d'entretien | Statut du plan (traduit dans l'interface) avec attributs `km_remaining`, `days_remaining`, `due_km`, `due_date`. |
| Photo du véhicule (entité image) | Affiche la photo téléversée, visible sur la page de l'appareil et dans les tableaux de bord. |
| Logo de marque (entité image) | Affiche le logo de la marque du véhicule, visible sur la page de l'appareil et dans les tableaux de bord. |

## Services

### `pitstop_log.update_odometer`

Met à jour le kilométrage actuel d'un véhicule.

```yaml
service: pitstop_log.update_odometer
data:
  vehicle_id: "yamaha_mt07"
  km: 15432
```

### `pitstop_log.add_maintenance_done`

Enregistre un entretien réalisé. Si `plan_id` est fourni, le plan d'entretien
associé est réinitialisé (nouveau point de départ des échéances).

```yaml
service: pitstop_log.add_maintenance_done
data:
  vehicle_id: "yamaha_mt07"
  date: "2025-05-01"
  km: 15432
  actions: "Vidange, remplacement du filtre à huile"
  cost: 89.5
  invoice_path: "/local/pitstop_log/invoices/vidange_2025.jpg"
  plan_id: "yamaha_mt07_vidange"
```

Vous pouvez aussi fournir directement une image encodée en base64 via
`invoice_base64` : elle sera sauvegardée automatiquement dans
`/config/www/pitstop_log/invoices/` et référencée par son URL locale.

### `pitstop_log.add_maintenance_plan`

Ajoute une règle d'entretien périodique (au moins un des deux intervalles requis).

```yaml
service: pitstop_log.add_maintenance_plan
data:
  vehicle_id: "yamaha_mt07"
  plan_name: "Vidange moteur"
  interval_km: 6000
  interval_months: 12
  last_km: 15000
  last_date: "2025-05-01"
```

## Structure du dépôt

```
hacs.json
README.md
custom_components/pitstop_log/
├── manifest.json
├── __init__.py
├── const.py
├── config_flow.py
├── coordinator.py
├── sensor.py
├── services.yaml
├── strings.json
└── translations/
    ├── fr.json
    └── en.json
```

## Carte Lovelace « PitStop Log »

L'intégration embarque une carte Lovelace personnalisée qui affiche toutes les
informations d'un véhicule : photo, logo de marque, kilométrage, immatriculation,
statut d'entretien, plans à faire (reste en km et en jours), derniers entretiens
réalisés (date, km, actions, coût), **mise à jour du kilométrage directement
depuis la carte** (champ de saisie + OK) et **graphique en courbe du kilométrage
dans le temps** (axe dates / km, survol des points pour le détail).

L'historique du kilométrage démarre à la date de mise en service (date d'achat)
au km 0 ; chaque mise à jour (service, carte ou interface) ajoute un point
(remplacé si plusieurs mises à jour le même jour).

**Installation (une seule fois) :**

1. Paramètres → Tableaux de bord → menu **⋮** → **Ressources** → **Ajouter** :
   - URL : `/local/pitstop_log/lovelace/pitstop-card.js`
   - Type : **Module JavaScript**
2. Rechargez la page (F5).

**Utilisation dans un tableau de bord** (Modifier → ajouter carte → « PitStop Log ») :
l'éditeur visuel propose un **menu déroulant listant les véhicules** de
l'intégration et un champ « Titre affiché » optionnel — aucun YAML n'est
nécessaire. Le véhicule est présélectionné automatiquement à l'ajout.
Le fichier JS est copié automatiquement dans `/config/www/pitstop_log/lovelace/`
au démarrage de Home Assistant.

## Marques et logos

La liste des marques proposées dans le sélecteur est définie dans
`custom_components/pitstop_log/brands.json` (fichier à part) : motos, voitures et
camping-cars les plus courants, chacun associé au chemin de son logo SVG stocké **localement** dans
`custom_components/pitstop_log/brands/` (39 logos embarqués, issus de Simple
Icons ; certaines marques retirées du projet n'ont pas de logo). Les logos
sont copiés automatiquement dans `/config/www/pitstop_log/brands/` au
démarrage et servis localement via `/local/pitstop_log/brands/...`.

Pour ajouter une marque : déposez son SVG dans `brands/` et éditez
`brands.json` :

```json
"Ma Marque": {"logo": "/local/pitstop_log/brands/mamarque.svg", "category": "moto", "label": "Ma Marque"}
```

Le logo de la marque et la photo du véhicule sont exposés en attributs du
capteur « Prochain entretien » (`brand_logo`, `photo`), utilisables dans les
tableaux de bord Lovelace.

## Stockage des données

- Données (véhicules, plans, historique) : `.storage/pitstop_log` (JSON, géré
  par `homeassistant.helpers.storage.Store`).
- Photos de factures : `/config/www/pitstop_log/invoices/` (créé
  automatiquement au démarrage), accessibles dans Lovelace via
  `/local/pitstop_log/invoices/...`.

## Licence

Fourni tel quel, sans garantie. Utilisation libre.

## Contribuer (traductions, marques, natures d'entretien)

L'intégration est conçue pour être enrichie par de simples Pull Requests, sans toucher au code :

| Sujet | Fichier à modifier | Comment |
|---|---|---|
| Traductions de l'intégration (assistant de config, options, services) | `custom_components/pitstop_log/translations/<langue>.json` | Dupliquez `fr.json`, traduisez les valeurs (gardez les clés). |
| Traductions de la carte Lovelace | `custom_components/pitstop_log/locales/<langue>.json` | Dupliquez `locales/fr.json` et traduisez les valeurs. La carte charge automatiquement la langue de Home Assistant. |
| Marques et logos | `custom_components/pitstop_log/brands.json` (+ logo SVG dans `brands/`) | Ajoutez la marque avec sa catégorie (`moto`, `car`, `camper`, `other`) et le chemin du logo. |
| Natures d'entretien | `custom_components/pitstop_log/maintenance_types.json` | Ajoutez la nature dans la liste `types`. |

Avant d'ouvrir la PR, vérifiez la cohérence des traductions :

```bash
python3 scripts/check_translations.py
```

Le script contrôle que toutes les langues contiennent les mêmes clés (intégration et carte) et qu'aucune valeur n'est vide.
