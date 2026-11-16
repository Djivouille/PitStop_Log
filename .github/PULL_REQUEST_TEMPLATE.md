## Sujet de la PR

<!-- Traduction / nouvelle marque + logo / nouvelle nature d'entretien / correction / fonctionnalité -->

## Description

<!-- Que modifie cette PR et pourquoi -->

## Contrôles effectués

- [ ] La CI passe (tous les jobs verts)
- [ ] (si traduction) `python3 scripts/check_translations.py` passe localement
- [ ] (si traduction) toutes les langues ont les mêmes clés
- [ ] (si marque) le logo SVG est bien ajouté dans `custom_components/pitstop_log/brands/` et référencé dans `brands.json`
- [ ] (si marque) j'ai régénéré la page des logos : `python3 scripts/generate_logos_page.py`
- [ ] (si nature d'entretien) ajoutée dans `maintenance_types.json` sans doublon
- [ ] Je n'ai pas modifié `custom_components/pitstop_log/lovelace/pitstop-card.js` (sauf accord préalable — fichier à échappement ASCII)
