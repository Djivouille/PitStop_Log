"""Constantes du domaine PitStop Log."""

from __future__ import annotations

# Domaine et version de l'intégration
DOMAIN = "pitstop_log"
VERSION = "0.1.0"
PLATFORMS = ["sensor"]

# Clé et version du stockage persistant (homeassistant.helpers.storage.Store)
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Dossier des factures (accessible via /local/pitstop_log/invoices/...)
INVOICE_DIR = "www/pitstop_log/invoices"
INVOICE_URL_PREFIX = "/local/pitstop_log/invoices"

# Clés de configuration des véhicules
CONF_VEHICLE_NAME = "vehicle_name"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_BRAND = "brand"
CONF_MODEL = "model"
CONF_MODEL_YEAR = "model_year"
CONF_PURCHASE_DATE = "purchase_date"
CONF_REGISTRATION = "registration"
CONF_ODOMETER = "odometer"

# Types de véhicules proposés dans le flux de configuration
VEHICLE_TYPES = ["moto", "car", "other"]

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

# États possibles des capteurs d'entretien
STATUS_OK = "OK"
STATUS_DUE_SOON = "Bientôt dû"
STATUS_OVERDUE = "En retard"
