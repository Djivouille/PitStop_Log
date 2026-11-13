"""Coordinateur central de PitStop Log.

Centralise les données persistées (véhicules, plans d'entretien, historique),
le calcul des échéances et la mise à jour des capteurs.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DUE_SOON_DAYS,
    DUE_SOON_KM_PERCENT,
    STATUS_DUE_SOON,
    STATUS_OK,
    STATUS_OVERDUE,
)

DEFAULT_SAVE_DELAY = 30  # Secondes avant écriture différée sur le disque


async def async_get_or_create_coordinator(
    hass: HomeAssistant,
) -> PitStopDataUpdateCoordinator:
    """Retourner le coordinateur, en le créant et chargeant s'il est absent.

    Garantit que le coordinateur existe même si le flux de configuration est
    démarré avant l'appel à async_setup de l'intégration.
    """
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "coordinator" not in hass.data[DOMAIN]:
        coordinator = PitStopDataUpdateCoordinator(hass)
        await coordinator.async_load()
        hass.data[DOMAIN]["coordinator"] = coordinator
    return hass.data[DOMAIN]["coordinator"]


class PitStopDataUpdateCoordinator:
    """Coordinateur de données pour PitStop Log.

    Ne dérive pas de DataUpdateCoordinator car il n'y a aucune source
    externe à interroger : les données sont locales et modifiées par
    des services. La méthode async_refresh() force simplement les
    entités à se recharger depuis les données en mémoire.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialiser le coordinateur et le stockage persistant."""
        self.hass = hass
        self.store: Store = Store(hass, 1, "pitstop_log")
        self.data: dict[str, Any] = {"vehicles": {}, "plans": {}, "history": []}
        self._listeners: list[Any] = []

    async def async_load(self) -> None:
        """Charger les données depuis le stockage persistant."""
        stored = await self.store.async_load()
        if isinstance(stored, dict):
            self.data = {
                "vehicles": stored.get("vehicles", {}),
                "plans": stored.get("plans", {}),
                "history": stored.get("history", []),
            }

    async def async_save(self) -> None:
        """Écrire les données sur le disque (écriture différée)."""
        await self.store.async_save(self.data)

    async def async_refresh(self) -> None:
        """Notifier les écouteurs (capteurs) que les données ont changé."""
        for callback in list(self._listeners):
            callback()

    def add_listener(self, callback: Any) -> None:
        """Ajouter un écouteur appelé lors d'un rafraîchissement."""
        self._listeners.append(callback)

    # ------------------------------------------------------------------
    # Véhicules
    # ------------------------------------------------------------------
    def get_vehicle(self, vehicle_id: str) -> dict[str, Any] | None:
        """Retourner un véhicule par son identifiant."""
        return self.data["vehicles"].get(vehicle_id)

    def find_vehicle_id(self, name_or_id: str) -> str | None:
        """Retrouver l'identifiant d'un véhicule par nom ou identifiant."""
        if name_or_id in self.data["vehicles"]:
            return name_or_id
        for vid, vehicle in self.data["vehicles"].items():
            if slugify(vehicle.get("name", "")) == slugify(name_or_id):
                return vid
        return None

    def set_vehicle(self, vehicle_id: str, vehicle: dict[str, Any]) -> None:
        """Créer ou mettre à jour un véhicule."""
        self.data["vehicles"][vehicle_id] = vehicle

    def delete_vehicle(self, vehicle_id: str) -> None:
        """Supprimer un véhicule, ses plans et son historique."""
        self.data["vehicles"].pop(vehicle_id, None)
        self.data["plans"] = {
            pid: plan
            for pid, plan in self.data["plans"].items()
            if plan.get("vehicle_id") != vehicle_id
        }
        self.data["history"] = [
            entry
            for entry in self.data["history"]
            if entry.get("vehicle_id") != vehicle_id
        ]

    async def async_update_odometer(self, vehicle_id: str, km: int) -> None:
        """Mettre à jour le kilométrage actuel d'un véhicule."""
        vehicle = self.get_vehicle(vehicle_id)
        if vehicle is None:
            raise HomeAssistantError(f"Véhicule inconnu : {vehicle_id}")
        if km < 0:
            raise HomeAssistantError("Le kilométrage ne peut pas être négatif")
        if km < vehicle.get("odometer", 0):
            raise HomeAssistantError(
                "Le kilométrage ne peut pas diminuer "
                f"({km} < {vehicle.get('odometer', 0)})"
            )
        vehicle["odometer"] = km
        vehicle["odometer_updated_at"] = dt_util.utcnow().isoformat()
        await self.async_save()
        await self.async_refresh()

    # ------------------------------------------------------------------
    # Plans d'entretien (entretiens à faire)
    # ------------------------------------------------------------------
    async def async_add_maintenance_plan(
        self,
        vehicle_id: str,
        name: str,
        interval_km: int | None,
        interval_months: int | None,
        last_km: int | None = None,
        last_date: str | None = None,
    ) -> str:
        """Ajouter une règle d'entretien périodique."""
        if self.get_vehicle(vehicle_id) is None:
            raise HomeAssistantError(f"Véhicule inconnu : {vehicle_id}")
        if not interval_km and not interval_months:
            raise HomeAssistantError(
                "Un intervalle en km ou en mois doit être défini"
            )
        plan_id = f"{vehicle_id}_{slugify(name)}"
        if plan_id in self.data["plans"]:
            index = 2
            while f"{plan_id}_{index}" in self.data["plans"]:
                index += 1
            plan_id = f"{plan_id}_{index}"
        self.data["plans"][plan_id] = {
            "vehicle_id": vehicle_id,
            "name": name,
            "interval_km": interval_km,
            "interval_months": interval_months,
            "last_km": last_km,
            "last_date": last_date,
            "active": True,
            "created_at": dt_util.utcnow().isoformat(),
        }
        await self.async_save()
        await self.async_refresh()
        return plan_id

    def get_plans(self, vehicle_id: str) -> list[tuple[str, dict[str, Any]]]:
        """Lister les plans d'entretien actifs d'un véhicule."""
        return [
            (plan_id, plan)
            for plan_id, plan in self.data["plans"].items()
            if plan.get("vehicle_id") == vehicle_id and plan.get("active", True)
        ]

    def set_plan(self, plan_id: str, plan: dict[str, Any]) -> None:
        """Créer ou mettre à jour un plan d'entretien en mémoire."""
        self.data["plans"][plan_id] = plan

    def delete_plan(self, plan_id: str) -> None:
        """Supprimer un plan d'entretien."""
        self.data["plans"].pop(plan_id, None)

    def get_history_entry(self, vehicle_id: str, index: int) -> dict[str, Any] | None:
        """Retourner une entrée d'historique par son index (ordre du menu)."""
        entries = self.get_history(vehicle_id)
        if 0 <= index < len(entries):
            return entries[index]
        return None

    def update_history_entry(
        self, vehicle_id: str, index: int, entry: dict[str, Any]
    ) -> bool:
        """Mettre à jour une entrée d'historique par son index."""
        target = self.get_history_entry(vehicle_id, index)
        if target is None:
            return False
        # Les entrées sont identifiées par leur date + kilométrage + actions
        for pos, stored in enumerate(self.data["history"]):
            if (
                stored.get("vehicle_id") == vehicle_id
                and stored.get("date") == target.get("date")
                and stored.get("km") == target.get("km")
                and stored.get("actions") == target.get("actions")
            ):
                self.data["history"][pos] = entry
                return True
        return False

    def delete_history_entry(self, vehicle_id: str, index: int) -> bool:
        """Supprimer une entrée d'historique par son index."""
        target = self.get_history_entry(vehicle_id, index)
        if target is None:
            return False
        for pos, stored in enumerate(self.data["history"]):
            if (
                stored.get("vehicle_id") == vehicle_id
                and stored.get("date") == target.get("date")
                and stored.get("km") == target.get("km")
                and stored.get("actions") == target.get("actions")
            ):
                del self.data["history"][pos]
                return True
        return False

    # ------------------------------------------------------------------
    # Historique (entretiens faits)
    # ------------------------------------------------------------------
    async def async_add_maintenance_done(
        self,
        vehicle_id: str,
        date: str,
        km: int,
        actions: str,
        cost: float | None = None,
        invoice_url: str | None = None,
        plan_id: str | None = None,
    ) -> None:
        """Enregistrer un entretien réalisé et mettre à jour le kilométrage."""
        vehicle = self.get_vehicle(vehicle_id)
        if vehicle is None:
            raise HomeAssistantError(f"Véhicule inconnu : {vehicle_id}")
        try:
            entry_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as err:
            raise HomeAssistantError(
                "Date invalide, format attendu AAAA-MM-JJ"
            ) from err
        if km < 0:
            raise HomeAssistantError("Le kilométrage ne peut pas être négatif")

        entry = {
            "vehicle_id": vehicle_id,
            "date": entry_date.isoformat(),
            "km": km,
            "actions": actions,
            "cost": cost,
            "invoice_url": invoice_url,
            "created_at": dt_util.utcnow().isoformat(),
        }
        self.data["history"].append(entry)

        # Mise à jour du kilométrage du véhicule si l'intervention est plus récente
        if km > vehicle.get("odometer", 0):
            vehicle["odometer"] = km
            vehicle["odometer_updated_at"] = dt_util.utcnow().isoformat()

        # Réinitialisation du plan d'entretien associé, s'il existe
        if plan_id and plan_id in self.data["plans"]:
            plan = self.data["plans"][plan_id]
            plan["last_km"] = km
            plan["last_date"] = entry_date.isoformat()

        await self.async_save()
        await self.async_refresh()

    def get_history(self, vehicle_id: str) -> list[dict[str, Any]]:
        """Retourner l'historique d'un véhicule, du plus récent au plus ancien."""
        entries = [
            entry
            for entry in self.data["history"]
            if entry.get("vehicle_id") == vehicle_id
        ]
        return sorted(entries, key=lambda e: (e.get("date", ""), e.get("km", 0)), reverse=True)

    # ------------------------------------------------------------------
    # Calcul des échéances
    # ------------------------------------------------------------------
    def get_due_info(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Calculer l'état d'un plan d'entretien.

        Retourne le statut (OK / Bientôt dû / En retard), le kilométrage
        cible, la date cible, et le reste à faire en km et en jours.
        """
        vehicle = self.get_vehicle(plan.get("vehicle_id", ""))
        odometer = vehicle.get("odometer", 0) if vehicle else 0
        interval_km = plan.get("interval_km")
        interval_months = plan.get("interval_months")
        last_km = plan.get("last_km")
        last_date_str = plan.get("last_date")

        km_remaining: int | None = None
        due_km: int | None = None
        days_remaining: int | None = None
        due_date: date | None = None
        today = dt_util.now().date()

        # Échéance basée sur le kilométrage
        if interval_km:
            base_km = last_km if last_km is not None else odometer
            due_km = base_km + interval_km
            km_remaining = due_km - odometer

        # Échéance basée sur le temps
        if interval_months:
            if last_date_str:
                base_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            else:
                base_date = today
            due_date = base_date + timedelta(days=interval_months * 30)
            days_remaining = (due_date - today).days

        # Détermination du statut d'alerte
        km_overdue = km_remaining is not None and km_remaining <= 0
        days_overdue = days_remaining is not None and days_remaining <= 0
        km_due_soon = (
            km_remaining is not None
            and interval_km is not None
            and km_remaining <= interval_km * DUE_SOON_KM_PERCENT
        )
        days_due_soon = (
            days_remaining is not None and 0 < days_remaining <= DUE_SOON_DAYS
        )

        if km_overdue or days_overdue:
            status = STATUS_OVERDUE
        elif km_due_soon or days_due_soon:
            status = STATUS_DUE_SOON
        else:
            status = STATUS_OK

        return {
            "status": status,
            "due_km": due_km,
            "due_date": due_date.isoformat() if due_date else None,
            "km_remaining": km_remaining,
            "days_remaining": days_remaining,
            "last_km": last_km,
            "last_date": last_date_str,
        }
