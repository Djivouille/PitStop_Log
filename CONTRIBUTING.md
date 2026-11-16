# Contribuer à PitStop Log

Merci de votre contribution ! La plupart des ajouts se font **sans toucher au code**.

## Ce que vous pouvez ajouter par simple PR

| Sujet | Fichier(s) |
|---|---|
| Traduction de l'intégration | `custom_components/pitstop_log/translations/<langue>.json` (dupliquez `fr.json`, gardez les clés) |
| Traduction de la carte Lovelace | `custom_components/pitstop_log/locales/<langue>.json` (dupliquez `locales/fr.json`) |
| Marque + logo | `custom_components/pitstop_log/brands.json` + SVG dans `custom_components/pitstop_log/brands/` |
| Nature d'entretien | `custom_components/pitstop_log/maintenance_types.json` |

## Règles importantes

- **Ne modifiez pas `lovelace/pitstop-card.js`** sans accord préalable : ce fichier doit rester en échappement ASCII (`\uXXXX`), toute insertion directe d'accents le casse.
- **Versionnement** : `X.Y.Z` pour la production, `X.Y.Z-beta.NN` pour les betas (numéros de beta **sur 2 chiffres**). La CI refuse tout autre format.
- Une PR = un sujet (ne mélangez pas une traduction et une marque).

## Vérifier avant d'ouvrir la PR

```bash
python3 scripts/check_translations.py   # cohérence des traductions
python3 scripts/check_data.py          # marques, natures, version
```

La CI (`.github/workflows/ci.yml`) rejoue ces contrôles + syntaxe Python/JS + validité JSON sur chaque PR. Elle doit être **entièrement verte** avant fusion.
