/**
 * \u00c9diteur visuel de la carte ${psT("editor_title")}
 * dans un menu d\u00e9roulant listant les v\u00e9hicules PitStop Log.
 */
class PitstopCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
    psLoadStrings(this._hass).then((s) => {
      if (s) this._render();
    });
  }

  /** Liste les v\u00e9hicules : nom de l'appareil (registre d'appareils HA). */
  async _vehicles() {
    if (!this._hass) return [];
    const sensors = [];
    for (const entityId in this._hass.states) {
      const state = this._hass.states[entityId];
      if (
        entityId.startsWith("sensor.") &&
        state.attributes &&
        state.attributes.vehicle !== undefined &&
        state.attributes.plans !== undefined
      ) {
        sensors.push(state);
      }
    }
    if (sensors.length === 0) return [];
    let devices = this._devices_cache;
    if (!devices) {
      try {
        devices = await this._hass.callWS({
          type: "config/device_registry/list",
        });
        this._devices_cache = devices;
      } catch (err) {
        devices = [];
      }
    }
    const labelFor = (vehicleId, fallback) => {
      const device = (devices || []).find(
        (d) =>
          Array.isArray(d.identifiers) &&
          d.identifiers.some(
            (i) => i[0] === "pitstop_log" && i[1] === vehicleId
          )
      );
      if (device) return device.name_by_user || device.name || fallback;
      return fallback;
    };
    const result = sensors.map((state) => {
      const vehicleId = state.attributes.vehicle_id;
      const fallback =
        state.attributes.vehicle || state.attributes.friendly_name;
      return {
        name: state.attributes.vehicle,
        label: vehicleId ? labelFor(vehicleId, fallback) : fallback,
      };
    });
    result.sort((a, b) => (a.label < b.label ? -1 : 1));
    return result;
  }

  _changed(config) {
    this._config = config;
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        bubbles: true,
        composed: true,
        detail: { config: config },
      })
    );
    this._render();
  }

  async _render() {
    if (!this._hass || !this._config) return;
    const root = this.shadowRoot;
    const vehicles = await this._vehicles();
    const options = vehicles
      .map(
        (v) =>
          `<option value="${v.name}"${v.name === this._config.vehicle ? " selected" : ""}>${v.label}</option>`
      )
      .join("");
    if (!options) {
      root.innerHTML =
        "<div>" + psT("no_vehicle") + "</div>";
      return;
    }
    root.innerHTML = `
      <style>
        .wrapper { display: flex; flex-direction: column; gap: 16px; padding: 4px 0; }
        label { display: block; font-weight: 500; margin-bottom: 4px; }
        select, input { width: 100%; font-size: 14px; padding: 8px 10px; border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; background: var(--card-background-color, #fff); color: var(--primary-text-color); box-sizing: border-box; }
      </style>
      <div class="wrapper">
        <div>
          <label>V\u00e9hicule</label>
          <select id="ps-vehicle">${options}</select>
        </div>
        <div>
          <label>${psT("title_optional")}</label>
          <input id="ps-title" type="text" value="${(this._config.title || "").replace(/"/g, "&quot;")}" placeholder="${psT("title_hint")}" />
        </div>
      </div>`;
    root.querySelector("#ps-vehicle").addEventListener("change", (ev) => {
      this._changed({ ...this._config, vehicle: ev.target.value });
    });
    root.querySelector("#ps-title").addEventListener("change", (ev) => {
      this._changed({ ...this._config, title: ev.target.value });
    });
  }
}

/**
 * PitStop Log \u2014 carte Lovelace de l'int\u00e9gration PitStop Log.
 *
 * Affiche toutes les informations d'un v\u00e9hicule : photo, logo de marque,
 * kilom\u00e9trage, statut d'entretien, natures \u00e0 faire, historique et graphique
 * du kilom\u00e9trage. L'ic\u00f4ne roue crant\u00e9e ouvre une page d'\u00e9dition du
 * kilom\u00e9trage (date + km, bouton Sauvegarder).
 *
 * Utilisation :
 *   type: custom:pitstop-card
 *   vehicle: Moto JV
 */
/* Localisation de la carte : les textes sont charg\u00e9s depuis
 * /local/pitstop_log/locales/<langue>.json (synchronis\u00e9s par l'int\u00e9gration).
 * Repli : fran\u00e7ais embarqu\u00e9 ci-dessous. Contribuer une langue = un fichier
 * JSON dans custom_components/pitstop_log/locales/, sans toucher au JS.
 */
