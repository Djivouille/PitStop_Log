"""Constantes du domaine PitStop Log."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def _load_brands() -> dict[str, dict[str, str]]:
    """Charger la liste des marques et leurs logos depuis brands.json."""
    brands_path = Path(__file__).parent / "brands.json"
    with open(brands_path, encoding="utf-8") as file:
        return json.load(file)["brands"]


# Marques disponibles pour le sélecteur (fichier à part : brands.json)
BRANDS = _load_brands()
BRAND_NAMES = list(BRANDS)


def brand_logo(brand: str) -> str:
    """Retourner l'URL du logo d'une marque (chaîne vide si inconnue)."""
    return BRANDS.get(brand, {}).get("logo", "")


def brands_for_type(vehicle_type: str) -> list[str]:
    """Lister les marques correspondant à un type de véhicule.

    « Autre » est toujours proposé ; pour le type « other »,
    toutes les marques sont affichées.
    """
    if vehicle_type == "other":
        return list(BRANDS)
    return [
        name
        for name, info in BRANDS.items()
        if info.get("category") == vehicle_type or name == "Autre"
    ]


# Gabarits de plans d'entretien par type de véhicule (fichier à part)
PLAN_TEMPLATES_FILE = "plan_templates.json"


def _load_plan_templates() -> dict[str, dict[str, Any]]:
    """Charger les gabarits de plans depuis plan_templates.json."""
    templates_path = Path(__file__).parent / PLAN_TEMPLATES_FILE
    with open(templates_path, encoding="utf-8") as file:
        return json.load(file)["templates"]


PLAN_TEMPLATES = _load_plan_templates()


def plan_template_for_type(vehicle_type: str) -> dict[str, Any]:
    """Retourner le gabarit de plans d'un type de véhicule (repli : « other »)."""
    return PLAN_TEMPLATES.get(vehicle_type) or PLAN_TEMPLATES.get("other", {})


