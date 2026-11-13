"""Flux de configuration de PitStop Log (ajout et édition de véhicules)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.util import slugify

from .const import (
    BRAND_NAMES,
    CONF_ACTIONS,
    CONF_BRAND,
    CONF_COST,
    CONF_DATE,
    CONF_INVOICE_PATH,
    CONF_INTERVAL_KM,
    CONF_INTERVAL_MONTHS,
    CONF_KM,
    CONF_LAST_DATE,
    CONF_LAST_KM,
    CONF_MODEL,
    CONF_MODEL_YEAR,
    CONF_ODOMETER,
    CONF_PHOTO,
    CONF_PLAN_NAME,
    CONF_PURCHASE_DATE,
    CONF_REGISTRATION,
    CONF_VEHICLE_NAME,
    CONF_VEHICLE_TYPE,
    DOMAIN,
    VEHICLE_TYPE_LABELS,
    brand_logo,
    brands_for_type,
)
from .coordinator import async_get_or_create_coordinator

# Schéma de la première étape : choix du type de véhicule
VEHICLE_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VEHICLE_TYPE, default="car"): vol.In(
            VEHICLE_TYPE_LABELS
        ),
    }
)


def vehicle_details_schema(brands: list[str]) -> vol.Schema:
    """Schéma de la seconde étape : marque (filtrée) puis détails du véhicule."""
    return vol.Schema(
        {
            vol.Required(CONF_VEHICLE_NAME): str,
            vol.Required(CONF_BRAND): vol.In(brands),
            vol.Required(CONF_MODEL): str,
            vol.Optional(CONF_MODEL_YEAR): int,
            vol.Optional(CONF_PURCHASE_DATE): str,
            vol.Optional(CONF_REGISTRATION): str,
            vol.Required(CONF_ODOMETER, default=0): int,
            vol.Optional(CONF_PHOTO): str,
        }
    )

# Schéma d'ajout d'un plan d'entretien depuis l'interface
PLAN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLAN_NAME): str,
        vol.Optional(CONF_INTERVAL_KM): int,
        vol.Optional(CONF_INTERVAL_MONTHS): int,
        vol.Optional(CONF_LAST_KM): int,
        vol.Optional(CONF_LAST_DATE): str,
    }
)

# Schéma d'édition d'une entrée d'historique depuis l'interface
HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DATE): str,
        vol.Required(CONF_KM): int,
        vol.Required(CONF_ACTIONS): str,
        vol.Optional(CONF_COST): vol.Coerce(float),
        vol.Optional(CONF_INVOICE_PATH): str,
        vol.Optional("delete"): bool,
    }
)


def _validate_date(value: str | None) -> str | None:
    """Valider une date au format AAAA-MM-JJ, retourne un code d'erreur ou None."""
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return "invalid_date"
    return None


class PitStopLogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration pour ajouter un véhicule."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialiser le flux et l'état de navigation."""
        super().__init__()
        self._vehicle_type: str = "car"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Première étape : choix du type de véhicule."""
        if user_input is not None:
            self._vehicle_type = user_input[CONF_VEHICLE_TYPE]
            return await self.async_step_vehicle_details()
        return self.async_show_form(
            step_id="user", data_schema=VEHICLE_TYPE_SCHEMA
        )

    async def async_step_vehicle_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Seconde étape : marque (filtrée par type) et détails du véhicule."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Vérifie que le nom du véhicule n'est pas déjà utilisé
            coordinator = await async_get_or_create_coordinator(self.hass)
            existing = coordinator.find_vehicle_id(user_input[CONF_VEHICLE_NAME])
            if existing is not None:
                errors[CONF_VEHICLE_NAME] = "name_already_used"
            else:
                error = _validate_date(user_input.get(CONF_PURCHASE_DATE))
                if error:
                    errors[CONF_PURCHASE_DATE] = error
            if not errors:
                # Identifiant interne stable basé sur le nom du véhicule
                vehicle_id = slugify(user_input[CONF_VEHICLE_NAME])
                return self.async_create_entry(
                    title=user_input[CONF_VEHICLE_NAME],
                    data={
                        "vehicle_id": vehicle_id,
                        CONF_VEHICLE_TYPE: self._vehicle_type,
                        **user_input,
                    },
                )

        return self.async_show_form(
            step_id="vehicle_details",
            data_schema=vehicle_details_schema(
                brands_for_type(self._vehicle_type)
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_supported_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PitStopLogOptionsFlow:
        """Retourner le flux d'options pour gérer le véhicule et ses entretiens."""
        return PitStopLogOptionsFlow(config_entry)


