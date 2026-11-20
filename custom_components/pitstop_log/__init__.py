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
    CONF_APPLY_TEMPLATE,
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
    SERVICE_UPDATE_MAINTENANCE,
    SERVICE_DELETE_MAINTENANCE,
    CONF_INDEX,
    MAINTENANCE_TYPES_FILE,
    SERVICE_UPDATE_ODOMETER,
    SERVICE_DELETE_ODOMETER_POINT,
    SERVICE_UPDATE_REGISTRATION,
    SERVICE_UPDATE_PURCHASE_DATE,
    SERVICE_UPDATE_BRAND_MODEL,
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
        vol.Optional("date"): str,
    }
)

ADD_MAINTENANCE_DONE_SCHEMA = vol.Schema(
    {
        vol.Required("vehicle_id"): str,
        vol.Required("date"): str,
        vol.Required("km"): int,
        vol.Required("actions"): vol.Any(str, [str]),
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

    # Liste des marques copiée vers www (lue par la carte pour ses
    # menus déroulants, identiques à ceux du flux de création)
    await hass.async_add_executor_job(
        _sync_single_file,
        os.path.join(integration_dir, "brands.json"),
        os.path.join(www_dir, "www/pitstop_log/brands.json"),
    )
    # Liste des natures d'entretien (lue par la carte pour son menu déroulant)
    await hass.async_add_executor_job(
        _sync_single_file,
        os.path.join(integration_dir, MAINTENANCE_TYPES_FILE),
        os.path.join(www_dir, "www/pitstop_log/maintenance_types.json"),
    )
    # Localisation de la carte Lovelace (locales/<langue>.json)
    locales_src = os.path.join(integration_dir, "locales")
    if os.path.isdir(locales_src):
        for locale_file in os.listdir(locales_src):
            if locale_file.endswith(".json"):
                await hass.async_add_executor_job(
                    _sync_single_file,
                    os.path.join(locales_src, locale_file),
                    os.path.join(
                        www_dir, "www/pitstop_log/locales", locale_file
                    ),
                )
    if not os.path.isdir(source_lovelace):
        _LOGGER.warning(
            "Dossier lovelace/ absent de l'installation ; la carte Lovelace "
            "La carte Lovelace PitStop Log ne sera pas disponible. Réinstallez l'intégration."
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
        await coordinator.async_update_odometer(
            vehicle_id, call.data["km"], call.data.get("date")
        )

    async def handle_delete_odometer_point(call: ServiceCall) -> None:
        """Service : supprimer un relevé de l'historique du kilométrage."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_delete_odometer_point(
            vehicle_id, call.data["date"]
        )

    async def handle_update_registration(call: ServiceCall) -> None:
        """Service : mettre à jour l'immatriculation d'un véhicule."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_update_registration(
            vehicle_id, call.data["registration"]
        )

    async def handle_update_purchase_date(call: ServiceCall) -> None:
        """Service : mettre à jour la date d'achat d'un véhicule."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_update_purchase_date(
            vehicle_id, call.data["date"]
        )

    async def handle_update_brand_model(call: ServiceCall) -> None:
        """Service : mettre à jour la marque et le modèle d'un véhicule."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_update_brand_model(
            vehicle_id,
            call.data["brand"],
            call.data["model"],
            model_year=call.data.get("model_year"),
            photo_base64=call.data.get("photo_base64"),
            registration=call.data.get("registration"),
            purchase_date=call.data.get("purchase_date"),
        )

    async def handle_add_maintenance_done(call: ServiceCall) -> None:
        """Service : enregistrer un entretien réalisé."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"Véhicule inconnu : {call.data['vehicle_id']}")
        invoice_url = call.data.get(CONF_INVOICE_PATH)
        # Si une image ou un PDF est fourni en base64, on le sauvegarde
        image_b64 = call.data.get(CONF_INVOICE_BASE64)
        if image_b64:
            invoice_dir = os.path.join(hass.config.path(), INVOICE_DIR)
            ext = _detect_invoice_ext(image_b64)
            filename = f"{secrets.token_hex(8)}.{ext}"
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
        DOMAIN, SERVICE_DELETE_ODOMETER_POINT, handle_delete_odometer_point,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("date"): str,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_REGISTRATION,
        handle_update_registration,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("registration"): str,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_PURCHASE_DATE,
        handle_update_purchase_date,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("date"): str,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_BRAND_MODEL,
        handle_update_brand_model,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("brand"): str,
                vol.Required("model"): str,
                vol.Optional("model_year"): int,
                vol.Optional("photo_base64"): str,
                vol.Optional("registration"): str,
                vol.Optional("purchase_date"): str,
            }
        ),
    )
    async def handle_update_maintenance(call: ServiceCall) -> None:
        """Service : modifier un entretien réalisé."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"V\u00e9hicule inconnu : {call.data['vehicle_id']}")
        invoice_url = None
        image_b64 = call.data.get(CONF_INVOICE_BASE64)
        if image_b64:
            invoice_dir = os.path.join(hass.config.path(), INVOICE_DIR)
            ext = _detect_invoice_ext(image_b64)
            filename = f"{secrets.token_hex(8)}.{ext}"
            filepath = os.path.join(invoice_dir, filename)
            await hass.async_add_executor_job(
                _save_invoice_image, filepath, image_b64
            )
            invoice_url = f"{INVOICE_URL_PREFIX}/{filename}"
        await coordinator.async_update_maintenance(
            vehicle_id=vehicle_id,
            index=call.data[CONF_INDEX],
            date=call.data[CONF_DATE],
            km=call.data[CONF_KM],
            actions=call.data[CONF_ACTIONS],
            cost=call.data.get(CONF_COST),
            invoice_url=invoice_url,
        )

    async def handle_delete_maintenance(call: ServiceCall) -> None:
        """Service : supprimer un entretien réalisé."""
        vehicle_id = coordinator.find_vehicle_id(call.data["vehicle_id"])
        if vehicle_id is None:
            raise ServiceValidationError(f"V\u00e9hicule inconnu : {call.data['vehicle_id']}")
        await coordinator.async_delete_maintenance(
            vehicle_id, call.data[CONF_INDEX]
        )

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_MAINTENANCE_DONE, handle_add_maintenance_done,
        schema=ADD_MAINTENANCE_DONE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_MAINTENANCE_PLAN, handle_add_maintenance_plan,
        schema=ADD_MAINTENANCE_PLAN_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_MAINTENANCE, handle_update_maintenance,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("index"): int,
                vol.Required("date"): str,
                vol.Required("km"): int,
                vol.Required("actions"): vol.Any(str, [str]),
                vol.Optional("cost"): vol.Coerce(float),
                vol.Optional("invoice_base64"): str,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_MAINTENANCE, handle_delete_maintenance,
        schema=vol.Schema(
            {
                vol.Required("vehicle_id"): str,
                vol.Required("index"): int,
            }
        ),
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


def _sync_single_file(source: str, target: str) -> None:
    """Copier un fichier vers www s'il diffère (exécuté hors boucle)."""
    if not os.path.isfile(source):
        return
    target_dir = os.path.dirname(target)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
    if os.path.isfile(target):
        with open(source, "rb") as src, open(target, "rb") as dst:
            if src.read() == dst.read():
                return
    with open(source, "rb") as src:
        with open(target, "wb") as dst:
            dst.write(src.read())


def _sync_files(source_dir: str, target_dir: str, suffix: str | None = None) -> None:
    """Copier les fichiers embarqués d'un dossier vers www (hors boucle).

    Un fichier n'est réécrit que si son contenu diffère ; l'opération
    est idempotente et ne fait rien si le dossier source est absent.
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
        if os.path.isfile(target):
            with open(source, "rb") as src, open(target, "rb") as dst:
                if src.read() == dst.read():
                    continue
        with open(source, "rb") as src:
            with open(target, "wb") as dst:
                dst.write(src.read())


def _detect_invoice_ext(image_b64: str) -> str:
    """D\u00e9tecter l'extension d'une facture (jpg/png/pdf) via son contenu."""
    if image_b64.startswith("data:"):
        mime = image_b64[5:].split(";", 1)[0]
        if mime == "application/pdf":
            return "pdf"
        if mime == "image/png":
            return "png"
        return "jpg"
    try:
        payload = base64.b64decode(image_b64[:2048], validate=False)
    except Exception:
        return "jpg"
    if payload[:4] == b"%PDF":
        return "pdf"
    if payload[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return "jpg"


def _save_invoice_image(filepath: str, image_b64: str) -> None:
    """Décoder et écrire une facture (image ou PDF) sur le disque."""
    payload_b64 = image_b64
    # Retire l'éventuel préfixe data URL (data:image/xxx;base64, ou pdf)
    if payload_b64.startswith("data:"):
        payload_b64 = payload_b64.split(",", 1)[1] if "," in payload_b64 else payload_b64
    try:
        payload = base64.b64decode(payload_b64)
    except Exception as err:
        raise HomeAssistantError("Fichier de facture base64 invalide") from err
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
        # Gabarit de plans demandé à la création : appliquer le modèle du type
        if entry.data.get(CONF_APPLY_TEMPLATE):
            await coordinator.async_apply_plan_template(
                vehicle_id, entry.data.get(CONF_VEHICLE_TYPE, "car")
            )
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