const PS_DEFAULT_STRINGS = {
  "err_vehicle_required": "Vous devez d\u00e9finir 'vehicle: <nom du v\u00e9hicule>'",
  "vehicle_not_found_pre": "V\u00e9hicule",
  "vehicle_not_found_post": "introuvable. V\u00e9rifiez le nom dans la configuration de la carte.",
  "km": "Kilom\u00e9trage",
  "km_update_hint": "Mettre \u00e0 jour le kilom\u00e9trage",
  "km_history_hint": "Voir l'historique du kilom\u00e9trage",
  "maintenances_done": "Carnet d'entretien",
  "last_maintenances": "Derni\u00e8res entr\u00e9es du carnet",
  "manage_history_hint": "G\u00e9rer le carnet d'entretien",
  "no_maintenance": "Aucune entr\u00e9e dans le carnet.",
  "add_maintenance": "Ajouter une entr\u00e9e au carnet",
  "plans_title": "Entretiens \u00e0 faire",
  "th_date": "Date",
  "th_km": "Km",
  "th_actions": "Actions",
  "th_cost": "Co\u00fbt",
  "th_nature": "Nature",
  "th_plan": "Nature",
  "th_status": "Statut",
  "th_remaining": "Reste",
  "th_due": "\u00c9ch\u00e9ance",
  "edit": "Modifier",
  "delete": "Supprimer",
  "back": "Retour",
  "cancel": "Annuler",
  "save": "Sauvegarder",
  "new_maintenance": "Nouvelle entr\u00e9e du carnet",
  "edit_maintenance": "Modifier l'entr\u00e9e du carnet",
  "date": "Date",
  "natures": "Natures de l'entretien",
  "other_natures": "Autre (pr\u00e9ciser, s\u00e9par\u00e9 par des virgules)",
  "cost_optional": "Co\u00fbt (\u20ac, optionnel)",
  "invoice_optional": "Facture (photo ou PDF, optionnel)",
  "invoice_attached": "Une facture est d\u00e9j\u00e0 associ\u00e9e :",
  "see": "voir",
  "plans_reset": "Natures r\u00e9initialis\u00e9es : ",
  "err_date_km": "Renseignez la date et le kilom\u00e9trage.",
  "err_nature": "Cochez au moins une nature d'entretien.",
  "err_save": "Erreur lors de la sauvegarde.",
  "confirm_delete_maintenance": "Supprimer cette entr\u00e9e du carnet ?",
  "badge_maintenance": "Entretien",
  "badge_maintenance_hint": "Cr\u00e9\u00e9 par un entretien \u2014 modifiable depuis la rubrique Derni\u00e8res entr\u00e9es du carnet",
  "km_update_title": "Mise \u00e0 jour du kilom\u00e9trage",
  "reading_date": "Date du relev\u00e9",
  "km_field": "Kilom\u00e9trage (km)",
  "km_history_title": "Historique des valeurs",
  "err_date": "Choisissez une date.",
  "err_km": "Kilom\u00e9trage invalide.",
  "confirm_delete_reading": "Supprimer le relev\u00e9 du",
  "vehicle_edit_title": "Modification du v\u00e9hicule",
  "brand": "Marque",
  "model": "Mod\u00e8le",
  "year_optional": "Ann\u00e9e-mod\u00e8le (optionnel)",
  "photo_optional": "Photo du v\u00e9hicule (optionnel)",
  "registration": "Immatriculation (carte grise)",
  "purchase_date": "Date d'achat (mise en service)",
  "err_model": "Saisissez un mod\u00e8le.",
  "editor_title": "PitStop Log : s\u00e9lection du v\u00e9hicule",
  "title_optional": "Titre affich\u00e9 (optionnel)",
  "title_hint": "Par d\u00e9faut : nom du v\u00e9hicule",
  "no_vehicle": "Aucun v\u00e9hicule PitStop Log trouv\u00e9. Cr\u00e9ez-en un dans Param\u00e8tres \u2192 Appareils et services.",
  "vehicle": "V\u00e9hicule",
  "manage_plans_hint": "G\u00e9rer les natures d'entretien",
  "no_plans": "Aucune nature d'entretien.",
  "add_plan": "Ajouter une nature",
  "new_plan": "Nouvelle nature d'entretien",
  "edit_plan": "Modifier la nature d'entretien",
  "interval_km": "Intervalle (km)",
  "interval_months": "Intervalle (mois)",
  "name_field": "Nom",
  "err_plan_name": "Saisissez un nom de nature.",
  "err_plan_interval": "D\u00e9finissez un intervalle en km ou en mois.",
  "confirm_delete_plan": "Supprimer cette nature d'entretien ? (les entr\u00e9es du carnet sont conserv\u00e9es)",
  "plan_rename_hint": "Renommer change l'identifiant : la r\u00e9initialisation auto depuis le carnet ne portera plus sur les anciennes entr\u00e9es.",
  "plan_names": {
    "autre": "Autre",
    "batterie": "Batterie",
    "bougies": "Bougies",
    "chaine_et_kit_de_transmission": "Cha\u00eene et kit de transmission",
    "controle_technique": "Contr\u00f4le technique",
    "disques_de_frein": "Disques de frein",
    "filtre_a_air": "Filtre \u00e0 air",
    "filtre_a_huile": "Filtre \u00e0 huile",
    "liquide_de_frein": "Liquide de frein",
    "plaquettes_de_frein": "Plaquettes de frein",
    "pneus": "Pneus",
    "revision": "R\u00e9vision",
    "vidange": "Vidange"
  },
};
let PS_STRINGS = null;

async function psLoadStrings(hass) {
  if (PS_STRINGS) return null;
  const lang = ((hass && hass.locale && hass.locale.language) || "fr")
    .split("-")[0];
  const fetchLang = async (l) => {
    try {
      const resp = await fetch(`/local/pitstop_log/locales/${l}.json`);
      if (resp.ok) return await resp.json();
    } catch (err) {}
    return null;
  };
  let data = await fetchLang(lang);
  if (!data && lang !== "fr") data = await fetchLang("fr");
  PS_STRINGS = Object.assign({}, PS_DEFAULT_STRINGS, data || {});
  return PS_STRINGS;
}

function psT(key) {
  return (PS_STRINGS && PS_STRINGS[key]) || PS_DEFAULT_STRINGS[key] || key;
}

