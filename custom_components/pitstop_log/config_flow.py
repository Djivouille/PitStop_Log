"""Flux de configuration de PitStop Log (ajout et édition de véhicules)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    FileSelector,
    FileSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util import slugify

from .const import (
    BRAND_NAMES,
    CONF_ACTIONS,
    CONF_APPLY_TEMPLATE,
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
    CONF_TEMPLATE_PLANS,
    CONF_REGISTRATION,
    CONF_VEHICLE_NAME,
    CONF_VEHICLE_TYPE,
    BRANDS,
    DOMAIN,
    VEHICLE_TYPE_LABELS,
    brand_logo,
    brands_for_type,
    REMINDER_DEFAULTS,
    plan_display_name,
    plan_template_for_type,
)
from .coordinator import (
    async_get_or_create_coordinator,
    async_save_uploaded_photo,
)


def dropdown_selector(options: list[dict[str, str]]) -> SelectSelector:
    """Construire un sélecteur déroulant (jamais de boutons radio)."""
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def vehicle_type_options() -> list[dict[str, str]]:
    """Options du sélecteur de type de véhicule."""
    return [
        {"value": value, "label": label}
        for value, label in VEHICLE_TYPE_LABELS.items()
    ]


def brand_options(brands: list[str]) -> list[dict[str, str]]:
    """Options du sélecteur de marque (libellés issus de brands.json)."""
    return [
        {"value": name, "label": BRANDS.get(name, {}).get("label", name)}
        for name in brands
    ]


def vehicle_details_schema(current_photo: str | None = None) -> vol.Schema:
    """Schéma de l'étape 2 : le reste des informations du véhicule."""
    return vol.Schema(
        {
            vol.Required(CONF_VEHICLE_NAME): str,
            vol.Optional(CONF_MODEL_YEAR): int,
            vol.Optional(CONF_PURCHASE_DATE): str,
            vol.Optional(CONF_REGISTRATION): str,
            vol.Required(CONF_ODOMETER, default=0): int,
            vol.Optional(CONF_PHOTO): FileSelector(
                FileSelectorConfig(accept="image/*")
            ),
        }
    )


# Schéma de la première étape : choix du type de véhicule (menu déroulant)
VEHICLE_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VEHICLE_TYPE, default="car"): dropdown_selector(
            vehicle_type_options()
        ),
    }
)




# Schéma de l'étape d'application du gabarit (flux d'options, défaut : non)
APPLY_TEMPLATE_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_APPLY_TEMPLATE, default=False): bool,
    }
)


def template_plan_fields(vehicle_type: str) -> list[tuple[str, dict[str, Any]]]:
    """Liste (préfixe de champs, plan) pour chaque plan du gabarit du type.

    Le préfixe est dérivé du nom du plan (ex. « tpl_vidange ») pour que les
    libellés affichés soient parlants ; un suffixe _N est ajouté en cas de
    collision.
    """
    template = plan_template_for_type(vehicle_type)
    fields: list[tuple[str, dict[str, Any]]] = []
    used: set[str] = set()
    for tpl in template.get("plans", []):
        base = f"tpl_{slugify(tpl.get('name', ''))}"
        prefix = base
        index = 2
        while prefix in used:
            prefix = f"{base}_{index}"
            index += 1
        used.add(prefix)
        fields.append((prefix, tpl))
    return fields


# Emplacements « plan personnalisé » ajoutables dans le formulaire gabarit
EXTRA_TEMPLATE_SLOTS = 3


def template_form_fields(vehicle_type: str) -> list[tuple[str, dict[str, Any], bool]]:
    """Blocs de champs du formulaire gabarit : gabarit + plans personnalisés.

    Retourne (préfixe, plan, activé_par_défaut) pour chaque bloc. Les plans
    du gabarit sont activés par défaut ; les emplacements personnalisés
    (tpl_custom_N, vides) sont désactivés par défaut.
    """
    fields: list[tuple[str, dict[str, Any], bool]] = [
        (prefix, tpl, True) for prefix, tpl in template_plan_fields(vehicle_type)
    ]
    for index in range(EXTRA_TEMPLATE_SLOTS):
        fields.append(
            (
                f"tpl_custom_{index}",
                {"name": "", "interval_km": None, "interval_months": None},
                False,
            )
        )
    return fields


