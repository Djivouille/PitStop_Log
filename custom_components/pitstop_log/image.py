"""Entités image PitStop Log : logo de marque et photo du véhicule.

Ces entités sont rattachées à l'appareil du véhicule et s'affichent
sur sa page dans l'interface (Informations sur l'appareil).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BRANDS_URL_PREFIX, DOMAIN, PHOTOS_URL_PREFIX
from .coordinator import PitStopDataUpdateCoordinator

# Types MIME selon l'extension du fichier
_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


def _local_url_to_path(hass: HomeAssistant, url: str | None) -> str | None:
    """Convertir une URL locale /local/... en chemin de fichier sûr."""
    if not url or not url.startswith("/local/"):
        return None
    # Basename seul : impossible de remonter dans l'arborescence
    filename = os.path.basename(url)
    if url.startswith(PHOTOS_URL_PREFIX):
        return os.path.join(hass.config.path(), "www/pitstop_log/photos", filename)
    if url.startswith(BRANDS_URL_PREFIX):
        return os.path.join(hass.config.path(), "www/pitstop_log/brands", filename)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créer les entités image du véhicule de cette entrée."""
    coordinator: PitStopDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    vehicle_id = entry.data["vehicle_id"]
    vehicle = coordinator.get_vehicle(vehicle_id)
    if vehicle is None:
        return
    entities: list[ImageEntity] = [PitStopVehiclePhoto(coordinator, entry, vehicle_id)]
    if vehicle.get("brand_logo"):
        entities.append(PitStopBrandLogo(coordinator, entry, vehicle_id))
    async_add_entities(entities)


class PitStopImageEntity(ImageEntity):
    """Entité image de base : fichier local servi en octets."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PitStopDataUpdateCoordinator,
        entry: ConfigEntry,
        vehicle_id: str,
    ) -> None:
        """Initialiser l'entité et l'appareil associé."""
        self.coordinator = coordinator
        self.vehicle_id = vehicle_id
        vehicle = coordinator.get_vehicle(vehicle_id) or {}
        self._attr_unique_id = f"{vehicle_id}_{self._attr_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vehicle_id)},
            "name": vehicle.get("name", vehicle_id),
            "manufacturer": vehicle.get("brand", ""),
            "model": vehicle.get("model", ""),
        }
        self._attr_image_last_updated = datetime.now(timezone.utc)
        coordinator.add_listener(self._handle_coordinator_update)

    @property
    def available(self) -> bool:
        """L'entité est disponible si le véhicule existe toujours."""
        return self.coordinator.get_vehicle(self.vehicle_id) is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Rafraîchir l'image quand les données du véhicule changent."""
        self._attr_image_last_updated = datetime.now(timezone.utc)
        self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        """Retourner le contenu de l'image depuis le disque."""
        vehicle = self.coordinator.get_vehicle(self.vehicle_id)
        if vehicle is None:
            return None
        path = _local_url_to_path(self.hass, vehicle.get(self._url_field))
        if not path or not os.path.exists(path):
            return None
        ext = os.path.splitext(path)[1].lower()
        self._attr_content_type = _CONTENT_TYPES.get(ext, "image/jpeg")
        return await self.hass.async_add_executor_job(self._read_file, path)

    @staticmethod
    def _read_file(path: str) -> bytes:
        """Lire un fichier binaire (exécuté hors boucle d'événements)."""
        with open(path, "rb") as file:
            return file.read()


class PitStopVehiclePhoto(PitStopImageEntity):
    """Photo du véhicule."""

    _attr_key = "photo"
    _attr_translation_key = "vehicle_photo"
    _url_field = "photo"


class PitStopBrandLogo(PitStopImageEntity):
    """Logo de la marque du véhicule."""

    _attr_key = "brand_logo"
    _attr_translation_key = "brand_logo"
    _url_field = "brand_logo"
