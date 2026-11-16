"""Intégration PitStop Log : carnet d'entretien multi-véhicules."""

from __future__ import annotations

import base64
import logging
import os
import secrets
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import (
    BRANDS_DIR,
    CONF_ACTIONS,
    CONF_BRAND,
    CONF_COST,
    CONF_DATE,
    CONF_MODEL,
    CONF_MODEL_YEAR,
    CONF_ODOMETER,
    CONF_PURCHASE_DATE,
    CONF_REGISTRATION,
    CONF_INVOICE_BASE64,
    CONF_INVOICE_PATH,
    CONF_INTERVAL_KM,
    CONF_INTERVAL_MONTHS,
    CONF_KM,
    CONF_LAST_DATE,
    CONF_LAST_KM,
    CONF_PLAN_ID,
    CONF_PLAN_NAME,
    CONF_VEHICLE_NAME,
    CONF_VEHICLE_TYPE,
    DOMAIN,
    brand_logo,
    INVOICE_DIR,
    INVOICE_URL_PREFIX,
    PHOTOS_DIR,
    PLATFORMS,
    SERVICE_ADD_MAINTENANCE_DONE,
    SERVICE_ADD_MAINTENANCE_PLAN,
    SERVICE_UPDATE_ODOMETER,
)
from .coordinator import (
    PitStopDataUpdateCoordinator,
    async_get_or_create_coordinator,
)

# Schémas de validation des services
UPDATE_ODOMETER_SCHEMA = vol.Schema(
    {
        vol.Required("vehicle_id"): str,
        vol.Required("km"): int,
    }
)

ADD_MAINTENANCE_DONE_SCHEMA = vol.Schema(
    {
        vol.Required("vehicle_id"): str,
        vol.Required("date"): str,
        vol.Required("km"): int,
        vol.Required("actions"): str,
        vol.Optional("cost"): vol.Coerce(float),
        vol.Optional("invoice_path"): str,
        vol.Optional("invoice_base64"): str,
        vol.Optional("plan_id"): str,
    }
)

ADD_MAINTENANCE_PLAN_SCHEMA = vol.Schema(
    {
        vol.Required("vehicle_id"): str,
        vol.Required("plan_name"): str,
        vol.Optional("interval_km"): int,
        vol.Optional("interval_months"): int,
        vol.Optional("last_km"): int,
        vol.Optional("last_date"): str,
    }
)


_LOGGER = logging.getLogger(__name__)