def apply_template_schema(vehicle_type: str) -> vol.Schema:
    """Schéma de l'étape gabarit : un bloc de champs éditables par plan.

    Le nom reste en Optional (avec défaut) : un plan non coché peut avoir un
    nom vide sans bloquer le formulaire ; la validation métier (nom requis si
    le plan est inclus) est faite dans template_plans_from_input().
    """
    schema: dict[Any, Any] = {}
    for prefix, tpl, enabled in template_form_fields(vehicle_type):
        schema[vol.Optional(f"{prefix}_enabled", default=enabled)] = bool
        schema[vol.Optional(f"{prefix}_name", default=tpl.get("name", ""))] = str
        if tpl.get("interval_km"):
            schema[vol.Optional(f"{prefix}_interval_km", default=tpl["interval_km"])] = int
        else:
            schema[vol.Optional(f"{prefix}_interval_km")] = int
        if tpl.get("interval_months"):
            schema[vol.Optional(f"{prefix}_interval_months", default=tpl["interval_months"])] = int
        else:
            schema[vol.Optional(f"{prefix}_interval_months")] = int
    return vol.Schema(schema)


def template_description(vehicle_type: str, lang: str = "fr") -> str:
    """Tableau du gabarit + emplacements personnalisés (description de l'étape)."""
    template = plan_template_for_type(vehicle_type)
    if lang == "en":
        header = "| Nature | Interval (km) | Interval (months) |"
        custom_label = "Custom nature"
    else:
        header = "| Nature | Intervalle (km) | Intervalle (mois) |"
        custom_label = "Nature personnalisée"
    rows = [
        f"| {plan_display_name(tpl.get('name', ''), lang)} | "
        f"{tpl.get('interval_km') or '—'} | {tpl.get('interval_months') or '—'} |"
        for tpl in template.get("plans", [])
    ]
    for index in range(EXTRA_TEMPLATE_SLOTS):
        rows.append(f"| {custom_label} {index + 1} |  |  |")
    return "\n".join([header, "|---|---|---|", *rows])


