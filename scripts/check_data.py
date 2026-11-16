#!/usr/bin/env python3
"""Vérifie la cohérence des données de PitStop Log.

Usage : python3 scripts/check_data.py

Contrôles :
1. brands.json : catégories valides, label présent, logo existant,
   pas de logo orphelin dans brands/.
2. maintenance_types.json : liste non vide, sans doublons.
3. manifest.json : version au format semver (X.Y.Z ou X.Y.Z-beta.NN,
   numéros de beta sur 2 chiffres).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "pitstop_log"
CATEGORIES = {"moto", "car", "camper", "other"}
LOCAL_PREFIX = "/local/pitstop_log/brands/"
VERSION_RE = re.compile(
    r"^\d+\.\d+\.\d+(-beta\.\d{2,}|-(?:rc|alpha)\.\d{1,2})?$"
)

errors = []

# ---- 1. brands.json ----
data = json.loads((ROOT / "brands.json").read_text(encoding="utf-8"))
brands = data.get("brands")
if not isinstance(brands, dict) or not brands:
    errors.append("brands.json : objet 'brands' vide ou absent")
    brands = brands or {}
brand_dir = ROOT / "brands"
referenced = set()
for name, info in brands.items():
    if not isinstance(info, dict):
        errors.append(f"brands.json : {name} doit être un objet")
        continue
    if info.get("category") not in CATEGORIES:
        errors.append(
            f"brands.json : {name} catégorie invalide {info.get('category')!r} "
            f"(attendu parmi {sorted(CATEGORIES)})"
        )
    if not (info.get("label") or "").strip():
        errors.append(f"brands.json : {name} sans label")
    logo = (info.get("logo") or "").strip()
    # logo vide : autoré (la marque s'affiche sans logo ; un contributeur
    # peut fournir le SVG dans brands/ et référencer le chemin dans brands.json)
    if not logo:
        continue
    if not logo.startswith(LOCAL_PREFIX):
        errors.append(
            f"brands.json : {name} logo {logo!r} doit commencer par {LOCAL_PREFIX}"
        )
        continue
    filename = logo[len(LOCAL_PREFIX):]
    referenced.add(filename)
    if not (brand_dir / filename).is_file():
        errors.append(f"brands.json : {name} logo introuvable : brands/{filename}")

for svg in sorted(brand_dir.glob("*.svg")):
    if svg.name not in referenced:
        errors.append(f"logo orphelin (absent de brands.json) : brands/{svg.name}")

# ---- 2. maintenance_types.json ----
types = json.loads((ROOT / "maintenance_types.json").read_text(encoding="utf-8"))
if not isinstance(types.get("types"), list) or not types["types"]:
    errors.append("maintenance_types.json : la liste 'types' est vide ou absente")
else:
    seen = set()
    for t in types["types"]:
        if not t.strip():
            errors.append("maintenance_types.json : nature vide")
        elif t in seen:
            errors.append(f"maintenance_types.json : doublon {t!r}")
        seen.add(t)

# ---- 3. manifest.json ----
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
version = manifest.get("version", "")
if not VERSION_RE.match(version):
    errors.append(
        f"manifest.json : version {version!r} invalide "
        "(formats attendus : X.Y.Z, X.Y.Z-beta.NN — betas sur 2 chiffres)"
    )

if errors:
    print("ERREURS DE DONNÉES :")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("Données cohérentes : OK")
