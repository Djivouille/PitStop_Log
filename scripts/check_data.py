#!/usr/bin/env python3
"""Vérifie la cohérence des données de PitStop Log.

Usage : python3 scripts/check_data.py

Contrôles :
1. brands.json : catégories valides, label présent, logo existant,
   pas de logo orphelin dans brands/.
2. maintenance_types.json : liste non vide, sans doublons.
2a. plan_names (strings.json) couvre toutes les natures de maintenance_types.json.
3. plan_templates.json : types connus, plans nommés (présents dans
   maintenance_types.json) avec au moins un intervalle.
4. manifest.json : version au format semver strict (X.Y.Z ou
   X.Y.Z-beta.N — pas de zéro de tête : beta.1…beta.9, beta.10…).
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "pitstop_log"
CATEGORIES = {"moto", "car", "camper", "other"}
LOCAL_PREFIX = "/local/pitstop_log/brands/"
VERSION_RE = re.compile(
    r"^\d+\.\d+\.\d+(-beta\.[1-9]\d?|-(?:rc|alpha)\.[1-9]\d?)?$"
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
    if svg.name not in referenced and svg.name != "_missing.svg":
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

# ---- 2a. plan_names (traductions) couvre maintenance_types.json ----
def _slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()

strings = json.loads((ROOT / "strings.json").read_text(encoding="utf-8"))
plan_names = strings.get("plan_names", {})
if not plan_names:
    errors.append("strings.json : section 'plan_names' vide ou absente")
for t in types.get("types", []):
    if _slug(t) not in plan_names:
        errors.append(
            f"strings.json : plan_names sans entrée pour {t!r} (clé {_slug(t)!r})"
        )

# ---- 2c. plan_names aussi présent dans les locales de la carte ----
for loc in ("fr", "en"):
    loc_path = ROOT / "locales" / f"{loc}.json"
    loc_names = {}
    if loc_path.is_file():
        loc_names = json.loads(loc_path.read_text(encoding="utf-8")).get("plan_names", {})
    if not loc_names:
        errors.append(f"locales/{loc}.json : section 'plan_names' vide ou absente")
    elif set(loc_names) != set(plan_names):
        errors.append(f"locales/{loc}.json : clés plan_names différentes de strings.json")

# ---- 2b. plan_templates.json ----
TEMPLATE_TYPES = {"moto", "car", "camper", "other"}
templates = json.loads(
    (ROOT / "plan_templates.json").read_text(encoding="utf-8")
)
if not isinstance(templates.get("templates"), dict) or not templates["templates"]:
    errors.append("plan_templates.json : objet 'templates' vide ou absent")
else:
    for vtype, tpl in templates["templates"].items():
        if vtype not in TEMPLATE_TYPES:
            errors.append(f"plan_templates.json : type de véhicule inconnu {vtype!r}")
            continue
        plans = tpl.get("plans")
        if not isinstance(plans, list) or not plans:
            errors.append(f"plan_templates.json : gabarit {vtype!r} sans plans")
            continue
        for plan in plans:
            name = (plan.get("name") or "").strip()
            if not name:
                errors.append(f"plan_templates.json : plan sans nom dans {vtype!r}")
            elif name not in types.get("types", []):
                errors.append(
                    f"plan_templates.json : {name!r} absent de maintenance_types.json "
                    f"(le plan ne se réinitialiserait jamais automatiquement)"
                )
            if not plan.get("interval_km") and not plan.get("interval_months"):
                errors.append(
                    f"plan_templates.json : plan {name!r} sans intervalle (km ou mois)"
                )

# ---- 3. manifest.json ----
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
version = manifest.get("version", "")
if not VERSION_RE.match(version):
    errors.append(
        f"manifest.json : version {version!r} invalide "
        "(formats attendus : X.Y.Z, X.Y.Z-beta.N — le semver interdit les "
        "zéros de tête : beta.1 à beta.9, puis beta.10, beta.11…)"
    )

if errors:
    print("ERREURS DE DONNÉES :")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("Données cohérentes : OK")