class PitStopLogOptionsFlow(config_entries.OptionsFlow):
    """Flux d'options : édition du véhicule, des plans et de l'historique."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Conserver l'entrée de configuration et l'état de navigation."""
        self.config_entry = config_entry
        self._plan_id: str | None = None
        self._history_index: int | None = None
        self._vehicle_type: str | None = None

    @property
    def _vehicle_id(self) -> str:
        """Identifiant du véhicule géré par ce flux d'options."""
        return self.config_entry.data["vehicle_id"]

    async def _async_save(self) -> None:
        """Sauvegarder les données et rafraîchir les capteurs."""
        coordinator = await async_get_or_create_coordinator(self.hass)
        await coordinator.async_save()
        await coordinator.async_refresh()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menu principal : véhicule, plans d'entretien ou historique."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["vehicle", "plans", "history", "done"],
        )

    async def async_step_done(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Terminer le flux d'options."""
        return self.async_create_entry(title="", data={})

    # ------------------------------------------------------------------
    # Édition du véhicule
    # ------------------------------------------------------------------
    async def async_step_vehicle(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Première étape de modification : choix du type du véhicule."""
        defaults = dict(self.config_entry.data)
        if user_input is not None:
            self._vehicle_type = user_input[CONF_VEHICLE_TYPE]
            return await self.async_step_vehicle_details()
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VEHICLE_TYPE,
                    default=defaults.get(CONF_VEHICLE_TYPE, "car"),
                ): vol.In(VEHICLE_TYPE_LABELS),
            }
        )
        return self.async_show_form(step_id="vehicle", data_schema=schema)

    async def async_step_vehicle_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Seconde étape : marque (filtrée par type) et détails du véhicule."""
        errors: dict[str, str] = {}
        coordinator = await async_get_or_create_coordinator(self.hass)
        defaults = dict(self.config_entry.data)
        if self._vehicle_type is None:
            self._vehicle_type = defaults.get(CONF_VEHICLE_TYPE, "car")
        if user_input is not None:
            error = _validate_date(user_input.get(CONF_PURCHASE_DATE))
            if error:
                errors[CONF_PURCHASE_DATE] = error
            if not errors:
                # Mise à jour des données persistées du véhicule (modèle normalisé)
                coordinator.set_vehicle(
                    self._vehicle_id,
                    {
                        "name": user_input[CONF_VEHICLE_NAME],
                        "type": self._vehicle_type,
                        "brand": user_input.get(CONF_BRAND, ""),
                        "model": user_input.get(CONF_MODEL, ""),
                        "model_year": user_input.get(CONF_MODEL_YEAR),
                        "purchase_date": user_input.get(CONF_PURCHASE_DATE),
                        "registration": user_input.get(CONF_REGISTRATION, ""),
                        "odometer": user_input.get(CONF_ODOMETER, 0),
                        "photo": user_input.get(CONF_PHOTO, ""),
                        "brand_logo": brand_logo(user_input.get(CONF_BRAND, "")),
                    },
                )
                await self._async_save()
                self.hass.async_create_task(
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={
                            "vehicle_id": self._vehicle_id,
                            CONF_VEHICLE_TYPE: self._vehicle_type,
                            **user_input,
                        },
                    )
                )
                return await self.async_step_init()

        # Marques filtrées selon le type choisi + valeurs actuelles
        brands = brands_for_type(self._vehicle_type)
        current_brand = defaults.get(CONF_BRAND, brands[0])
        if current_brand not in brands:
            brands.insert(0, current_brand)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VEHICLE_NAME, default=defaults.get(CONF_VEHICLE_NAME)
                ): str,
                vol.Required(CONF_BRAND, default=current_brand): vol.In(brands),
                vol.Required(CONF_MODEL, default=defaults.get(CONF_MODEL, "")): str,
                vol.Optional(
                    CONF_MODEL_YEAR, default=defaults.get(CONF_MODEL_YEAR)
                ): int,
                vol.Optional(
                    CONF_PURCHASE_DATE, default=defaults.get(CONF_PURCHASE_DATE, "")
                ): str,
                vol.Optional(
                    CONF_REGISTRATION,
                    default=defaults.get(CONF_REGISTRATION, ""),
                ): str,
                vol.Required(
                    CONF_ODOMETER, default=defaults.get(CONF_ODOMETER, 0)
                ): int,
                vol.Optional(
                    CONF_PHOTO, default=defaults.get(CONF_PHOTO, "")
                ): str,
            }
        )
        return self.async_show_form(
            step_id="vehicle_details", data_schema=schema, errors=errors
        )

    # ------------------------------------------------------------------
    # Plans d'entretien
    # ------------------------------------------------------------------
    async def async_step_plans(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Sélectionner un plan d'entretien à modifier, ou en ajouter un."""
        coordinator = await async_get_or_create_coordinator(self.hass)
        plans = coordinator.get_plans(self._vehicle_id)
        choices: dict[str, str] = {
            plan_id: plan.get("name", plan_id) for plan_id, plan in plans
        }
        choices["__add__"] = "➕ Ajouter un plan d'entretien"
        choices["__back__"] = "↩️ Retour"
        if user_input is not None:
            choice = user_input["choice"]
            if choice == "__add__":
                return await self.async_step_add_plan()
            if choice == "__back__":
                return await self.async_step_init()
            if choice in coordinator.data["plans"]:
                self._plan_id = choice
                return await self.async_step_plan()
        schema = vol.Schema({vol.Required("choice"): vol.In(choices)})
        return self.async_show_form(step_id="plans", data_schema=schema)

    async def async_step_add_plan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ajouter un plan d'entretien périodique."""
        errors: dict[str, str] = {}
        coordinator = await async_get_or_create_coordinator(self.hass)
        if user_input is not None:
            if not user_input.get(CONF_INTERVAL_KM) and not user_input.get(
                CONF_INTERVAL_MONTHS
            ):
                errors["base"] = "interval_required"
            else:
                error = _validate_date(user_input.get(CONF_LAST_DATE))
                if error:
                    errors[CONF_LAST_DATE] = error
            if not errors:
                await coordinator.async_add_maintenance_plan(
                    vehicle_id=self._vehicle_id,
                    name=user_input[CONF_PLAN_NAME],
                    interval_km=user_input.get(CONF_INTERVAL_KM),
                    interval_months=user_input.get(CONF_INTERVAL_MONTHS),
                    last_km=user_input.get(CONF_LAST_KM),
                    last_date=user_input.get(CONF_LAST_DATE),
                )
                return await self.async_step_plans()
        return self.async_show_form(
            step_id="add_plan", data_schema=PLAN_SCHEMA, errors=errors
        )

    async def async_step_plan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifier ou supprimer un plan d'entretien existant."""
        errors: dict[str, str] = {}
        coordinator = await async_get_or_create_coordinator(self.hass)
        plan_id = self._plan_id or ""
        plan = coordinator.data["plans"].get(plan_id)
        if plan is None:
            return await self.async_step_plans()
        if user_input is not None:
            if user_input.get("delete"):
                coordinator.delete_plan(plan_id)
                await self._async_save()
                return await self.async_step_plans()
            if not user_input.get(CONF_INTERVAL_KM) and not user_input.get(
                CONF_INTERVAL_MONTHS
            ):
                errors["base"] = "interval_required"
            else:
                error = _validate_date(user_input.get(CONF_LAST_DATE))
                if error:
                    errors[CONF_LAST_DATE] = error
            if not errors:
                coordinator.set_plan(
                    plan_id,
                    {
                        **plan,
                        "name": user_input[CONF_PLAN_NAME],
                        "interval_km": user_input.get(CONF_INTERVAL_KM),
                        "interval_months": user_input.get(CONF_INTERVAL_MONTHS),
                        "last_km": user_input.get(CONF_LAST_KM),
                        "last_date": user_input.get(CONF_LAST_DATE),
                    },
                )
                await self._async_save()
                return await self.async_step_plans()

        schema = vol.Schema(
            {
                vol.Required(CONF_PLAN_NAME, default=plan.get("name", "")): str,
                vol.Optional(
                    CONF_INTERVAL_KM, default=plan.get("interval_km")
                ): int,
                vol.Optional(
                    CONF_INTERVAL_MONTHS, default=plan.get("interval_months")
                ): int,
                vol.Optional(CONF_LAST_KM, default=plan.get("last_km")): int,
                vol.Optional(
                    CONF_LAST_DATE, default=plan.get("last_date", "")
                ): str,
                vol.Optional("delete", default=False): bool,
            }
        )
        return self.async_show_form(step_id="plan", data_schema=schema, errors=errors)

    # ------------------------------------------------------------------
    # Historique des entretiens
    # ------------------------------------------------------------------
    async def async_step_history(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Sélectionner une entrée d'historique à modifier."""
        coordinator = await async_get_or_create_coordinator(self.hass)
        entries = coordinator.get_history(self._vehicle_id)
        choices: dict[str, str] = {
            str(index): (
                f"{entry.get('date', '?')} — {entry.get('km', '?')} km — "
                f"{(entry.get('actions', '') or '')[:40]}"
            )
            for index, entry in enumerate(entries)
        }
        choices["__back__"] = "↩️ Retour"
        if user_input is not None:
            choice = user_input["choice"]
            if choice == "__back__":
                return await self.async_step_init()
            if choice.isdigit() and int(choice) < len(entries):
                self._history_index = int(choice)
                return await self.async_step_history_entry()
        schema = vol.Schema({vol.Required("choice"): vol.In(choices)})
        return self.async_show_form(step_id="history", data_schema=schema)

    async def async_step_history_entry(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifier ou supprimer une entrée de l'historique."""
        errors: dict[str, str] = {}
        coordinator = await async_get_or_create_coordinator(self.hass)
        index = self._history_index if self._history_index is not None else -1
        entry = coordinator.get_history_entry(self._vehicle_id, index)
        if entry is None:
            return await self.async_step_history()
        if user_input is not None:
            error = _validate_date(user_input.get(CONF_DATE))
            if error:
                errors[CONF_DATE] = error
            if not errors:
                if user_input.get("delete"):
                    coordinator.delete_history_entry(self._vehicle_id, index)
                else:
                    coordinator.update_history_entry(
                        self._vehicle_id,
                        index,
                        {
                            "vehicle_id": self._vehicle_id,
                            "date": user_input[CONF_DATE],
                            "km": user_input[CONF_KM],
                            "actions": user_input[CONF_ACTIONS],
                            "cost": user_input.get(CONF_COST),
                            "invoice_url": user_input.get(CONF_INVOICE_PATH),
                            "created_at": entry.get("created_at"),
                        },
                    )
                await self._async_save()
                return await self.async_step_history()

        schema = vol.Schema(
            {
                vol.Required(CONF_DATE, default=entry.get("date", "")): str,
                vol.Required(CONF_KM, default=entry.get("km", 0)): int,
                vol.Required(CONF_ACTIONS, default=entry.get("actions", "")): str,
                vol.Optional(
                    CONF_COST, default=entry.get("cost")
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_INVOICE_PATH, default=entry.get("invoice_url", "")
                ): str,
                vol.Optional("delete", default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="history_entry", data_schema=schema, errors=errors
        )
