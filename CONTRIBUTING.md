# Contribuer à PitStop Log

Merci de votre contribution ! La plupart des ajouts se font **sans toucher au code**.

## Ce que vous pouvez ajouter par simple PR

| Sujet | Fichier(s) |
|---|---|
| Traduction de l'intégration | `custom_components/pitstop_log/translations/<langue>.json` (dupliquez `fr.json`, gardez les clés) |
| Traduction de la carte Lovelace | `custom_components/pitstop_log/locales/<langue>.json` (dupliquez `locales/fr.json`) |
| Marque + logo | `custom_components/pitstop_log/brands.json` + SVG dans `custom_components/pitstop_log/brands/` |
| Nature d'entretien | `custom_components/pitstop_log/maintenance_types.json` |
| Gabarit de natures (type de véhicule) | `custom_components/pitstop_log/plan_templates.json` |

## Règles importantes

- **Ne modifiez pas `lovelace/pitstop-card.js`** sans accord préalable : ce fichier doit rester en échappement ASCII (`\uXXXX`), toute insertion directe d'accents le casse.
- **Gabarits de natures** : les noms des natures doivent rester dans `maintenance_types.json` (sinon la réinitialisation automatique depuis le carnet ne fonctionne plus). Après toute modification de `plan_templates.json`, régénérez la page de visualisation et committez-la : `python3 scripts/generate_templates_page.py` (la CI échoue sinon).
- **Versionnement** : `X.Y.Z` pour la production, `X.Y.Z-beta.N` pour les betas. **Semver strict : pas de zéro de tête** (`beta.1`…`beta.9`, puis `beta.10`… — à partir de beta.10 le numéro fait 2 chiffres naturellement). HACS/HA rejettent un manifest avec `beta.01`. La CI refuse tout autre format.
- Une PR = un sujet (ne mélangez pas une traduction et une marque).

## Vérifier avant d'ouvrir la PR

```bash
python3 scripts/check_translations.py        # cohérence des traductions
python3 scripts/check_data.py               # marques, natures, gabarits, version
python3 scripts/generate_logos_page.py      # page docs/logos.md à jour (si brands.json modifié)
python3 scripts/generate_templates_page.py # page docs/plan_templates.md à jour (si plan_templates.json modifié)
```

La CI (`.github/workflows/ci.yml`) rejoue ces contrôles + syntaxe Python/JS + validité JSON sur chaque PR. Elle doit être **entièrement verte** avant fusion.
