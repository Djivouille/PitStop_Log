# PitStop Log

**PitStop Log** est une intégration personnalisée pour Home Assistant qui sert de
carnet d'entretien numérique multi-véhicules (motos, voitures, camping-cars, etc.).

## Fonctionnalités

- **Gestion multi-véhicules** via l'interface de Home Assistant (Config Flow) :
  type, marque, modèle, année-modèle, date d'achat, immatriculation (carte grise)
  et kilométrage actuel. Modification possible via l'Options Flow.
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

## Installation via HACS

1. Ouvrez **HACS** → **Intégrations**.
2. Cliquez sur les trois points en haut à droite → **Dépôts personnalisés**.
3. Ajoutez ce dépôt avec la catégorie **Intégration**.
4. Recherchez **PitStop Log** et installez-le.
5. Redémarrez Home Assistant.

## Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**.
2. Recherchez **PitStop Log** et suivez l'assistant pour créer un véhicule.
3. Répétez pour chaque véhicule du parc.
4. Pour modifier un véhicule : roulez sa carte → **Configurer** (Options Flow).

## Capteurs créés par véhicule

| Capteur | Description |
|---|---|
| Kilométrage | Kilométrage actuel du véhicule (km). |
| Prochain entretien | Statut le plus urgent (`OK` / `Bientôt dû` / `En retard`, traduit dans l'interface), avec en attributs le détail des plans et l'historique complet (dates, km, actions, coûts, liens vers les factures). |
| Un capteur par plan d'entretien | Statut du plan (traduit dans l'interface) avec attributs `km_remaining`, `days_remaining`, `due_km`, `due_date`. |

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

## Stockage des données

- Données (véhicules, plans, historique) : `.storage/pitstop_log` (JSON, géré
  par `homeassistant.helpers.storage.Store`).
- Photos de factures : `/config/www/pitstop_log/invoices/` (créé
  automatiquement au démarrage), accessibles dans Lovelace via
  `/local/pitstop_log/invoices/...`.

## Licence

Fourni tel quel, sans garantie. Utilisation libre.
