# Gabarits de natures d'entretien par type de véhicule

Page générée automatiquement depuis
[`plan_templates.json`](../custom_components/pitstop_log/plan_templates.json)
par [`scripts/generate_templates_page.py`](../scripts/generate_templates_page.py) —
ne pas éditer ce fichier à la main : relancer le script après toute
modification des gabarits (la CI vérifie que la page est à jour).

- **Nom stocké** : identifiant stable de la nature (valeur `name` du JSON). Il doit
  rester dans `maintenance_types.json` : c'est lui qui permet la
  réinitialisation automatique d'une nature depuis le carnet d'entretien.
- **Slug** : clé de `plan_names` dans les traductions (noms affichés FR/EN)
  et préfixe des champs du formulaire (`tpl_<slug>_…`).
- En plus des natures du gabarit, l'interface propose **3 natures personnalisées**
  (`tpl_custom_1` à `tpl_custom_3`), non stockés dans ce fichier.
- Copie servie à l'exécution : `/local/pitstop_log/plan_templates.json`.

## Moto (7 natures)

| Entretien (FR) | Maintenance (EN) | Nom stocké | Slug | Intervalle (km) | Intervalle (mois) |
|---|---|---|---|---|---|
| Vidange | Oil change | `Vidange` | `vidange` | 6 000 | 12 |
| Chaîne et kit de transmission | Chain and sprocket kit | `Chaîne et kit de transmission` | `chaine_et_kit_de_transmission` | 15 000 | — |
| Liquide de frein | Brake fluid | `Liquide de frein` | `liquide_de_frein` | — | 24 |
| Plaquettes de frein | Brake pads | `Plaquettes de frein` | `plaquettes_de_frein` | 20 000 | — |
| Pneus | Tires | `Pneus` | `pneus` | 10 000 | — |
| Batterie | Battery | `Batterie` | `batterie` | — | 12 |
| Révision | General service | `Révision` | `revision` | 12 000 | 12 |

## Voiture (7 natures)

| Entretien (FR) | Maintenance (EN) | Nom stocké | Slug | Intervalle (km) | Intervalle (mois) |
|---|---|---|---|---|---|
| Vidange | Oil change | `Vidange` | `vidange` | 15 000 | 12 |
| Filtre à air | Air filter | `Filtre à air` | `filtre_a_air` | 30 000 | 24 |
| Liquide de frein | Brake fluid | `Liquide de frein` | `liquide_de_frein` | — | 24 |
| Plaquettes de frein | Brake pads | `Plaquettes de frein` | `plaquettes_de_frein` | 30 000 | — |
| Pneus | Tires | `Pneus` | `pneus` | 30 000 | — |
| Batterie | Battery | `Batterie` | `batterie` | — | 24 |
| Contrôle technique | Technical inspection (MOT) | `Contrôle technique` | `controle_technique` | — | 24 |

## Camping-car (6 natures)

| Entretien (FR) | Maintenance (EN) | Nom stocké | Slug | Intervalle (km) | Intervalle (mois) |
|---|---|---|---|---|---|
| Vidange | Oil change | `Vidange` | `vidange` | 20 000 | 12 |
| Liquide de frein | Brake fluid | `Liquide de frein` | `liquide_de_frein` | — | 24 |
| Batterie | Battery | `Batterie` | `batterie` | — | 12 |
| Révision | General service | `Révision` | `revision` | — | 12 |
| Pneus | Tires | `Pneus` | `pneus` | 30 000 | — |
| Contrôle technique | Technical inspection (MOT) | `Contrôle technique` | `controle_technique` | — | 24 |

## Autre (1 nature)

| Entretien (FR) | Maintenance (EN) | Nom stocké | Slug | Intervalle (km) | Intervalle (mois) |
|---|---|---|---|---|---|
| Révision | General service | `Révision` | `revision` | — | 12 |