/** Slug identique au slugify Python/HA (NFKD + ASCII, non-alnum -> "_"). */
function psSlug(name) {
  return String(name || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

/** Nom affich\u00e9 d'une nature : mapping plan_names, repli sur le brut. */
function psName(name) {
  const names =
    (PS_STRINGS && PS_STRINGS.plan_names) || PS_DEFAULT_STRINGS.plan_names || {};
  return names[psSlug(name)] || name;
}

class PitstopCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
    this._device_label = null;
    this._device_promise = null;
  }

  setConfig(config) {
    if (!config.vehicle) {
      throw new Error(psT("err_vehicle_required"));
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
    this._loadDeviceName();
    psLoadStrings(this._hass).then((s) => {
      if (s) this._render();
    });
  }

  /** R\u00e9cup\u00e8re le nom de l'appareil (registre HA), mis en cache. */
  _loadDeviceName() {
    if (!this._hass || this._device_promise) return;
    const main = this._findMainSensor();
    if (!main || !main.attributes || !main.attributes.vehicle_id) return;
    const vehicleId = main.attributes.vehicle_id;
    this._device_promise = this._hass
      .callWS({ type: "config/device_registry/list" })
      .then(
        (devices) => {
          const device = (devices || []).find(
            (dv) =>
              Array.isArray(dv.identifiers) &&
              dv.identifiers.some(
                (i) => i[0] === "pitstop_log" && i[1] === vehicleId
              )
          );
          this._device_label = device
            ? device.name_by_user || device.name || null
            : null;
          this._render();
        },
        () => {
          this._device_promise = null;
        }
      );
  }

  /** Nom affich\u00e9 : titre de la carte, sinon nom de l'appareil, sinon nom interne. */
  _displayName() {
    return (
      this._config.title ||
      this._device_label ||
      this._config.vehicle
    );
  }

  /** Nom de l'appareil avec repli sur le nom interne. */
  _deviceOrVehicle() {
    return this._device_label || this._config.vehicle;
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: "full" };
  }

  _slug() {
    return (this._config.vehicle || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
  }

  /** Trouve le capteur \u00ab Prochain entretien \u00bb du v\u00e9hicule. */
  _findMainSensor() {
    const slug = this._slug();
    const direct = this._hass.states[`sensor.${slug}_prochain_entretien`];
    if (direct) return direct;
    for (const entityId in this._hass.states) {
      const state = this._hass.states[entityId];
      if (
        entityId.startsWith("sensor.") &&
        state.attributes &&
        state.attributes.vehicle === this._config.vehicle &&
        state.attributes.plans !== undefined
      ) {
        return state;
      }
    }
    return null;
  }

  /** Trouve l'odom\u00e8tre et les capteurs de natures du v\u00e9hicule. */
  _findEntities() {
    const slug = this._slug();
    const found = { odometer: null, plans: [] };
    for (const entityId in this._hass.states) {
      const state = this._hass.states[entityId];
      if (!entityId.startsWith("sensor.") || !state.attributes) {
        continue;
      }
      const attrs = state.attributes;
      if (
        entityId === `sensor.${slug}_kilometrage` ||
        (attrs.odometer === true && attrs.vehicle === this._config.vehicle)
      ) {
        found.odometer = state;
        continue;
      }
      if (
        attrs.vehicle === this._config.vehicle &&
        attrs.km_remaining !== undefined
      ) {
        found.plans.push(state);
      }
    }
    if (!found.odometer) {
      const main = this._findMainSensor();
      if (main && main.attributes && main.attributes.history) {
        let maxKm = null;
        for (const h of main.attributes.history) {
          if (h.km != null && (maxKm === null || h.km > maxKm)) maxKm = h.km;
        }
        if (maxKm !== null) {
          found.odometer = { state: maxKm, attributes: {} };
        }
      }
    }
    return found;
  }

  /** Ouvre la fen\u00eatre d'\u00e9dition du kilom\u00e9trage (overlay). */
  _openEditor() {
    this._odo_edit_date = null;
    this._render();
    const root = this.shadowRoot;
    const card = root.querySelector("ha-card");
    if (!card) return;
    const main = this._findMainSensor();
    const entities = this._findEntities();
    const today = new Date().toISOString().slice(0, 10);
    const currentKm = entities.odometer
      ? Math.round(Number(entities.odometer.state))
      : "";
    const vehicleId =
      main && main.attributes && main.attributes.vehicle_id
        ? main.attributes.vehicle_id
        : this._config.vehicle;
    const rows = (entities.odometer && entities.odometer.attributes
      ? entities.odometer.attributes.odometer_history || []
      : [])
      .slice()
      .sort((a, b) => (a.date < b.date ? 1 : -1))
      .map(
        (p, i) =>
          `<tr><td>${p.date}</td><td class="num">${Number(p.km).toLocaleString()} km</td><td class="num">${
            p.source === "maintenance"
              ? `<span class="src-badge" title="${psT("badge_maintenance_hint")}">${psT("badge_maintenance")}</span>`
              : `<span class="icon-btn edit" data-date="${p.date}" data-km="${p.km}" title="${psT("edit")}">\u270e</span><span class="icon-btn del" data-date="${p.date}" title="${psT("delete")}">\u2716</span>`
          }</td></tr>`
      )
      .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal">
        <div class="editor-title">${psT("km_update_title")}</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        <div class="field">
          <label for="ps-date">${psT("reading_date")}</label>
          <input id="ps-date" class="ps-input" type="date" value="${today}" />
        </div>
        <div class="field">
          <label for="ps-km">${psT("km_field")}</label>
          <input id="ps-km" class="ps-input" type="number" min="0" step="1" placeholder="${currentKm}" value="${currentKm}" />
        </div>
        <div class="section editor-section">${psT("km_history_title")}</div>
        <table class="table editor-table">
          <thead><tr><th>${psT("th_date")}</th><th class="num">${psT("km")}</th><th></th></tr></thead>
          <tbody id="ps-odo-rows">
            ${rows}
          </tbody>
        </table>
        <div class="editor-error" id="ps-error"></div>
        <div class="editor-actions">
          <button class="ps-cancel" id="ps-cancel">${psT("cancel")}</button>
          <button class="ps-save" id="ps-save">${psT("save")}</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    overlay.querySelector("#ps-cancel").addEventListener("click", () => {
      overlay.remove();
    });
    overlay.querySelector("#ps-save").addEventListener("click", () =>
      this._saveOdometer(vehicleId, overlay)
    );
    overlay.querySelector("#ps-km").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveOdometer(vehicleId, overlay);
    });
    overlay.querySelector("#ps-date").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveOdometer(vehicleId, overlay);
    });
    overlay.querySelectorAll(".icon-btn.edit").forEach((btn) =>
      btn.addEventListener("click", () => {
        this._odo_edit_date = btn.dataset.date;
        overlay.querySelector("#ps-date").value = btn.dataset.date;
        overlay.querySelector("#ps-km").value = btn.dataset.km;
      })
    );
    overlay.querySelectorAll(".icon-btn.del").forEach((btn) =>
      btn.addEventListener("click", () => {
        if (!window.confirm(psT("confirm_delete_reading") + " " + btn.dataset.date + " ?"))
          return;
        this._hass
          .callService("pitstop_log", "delete_odometer_point", {
            vehicle_id: vehicleId,
            date: btn.dataset.date,
          })
          .then(
            () => this._openEditor(),
            () => this._openEditor()
          );
      })
    );
  }

  /** Valide la saisie d'un nouveau kilom\u00e9trage et appelle le service. */
  _saveOdometer(vehicleId, overlay) {
    const dateValue = overlay.querySelector("#ps-date").value;
    const kmValue = parseFloat(overlay.querySelector("#ps-km").value);
    const errorBox = overlay.querySelector("#ps-error");
    errorBox.textContent = "";
    if (!dateValue) {
      errorBox.textContent = psT("err_date");
      return;
    }
    if (isNaN(kmValue) || kmValue < 0) {
      errorBox.textContent = psT("err_km");
      return;
    }
    const button = overlay.querySelector("#ps-save");
    button.disabled = true;
    const done = () => {
      overlay.remove();
      this._render();
    };
    const fail = (err) => {
      button.disabled = false;
      errorBox.textContent =
        (err && err.message) || psT("err_save");
    };
    // \u00c9dition d'un relev\u00e9 dont on change la date : on supprime l'ancien
    const editDate = this._odo_edit_date;
    this._odo_edit_date = null;
    if (editDate && editDate !== dateValue) {
      this._hass
        .callService("pitstop_log", "delete_odometer_point", {
          vehicle_id: vehicleId,
          date: editDate,
        })
        .then(() =>
          this._hass
            .callService("pitstop_log", "update_odometer", {
              vehicle_id: vehicleId,
              km: kmValue,
              date: dateValue,
            })
            .then(done, fail)
        , fail);
      return;
    }
    this._hass
      .callService("pitstop_log", "update_odometer", {
        vehicle_id: vehicleId,
        km: kmValue,
        date: dateValue,
      })
      .then(done, fail);
  }

  /** Charge la liste des marques (identique au flux de cr\u00e9ation). */
  async _loadBrands() {
    if (this._brands !== undefined) return this._brands;
    try {
      const resp = await fetch("/local/pitstop_log/brands.json");
      const data = await resp.json();
      this._brands = data && data.brands ? data.brands : null;
    } catch (err) {
      this._brands = null;
    }
    return this._brands;
  }

  /** Ouvre la fen\u00eatre de modification de la marque et du mod\u00e8le. */
  async _openBrandEditor() {
    const brands = await this._loadBrands();
    const root = this.shadowRoot;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleType = attrs.type || "";
    const currentBrand = attrs.brand || "";
    const currentModel = attrs.model || "";
    const vehicleId = attrs.vehicle_id || this._config.vehicle;

    // M\u00eames valeurs que le flux de cr\u00e9ation : cat\u00e9gorie du type + Autre
    let names = [];
    if (brands) {
      if (vehicleType === "other" || !vehicleType) {
        names = Object.keys(brands);
      } else {
        names = Object.keys(brands).filter(
          (n) =>
            (brands[n] && brands[n].category === vehicleType) || n === "Autre"
        );
      }
    }
    if (currentBrand && !names.includes(currentBrand)) {
      names.unshift(currentBrand);
    }
    const options = names
      .map(
        (n) =>
          `<option value="${n}"${n === currentBrand ? " selected" : ""}>${
            (brands && brands[n] && brands[n].label) || n
          }</option>`
      )
      .join("");

    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="editor">
          <div class="editor-title">${psT("vehicle_edit_title")}</div>
          <div class="editor-sub">${this._deviceOrVehicle()}</div>
          <div class="field">
            <label for="ps-brand">${psT("brand")}</label>
            <select id="ps-brand" class="ps-input">${options}</select>
          </div>
          <div class="field">
            <label for="ps-model">${psT("model")}</label>
            <input id="ps-model" class="ps-input" type="text" value="${currentModel}" />
          </div>
          <div class="field">
            <label for="ps-year">${psT("year_optional")}</label>
            <input id="ps-year" class="ps-input" type="number" min="1900" max="2100" value="${(attrs.model_year || "") || ""}" />
          </div>
          <div class="field">
            <label for="ps-photo">${psT("photo_optional")}</label>
            <input id="ps-photo" class="ps-input" type="file" accept="image/*" />
          </div>
          <div class="field">
            <label for="ps-reg">${psT("registration")}</label>
            <input id="ps-reg" class="ps-input" type="text" value="${attrs.registration || ""}" />
          </div>
          <div class="field">
            <label for="ps-pdate">${psT("purchase_date")}</label>
            <input id="ps-pdate" class="ps-input" type="date" value="${attrs.purchase_date || ""}" />
          </div>
          <div class="editor-error" id="ps-error"></div>
          <div class="editor-actions">
            <button class="ps-cancel" id="ps-cancel">${psT("cancel")}</button>
            <button class="ps-save" id="ps-save">${psT("save")}</button>
          </div>
        </div>
      </ha-card>`;
    root.querySelector("#ps-cancel").addEventListener("click", () => {
      this._render();
    });
    root.querySelector("#ps-save").addEventListener("click", () =>
      this._saveBrandModel(vehicleId)
    );
    root.querySelector("#ps-model").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveBrandModel(vehicleId);
    });
  }

  /** Sauvegarde la marque, le mod\u00e8le, l'ann\u00e9e et la photo via le service. */
  async _saveBrandModel(vehicleId) {
    const root = this.shadowRoot;
    const brand = root.querySelector("#ps-brand").value;
    const model = root.querySelector("#ps-model").value.trim();
    const year = root.querySelector("#ps-year").value;
    const photoInput = root.querySelector("#ps-photo");
    const errorBox = root.querySelector("#ps-error");
    errorBox.textContent = "";
    if (!model) {
      errorBox.textContent = psT("err_model");
      return;
    }
    const button = root.querySelector("#ps-save");
    button.disabled = true;

    // Lecture de la photo en base64 si un fichier est choisi
    let photoBase64 = null;
    if (photoInput && photoInput.files && photoInput.files[0]) {
      photoBase64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(photoInput.files[0]);
      }).catch(() => null);
    }

    const reg = root.querySelector("#ps-reg").value.trim();
    const pdate = root.querySelector("#ps-pdate").value;
    const data = { vehicle_id: vehicleId, brand: brand, model: model };
    if (year) data.model_year = parseInt(year, 10);
    if (photoBase64) data.photo_base64 = photoBase64;
    if (reg) data.registration = reg;
    if (pdate) data.purchase_date = pdate;

    this._hass.callService("pitstop_log", "update_brand_model", data).then(
      () => {
        this._render();
      },
      (err) => {
        button.disabled = false;
        errorBox.textContent =
          (err && err.message) || psT("err_save");
      }
    );
  }

  _render() {
    if (!this._hass || !this._config) return;
    const main = this._findMainSensor();
    const entities = this._findEntities();
    const root = this.shadowRoot;

    if (!main) {
      root.innerHTML = `
        <style>${PitstopCard._styles()}</style>
        <ha-card>
          <div class="pad error">
            ${psT("vehicle_not_found_pre")} \u00ab ${this._deviceOrVehicle()} \u00bb ${psT("vehicle_not_found_post")}
          </div>
        </ha-card>`;
      return;
    }

    const attrs = main.attributes || {};
    const statusColors = {
      "Pas urgent": "var(--label-badge-green, #13ba6e)",
      Urgent: "var(--label-badge-yellow, #ffab40)",
      "Tr\u00e8s urgent": "var(--label-badge-orange, #ff9800)",
      "En retard": "var(--label-badge-red, #fce588)",
      "Not urgent": "var(--label-badge-green, #13ba6e)",
      "Very urgent": "var(--label-badge-orange, #ff9800)",
      "Past Due": "var(--label-badge-red, #fce588)",
    };
    const statusColor =
      statusColors[main.state] || "var(--primary-color, #03a9f4)";

    const plans = entities.plans
      .map(
        (p) => `
        <tr>
          <td>${p.attributes.friendly_name || p.entity_id}</td>
          <td><span class="badge" style="background:${statusColors[p.state] || "var(--primary-color)"}">${p.state}</span></td>
          <td class="num">${p.attributes.km_remaining != null ? p.attributes.km_remaining.toLocaleString() + " km" : p.attributes.days_remaining != null ? p.attributes.days_remaining + " j" : "\u2014"}</td>
          <td class="num">${PitstopCard._fmtDue(p.attributes)}</td>
        </tr>`
      )
      .join("");

    const history = (attrs.history || [])
      .slice(0, 5)
      .map(
        (h) => `
        <tr>
          <td>${h.date || ""}</td>
          <td class="num">${h.km != null ? Number(h.km).toLocaleString() + " km" : ""}</td>
          <td>${this._fmtActions(h.actions)}</td>
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " \u20ac" : ""}</td>
          <td class="num">${h.invoice_url ? `<a class="inv" href="${h.invoice_url}" target="_blank" title="Facture">\ud83d\udcc4</a>` : ""}</td>
        </tr>`
      )
      .join("");

    const logo = PitstopCard._logoHtml(attrs);
    const photo = attrs.photo
      ? `<img class="photo" src="${attrs.photo}" alt="${this._deviceOrVehicle()}">`
      : "";

    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="header">
          ${logo}
          <div class="titles">
            <div class="name">${this._displayName()}</div>
            <div class="brand">${attrs.brand || ""}${attrs.brand ? " \u00b7 " : ""}${attrs.model || ""}${attrs.model_year ? " (" + attrs.model_year + ")" : ""} <span class="gear gear-brand" title="Mettre \u00e0 jour la marque et le mod\u00e8le">
                <svg viewBox="0 0 24 24" width="13" height="13">
                  <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
                </svg>
              </span></div>
            <div class="meta">${
              (attrs.purchase_date || "\u2014") +
              " - " +
              (attrs.registration || "\u2014")
            }</div>
          </div>
          <div class="statusbox">
            <div class="status" style="border-color:${statusColor};color:${statusColor}">${main.state}</div>
          </div>
        </div>
        ${photo}
        <div class="grid">
          <div class="cell cell-km" title="${psT("km_history_hint")}">
            <div class="label">${psT("km")}
              <span class="gear gear-km" title="${psT("km_update_hint")}">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
                </svg>
              </span>
            </div>
            <div class="value">${
              entities.odometer
                ? Number(entities.odometer.state).toLocaleString() + " km"
                : "\u2014"
            }</div>
          </div>
          <div class="cell">
            <div class="label">${psT("maintenances_done")}</div>
            <div class="value">${attrs.history_count != null ? attrs.history_count : "\u2014"}</div>
          </div>
        </div>
        <div class="section">${psT("plans_title")}
          <span class="gear gear-plans" title="${psT("manage_plans_hint")}">
            <svg viewBox="0 0 24 24" width="14" height="14">
              <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
            </svg>
          </span>
        </div>
        ${
          plans
            ? `<table class="table"><thead><tr><th>${psT("th_plan")}</th><th>${psT("th_status")}</th><th>${psT("th_remaining")}</th><th>${psT("th_due")}</th></tr></thead><tbody>${plans}</tbody></table>`
            : `<div class="empty">${psT("no_plans")}</div>`
        }
        <div class="section">${psT("last_maintenances")}
          <span class="gear gear-history" title="${psT("manage_history_hint")}">
            <svg viewBox="0 0 24 24" width="14" height="14">
              <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
            </svg>
          </span>
        </div>
        ${
          history
            ? `<table class="table"><thead><tr><th>${psT("th_date")}</th><th>${psT("th_km")}</th><th>${psT("th_actions")}</th><th>${psT("th_cost")}</th><th></th></tr></thead><tbody>${history}</tbody></table>`
            : `<div class="empty">${psT("no_maintenance")}</div>`
        }
        <div class="addrow">
          <button class="ps-add" id="ps-add-maint">+ ${psT("add_maintenance")}</button>
        </div>
      </ha-card>`;
    const logoImg = root.querySelector("img.logo");
    if (logoImg)
      logoImg.addEventListener("error", () => {
        logoImg.outerHTML = PitstopCard._missingLogoSvg();
      });
    const gearKm = root.querySelector(".gear-km");
    if (gearKm) gearKm.addEventListener("click", () => this._openEditor());
    const cellKm = root.querySelector(".cell-km");
    if (cellKm)
      cellKm.addEventListener("click", (ev) => {
        if (ev.target.closest(".gear-km")) return;
        const entities = this._findEntities();
        if (!entities.odometer) return;
        const entityId =
          entities.odometer.entity_id ||
          `sensor.${this._slug()}_kilometrage`;
        const moreInfo = new Event("hass-more-info", {
          bubbles: true,
          composed: true,
        });
        moreInfo.detail = { entityId: entityId };
        this.dispatchEvent(moreInfo);
      });
    const gearBrand = root.querySelector(".gear-brand");
    if (gearBrand)
      gearBrand.addEventListener("click", () => this._openBrandEditor());
    const gearHistory = root.querySelector(".gear-history");
    if (gearHistory)
      gearHistory.addEventListener("click", () => this._openHistoryEditor());
    const gearPlans = root.querySelector(".gear-plans");
    if (gearPlans)
      gearPlans.addEventListener("click", () => this._openPlansEditor());
    const addMaint = root.querySelector("#ps-add-maint");
    if (addMaint)
      addMaint.addEventListener("click", () => this._openMaintenanceEditor(null));
  }

  /** Logo de marque, avec ic\u00f4ne par d\u00e9faut si l'image est manquante. */
  /** Formate l'\u00e9ch\u00e9ance d'une nature : date pr\u00e9vue (JJ/MM/AAAA) ou km cible. */
  static _fmtDue(attrs) {
    if (attrs.due_date) {
      const d = String(attrs.due_date);
      return d.slice(8) + "/" + d.slice(5, 7) + "/" + d.slice(0, 4);
    }
    if (attrs.due_km != null) return attrs.due_km.toLocaleString() + " km";
    return "\u2014";
  }

  static _logoHtml(attrs) {
    if (attrs.brand_logo) {
      return `<img class="logo" src="${attrs.brand_logo}" alt="${attrs.brand || ""}">`;
    }
    return PitstopCard._missingLogoSvg();
  }

  /** Ic\u00f4ne \u00ab image manquante \u00bb (cadre photo barr\u00e9). */
  static _missingLogoSvg() {
    return `<svg class="logo logo-missing" viewBox="0 0 24 24">
      <path fill="currentColor" d="M21 5v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2m-2 12v-2.6l-3-3L11 16.4l-2-2L5 17v2h14zM8.5 9a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"/>
      <path d="M3 3l18 18" stroke="currentColor" stroke-width="2"/>
    </svg>`;
  }

  /** Formate les natures d'un entretien (liste ou cha\u00eene), traduites. */
  _fmtActions(actions) {
    if (Array.isArray(actions)) return actions.map((a) => psName(a)).join(" + ");
    return actions ? psName(actions) : "";
  }

  /** Km courant du v\u00e9hicule (pour pr\u00e9-remplir le formulaire). */
  _currentKm() {
    const entities = this._findEntities();
    if (entities.odometer && entities.odometer.state != null) {
      const n = Number(entities.odometer.state);
      if (!isNaN(n)) return n;
    }
    return "";
  }

  /** Charge la liste des natures d'entretien (fichier local). */
  async _loadMaintenanceTypes() {
    if (this._maint_types !== undefined) return this._maint_types;
    try {
      const resp = await fetch("/local/pitstop_log/maintenance_types.json");
      const data = await resp.json();
      this._maint_types =
        data && Array.isArray(data.types) && data.types.length
          ? data.types
          : ["Vidange", "R\u00e9vision", "Autre"];
    } catch (err) {
      this._maint_types = ["Vidange", "R\u00e9vision", "Autre"];
    }
    return this._maint_types;
  }

  /** Fen\u00eatre : carnet d'entretien complet (modifier/supprimer). */
  async _openHistoryEditor() {
    await this._loadMaintenanceTypes();
    this._render();
    const root = this.shadowRoot;
    const card = root.querySelector("ha-card");
    if (!card) return;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const entries = attrs.history || [];
    const rows = entries
      .map(
        (h, i) => `
        <tr>
          <td>${h.date || ""}</td>
          <td class="num">${h.km != null ? Number(h.km).toLocaleString() + " km" : ""}</td>
          <td>${this._fmtActions(h.actions)}</td>
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " \u20ac" : ""}</td>
          <td class="num">
            ${h.invoice_url ? `<a class="inv" href="${h.invoice_url}" target="_blank" title="Facture">\ud83d\udcc4</a>` : ""}
            <span class="icon-btn edit" data-index="${i}" title="${psT("edit")}">\u270e</span>
            <span class="icon-btn del" data-index="${i}" title="${psT("delete")}">\u2716</span>
          </td>
        </tr>`
      )
      .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal wide">
        <div class="editor-title">${psT("maintenances_done")}</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        ${
          rows
            ? `<table class="table inner"><thead><tr><th>${psT("th_date")}</th><th>${psT("th_km")}</th><th>${psT("th_nature")}</th><th>${psT("th_cost")}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<div class="empty">${psT("no_maintenance")}</div>`
        }
        <div class="editor-actions">
          <button class="ps-cancel" data-act="back">${psT("back")}</button>
          <button class="ps-save" data-act="new">+ ${psT("add_maintenance")}</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    overlay.querySelector('[data-act="back"]').addEventListener("click", () => {
      overlay.remove();
    });
    overlay.querySelector('[data-act="new"]').addEventListener("click", () => {
      overlay.remove();
      this._openMaintenanceEditor(null);
    });
    overlay.querySelectorAll(".icon-btn.edit").forEach((btn) =>
      btn.addEventListener("click", () => {
        overlay.remove();
        this._openMaintenanceEditor(Number(btn.dataset.index));
      })
    );
    overlay.querySelectorAll(".icon-btn.del").forEach((btn) =>
      btn.addEventListener("click", () => {
        overlay.remove();
        this._deleteMaintenance(Number(btn.dataset.index));
      })
    );
  }

  /** Fen\u00eatre : ajout (index null) ou modification (index) d'un entretien. */
  async _openMaintenanceEditor(index) {
    const types = await this._loadMaintenanceTypes();
    this._render();
    const root = this.shadowRoot;
    const card = root.querySelector("ha-card");
    if (!card) return;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const entries = attrs.history || [];
    const entry = index != null ? entries[index] || {} : {};
    const plans = attrs.plans || [];
    const currentKm = this._currentKm();
    const today = new Date().toISOString().slice(0, 10);
    const natureList = Array.isArray(entry.actions)
      ? entry.actions
      : entry.actions
      ? [entry.actions]
      : [];
    const known = types.slice();
    for (const nat of natureList) {
      if (nat !== "Autre" && !known.includes(nat)) known.unshift(nat);
    }
    const natureBoxes = known
      .map(
        (t) =>
          `<label class="chk"><input type="checkbox" class="ps-nature" value="${t}"${natureList.includes(t) ? " checked" : ""}/> ${psName(t)}</label>`
      )
      .join(" ");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal">
        <div class="editor-title">${
          index != null ? psT("edit_maintenance") : psT("new_maintenance")
        }</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        <div class="field">
          <label for="ps-m-date">${psT("date")}</label>
          <input id="ps-m-date" class="ps-input" type="date" value="${entry.date || today}" />
        </div>
        <div class="field">
          <label for="ps-m-km">${psT("km")}</label>
          <input id="ps-m-km" class="ps-input" type="number" min="0" value="${entry.km != null ? entry.km : currentKm}" />
        </div>
        <div class="field">
          <label>${psT("natures")}</label>
          <div class="chips">${natureBoxes}</div>
        </div>
        <div class="field">
          <label for="ps-m-free">${psT("other_natures")}</label>
          <input id="ps-m-free" class="ps-input" type="text" value="${natureList.filter((t) => !known.includes(t)).join(", ")}" />
        </div>
        ${index == null && plans.length ? `<div class="hint" id="ps-m-plans-hint"></div>` : ""}
        <div class="field">
          <label for="ps-m-cost">${psT("cost_optional")}</label>
          <input id="ps-m-cost" class="ps-input" type="number" min="0" step="0.01" value="${entry.cost != null ? entry.cost : ""}" />
        </div>
        <div class="field">
          <label for="ps-m-invoice">${psT("invoice_optional")}</label>
          <input id="ps-m-invoice" class="ps-input" type="file" accept="image/*,application/pdf" />
          ${entry.invoice_url ? `<div class="hint">${psT("invoice_attached")} <a class="inv" href="${entry.invoice_url}" target="_blank">\ud83d\udcc4 ${psT("see")}</a></div>` : ""}
        </div>
<div class="editor-error" id="ps-m-error"></div>
        <div class="editor-actions">
          <button class="ps-cancel" id="ps-m-cancel">${psT("cancel")}</button>
          <button class="ps-save" id="ps-m-save">${psT("save")}</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    const plansHint = overlay.querySelector("#ps-m-plans-hint");
    const updatePlansHint = () => {
      if (!plansHint) return;
      const selected = [...overlay.querySelectorAll(".ps-nature:checked")].map(
        (el) => el.value.toLowerCase()
      );
      const matches = plans
        .filter((p) => p.name && selected.includes(p.name.toLowerCase()))
        .map((p) => psName(p.name));
      plansHint.textContent = matches.length
        ? psT("plans_reset") + matches.join(", ")
        : "";
    };
    overlay.querySelectorAll(".ps-nature").forEach((chk) =>
      chk.addEventListener("change", updatePlansHint)
    );
    updatePlansHint();
    overlay.querySelector("#ps-m-cancel").addEventListener("click", () => {
      overlay.remove();
      if (index != null) this._openHistoryEditor();
    });
    overlay.querySelector("#ps-m-save").addEventListener("click", () =>
      this._saveMaintenance(index, overlay)
    );
  }

  /** Sauvegarde l'entretien (ajout ou modification) via les services. */
  async _saveMaintenance(index, overlay) {
    const root = this.shadowRoot;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleId = attrs.vehicle_id || this._config.vehicle;
    const errorBox = overlay.querySelector("#ps-m-error");
    const button = overlay.querySelector("#ps-m-save");
    errorBox.textContent = "";
    const date = overlay.querySelector("#ps-m-date").value;
    const km = parseInt(overlay.querySelector("#ps-m-km").value, 10);
    if (!date || isNaN(km) || km < 0) {
      errorBox.textContent = psT("err_date_km");
      return;
    }
    const checked = [...overlay.querySelectorAll(".ps-nature:checked")].map(
      (el) => el.value
    );
    const free = overlay.querySelector("#ps-m-free").value;
    const freeNatures = free
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t && t !== "Autre");
    const actions = [...new Set([...checked, ...freeNatures])];
    if (actions.length === 0) {
      errorBox.textContent = psT("err_nature");
      return;
    }
    const costVal = overlay.querySelector("#ps-m-cost").value;
    const invoiceInput = overlay.querySelector("#ps-m-invoice");
    button.disabled = true;

    let invoiceBase64 = null;
    if (invoiceInput && invoiceInput.files && invoiceInput.files[0]) {
      invoiceBase64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(invoiceInput.files[0]);
      }).catch(() => null);
    }

    const data = {
      vehicle_id: vehicleId,
      date: date,
      km: km,
      actions: actions,
    };
    if (costVal !== "") data.cost = parseFloat(costVal);
    if (invoiceBase64) data.invoice_base64 = invoiceBase64;
    if (index != null) {
      data.index = index;
    }
    const service =
      index != null ? "update_maintenance" : "add_maintenance_done";
    this._hass.callService("pitstop_log", service, data).then(
      () => {
        overlay.remove();
        this._render();
      },
      (err) => {
        button.disabled = false;
        errorBox.textContent =
          (err && err.message) || psT("err_save");
      }
    );
  }

  /** Supprime un entretien apr\u00e8s confirmation. */
  _deleteMaintenance(index) {
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleId = attrs.vehicle_id || this._config.vehicle;
    if (!window.confirm(psT("confirm_delete_maintenance"))) {
      this._openHistoryEditor();
      return;
    }
    this._hass.callService("pitstop_log", "delete_maintenance", {
      vehicle_id: vehicleId,
      index: index,
    }).then(
      () => this._openHistoryEditor(),
      () => this._openHistoryEditor()
    );
  }

  /** Fen\u00eatre : gestion des natures d'entretien (ajouter/modifier/supprimer). */
  async _openPlansEditor() {
    await this._loadMaintenanceTypes();
    this._render();
    const root = this.shadowRoot;
    const card = root.querySelector("ha-card");
    if (!card) return;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const plans = attrs.plans || [];
    const rows = plans
      .map(
        (p) => `
        <tr>
          <td>${psName(p.name || "")}</td>
          <td class="num">${p.interval_km ? Number(p.interval_km).toLocaleString() + " km" : "\u2014"}</td>
          <td class="num">${p.interval_months ? p.interval_months : "\u2014"}</td>
          <td class="num">
            <span class="icon-btn edit" data-plan="${p.plan_id}" title="${psT("edit")}">\u270e</span>
            <span class="icon-btn del" data-plan="${p.plan_id}" title="${psT("delete")}">\u2716</span>
          </td>
        </tr>`
      )
      .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal wide">
        <div class="editor-title">${psT("plans_title")}</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        ${
          rows
            ? `<table class="table inner"><thead><tr><th>${psT("th_plan")}</th><th>${psT("interval_km")}</th><th>${psT("interval_months")}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<div class="empty">${psT("no_plans")}</div>`
        }
        <div class="editor-actions">
          <button class="ps-cancel" data-act="back">${psT("back")}</button>
          <button class="ps-save" data-act="new">+ ${psT("add_plan")}</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    overlay.querySelector('[data-act="back"]').addEventListener("click", () => {
      overlay.remove();
    });
    overlay.querySelector('[data-act="new"]').addEventListener("click", () => {
      overlay.remove();
      this._openPlanEditor(null);
    });
    overlay.querySelectorAll(".icon-btn.edit").forEach((btn) =>
      btn.addEventListener("click", () => {
        overlay.remove();
        this._openPlanEditor(btn.dataset.plan);
      })
    );
    overlay.querySelectorAll(".icon-btn.del").forEach((btn) =>
      btn.addEventListener("click", () => {
        overlay.remove();
        this._deletePlan(btn.dataset.plan);
      })
    );
  }

  /** Fen\u00eatre : ajout (planId null) ou modification d'une nature d'entretien. */
  async _openPlanEditor(planId) {
    const types = await this._loadMaintenanceTypes();
    this._render();
    const root = this.shadowRoot;
    const card = root.querySelector("ha-card");
    if (!card) return;
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const plans = attrs.plans || [];
    const plan =
      planId != null ? plans.find((p) => p.plan_id === planId) || {} : {};
    const known = types.slice();
    if (plan.name && !known.includes(plan.name)) known.unshift(plan.name);
    const options = known
      .map((tp) => `<option value="${tp}">${psName(tp)}</option>`)
      .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal">
        <div class="editor-title">${planId != null ? psT("edit_plan") : psT("new_plan")}</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        <div class="field">
          <label for="ps-p-name">${psT("name_field")}</label>
          <input id="ps-p-name" class="ps-input" type="text" list="ps-p-types" value="${plan.name || ""}" />
          <datalist id="ps-p-types">${options}</datalist>
        </div>
        <div class="field">
          <label for="ps-p-km">${psT("interval_km")}</label>
          <input id="ps-p-km" class="ps-input" type="number" min="0" step="1" value="${plan.interval_km || 0}" />
        </div>
        <div class="field">
          <label for="ps-p-months">${psT("interval_months")}</label>
          <input id="ps-p-months" class="ps-input" type="number" min="0" step="1" value="${plan.interval_months || 0}" />
        </div>
        ${planId != null ? `<div class="hint">${psT("plan_rename_hint")}</div>` : ""}
        <div class="editor-error" id="ps-p-error"></div>
        <div class="editor-actions">
          <button class="ps-cancel" id="ps-p-cancel">${psT("cancel")}</button>
          <button class="ps-save" id="ps-p-save">${psT("save")}</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    overlay.querySelector("#ps-p-cancel").addEventListener("click", () => {
      overlay.remove();
      if (planId != null) this._openPlansEditor();
    });
    overlay.querySelector("#ps-p-save").addEventListener("click", () =>
      this._savePlan(planId, overlay)
    );
  }

  /** Sauvegarde la nature (ajout ou modification) via les services. */
  async _savePlan(planId, overlay) {
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleId = attrs.vehicle_id || this._config.vehicle;
    const errorBox = overlay.querySelector("#ps-p-error");
    const button = overlay.querySelector("#ps-p-save");
    errorBox.textContent = "";
    const name = (overlay.querySelector("#ps-p-name").value || "").trim();
    const km = parseInt(overlay.querySelector("#ps-p-km").value, 10) || 0;
    const months = parseInt(overlay.querySelector("#ps-p-months").value, 10) || 0;
    if (!name) {
      errorBox.textContent = psT("err_plan_name");
      return;
    }
    if (km <= 0 && months <= 0) {
      errorBox.textContent = psT("err_plan_interval");
      return;
    }
    button.disabled = true;
    const data = {
      vehicle_id: vehicleId,
      plan_name: name,
      interval_km: km > 0 ? km : 0,
      interval_months: months > 0 ? months : 0,
    };
    if (planId != null) data.plan_id = planId;
    const service =
      planId != null ? "update_maintenance_plan" : "add_maintenance_plan";
    this._hass.callService("pitstop_log", service, data).then(
      () => {
        overlay.remove();
        this._render();
      },
      (err) => {
        button.disabled = false;
        errorBox.textContent = (err && err.message) || psT("err_save");
      }
    );
  }

  /** Supprime une nature d'entretien apr\u00e8s confirmation. */
  _deletePlan(planId) {
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleId = attrs.vehicle_id || this._config.vehicle;
    if (!window.confirm(psT("confirm_delete_plan"))) {
      this._openPlansEditor();
      return;
    }
    this._hass.callService("pitstop_log", "delete_maintenance_plan", {
      vehicle_id: vehicleId,
      plan_id: planId,
    }).then(
      () => this._openPlansEditor(),
      () => this._openPlansEditor()
    );
  }

  /** \u00c9diteur visuel de la carte (WYSIWYG, sans YAML). */
  static getConfigElement() {
    return document.createElement("pitstop-card-editor");
  }

  /** Configuration propos\u00e9e par d\u00e9faut \u00e0 l'ajout de la carte. */
  static getStubConfig(hass) {
    for (const entityId in hass.states) {
      const state = hass.states[entityId];
      if (
        entityId.startsWith("sensor.") &&
        state.attributes &&
        state.attributes.vehicle !== undefined &&
        state.attributes.plans !== undefined
      ) {
        return { vehicle: state.attributes.vehicle };
      }
    }
    return { vehicle: "" };
  }

  static _styles() {
    return `
      ha-card { overflow: hidden; position: relative; }
      .pad { padding: 16px; }
      .error { color: var(--error-color, #db4437); }
      .header { display: flex; align-items: center; gap: 12px; padding: 16px 16px 8px; }
      .gear { cursor: pointer; color: var(--secondary-text-color, #727272); float: right; display: inline-flex; }
      .logo { width: 40px; height: 40px; object-fit: contain; flex: none; }
      .logo-missing { color: var(--secondary-text-color, #727272); opacity: 0.7; }
      .titles { flex: 1; min-width: 0; }
      .brand { font-size: 12px; color: var(--secondary-text-color, #727272); }
      .meta { font-size: 12px; color: var(--secondary-text-color, #727272); margin-top: 2px; }
      .name { font-size: 20px; font-weight: 500; }
      .status { font-size: 13px; font-weight: 600; border: 1.5px solid; border-radius: 16px; padding: 4px 12px; white-space: nowrap; }
      .photo { width: 100%; max-height: 260px; object-fit: cover; display: block; margin: 8px 0; border-radius: var(--ha-card-border-radius, 12px); }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; padding: 0 16px 8px; }
      .cell { background: var(--secondary-background-color, #f5f5f5); border-radius: 10px; padding: 10px; }
      .cell-km { cursor: pointer; }
      .src-badge { font-size: 10px; font-weight: 600; color: var(--secondary-text-color, #727272); border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; padding: 1px 6px; white-space: nowrap; }
      .label { font-size: 11px; color: var(--secondary-text-color, #727272); text-transform: uppercase; letter-spacing: 0.5px; }
      .value { font-size: 20px; font-weight: 500; margin-top: 2px; }
      .value.small { font-size: 15px; }
      .section { font-size: 13px; font-weight: 600; color: var(--secondary-text-color, #727272); padding: 10px 16px 4px; text-transform: uppercase; letter-spacing: 0.5px; }
      .table { width: calc(100% - 32px); margin: 0 16px 16px; border-collapse: collapse; font-size: 13px; }
      .table th { text-align: left; color: var(--secondary-text-color, #727272); font-weight: 500; padding: 4px 6px; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .table td { padding: 6px; border-bottom: 1px solid var(--divider-color, #e0e0e0); vertical-align: top; }
      .table .num { text-align: right; white-space: nowrap; }
      .badge { color: #fff; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
      .editor { padding: 16px; max-width: 420px; margin: 0 auto; }
      .editor-title { font-size: 20px; font-weight: 500; }
      .editor-sub { font-size: 13px; color: var(--secondary-text-color, #727272); margin-bottom: 16px; }
      .field { margin-bottom: 14px; }
      .field label { display: block; font-size: 12px; color: var(--secondary-text-color, #727272); margin-bottom: 4px; }
      .ps-input { width: 100%; font-size: 15px; padding: 8px 10px; border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; background: var(--card-background-color, #fff); color: var(--primary-text-color); box-sizing: border-box; }
      .editor-error { color: var(--error-color, #db4437); font-size: 13px; min-height: 18px; }
      .editor-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
      .ps-cancel, .ps-save { font-size: 14px; padding: 8px 18px; border: none; border-radius: 8px; cursor: pointer; }
      .ps-cancel { background: var(--secondary-background-color, #f5f5f5); color: var(--primary-text-color); }
      .ps-save { background: var(--primary-color, #03a9f4); color: #fff; font-weight: 500; }
      .ps-save:disabled { opacity: 0.5; cursor: wait; }
      .editor-section { padding: 10px 0 4px; }
      .editor-table { width: 100%; margin: 0 0 8px; }
      .editor.wide { max-width: 640px; }
      .table.inner { width: 100%; margin: 0 0 8px; }
      .addrow { display: flex; justify-content: center; padding: 0 16px 16px; }
      .ps-add { font-size: 14px; padding: 8px 18px; border: 1px dashed var(--primary-color, #03a9f4); border-radius: 8px; background: transparent; color: var(--primary-color, #03a9f4); cursor: pointer; }
      .ps-add:hover { background: rgba(3, 169, 244, 0.08); }
      .icon-btn { cursor: pointer; margin-left: 8px; display: inline-flex; }
      .icon-btn.del { color: var(--error-color, #db4437); }
      .icon-btn.edit { color: var(--primary-color, #03a9f4); }
      .inv { text-decoration: none; }
      .empty { padding: 0 16px 8px; font-size: 13px; color: var(--secondary-text-color, #727272); }
      .hint { font-size: 12px; color: var(--secondary-text-color, #727272); margin-top: 4px; }
      .chips { display: flex; flex-wrap: wrap; gap: 8px 12px; }
      .chk { font-size: 14px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; }
 
      .ps-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.35); z-index: 10; border-radius: var(--ha-card-border-radius, 12px); }
      .ps-modal { background: var(--card-background-color, #fff); border-radius: 12px; padding: 16px; width: calc(100% - 32px); max-width: 420px; max-height: 85%; overflow-y: auto; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25); }
      .ps-modal.wide { max-width: 640px; }
    `;
  }
}

customElements.define("pitstop-card-editor", PitstopCardEditor);
customElements.define("pitstop-card", PitstopCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "pitstop-card",
  name: "PitStop Log",
  description: "Carte PitStop Log : toutes les informations d'un v\u00e9hicule du garage.",
});