def template_plans_from_input(
    user_input: dict[str, Any], vehicle_type: str
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Extraire les plans saisis (gabarit + personnalisés) ; retourne (plans, erreurs)."""
    plans: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    for prefix, tpl, enabled in template_form_fields(vehicle_type):
        if not user_input.get(f"{prefix}_enabled", enabled):
            continue
        name = (user_input.get(f"{prefix}_name") or "").strip() or tpl.get("name", "")
        interval_km = user_input.get(f"{prefix}_interval_km")
        interval_months = user_input.get(f"{prefix}_interval_months")
        if not name:
            errors[f"{prefix}_name"] = "name_required"
        if not interval_km and not interval_months:
            errors[f"{prefix}_interval_km"] = "interval_required"
        if f"{prefix}_name" in errors or f"{prefix}_interval_km" in errors:
            continue
        plans.append(
            {
                "name": name,
                "interval_km": interval_km or None,
                "interval_months": interval_months or None,
            }
        )
    return plans, errors

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
        self._vehicle_brand: str = ""
        self._vehicle_model: str = ""
        self._pending_vehicle: tuple[str, dict[str, Any], str] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1a : choix du type de véhicule (menu déroulant)."""
        if user_input is not None:
            self._vehicle_type = user_input[CONF_VEHICLE_TYPE]
            return await self.async_step_vehicle_brand()
        return self.async_show_form(
            step_id="user", data_schema=VEHICLE_TYPE_SCHEMA
        )

    async def async_step_vehicle_brand(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1b : choix de la marque (menu déroulant filtré par type)."""
        if user_input is not None:
            self._vehicle_brand = user_input[CONF_BRAND]
            return await self.async_step_vehicle_model()
        schema = vol.Schema(
            {
                vol.Required(CONF_BRAND): dropdown_selector(
                    brand_options(brands_for_type(self._vehicle_type))
                ),
            }
        )
        return self.async_show_form(step_id="vehicle_brand", data_schema=schema)

    async def async_step_vehicle_model(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1c : saisie du modèle du véhicule."""
        if user_input is not None:
            self._vehicle_model = user_input[CONF_MODEL]
            return await self.async_step_vehicle_details()
        schema = vol.Schema({vol.Required(CONF_MODEL): str})
        return self.async_show_form(step_id="vehicle_model", data_schema=schema)

    async def async_step_vehicle_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 2 : le reste des informations du véhicule."""
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
                # Copie de la photo téléversée (si fournie) vers www
                photo_url = ""
                if user_input.get(CONF_PHOTO):
                    photo_url = await async_save_uploaded_photo(
                        self.hass, user_input[CONF_PHOTO], vehicle_id
                    )
                # Étape suivante : appliquer ou non le gabarit de plans
                self._pending_vehicle = (vehicle_id, dict(user_input), photo_url)
                return await self.async_step_apply_template()

        return self.async_show_form(
            step_id="vehicle_details",
            data_schema=vehicle_details_schema(),
            errors=errors,
        )

    async def async_step_apply_template(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 3 : afficher et personnaliser le gabarit de plans du type choisi."""
        errors: dict[str, str] = {}
        if user_input is not None and self._pending_vehicle is not None:
            plans, errors = template_plans_from_input(user_input, self._vehicle_type)
            if not errors:
                vehicle_id, details, photo_url = self._pending_vehicle
                return self.async_create_entry(
                    title=details[CONF_VEHICLE_NAME],
                    data={
                        "vehicle_id": vehicle_id,
                        CONF_VEHICLE_TYPE: self._vehicle_type,
                        CONF_BRAND: self._vehicle_brand,
                        CONF_MODEL: self._vehicle_model,
                        **details,
                        CONF_PHOTO: photo_url,
                        CONF_TEMPLATE_PLANS: plans,
                    },
                )
        return self.async_show_form(
            step_id="apply_template",
            data_schema=apply_template_schema(self._vehicle_type),
            description_placeholders={
                "plans": template_description(
                    self._vehicle_type,
                    getattr(self.hass.config, "language", "fr"),
                )
            },
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
        self._vehicle_brand: str | None = None
        self._vehicle_model: str | None = None

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
            menu_options=["vehicle", "plans", "templates", "reminders", "history", "done"],
        )

    async def async_step_reminders(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Seuils personnalisés du reminder (4 statuts d'entretien)."""
        if user_input is not None:
            options = dict(self.config_entry.options)
            for key in REMINDER_DEFAULTS:
                options[key] = user_input.get(key, REMINDER_DEFAULTS[key])
            return self.async_create_entry(title="", data=options)
        defaults = {**REMINDER_DEFAULTS, **dict(self.config_entry.options)}
        schema = vol.Schema(
            {
                vol.Optional(key, default=defaults[key]): int
                for key in REMINDER_DEFAULTS
            }
        )
        return self.async_show_form(step_id="reminders", data_schema=schema)

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
        """Étape 1a de modification : type du véhicule (menu déroulant)."""
        defaults = dict(self.config_entry.data)
        if user_input is not None:
            self._vehicle_type = user_input[CONF_VEHICLE_TYPE]
            return await self.async_step_vehicle_brand()
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VEHICLE_TYPE,
                    default=defaults.get(CONF_VEHICLE_TYPE, "car"),
                ): dropdown_selector(vehicle_type_options()),
            }
        )
        return self.async_show_form(step_id="vehicle", data_schema=schema)

    async def async_step_vehicle_brand(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1b : marque du véhicule (menu déroulant filtré par type)."""
        defaults = dict(self.config_entry.data)
        if self._vehicle_type is None:
            self._vehicle_type = defaults.get(CONF_VEHICLE_TYPE, "car")
        if user_input is not None:
            self._vehicle_brand = user_input[CONF_BRAND]
            return await self.async_step_vehicle_model()
        brands = brands_for_type(self._vehicle_type)
        current_brand = defaults.get(CONF_BRAND, brands[0])
        if current_brand not in brands:
            brands.insert(0, current_brand)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_BRAND, default=current_brand
                ): dropdown_selector(brand_options(brands)),
            }
        )
        return self.async_show_form(step_id="vehicle_brand", data_schema=schema)

    async def async_step_vehicle_model(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1c : modèle du véhicule."""
        defaults = dict(self.config_entry.data)
        if user_input is not None:
            self._vehicle_model = user_input[CONF_MODEL]
            return await self.async_step_vehicle_details()
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MODEL, default=defaults.get(CONF_MODEL, "")
                ): str,
            }
        )
        return self.async_show_form(step_id="vehicle_model", data_schema=schema)

    async def async_step_vehicle_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 2 : le reste des informations du véhicule."""
        errors: dict[str, str] = {}
        coordinator = await async_get_or_create_coordinator(self.hass)
        defaults = dict(self.config_entry.data)
        if self._vehicle_type is None:
            self._vehicle_type = defaults.get(CONF_VEHICLE_TYPE, "car")
        if self._vehicle_brand is None:
            self._vehicle_brand = defaults.get(CONF_BRAND, "")
        if self._vehicle_model is None:
            self._vehicle_model = defaults.get(CONF_MODEL, "")
        if user_input is not None:
            error = _validate_date(user_input.get(CONF_PURCHASE_DATE))
            if error:
                errors[CONF_PURCHASE_DATE] = error
            if not errors:
                # Copie de la nouvelle photo téléversée, sinon conservation de l'actuelle
                photo_url = defaults.get(CONF_PHOTO, "")
                if user_input.get(CONF_PHOTO):
                    photo_url = await async_save_uploaded_photo(
                        self.hass, user_input[CONF_PHOTO], self._vehicle_id
                    )
                # Mise à jour des données persistées du véhicule (modèle normalisé)
                coordinator.set_vehicle(
                    self._vehicle_id,
                    {
                        "name": user_input[CONF_VEHICLE_NAME],
                        "type": self._vehicle_type,
                        "brand": self._vehicle_brand,
                        "model": self._vehicle_model,
                        "model_year": user_input.get(CONF_MODEL_YEAR),
                        "purchase_date": user_input.get(CONF_PURCHASE_DATE),
                        "registration": user_input.get(CONF_REGISTRATION, ""),
                        "odometer": user_input.get(CONF_ODOMETER, 0),
                        "photo": photo_url,
                        "brand_logo": brand_logo(self._vehicle_brand),
                    },
                )
                await self._async_save()
                self.hass.async_create_task(
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={
                            "vehicle_id": self._vehicle_id,
                            CONF_VEHICLE_TYPE: self._vehicle_type,
                            CONF_BRAND: self._vehicle_brand,
                            CONF_MODEL: self._vehicle_model,
                            **user_input,
                            CONF_PHOTO: photo_url,
                        },
                    )
                )
                return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VEHICLE_NAME, default=defaults.get(CONF_VEHICLE_NAME)
                ): str,
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
                vol.Optional(CONF_PHOTO): FileSelector(
                    FileSelectorConfig(accept="image/*")
                ),
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
    # Gabarits de plans par type de véhicule
    # ------------------------------------------------------------------
    async def async_step_templates(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Appliquer le gabarit du type du véhicule (sans doublon de nom)."""
        coordinator = await async_get_or_create_coordinator(self.hass)
        if user_input is not None:
            if user_input.get(CONF_APPLY_TEMPLATE):
                vehicle = coordinator.get_vehicle(self._vehicle_id) or {}
                await coordinator.async_apply_plan_template(
                    self._vehicle_id, vehicle.get("type", "car")
                )
            return await self.async_step_init()
        return self.async_show_form(
            step_id="templates", data_schema=APPLY_TEMPLATE_OPTIONS_SCHEMA
        )

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
