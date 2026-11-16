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

  /** Ouvre la fen\u00eatre de modification de l'immatriculation. */
  _openRegEditor() {
    const root = this.shadowRoot;
    const main = this._findMainSensor();
    const currentReg =
      main && main.attributes ? main.attributes.registration || "" : "";
    const vehicleId =
      main && main.attributes && main.attributes.vehicle_id
        ? main.attributes.vehicle_id
        : this._config.vehicle;
    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="editor">
          <div class="editor-title">Modification de l'immatriculation</div>
          <div class="editor-sub">${this._config.vehicle}</div>
          <div class="field">
            <label for="ps-reg">Immatriculation (carte grise)</label>
            <input id="ps-reg" class="ps-input" type="text" value="${currentReg}" />
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
      this._saveRegistration(vehicleId)
    );
    root.querySelector("#ps-reg").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._saveRegistration(vehicleId);
    });
  }

  /** Sauvegarde l'immatriculation via le service. */
  _saveRegistration(vehicleId) {
    const root = this.shadowRoot;
    const value = root.querySelector("#ps-reg").value.trim();
    const errorBox = root.querySelector("#ps-error");
    errorBox.textContent = "";
    if (!value) {
      errorBox.textContent = "Saisissez une immatriculation.";
      return;
    }
    const button = root.querySelector("#ps-save");
    button.disabled = true;
    this._hass
      .callService("pitstop_log", "update_registration", {
        vehicle_id: vehicleId,
        registration: value,
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

  /** Ouvre la fen\u00eatre de modification de la date d'achat. */
  _openDateEditor() {
    const root = this.shadowRoot;
    const main = this._findMainSensor();
    const currentDate =
      main && main.attributes ? main.attributes.purchase_date || "" : "";
    const vehicleId =
      main && main.attributes && main.attributes.vehicle_id
        ? main.attributes.vehicle_id
        : this._config.vehicle;
    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="editor">
          <div class="editor-title">Modification de la date d'achat</div>
          <div class="editor-sub">${this._config.vehicle}</div>
          <div class="field">
            <label for="ps-date">Date d'achat (mise en service)</label>
            <input id="ps-date" class="ps-input" type="date" value="${currentDate}" />
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
      this._savePurchaseDate(vehicleId)
    );
    root.querySelector("#ps-date").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._savePurchaseDate(vehicleId);
    });
  }

  /** Sauvegarde la date d'achat via le service. */
  _savePurchaseDate(vehicleId) {
    const root = this.shadowRoot;
    const value = root.querySelector("#ps-date").value;
    const errorBox = root.querySelector("#ps-error");
    errorBox.textContent = "";
    if (!value) {
      errorBox.textContent = "Choisissez une date.";
      return;
    }
    const button = root.querySelector("#ps-save");
    button.disabled = true;
    this._hass
      .callService("pitstop_log", "update_purchase_date", {
        vehicle_id: vehicleId,
        date: value,
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
            V\u00e9hicule \u00ab ${this._config.vehicle} \u00bb introuvable.
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
      .slice()
      .reverse()
      .slice(0, 5)
      .map(
        (h) => `
        <tr>
          <td>${h.date || ""}</td>
          <td class="num">${h.km != null ? Number(h.km).toLocaleString() + " km" : ""}</td>
          <td>${h.actions || ""}</td>
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " \u20ac" : ""}</td>
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
      ? `<img class="photo" src="${attrs.photo}" alt="${this._config.vehicle}">`
      : "";

    root.innerHTML = `
      <style>${PitstopCard._styles()}</style>
      <ha-card>
        <div class="header">
          ${logo}
          <div class="titles">
            <div class="name">${this._config.title || this._config.vehicle}</div>
            <div class="brand">${attrs.brand || ""}${attrs.brand ? " \u00b7 " : ""}${attrs.model || ""}</div>
          </div>
          <div class="statusbox">
            <div class="status" style="border-color:${statusColor};color:${statusColor}">${main.state}</div>
          </div>
        </div>
        ${photo}
        <div class="grid">
          <div class="cell">
            <div class="label">Kilom\u00e9trage
              <span class="gear" title="Mettre \u00e0 jour le kilom\u00e9trage">
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
              <span class="gear gear-reg" title="Mettre \u00e0 jour l'immatriculation">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
                </svg>
              </span>
            </div>
            <div class="value small">${attrs.registration || "\u2014"}</div>
          </div>
          <div class="cell">
            <div class="label">Date d'achat
              <span class="gear gear-date" title="Mettre \u00e0 jour la date d'achat">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19.14 12.94a7.07 7.07 0 0 0 .05-.94 7.07 7.07 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 0 0-.6.22L2.66 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.03.31-.05.63-.05.94s.02.63.05.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z"/>
                </svg>
              </span>
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
        ${
          history
            ? `<div class="section">Derniers entretiens</div>
               <table class="table"><thead><tr><th>Date</th><th>Km</th><th>Actions</th><th>Co\u00fbt</th></tr></thead><tbody>${history}</tbody></table>`
            : ""
        }
      </ha-card>`;
    const gear = root.querySelector(".gear:not(.gear-reg)");
    if (gear) gear.addEventListener("click", () => this._openEditor());
    const gearReg = root.querySelector(".gear-reg");
    if (gearReg) gearReg.addEventListener("click", () => this._openRegEditor());
    const gearDate = root.querySelector(".gear-date");
    if (gearDate) gearDate.addEventListener("click", () => this._openDateEditor());
  }

  static _styles() {
    return `
      ha-card { overflow: hidden; }
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
    `;
  }
}

customElements.define("pitstop-card", PitstopCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "pitstop-card",
  name: "PitStop Card",
  description: "Affiche toutes les informations d'un v\u00e9hicule PitStop Log.",
});
