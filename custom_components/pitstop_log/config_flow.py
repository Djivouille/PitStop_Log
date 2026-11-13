"""Flux de configuration de PitStop Log (ajout et édition de véhicules)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.util import slugify

from .const import (
    CONF_BRAND,
    CONF_MODEL,
    CONF_MODEL_YEAR,
    CONF_ODOMETER,
    CONF_PURCHASE_DATE,
    CONF_REGISTRATION,
    CONF_VEHICLE_NAME,
    CONF_VEHICLE_TYPE,
    DOMAIN,
    VEHICLE_TYPES,
)
from .coordinator import PitStopDataUpdateCoordinator

# Schéma du formulaire de création/modification d'un véhicule
VEHICLE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VEHICLE_NAME): str,
        vol.Required(CONF_VEHICLE_TYPE, default="car"): vol.In(VEHICLE_TYPES),
        vol.Required(CONF_BRAND): str,
        vol.Required(CONF_MODEL): str,
        vol.Optional(CONF_MODEL_YEAR): int,
        vol.Optional(CONF_PURCHASE_DATE): str,
        vol.Optional(CONF_REGISTRATION): str,
        vol.Required(CONF_ODOMETER, default=0): int,
    }
)


class PitStopLogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration pour ajouter un véhicule."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape initiale : formulaire de saisie des métadonnées du véhicule."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Vérifie que le nom du véhicule n'est pas déjà utilisé
            coordinator: PitStopDataUpdateCoordinator = self.hass.data[DOMAIN][
                "coordinator"
            ]
            existing = coordinator.find_vehicle_id(user_input[CONF_VEHICLE_NAME])
            if existing is not None:
                errors[CONF_VEHICLE_NAME] = "name_already_used"
            elif user_input.get(CONF_PURCHASE_DATE):
                # Validation simple de la date d'achat (AAAA-MM-JJ)
                try:
                    from datetime import datetime

                    datetime.strptime(
                        user_input[CONF_PURCHASE_DATE], "%Y-%m-%d"
                    )
                except ValueError:
                    errors[CONF_PURCHASE_DATE] = "invalid_date"
            if not errors:
                # Identifiant interne stable basé sur le nom du véhicule
                vehicle_id = slugify(user_input[CONF_VEHICLE_NAME])
                return self.async_create_entry(
                    title=user_input[CONF_VEHICLE_NAME],
                    data={"vehicle_id": vehicle_id, **user_input},
                )

        return self.async_show_form(
            step_id="user", data_schema=VEHICLE_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_supported_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PitStopLogOptionsFlow:
        """Retourner le flux d'options pour éditer un véhicule existant."""
        return PitStopLogOptionsFlow(config_entry)


class PitStopLogOptionsFlow(config_entries.OptionsFlow):
    """Flux d'options pour modifier les informations d'un véhicule."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Conserver l'entrée de configuration associée."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Présenter le formulaire pré-rempli et enregistrer les modifications."""
        errors: dict[str, str] = {}
        if user_input is not None:
            coordinator: PitStopDataUpdateCoordinator = self.hass.data[DOMAIN][
                "coordinator"
            ]
            vehicle_id = self.config_entry.data["vehicle_id"]
            if user_input.get(CONF_PURCHASE_DATE):
                try:
                    from datetime import datetime

                    datetime.strptime(
                        user_input[CONF_PURCHASE_DATE], "%Y-%m-%d"
                    )
                except ValueError:
                    errors[CONF_PURCHASE_DATE] = "invalid_date"
            if not errors:
                # Mise à jour des données persistées du véhicule
                coordinator.set_vehicle(vehicle_id, user_input)
                await coordinator.async_save()
                await coordinator.async_refresh()
                self.hass.async_create_task(
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={"vehicle_id": vehicle_id, **user_input},
                    )
                )
                return self.async_create_entry(title="", data={})

        # Pré-remplissage avec les valeurs actuelles du véhicule
        defaults = dict(self.config_entry.data)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VEHICLE_NAME, default=defaults.get(CONF_VEHICLE_NAME)
                ): str,
                vol.Required(
                    CONF_VEHICLE_TYPE, default=defaults.get(CONF_VEHICLE_TYPE, "car")
                ): vol.In(VEHICLE_TYPES),
                vol.Required(CONF_BRAND, default=defaults.get(CONF_BRAND, "")): str,
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
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
