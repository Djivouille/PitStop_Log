#!/usr/bin/env python3
"""Génère la page de visualisation des gabarits de plans d'entretien.

Usage : python3 scripts/generate_templates_page.py

Lit custom_components/pitstop_log/plan_templates.json et écrit
docs/plan_templates.md (un tableau par type de véhicule). Les noms
affichés (FR/EN) viennent de la section « plan_names » des traductions ;
le « nom stocké » est l'identifiant stable du plan, utilisé pour la
réinitialisation automatique depuis le carnet d'entretien.

La CI (job « templates-page ») régénère la page et échoue si elle n'est
pas à jour : toute PR modifiant plan_templates.json doit relancer ce script.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_JSON = ROOT / "custom_components" / "pitstop_log" / "plan_templates.json"
TRANSLATIONS_DIR = ROOT / "custom_components" / "pitstop_log" / "translations"
OUT = ROOT / "docs" / "plan_templates.md"

TYPES = [
    ("moto", "Moto"),
    ("car", "Voiture"),
    ("camper", "Camping-car"),
    ("other", "Autre"),
]


def _slug(text: str) -> str:
    """Slug identique à homeassistant.util.slugify (sans dépendre de HA)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()


def _fmt_number(value) -> str:
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


def main() -> int:
    templates = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))["templates"]
    names: dict[str, dict[str, str]] = {}
    for lang in ("fr", "en"):
        data = json.loads(
            (TRANSLATIONS_DIR / f"{lang}.json").read_text(encoding="utf-8")
        )
        names[lang] = data.get("plan_names", {})

    lines = [
        "# Gabarits de plans d'entretien par type de véhicule",
        "",
        "Page générée automatiquement depuis",
        "[`plan_templates.json`](../custom_components/pitstop_log/plan_templates.json)",
        "par [`scripts/generate_templates_page.py`](../scripts/generate_templates_page.py) —",
        "ne pas éditer ce fichier à la main : relancer le script après toute",
        "modification des gabarits (la CI vérifie que la page est à jour).",
        "",
        "- **Nom stocké** : identifiant stable du plan (valeur `name` du JSON). Il doit",
        "  rester dans `maintenance_types.json` : c'est lui qui permet la",
        "  réinitialisation automatique d'un plan depuis le carnet d'entretien.",
        "- **Slug** : clé de `plan_names` dans les traductions (noms affichés FR/EN)",
        "  et préfixe des champs du formulaire (`tpl_<slug>_…`).",
        "- En plus des plans du gabarit, l'interface propose **3 plans personnalisés**",
        "  (`tpl_custom_1` à `tpl_custom_3`), non stockés dans ce fichier.",
        "- Copie servie à l'exécution : `/local/pitstop_log/plan_templates.json`.",
        "",
    ]

    for vtype, title in TYPES:
        tpl = templates.get(vtype)
        if not tpl:
            continue
        plans = tpl.get("plans", [])
        plural = "s" if len(plans) != 1 else ""
        lines += [f"## {title} ({len(plans)} plan{plural})", ""]
        lines += [
            "| Entretien (FR) | Maintenance (EN) | Nom stocké | Slug | Intervalle (km) | Intervalle (mois) |",
            "|---|---|---|---|---|---|",
        ]
        for plan in plans:
            name = plan.get("name", "")
            slug = _slug(name)
            fr = names["fr"].get(slug, name)
            en = names["en"].get(slug, name)
            km = plan.get("interval_km") or "—"
            months = plan.get("interval_months") or "—"
            if km != "—":
                km = _fmt_number(km)
            lines.append(
                f"| {fr} | {en} | `{name}` | `{slug}` | {km} | {months} |"
            )
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Page générée : {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
