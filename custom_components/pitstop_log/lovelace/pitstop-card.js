/**
 * PitStop Card — carte Lovelace pour l'intégration PitStop Log.
 *
 * Affiche toutes les informations d'un véhicule : photo, logo de marque,
 * kilométrage, statut d'entretien, plans à faire et historique.
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
      throw new Error("Vous devez définir 'vehicle: <nom du véhicule>'");
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

  /** Trouve le capteur « Prochain entretien » du véhicule. */
  _findMainSensor() {
    const slug = this._config.vehicle
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
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

  /** Trouve les entités du véhicule par préfixe de nom. */
  _findEntities() {
    const slug = this._config.vehicle
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
    const found = { odometer: null, plans: [], history: null };
    for (const entityId in this._hass.states) {
      const state = this._hass.states[entityId];
      if (state.attributes && state.attributes.vehicle !== this._config.vehicle) {
        continue;
      }
      if (entityId === `sensor.${slug}_kilometrage`) found.odometer = state;
      else if (state.attributes && state.attributes.km_remaining !== undefined) {
        found.plans.push(state);
      }
    }
    return found;
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
            Véhicule « ${this._config.vehicle} » introuvable.
            Vérifiez le nom dans la configuration de la carte.
          </div>
        </ha-card>`;
      return;
    }

    const attrs = main.attributes || {};
    const statusColors = {
      "OK": "var(--label-badge-green, #13ba6e)",
      "Bientôt dû": "var(--label-badge-yellow, #ffab40)",
      "En retard": "var(--label-badge-red, #fce588)",
      "Due soon": "var(--label-badge-yellow, #ffab40)",
      "Overdue": "var(--label-badge-red, #fce588)",
    };
    const statusColor =
      statusColors[main.state] || "var(--primary-color, #03a9f4)";

    const plans = entities.plans
      .map(
        (p) => `
        <tr>
          <td>${p.attributes.friendly_name || p.entity_id}</td>
          <td><span class="badge" style="background:${statusColors[p.state] || "var(--primary-color)"}">${p.state}</span></td>
          <td class="num">${p.attributes.km_remaining != null ? p.attributes.km_remaining.toLocaleString() + " km" : "—"}</td>
          <td class="num">${p.attributes.days_remaining != null ? p.attributes.days_remaining + " j" : "—"}</td>
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
          <td class="num">${h.cost != null ? Number(h.cost).toLocaleString() + " €" : ""}</td>
        </tr>`
      )
      .join("");

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
            <div class="brand">${attrs.brand || ""}${attrs.brand ? " · " : ""}${attrs.model || ""}</div>
            <div class="name">${this._config.title || this._config.vehicle}</div>
          </div>
          <div class="statusbox">
            <div class="status" style="border-color:${statusColor};color:${statusColor}">${main.state}</div>
          </div>
        </div>
        ${photo}
        <div class="grid">
          <div class="cell">
            <div class="label">Kilométrage</div>
            <div class="value">${
              entities.odometer
                ? Number(entities.odometer.state).toLocaleString() + " km"
                : "—"
            }</div>
          </div>
          <div class="cell">
            <div class="label">Immatriculation</div>
            <div class="value small">${attrs.registration || "—"}</div>
          </div>
          <div class="cell">
            <div class="label">Date d'achat</div>
            <div class="value small">${attrs.purchase_date || "—"}</div>
          </div>
          <div class="cell">
            <div class="label">Entretiens réalisés</div>
            <div class="value">${attrs.history_count != null ? attrs.history_count : "—"}</div>
          </div>
        </div>
        ${
          plans
            ? `<div class="section">Entretiens à faire</div>
               <table class="table"><thead><tr><th>Plan</th><th>Statut</th><th>Reste</th><th>Échéance</th></tr></thead><tbody>${plans}</tbody></table>`
            : ""
        }
        ${
          history
            ? `<div class="section">Derniers entretiens</div>
               <table class="table"><thead><tr><th>Date</th><th>Km</th><th>Actions</th><th>Coût</th></tr></thead><tbody>${history}</tbody></table>`
            : ""
        }
      </ha-card>`;
  }

  static _styles() {
    return `
      ha-card { overflow: hidden; }
      .pad { padding: 16px; }
      .error { color: var(--error-color, #db4437); }
      .header { display: flex; align-items: center; gap: 12px; padding: 16px 16px 8px; }
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
    `;
  }
}

customElements.define("pitstop-card", PitstopCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "pitstop-card",
  name: "PitStop Card",
  description: "Affiche toutes les informations d'un véhicule PitStop Log.",
});