async def _sync_www_assets(hass: HomeAssistant) -> None:
    """Copier les ressources embarquées (logos, carte Lovelace) vers www.

    Idempotent : appelé au démarrage du composant ET à chaque configuration
    d'entrée, pour couvrir tous les scénarios de chargement.
    """
    integration_dir = os.path.dirname(__file__)
    www_dir = hass.config.path()

    # Dossier des factures et des photos des véhicules
    await hass.async_add_executor_job(
        _ensure_invoice_dir, os.path.join(www_dir, INVOICE_DIR)
    )
    await hass.async_add_executor_job(
        _ensure_invoice_dir, os.path.join(www_dir, PHOTOS_DIR)
    )

    # Logos de marques embarqués (SVG servis via /local/)
    await hass.async_add_executor_job(
        _sync_brand_logos,
        os.path.join(integration_dir, "brands"),
        os.path.join(www_dir, BRANDS_DIR),
    )

    # Carte Lovelace embarquée (JS servi via /local/)
    source_lovelace = os.path.join(integration_dir, "lovelace")
    target_lovelace = os.path.join(www_dir, "www/pitstop_log/lovelace")
    await hass.async_add_executor_job(_sync_files, source_lovelace, target_lovelace)
    if not os.path.isdir(source_lovelace):
        _LOGGER.warning(
            "Dossier lovelace/ absent de l'installation ; la carte Lovelace "
            "PitStop Card ne sera pas disponible. Réinstallez l'intégration."
        )
    elif not os.path.isfile(os.path.join(target_lovelace, "pitstop-card.js")):
        _LOGGER.error(
            "La carte Lovelace n'a pas pu être copiée dans %s",
            target_lovelace,
        )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Initialiser l'intégration : stockage, dossier factures et services."""
    coordinator = await async_get_or_create_coordinator(hass)

    # Ressources www : factures, photos, logos de marques, carte Lovelace
    await _sync_www_assets(hass)

    async def handle_update_odometer(call: ServiceCall) -> None:
        """Service : mettre à jour le kilométrage d'un véhicule."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_update_odometer(vehicle_id, call.data["km"])

    async def handle_add_maintenance_done(call: ServiceCall) -> None:
        """Service : enregistrer un entretien réalisé."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        invoice_url = call.data.get(CONF_INVOICE_PATH)
        # Si une image est fournie en base64, on la sauvegarde dans le dossier local
        image_b64 = call.data.get(CONF_INVOICE_BASE64)
        if image_b64:
            invoice_dir = os.path.join(hass.config.path(), INVOICE_DIR)
            filename = f"{secrets.token_hex(8)}.jpg"
            filepath = os.path.join(invoice_dir, filename)
            await hass.async_add_executor_job(
                _save_invoice_image, filepath, image_b64
            )
            invoice_url = f"{INVOICE_URL_PREFIX}/{filename}"
        await coordinator.async_add_maintenance_done(
            vehicle_id=vehicle_id,
            date=call.data[CONF_DATE],
            km=call.data[CONF_KM],
            actions=call.data[CONF_ACTIONS],
            cost=call.data.get(CONF_COST),
            invoice_url=invoice_url,
            plan_id=call.data.get(CONF_PLAN_ID),
        )

    async def handle_add_maintenance_plan(call: ServiceCall) -> None:
        """Service : ajouter une règle d'entretien périodique."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_add_maintenance_plan(
            vehicle_id=vehicle_id,
            name=call.data[CONF_PLAN_NAME],
            interval_km=call.data.get(CONF_INTERVAL_KM),
            interval_months=call.data.get(CONF_INTERVAL_MONTHS),
            last_km=call.data.get(CONF_LAST_KM),
            last_date=call.data.get(CONF_LAST_DATE),
        )

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_ODOMETER, handle_update_odometer,
        schema=UPDATE_ODOMETER_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_MAINTENANCE_DONE, handle_add_maintenance_done,
        schema=ADD_MAINTENANCE_DONE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_MAINTENANCE_PLAN, handle_add_maintenance_plan,
        schema=ADD_MAINTENANCE_PLAN_SCHEMA,
    )
    return True


def _ensure_invoice_dir(invoice_dir: str) -> None:
    """Créer le dossier des factures s'il n'existe pas (exécuté hors boucle)."""
    os.makedirs(invoice_dir, exist_ok=True)


def _sync_brand_logos(source_dir: str, target_dir: str) -> None:
    """Copier les SVG de marques embarqués vers www (exécuté hors boucle).

    Les fichiers déjà présents ne sont pas écrasés ; l'opération est
    idempotente et ne fait rien si le dossier source est absent.
    """
    _sync_files(source_dir, target_dir, suffix=".svg")


def _sync_files(source_dir: str, target_dir: str, suffix: str | None = None) -> None:
    """Copier les fichiers embarqués d'un dossier vers www (hors boucle).

    Les fichiers déjà présents ne sont pas écrasés ; l'opération est
    idempotente et ne fait rien si le dossier source est absent.
    """
    if not os.path.isdir(source_dir):
        return
    os.makedirs(target_dir, exist_ok=True)
    for filename in os.listdir(source_dir):
        if suffix and not filename.endswith(suffix):
            continue
        source = os.path.join(source_dir, filename)
        if not os.path.isfile(source):
            continue
        target = os.path.join(target_dir, filename)
        if os.path.exists(target):
            continue
        with open(source, "rb") as src:
            with open(target, "wb") as dst:
                dst.write(src.read())


def _save_invoice_image(filepath: str, image_b64: str) -> None:
    """Décoder et écrire une image de facture sur le disque (hors boucle)."""
    try:
        payload = base64.b64decode(image_b64)
    except Exception as err:
        raise HomeAssistantError("Image de facture base64 invalide") from err
    with open(filepath, "wb") as file:
        file.write(payload)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Configurer une entrée (un véhicule) et charger la plateforme capteur."""
    # Enregistre le véhicule dans les données persistées du coordinateur
    coordinator = await async_get_or_create_coordinator(hass)
    vehicle_id = entry.data["vehicle_id"]
    vehicle = coordinator.get_vehicle(vehicle_id)
    if vehicle is None:
        coordinator.set_vehicle(
            vehicle_id,
            {
                "name": entry.data[CONF_VEHICLE_NAME],
                "type": entry.data.get(CONF_VEHICLE_TYPE, "car"),
                "brand": entry.data.get(CONF_BRAND, ""),
                "model": entry.data.get(CONF_MODEL, ""),
                "model_year": entry.data.get(CONF_MODEL_YEAR),
                "purchase_date": entry.data.get(CONF_PURCHASE_DATE),
                "registration": entry.data.get(CONF_REGISTRATION, ""),
                "odometer": entry.data.get(CONF_ODOMETER, 0),
                "photo": entry.data.get("photo", ""),
                "brand_logo": brand_logo(entry.data.get(CONF_BRAND, "")),
            },
        )
        await coordinator.async_save()
    # Ressources www : couvre aussi le cas d'un composant non encore initialisé
    await _sync_www_assets(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Décharger une entrée et supprimer le véhicule associé."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: PitStopDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
        coordinator.delete_vehicle(entry.data["vehicle_id"])
        await coordinator.async_save()
        await coordinator.async_refresh()
    return unload_ok
