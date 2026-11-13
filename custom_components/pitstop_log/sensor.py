"""Capteurs PitStop Log : kilométrage et suivi des entretiens par véhicule."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    STATUS_DUE_SOON,
    STATUS_OK,
    STATUS_OVERDUE,
    TRANSLATION_KEY_MAINTENANCE_STATUS,
)
from .coordinator import PitStopDataUpdateCoordinator

# Priorité d'affichage des statuts (le plus urgent remonte en tête)
_STATUS_PRIORITY = {STATUS_OVERDUE: 0, STATUS_DUE_SOON: 1, STATUS_OK: 2}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créer les capteurs pour le véhicule de cette entrée de configuration."""
    coordinator: PitStopDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    vehicle_id = entry.data["vehicle_id"]
    vehicle = coordinator.get_vehicle(vehicle_id)
    if vehicle is None:
        return
    entities: list[SensorEntity] = [
        PitStopOdometerSensor(coordinator, entry, vehicle_id),
        PitStopNextMaintenanceSensor(coordinator, entry, vehicle_id),
    ]
    for plan_id, _plan in coordinator.get_plans(vehicle_id):
        entities.append(
            PitStopMaintenancePlanSensor(coordinator, entry, vehicle_id, plan_id)
        )
    async_add_entities(entities)


class PitStopEntity(SensorEntity):
    """Entité de base partageant le coordinateur et le véhicule."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PitStopDataUpdateCoordinator,
        entry: ConfigEntry,
        vehicle_id: str,
    ) -> None:
        """Initialiser l'entité et son appareil associé."""
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
        # Abonnement aux mises à jour du coordinateur pour rafraîchir l'état
        coordinator.add_listener(self._handle_coordinator_update)

    @property
    def available(self) -> bool:
        """L'entité est disponible si le véhicule existe toujours."""
        return self.coordinator.get_vehicle(self.vehicle_id) is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Rafraîchir l'état quand les données du coordinateur changent."""
        self.async_write_ha_state()


class PitStopOdometerSensor(PitStopEntity):
    """Capteur du kilométrage actuel du véhicule."""

    _attr_key = "odometer"
    _attr_translation_key = "odometer"
    _attr_native_unit_of_measurement = "km"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    @property
    def native_value(self) -> StateType:
        """Retourner le kilométrage actuel."""
        vehicle = self.coordinator.get_vehicle(self.vehicle_id)
        if vehicle is None:
            return None
        return vehicle.get("odometer")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributs : date de dernière mise à jour du kilométrage."""
        vehicle = self.coordinator.get_vehicle(self.vehicle_id) or {}
        return {
            "updated_at": vehicle.get("odometer_updated_at"),
        }


class PitStopNextMaintenanceSensor(PitStopEntity):
    """Capteur du prochain entretien prévu (statut le plus urgent)."""

    _attr_key = "next_maintenance"
    _attr_translation_key = "next_maintenance"
    _attr_icon = "mdi:wrench-clock"

    @property
    def native_value(self) -> StateType:
        """Statut d'entretien le plus urgent (jeton traduit dans l'interface)."""
        plans = self.coordinator.get_plans(self.vehicle_id)
        if not plans:
            return STATUS_OK
        infos = [
            (self.coordinator.get_due_info(plan), plan)
            for _, plan in plans
        ]
        infos.sort(
            key=lambda item: _STATUS_PRIORITY.get(item[0]["status"], 9)
        )
        return infos[0][0]["status"]

    def __init__(
        self,
        coordinator: PitStopDataUpdateCoordinator,
        entry: ConfigEntry,
        vehicle_id: str,
    ) -> None:
        """Initialiser et s'abonner aux mises à jour du coordinateur."""
        super().__init__(coordinator, entry, vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributs détaillés : plans, historique et factures associées."""
        plans_attr: list[dict[str, Any]] = []
        for plan_id, plan in self.coordinator.get_plans(self.vehicle_id):
            info = self.coordinator.get_due_info(plan)
            plans_attr.append(
                {
                    "plan_id": plan_id,
                    "name": plan.get("name"),
                    "interval_km": plan.get("interval_km"),
                    "interval_months": plan.get("interval_months"),
                    **info,
                }
            )
        history_attr: list[dict[str, Any]] = []
        for entry_data in self.coordinator.get_history(self.vehicle_id):
            history_attr.append(
                {
                    "date": entry_data.get("date"),
                    "km": entry_data.get("km"),
                    "actions": entry_data.get("actions"),
                    "cost": entry_data.get("cost"),
                    "invoice_url": entry_data.get("invoice_url"),
                }
            )
        vehicle = self.coordinator.get_vehicle(self.vehicle_id) or {}
        return {
            "vehicle": vehicle.get("name"),
            "brand": vehicle.get("brand"),
            "brand_logo": vehicle.get("brand_logo"),
            "photo": vehicle.get("photo"),
            "registration": vehicle.get("registration"),
            "plans": plans_attr,
            "history": history_attr,
            "history_count": len(history_attr),
        }


class PitStopMaintenancePlanSensor(PitStopEntity):
    """Capteur de statut pour un plan d'entretien donné."""

    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        coordinator: PitStopDataUpdateCoordinator,
        entry: ConfigEntry,
        vehicle_id: str,
        plan_id: str,
    ) -> None:
        """Initialiser le capteur lié à un plan d'entretien précis."""
        self.plan_id = plan_id
        plan = coordinator.data["plans"].get(plan_id, {})
        self._attr_key = f"plan_{plan_id}"
        # Nom et état traduits via translation_key + paramètres de traduction
        self._attr_translation_key = TRANSLATION_KEY_MAINTENANCE_STATUS
        self._attr_translation_placeholders = {
            "plan_name": plan.get("name", plan_id)
        }
        super().__init__(coordinator, entry, vehicle_id)

    @property
    def native_value(self) -> StateType:
        """Statut du plan (jeton traduit dans l'interface)."""
        plan = self.coordinator.data["plans"].get(self.plan_id)
        if plan is None:
            return None
        return self.coordinator.get_due_info(plan)["status"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributs de calcul : reste à faire en km et en jours."""
        plan = self.coordinator.data["plans"].get(self.plan_id)
        if plan is None:
            return {}
        return self.coordinator.get_due_info(plan)
