#!/usr/bin/env python3
"""Génère la page de visualisation des logos de marques.

Usage : python3 scripts/generate_logos_page.py

Lit custom_components/pitstop_log/brands.json et écrit docs/logos.md
(galerie de vignettes, groupée par catégorie). Les logos sont référencés
via raw.githubusercontent.com ; une marque sans logo affiche l'icône
« image manquante » (brands/_missing.svg), identique à celle de la carte.

La CI (job « logos-page ») régénère la page et échoue si elle n'est pas
à jour : toute PR modifiant brands.json doit relancer ce script.
"""

import json
import sys
from pathlib import Path

REPO = "Djivouille/PitStop_Log"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent.parent
BRANDS_JSON = ROOT / "custom_components" / "pitstop_log" / "brands.json"
OUT = ROOT / "docs" / "logos.md"

CATEGORIES = [
    ("moto", "Motos"),
    ("car", "Voitures"),
    ("camper", "Camping-cars"),
    ("other", "Autres"),
]

RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/custom_components/pitstop_log/brands"


def raw_url(filename: str) -> str:
    return f"{RAW}/{filename}"


def main() -> int:
    data = json.loads(BRANDS_JSON.read_text(encoding="utf-8"))
    brands = data.get("brands", {})

    lines = [
        "# Galerie des logos de marques",
        "",
        "Toutes les marques connues de PitStop Log, générée automatiquement",
        "depuis [`brands.json`](../custom_components/pitstop_log/brands.json)",
        "par [`scripts/generate_logos_page.py`](../scripts/generate_logos_page.py).",
        "",
        "L'icône barrée indique une marque en attente de logo —",
        "vos PR sont les bienvenues (voir [`CONTRIBUTING.md`](../CONTRIBUTING.md)).",
        "",
    ]

    for category, title in CATEGORIES:
        entries = [
            (name, info)
            for name, info in brands.items()
            if info.get("category") == category
        ]
        if not entries:
            continue
        entries.sort(key=lambda item: item[0].lower())
        lines += [f"## {title} ({len(entries)})", ""]
        # tableau de 4 vignettes par ligne
        per_row = 4
        header = "|" + "|".join([" Logo "] * per_row) + "|"
        sep = "|" + "|".join(["---"] * per_row) + "|"
        lines += [header, sep]
        for i in range(0, len(entries), per_row):
            row = entries[i : i + per_row]
            cells = []
            for name, info in row:
                logo = (info.get("logo") or "").strip()
                filename = logo.rsplit("/", 1)[-1] if logo else "_missing.svg"
                url = raw_url(filename)
                cells.append(
                    f'<img src="{url}" width="48" height="48" alt="{name}"><br>{name}'
                )
            cells += [""] * (per_row - len(row))
            lines.append("|" + "|".join(cells) + "|")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Page générée : {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
