/* Maxxicharge-Seite (eigenes Panel): zeigt die Karte für die Gesamtübersicht und jede CCU.
 * Wird von „Geräte-Informationen“ eines Geräts (Knopf „Besuchen“) und aus der Seitenleiste geöffnet.
 * Adresse: /maxxicharge?d=total  oder  /maxxicharge?d=06E8  (letzte Zeichen des CCU-Namens)  oder  ?d=alle
 */
(() => {
  class MaxxichargePanel extends HTMLElement {
    set hass(hass) {
      this._hass = hass;
      if (!this._init) {
        this._init = true;
        customElements.whenDefined("maxxicharge-card").then(() => this._build());
      } else if (this._built) {
        this._pass();
      }
    }
    set narrow(narrow) {
      this._narrow = narrow;
      if (this._menu) this._menu.narrow = narrow;
    }
    set route(_r) {}
    set panel(_p) {}

    // Geräte der Integration aus der Entity-Registry (Gesamt zuerst)
    _devices() {
      const reg = this._hass.entities || {}, seen = new Map();
      for (const e of Object.values(reg)) {
        if (e.platform !== "maxxicharge" || !e.device_id) continue;
        const d = seen.get(e.device_id) || { id: e.device_id, total: false };
        if (e.translation_key === "total_soc") d.total = true;
        seen.set(e.device_id, d);
      }
      const devs = [...seen.values()].map((d) => {
        const dev = (this._hass.devices || {})[d.id] || {};
        return { ...d, name: dev.name_by_user || dev.name || (d.total ? "Maxxicharge Gesamt" : "CCU") };
      });
      return devs.sort((a, b) => (a.total === b.total ? a.name.localeCompare(b.name) : a.total ? -1 : 1));
    }

    _wanted(devs) {
      const q = (new URLSearchParams(location.search).get("d") || this._choice || "total").trim();
      if (q.toLowerCase() === "alle") return "alle";
      if (q.toLowerCase() === "total") return (devs.find((d) => d.total) || {}).id || "alle";
      const hit = devs.find((d) => d.id === q || d.name.toLowerCase().endsWith(q.toLowerCase()));
      return hit ? hit.id : "alle";
    }

    _build() {
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      this.shadowRoot.innerHTML = `
        <style>
          :host { display:block; min-height:100%; background:var(--primary-background-color,#0b0f0d); color:var(--primary-text-color,#e8eceb); }
          .bar { display:flex; align-items:center; gap:10px; padding:10px 16px; background:var(--app-header-background-color,#101916); color:var(--app-header-text-color,#fff); position:sticky; top:0; z-index:2; }
          .bar h1 { font-size:1.15em; font-weight:500; margin:0; flex:1; }
          .tabs { display:flex; gap:8px; flex-wrap:wrap; padding:14px 16px 4px; max-width:1200px; margin:0 auto; }
          .tab { cursor:pointer; border:1px solid rgba(255,255,255,.18); background:transparent; color:inherit; border-radius:18px; padding:6px 14px; font:inherit; }
          .tab.on { background:#34c759; border-color:#34c759; color:#06210f; font-weight:600; }
          .body { display:grid; gap:16px; padding:12px 16px 24px; max-width:1200px; margin:0 auto; grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr)); justify-items:center; }
          .body.one { grid-template-columns:minmax(0,560px); justify-content:center; }
          .body > * { width:100%; }
          a.web { color:#9fe3b0; font-size:.9em; text-decoration:none; border:1px solid rgba(255,255,255,.2); border-radius:14px; padding:4px 10px; }
          .empty { padding:40px 16px; text-align:center; opacity:.7; }
        </style>
        <div class="bar"><ha-menu-button id="menu"></ha-menu-button><h1>Maxxicharge</h1><a class="web" id="web" target="_blank" rel="noopener" hidden>CCU-Weboberfläche</a></div>
        <div class="tabs" id="tabs"></div>
        <div class="body" id="body"></div>`;
      this._menu = this.shadowRoot.getElementById("menu");
      if (this._menu) { this._menu.hass = this._hass; this._menu.narrow = !!this._narrow; }
      this._built = true;
      this._render();
    }

    _render() {
      const $ = (id) => this.shadowRoot.getElementById(id);
      const devs = this._devices();
      const want = this._wanted(devs);
      this._choice = want === "alle" ? "alle" : devs.find((d) => d.id === want)?.total ? "total" : (devs.find((d) => d.id === want)?.name || "").slice(-4);
      $("tabs").innerHTML = "";
      const mk = (label, id) => {
        const b = document.createElement("button");
        b.className = `tab${want === id ? " on" : ""}`;
        b.textContent = label;
        b.onclick = () => {
          const key = id === "alle" ? "alle" : devs.find((d) => d.id === id).total ? "total" : devs.find((d) => d.id === id).name.slice(-4);
          history.replaceState(null, "", `${location.pathname}?d=${encodeURIComponent(key)}`);
          this._render();
        };
        $("tabs").appendChild(b);
      };
      devs.forEach((d) => mk(d.name, d.id));
      if (devs.length > 1) mk("Alle", "alle");

      const body = $("body");
      body.innerHTML = "";
      this._cards = [];
      body.className = `body${want === "alle" ? "" : " one"}`;
      if (!devs.length) {
        body.innerHTML = '<div class="empty">Keine Maxxicharge-Geräte gefunden. Ist die Integration eingerichtet?</div>';
        $("web").hidden = true;
        return;
      }
      const show = want === "alle" ? devs : devs.filter((d) => d.id === want);
      for (const d of show) {
        const card = document.createElement("maxxicharge-card");
        card.setConfig(d.total ? { switcher: false } : { device: d.id, switcher: false });
        card.hass = this._hass;
        body.appendChild(card);
        this._cards.push(card);
      }
      // Link zur CCU-Weboberfläche, wenn genau eine CCU gewählt ist
      const web = $("web");
      web.hidden = true;
      if (show.length === 1 && !show[0].total) {
        for (const [id, e] of Object.entries(this._hass.entities || {})) {
          if (e.platform === "maxxicharge" && e.device_id === show[0].id && e.translation_key === "ccu_ip") {
            const ip = this._hass.states[id] && this._hass.states[id].state;
            if (ip && /^[0-9a-f.:]+$/i.test(ip)) { web.href = `http://${ip}`; web.hidden = false; }
          }
        }
      }
    }

    _pass() {
      if (this._menu) this._menu.hass = this._hass;
      (this._cards || []).forEach((c) => (c.hass = this._hass));
    }
  }

  if (!customElements.get("maxxicharge-panel")) customElements.define("maxxicharge-panel", MaxxichargePanel);
})();