def _slug(text: str) -> str:
    """Slug identique à homeassistant.util.slugify (sans dépendre de HA)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()


def _load_plan_names() -> dict[str, dict[str, str]]:
    """Charger les noms affichés des plans depuis les traductions (plan_names)."""
    translations_dir = Path(__file__).parent / "translations"
    names: dict[str, dict[str, str]] = {}
    for lang in ("fr", "en"):
        path = translations_dir / f"{lang}.json"
        with open(path, encoding="utf-8") as file:
            names[lang] = json.load(file).get("plan_names", {})
    return names


# Noms affichés des plans par langue (clé = slug du nom d'origine, ex. « vidange »)
PLAN_NAMES = _load_plan_names()


def plan_display_name(name: str, lang: str = "fr") -> str:
    """Nom affiché d'un plan traduit (repli : fr, puis nom d'origine)."""
    slug = _slug(name)
    return (
        PLAN_NAMES.get(lang, {}).get(slug)
        or PLAN_NAMES.get("fr", {}).get(slug)
        or name
    )

# Domaine et version de l'intégration
# Versionnement sémantique : MAJOR.MINOR.PATCH pour la production,
# MAJOR.MINOR.PATCH-beta.N pour les versions de test (pre-release).
DOMAIN = "pitstop_log"
VERSION = "0.4.0-beta.3"
PLATFORMS = ["sensor", "image"]

# Clé et version du stockage persistant (homeassistant.helpers.storage.Store)
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Dossier des factures (accessible via /local/pitstop_log/invoices/...)
INVOICE_DIR = "www/pitstop_log/invoices"
INVOICE_URL_PREFIX = "/local/pitstop_log/invoices"

# Dossier des logos de marques (copiés dans www au démarrage, servis localement)
BRANDS_DIR = "www/pitstop_log/brands"
BRANDS_URL_PREFIX = "/local/pitstop_log/brands"

# Dossier des photos des véhicules (servies localement)
PHOTOS_DIR = "www/pitstop_log/photos"
PHOTOS_URL_PREFIX = "/local/pitstop_log/photos"

# Clés de configuration des véhicules
CONF_VEHICLE_NAME = "vehicle_name"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_BRAND = "brand"
CONF_MODEL = "model"
CONF_MODEL_YEAR = "model_year"
CONF_PURCHASE_DATE = "purchase_date"
CONF_REGISTRATION = "registration"
CONF_ODOMETER = "odometer"
CONF_PHOTO = "photo"
CONF_BRAND_LOGO = "brand_logo"

# Types de véhicules proposés dans le flux de configuration
VEHICLE_TYPES = ["moto", "car", "camper", "other"]

# Libellés affichés pour chaque type de véhicule
VEHICLE_TYPE_LABELS = {
    "moto": "Moto",
    "car": "Voiture",
    "camper": "Camping-car",
    "other": "Autre",
}

# Clés des plans d'entretien (entretiens à faire)
CONF_APPLY_TEMPLATE = "apply_template"
CONF_TEMPLATE_PLANS = "template_plans"
CONF_PLAN_NAME = "plan_name"
CONF_INTERVAL_KM = "interval_km"
CONF_INTERVAL_MONTHS = "interval_months"
CONF_LAST_KM = "last_km"
CONF_LAST_DATE = "last_date"
CONF_ACTIVE = "active"

# Clés des entretiens réalisés (historique)
CONF_DATE = "date"
CONF_KM = "km"
CONF_ACTIONS = "actions"
CONF_COST = "cost"
CONF_INVOICE_PATH = "invoice_path"
CONF_INVOICE_BASE64 = "invoice_base64"
CONF_INVOICE_URL = "invoice_url"
CONF_PLAN_ID = "plan_id"
CONF_INDEX = "index"
MAINTENANCE_TYPES_FILE = "maintenance_types.json"

# Noms des services exposés
SERVICE_UPDATE_ODOMETER = "update_odometer"
SERVICE_DELETE_ODOMETER_POINT = "delete_odometer_point"
SERVICE_UPDATE_REGISTRATION = "update_registration"
SERVICE_UPDATE_PURCHASE_DATE = "update_purchase_date"
SERVICE_UPDATE_BRAND_MODEL = "update_brand_model"
SERVICE_ADD_MAINTENANCE_DONE = "add_maintenance_done"
SERVICE_ADD_MAINTENANCE_PLAN = "add_maintenance_plan"
SERVICE_UPDATE_MAINTENANCE = "update_maintenance"
SERVICE_DELETE_MAINTENANCE = "delete_maintenance"
SERVICE_UPDATE_MAINTENANCE_PLAN = "update_maintenance_plan"
SERVICE_DELETE_MAINTENANCE_PLAN = "delete_maintenance_plan"

# Attributs communs
ATTR_VEHICLE_ID = "vehicle_id"
ATTR_ENTITY_ID = "entity_id"

# Seuils de rappel par défaut (modifiables par véhicule, étape « Rappels »)
CONF_REMINDER_URGENT_DAYS = "reminder_urgent_days"
CONF_REMINDER_VERY_URGENT_DAYS = "reminder_very_urgent_days"
CONF_REMINDER_URGENT_KM = "reminder_urgent_km"
CONF_REMINDER_VERY_URGENT_KM = "reminder_very_urgent_km"

REMINDER_DEFAULTS: dict[str, int] = {
    CONF_REMINDER_URGENT_DAYS: 30,      # Urgent sous 30 jours restants
    CONF_REMINDER_VERY_URGENT_DAYS: 7, # Très urgent sous 7 jours restants
    CONF_REMINDER_URGENT_KM: 100,       # Urgent à moins de 100 km de l'échéance
    CONF_REMINDER_VERY_URGENT_KM: 50,  # Très urgent à moins de 50 km de l'échéance
}

# États possibles des capteurs d'entretien (jetons neutres, traduits dans
# l'interface via translation_key + sélecteur de texte).
# past_due (échéance dépassée) est toujours prioritaire et non paramétrable.
STATUS_NOT_URGENT = "not_urgent"
STATUS_URGENT = "urgent"
STATUS_VERY_URGENT = "very_urgent"
STATUS_PAST_DUE = "past_due"

# Clé de traduction commune des capteurs de statut d'entretien
TRANSLATION_KEY_MAINTENANCE_STATUS = "maintenance_status"
