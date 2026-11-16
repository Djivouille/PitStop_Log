#!/usr/bin/env python3
"""Vérifie la cohérence des traductions de PitStop Log.

Usage : python3 scripts/check_translations.py

Contrôles :
1. strings.json, translations/fr.json et translations/en.json ont les mêmes clés
   (config, options, entity, services — récursivement).
2. locales/fr.json et locales/en.json (carte Lovelace) ont les mêmes clés.
3. Les valeurs ne sont pas vides.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "pitstop_log"


def diff_keys(a, b, path=""):
    """Retourne la liste des clés divergentes entre deux dict."""
    errors = []
    for key in sorted(set(a) | set(b)):
        sub = f"{path}{key}"
        if key not in a:
            errors.append(f"absent de la référence : {sub}")
        elif key not in b:
            errors.append(f"absent de la traduction : {sub}")
        elif isinstance(a[key], dict) and isinstance(b[key], dict):
            errors += diff_keys(a[key], b[key], sub + ".")
        elif isinstance(a[key], dict) or isinstance(b[key], dict):
            errors.append(f"type divergent (objet vs valeur) : {sub}")
        elif isinstance(a[key], str) and not b[key].strip():
            errors.append(f"valeur vide : {sub}")
    return errors


def main() -> int:
    errors = []

    # 1. Traductions de l'intégration
    base = json.loads((ROOT / "strings.json").read_text(encoding="utf-8"))
    for lang in ["fr", "en"]:
        path = ROOT / "translations" / f"{lang}.json"
        if not path.is_file():
            errors.append(f"fichier manquant : {path.name}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        errors += [f"[{lang}] {e}" for e in diff_keys(base, data)]

    # 2. Locales de la carte Lovelace
    loc_root = ROOT / "locales"
    fr = json.loads((loc_root / "fr.json").read_text(encoding="utf-8"))
    for loc in sorted(loc_root.glob("*.json")):
        data = json.loads(loc.read_text(encoding="utf-8"))
        errors += [f"[locales/{loc.name}] {e}" for e in diff_keys(fr, data)]

    if errors:
        print("ERREURS DE TRADUCTION :")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Traductions cohérentes : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
