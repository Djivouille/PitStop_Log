"""Constantes du domaine PitStop Log."""

from __future__ import annotations

import json
from pathlib import Path


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

# Domaine et version de l'intégration
# Convention : AAAA.MM.JJ (date de publication)
DOMAIN = "pitstop_log"
VERSION = "2026.11.22"
PLATFORMS = ["sensor"]

# Clé et version du stockage persistant (homeassistant.helpers.storage.Store)
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Dossier des factures (accessible via /local/pitstop_log/invoices/...)
INVOICE_DIR = "www/pitstop_log/invoices"
INVOICE_URL_PREFIX = "/local/pitstop_log/invoices"

# Dossier des logos de marques (copiés dans www au démarrage, servis localement)
BRANDS_DIR = "www/pitstop_log/brands"
BRANDS_URL_PREFIX = "/local/pitstop_log/brands"

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

# Noms des services exposés
SERVICE_UPDATE_ODOMETER = "update_odometer"
SERVICE_ADD_MAINTENANCE_DONE = "add_maintenance_done"
SERVICE_ADD_MAINTENANCE_PLAN = "add_maintenance_plan"

# Attributs communs
ATTR_VEHICLE_ID = "vehicle_id"
ATTR_ENTITY_ID = "entity_id"

# Seuils d'alerte (en % de l'intervalle ou en jours restants)
DUE_SOON_KM_PERCENT = 0.15  # Bientôt dû sous 15 % de l'intervalle km restant
DUE_SOON_DAYS = 30  # Bientôt dû sous 30 jours

# États possibles des capteurs d'entretien (jetons neutres, traduits dans
# l'interface via translation_key + sélecteur de texte)
STATUS_OK = "ok"
STATUS_DUE_SOON = "due_soon"
STATUS_OVERDUE = "overdue"

# Clé de traduction commune des capteurs de statut d'entretien
TRANSLATION_KEY_MAINTENANCE_STATUS = "maintenance_status"
