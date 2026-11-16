/**
 * \u00c9diteur visuel de la carte PitStop : s\u00e9lection du v\u00e9hicule
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
        "<div>Aucun v\u00e9hicule PitStop Log trouv\u00e9. Cr\u00e9ez-en un dans Param\u00e8tres \u2192 Appareils et services.</div>";
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
          <label>Titre affich\u00e9 (optionnel)</label>
          <input id="ps-title" type="text" value="${(this._config.title || "").replace(/"/g, "&quot;")}" placeholder="Par d\u00e9faut : nom du v\u00e9hicule" />
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
 * PitStop Card \u2014 carte Lovelace pour l'int\u00e9gration PitStop Log.
 *
 * Affiche toutes les informations d'un v\u00e9hicule : photo, logo de marque,
 * kilom\u00e9trage, statut d'entretien, plans \u00e0 faire, historique et graphique
 * du kilom\u00e9trage. L'ic\u00f4ne roue crant\u00e9e ouvre une page d'\u00e9dition du
 * kilom\u00e9trage (date + km, bouton Sauvegarder).
 *
 * Utilisation :
 *   type: custom:pitstop-card
 *   vehicle: Moto JV
 */
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
      throw new Error("Vous devez d\u00e9finir 'vehicle: <nom du v\u00e9hicule>'");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
    this._loadDeviceName();
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

  /** Trouve l'odom\u00e8tre et les capteurs de plans du v\u00e9hicule. */
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

  /** Construit un graphique SVG (courbe km / date). */
  _buildChart(history) {
    if (!history || history.length === 0) return "";
    const points = history.slice().sort((a, b) => (a.date < b.date ? -1 : 1));
    const width = 1000;
    const height = 220;
    const pad = 40;
    const dates = points.map((p) => new Date(p.date).getTime());
    const minDate = Math.min(...dates);
    const maxDate = Math.max(...dates);
    const maxKm = Math.max(...points.map((p) => p.km), 1);
    const span = Math.max(maxDate - minDate, 1);
    const x = (d) => pad + ((d - minDate) / span) * (width - 2 * pad);
    const y = (km) => height - pad - (km / maxKm) * (height - 2 * pad);
    const poly = points
      .map(
        (p, i) =>
          `${i === 0 ? "M" : "L"}${x(dates[i]).toFixed(1)},${y(p.km).toFixed(1)}`
      )
      .join(" ");
    const area = `${poly} L${x(dates[dates.length - 1]).toFixed(1)},${height - pad} L${x(dates[0]).toFixed(1)},${height - pad} Z`;
    const dots = points
      .map(
        (p, i) =>
          `<circle cx="${x(dates[i]).toFixed(1)}" cy="${y(p.km).toFixed(1)}" r="4" fill="var(--primary-color, #03a9f4)"><title>${p.date} \u2014 ${Number(p.km).toLocaleString()} km</title></circle>`
      )
      .join("");
    const fmt = (d) =>
      new Date(d).toLocaleDateString(undefined, {
        month: "short",
        year: "2-digit",
      });
    return `
      <div class="section">Kilom\u00e9trage dans le temps</div>
      <svg class="chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <path d="${area}" fill="var(--primary-color, #03a9f4)" opacity="0.12"/>
        <path d="${poly}" fill="none" stroke="var(--primary-color, #03a9f4)" stroke-width="3"/>
        ${dots}
        <text x="${pad}" y="${height - 12}" class="axis">${fmt(minDate)}</text>
        <text x="${width - pad}" y="${height - 12}" text-anchor="end" class="axis">${fmt(maxDate)}</text>
        <text x="${width - pad}" y="${pad - 12}" text-anchor="end" class="axis">${maxKm.toLocaleString()} km</text>
      </svg>`;
  }

  /** Ouvre la page d'\u00e9dition du kilom\u00e9trage. */
  _openEditor() {
    const root = this.shadowRoot;
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
    const history = (entities.odometer && entities.odometer.attributes
      ? entities.odometer.attributes.odometer_history || []
      : []
    )
      .slice()
      .sort((a, b) => (a.date < b.date ? 1 : -1))
      .map(
        (p) =>
          `<tr><td>${p.date}</td><td class="num">${Number(p.km).toLocaleString()} km</td></tr>`
      )
      .join("");
    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="editor">
          <div class="editor-title">Mise \u00e0 jour du kilom\u00e9trage</div>
          <div class="editor-sub">${this._deviceOrVehicle()}</div>
          <div class="field">
            <label for="ps-date">Date du relev\u00e9</label>
            <input id="ps-date" class="ps-input" type="date" value="${today}" />
          </div>
          <div class="field">
            <label for="ps-km">Kilom\u00e9trage (km)</label>
            <input id="ps-km" class="ps-input" type="number" min="0" step="1" placeholder="${currentKm}" value="${currentKm}" />
          </div>
          <div class="section editor-section">Historique des valeurs</div>
          <table class="table editor-table">
            <thead><tr><th>Date</th><th class="num">Kilom\u00e9trage</th></tr></thead>
            <tbody>
              ${history}
            </tbody>
          </table>
          <div class="editor-error" id="ps-error"></div>
          <div class="editor-actions">
            <button class="ps-cancel" id="ps-cancel">Annuler</button>
            <button class="ps-save" id="ps-save">Sauvegarder</button>
          </div>
        </div>
      </ha-card>`;
    root.querySelector("#ps-cancel").addEventListener("click", () => {
      this._render();
    });
    root.querySelector("#ps-save").addEventListener("click", () =>
      this._saveOdometer(vehicleId)
    );
    root.querySelector("#ps-km").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveOdometer(vehicleId);
    });
    root.querySelector("#ps-date").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveOdometer(vehicleId);
    });
  }

  /** Valide la saisie d'un nouveau kilom\u00e9trage et appelle le service. */
  _saveOdometer(vehicleId) {
    const root = this.shadowRoot;
    const dateValue = root.querySelector("#ps-date").value;
    const kmValue = parseFloat(root.querySelector("#ps-km").value);
    const errorBox = root.querySelector("#ps-error");
    errorBox.textContent = "";
    if (!dateValue) {
      errorBox.textContent = "Choisissez une date.";
      return;
    }
    if (isNaN(kmValue) || kmValue < 0) {
      errorBox.textContent = "Kilom\u00e9trage invalide.";
      return;
    }
    const button = root.querySelector("#ps-save");
    button.disabled = true;
    this._hass
      .callService("pitstop_log", "update_odometer", {
        vehicle_id: vehicleId,
        km: kmValue,
        date: dateValue,
      })
      .then(
        () => {
          this._render();
        },
        (err) => {
          button.disabled = false;
          errorBox.textContent =
            (err && err.message) || "Erreur lors de la sauvegarde.";
        }
      );
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
          <div class="editor-title">Modification du v\u00e9hicule</div>
          <div class="editor-sub">${this._deviceOrVehicle()}</div>
          <div class="field">
            <label for="ps-brand">Marque</label>
            <select id="ps-brand" class="ps-input">${options}</select>
          </div>
          <div class="field">
            <label for="ps-model">Mod\u00e8le</label>
            <input id="ps-model" class="ps-input" type="text" value="${currentModel}" />
          </div>
          <div class="field">
            <label for="ps-year">Ann\u00e9e-mod\u00e8le (optionnel)</label>
            <input id="ps-year" class="ps-input" type="number" min="1900" max="2100" value="${(attrs.model_year || "") || ""}" />
          </div>
          <div class="field">
            <label for="ps-photo">Photo du v\u00e9hicule (optionnel)</label>
            <input id="ps-photo" class="ps-input" type="file" accept="image/*" />
          </div>
          <div class="field">
            <label for="ps-reg">Immatriculation (carte grise)</label>
            <input id="ps-reg" class="ps-input" type="text" value="${attrs.registration || ""}" />
          </div>
          <div class="field">
            <label for="ps-pdate">Date d'achat (mise en service)</label>
            <input id="ps-pdate" class="ps-input" type="date" value="${attrs.purchase_date || ""}" />
          </div>
          <div class="editor-error" id="ps-error"></div>
          <div class="editor-actions">
            <button class="ps-cancel" id="ps-cancel">Annuler</button>
            <button class="ps-save" id="ps-save">Sauvegarder</button>
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
      errorBox.textContent = "Saisissez un mod\u00e8le.";
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
          (err && err.message) || "Erreur lors de la sauvegarde.";
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
            V\u00e9hicule \u00ab ${this._deviceOrVehicle()} \u00bb introuvable.
            V\u00e9rifiez le nom dans la configuration de la carte.
          </div>
        </ha-card>`;
      return;
    }

    const attrs = main.attributes || {};
    const statusColors = {
      OK: "var(--label-badge-green, #13ba6e)",
      "Bient\u00f4t d\u00fb": "var(--label-badge-yellow, #ffab40)",
      "En retard": "var(--label-badge-red, #fce588)",
      "Due soon": "var(--label-badge-yellow, #ffab40)",
      Overdue: "var(--label-badge-red, #fce588)",
    };
    const statusColor =
      statusColors[main.state] || "var(--primary-color, #03a9f4)";

    const plans = entities.plans
      .map(
        (p) => `
        <tr>
          <td>${p.attributes.friendly_name || p.entity_id}</td>
          <td><span class="badge" style="background:${statusColors[p.state] || "var(--primary-color)"}">${p.state}</span></td>
          <td class="num">${p.attributes.km_remaining != null ? p.attributes.km_remaining.toLocaleString() + " km" : "\u2014"}</td>
          <td class="num">${p.attributes.days_remaining != null ? p.attributes.days_remaining + " j" : "\u2014"}</td>
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
          <td>${h.actions || ""}</td>
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " \u20ac" : ""}</td>
          <td class="num">${h.invoice_url ? `<a class="inv" href="${h.invoice_url}" target="_blank" title="Facture">\ud83d\udcc4</a>` : ""}</td>
        </tr>`
      )
      .join("");

    const odometerHistory = entities.odometer && entities.odometer.attributes
      ? entities.odometer.attributes.odometer_history || []
      : [];
    const chart = this._buildChart(odometerHistory);
    const logo = attrs.brand_logo
      ? `<img class="logo" src="${attrs.brand_logo}" alt="${attrs.brand || ""}">`
      : "";
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
          </div>
          <div class="statusbox">
            <div class="status" style="border-color:${statusColor};color:${statusColor}">${main.state}</div>
          </div>
        </div>
        ${photo}
        <div class="grid">
          <div class="cell">
            <div class="label">Kilom\u00e9trage
              <span class="gear gear-km" title="Mettre \u00e0 jour le kilom\u00e9trage">
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
            <div class="label">Immatriculation
                          </div>
            <div class="value small">${attrs.registration || "\u2014"}</div>
          </div>
          <div class="cell">
            <div class="label">Date d'achat
                          </div>
            <div class="value small">${attrs.purchase_date || "\u2014"}</div>
          </div>
          <div class="cell">
            <div class="label">Entretiens r\u00e9alis\u00e9s</div>
            <div class="value">${attrs.history_count != null ? attrs.history_count : "\u2014"}</div>
          </div>
        </div>
        ${chart}
        ${
          plans
            ? `<div class="section">Entretiens \u00e0 faire</div>
               <table class="table"><thead><tr><th>Plan</th><th>Statut</th><th>Reste</th><th>\u00c9ch\u00e9ance</th></tr></thead><tbody>${plans}</tbody></table>`
            : ""
        }
        <div class="section">Derniers entretiens
          <span class="gear gear-history" title="G\u00e9rer l'historique des entretiens">
            <svg viewBox="0 0 24 24" width="14" height="14">
              <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
            </svg>
          </span>
        </div>
        ${
          history
            ? `<table class="table"><thead><tr><th>Date</th><th>Km</th><th>Actions</th><th>Co\u00fbt</th><th></th></tr></thead><tbody>${history}</tbody></table>`
            : `<div class="empty">Aucun entretien enregistr\u00e9.</div>`
        }
        <div class="addrow">
          <button class="ps-add" id="ps-add-maint">+ Ajouter un entretien</button>
        </div>
      </ha-card>`;
    const gearKm = root.querySelector(".gear-km");
    if (gearKm) gearKm.addEventListener("click", () => this._openEditor());
    const gearBrand = root.querySelector(".gear-brand");
    if (gearBrand)
      gearBrand.addEventListener("click", () => this._openBrandEditor());
    const gearHistory = root.querySelector(".gear-history");
    if (gearHistory)
      gearHistory.addEventListener("click", () => this._openHistoryEditor());
    const addMaint = root.querySelector("#ps-add-maint");
    if (addMaint)
      addMaint.addEventListener("click", () => this._openMaintenanceEditor(null));
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

  /** Fen\u00eatre : historique complet des entretiens (modifier/supprimer). */
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
          <td>${h.actions || ""}</td>
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " \u20ac" : ""}</td>
          <td class="num">
            ${h.invoice_url ? `<a class="inv" href="${h.invoice_url}" target="_blank" title="Facture">\ud83d\udcc4</a>` : ""}
            <span class="icon-btn edit" data-index="${i}" title="Modifier">\u270E</span>
            <span class="icon-btn del" data-index="${i}" title="Supprimer">\u2716</span>
          </td>
        </tr>`
      )
      .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal wide">
        <div class="editor-title">Entretiens r\u00e9alis\u00e9s</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        ${
          rows
            ? `<table class="table inner"><thead><tr><th>Date</th><th>Km</th><th>Nature</th><th>Co\u00fbt</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<div class="empty">Aucun entretien enregistr\u00e9.</div>`
        }
        <div class="editor-actions">
          <button class="ps-cancel" data-act="back">Retour</button>
          <button class="ps-save" data-act="new">+ Ajouter un entretien</button>
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
    const nature = entry.actions || "";
    const natureOptions = types.slice();
    if (nature && !natureOptions.includes(nature)) {
      natureOptions.unshift(nature);
    }
    const natureSel = natureOptions
      .map(
        (t) =>
          `<option value="${t}"${t === nature ? " selected" : ""}>${t}</option>`
      )
      .join("");
    const planOptions =
      `<option value="">\u2014 Aucun \u2014</option>` +
      plans
        .map(
          (p) =>
            `<option value="${p.plan_id}">${p.name || p.plan_id}</option>`
        )
        .join("");
    const overlay = document.createElement("div");
    overlay.className = "ps-overlay";
    overlay.innerHTML = `
      <div class="ps-modal">
        <div class="editor-title">${
          index != null ? "Modifier l'entretien" : "Nouvel entretien"
        }</div>
        <div class="editor-sub">${this._deviceOrVehicle()}</div>
        <div class="field">
          <label for="ps-m-date">Date</label>
          <input id="ps-m-date" class="ps-input" type="date" value="${entry.date || today}" />
        </div>
        <div class="field">
          <label for="ps-m-km">Kilom\u00e9trage</label>
          <input id="ps-m-km" class="ps-input" type="number" min="0" value="${entry.km != null ? entry.km : currentKm}" />
        </div>
        <div class="field">
          <label for="ps-m-nature">Nature de l'entretien</label>
          <select id="ps-m-nature" class="ps-input">${natureSel}<option value="Autre"${nature === "Autre" ? " selected" : ""}>Autre (pr\u00e9ciser)</option></select>
        </div>
        <div class="field" id="ps-m-free-field" style="display:none">
          <label for="ps-m-free">Pr\u00e9cisez la nature</label>
          <input id="ps-m-free" class="ps-input" type="text" value="" />
        </div>
        <div class="field">
          <label for="ps-m-cost">Co\u00fbt (\u20ac, optionnel)</label>
          <input id="ps-m-cost" class="ps-input" type="number" min="0" step="0.01" value="${entry.cost != null ? entry.cost : ""}" />
        </div>
        <div class="field">
          <label for="ps-m-invoice">Facture (photo ou PDF, optionnel)</label>
          <input id="ps-m-invoice" class="ps-input" type="file" accept="image/*,application/pdf" />
          ${entry.invoice_url ? `<div class="hint">Une facture est d\u00e9j\u00e0 associ\u00e9e : <a class="inv" href="${entry.invoice_url}" target="_blank">\ud83d\udcc4 voir</a></div>` : ""}
        </div>
        ${
          index == null && plans.length
            ? `<div class="field">
                 <label for="ps-m-plan">Plan d'entretien concern\u00e9 (optionnel)</label>
                 <select id="ps-m-plan" class="ps-input">${planOptions}</select>
                 <div class="hint">Si s\u00e9lectionn\u00e9, l'\u00e9ch\u00e9ance du plan repart de cet entretien.</div>
               </div>`
            : ""
        }
        <div class="editor-error" id="ps-m-error"></div>
        <div class="editor-actions">
          <button class="ps-cancel" id="ps-m-cancel">Annuler</button>
          <button class="ps-save" id="ps-m-save">Sauvegarder</button>
        </div>
      </div>`;
    card.appendChild(overlay);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) overlay.remove();
    });
    const natureSelEl = overlay.querySelector("#ps-m-nature");
    const freeField = overlay.querySelector("#ps-m-free-field");
    natureSelEl.addEventListener("change", () => {
      freeField.style.display =
        natureSelEl.value === "Autre" ? "block" : "none";
    });
    if (nature === "Autre") freeField.style.display = "block";
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
      errorBox.textContent = "Renseignez la date et le kilom\u00e9trage.";
      return;
    }
    const natureSel = overlay.querySelector("#ps-m-nature");
    let actions = natureSel.value;
    if (actions === "Autre") {
      const free = overlay.querySelector("#ps-m-free").value.trim();
      if (!free) {
        errorBox.textContent = "Pr\u00e9cisez la nature de l'entretien.";
        return;
      }
      actions = free;
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
    } else {
      const planSel = overlay.querySelector("#ps-m-plan");
      if (planSel && planSel.value) data.plan_id = planSel.value;
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
          (err && err.message) || "Erreur lors de la sauvegarde.";
      }
    );
  }

  /** Supprime un entretien apr\u00e8s confirmation. */
  _deleteMaintenance(index) {
    const main = this._findMainSensor();
    const attrs = (main && main.attributes) || {};
    const vehicleId = attrs.vehicle_id || this._config.vehicle;
    if (!window.confirm("Supprimer cet entretien ?")) {
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
      .titles { flex: 1; min-width: 0; }
      .brand { font-size: 12px; color: var(--secondary-text-color, #727272); }
      .name { font-size: 20px; font-weight: 500; }
      .status { font-size: 13px; font-weight: 600; border: 1.5px solid; border-radius: 16px; padding: 4px 12px; white-space: nowrap; }
      .photo { width: 100%; max-height: 260px; object-fit: cover; display: block; margin: 8px 0; border-radius: var(--ha-card-border-radius, 12px); }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; padding: 0 16px 8px; }
      .cell { background: var(--secondary-background-color, #f5f5f5); border-radius: 10px; padding: 10px; }
      .label { font-size: 11px; color: var(--secondary-text-color, #727272); text-transform: uppercase; letter-spacing: 0.5px; }
      .value { font-size: 20px; font-weight: 500; margin-top: 2px; }
      .value.small { font-size: 15px; }
      .section { font-size: 13px; font-weight: 600; color: var(--secondary-text-color, #727272); padding: 10px 16px 4px; text-transform: uppercase; letter-spacing: 0.5px; }
      .table { width: calc(100% - 32px); margin: 0 16px 16px; border-collapse: collapse; font-size: 13px; }
      .table th { text-align: left; color: var(--secondary-text-color, #727272); font-weight: 500; padding: 4px 6px; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .table td { padding: 6px; border-bottom: 1px solid var(--divider-color, #e0e0e0); vertical-align: top; }
      .table .num { text-align: right; white-space: nowrap; }
      .badge { color: #fff; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
      .chart { width: calc(100% - 32px); margin: 0 16px 8px; border-radius: 10px; background: var(--secondary-background-color, #f5f5f5); }
      .axis { font-size: 20px; fill: var(--secondary-text-color, #727272); }
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
  name: "PitStop Card",
  description: "Affiche toutes les informations d'un v\u00e9hicule PitStop Log.",
});
