/* Maxxicharge-Karte im Stil der Maxxisun-App: Haus mit PV und Speicher, Kacheln, Verlauf „Haushalt“.
 * Eine Datei, keine Abhängigkeiten. Dashboard: type: custom:maxxicharge-card
 *
 * Optionen (alle optional):
 *   device: <Geräte-ID>       # CCU oder „Maxxicharge Gesamt“ (ohne Angabe: Gesamtübersicht); im Editor auswählbar
 *   switcher: true            # Umschalter Gesamt / CCUs in der Karte (Standard: an, wenn kein Gerät festgelegt ist)
 *   modules: [scene, tiles, chart, stats]   # Bausteine: Haus-Grafik, Kacheln, Verlauf, Kennzahlen
 *   tiles: [pv, house, grid, ccu, store]    # welche Kacheln
 *   title: Maxxicharge        # Überschrift
 *   hours: 3                  # Zeitraum des Verlaufs in Stunden
 *   pv_max: 4000              # Skala des PV-Balkens in W
 *   house_max: 3000           # Skala des Verbrauchs-Balkens in W
 *   ccu_max: 2300             # Skala des CCU-Balkens in W
 *   entities: { pv: sensor.xxx, grid: sensor.xxx }   # Entities überschreiben (Schlüssel siehe KEYS)
 * Die Entities werden automatisch gefunden (Gesamtübersicht oder gewählte CCU).
 */
(() => {
  const TOTAL_KEYS = {
    pv: "total_pv_power",
    charge: "total_battery_charge_power",
    discharge: "total_battery_discharge_power",
    grid: "total_grid_power",
    house: "total_house_power",
    soc: "total_soc",
    feed: "total_ac_feed",
    draw: "total_ac_draw",
    runtime: "total_runtime",
    ttf: "total_time_to_full",
    autarky: "total_autarky",
    usable: "total_usable_energy",
    pvtoday: "total_pv_today",
    temp: "total_temperature",
    fault: "total_fault",
    lock: "write_lock",
    online: "total_online",
  };
  // Entities einer einzelnen CCU (Übersetzungsschlüssel der Integration)
  const CCU_KEYS = {
    pv: "pv_power",
    charge: "battery_charge_power",
    discharge: "battery_discharge_power",
    grid: "grid_power",
    soc: "soc",
    feed: "ac_feed_power",
    draw: "ac_draw_power",
    runtime: "runtime",
    ttf: "time_to_full",
    usable: "usable_energy_kwh",
    pvtoday: "pv_energy_today",
    temp: "temperature",
    online: "online",
    f1: "inverter_fault",
    f2: "battery_fault",
    f3: "meter_timeout",
  };
  const ALL_MODULES = ["scene", "tiles", "chart", "stats"];
  const ALL_TILES = ["pv", "house", "grid", "ccu", "store"];
  const C = { grid: "#e0568a", ccu: "#a98bf0", draw: "#f5a623", pv: "#f5a623", green: "#3ecf5a", blue: "#4a90e2" };

  const fmtW = (v) => {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    return Math.abs(v) >= 10000 ? `${(v / 1000).toFixed(1).replace(".", ",")} kW` : `${Math.round(v)} W`;
  };
  const fmtH = (h) => {
    if (h === null || h === undefined || Number.isNaN(h)) return "–";
    if (h < 1) return `${Math.round(h * 60)} min`;
    return `${Math.floor(h)} h ${Math.round((h % 1) * 60)} min`;
  };
  const pct = (v, max) => (v === null || !max ? 0 : Math.max(0, Math.min(100, (v / max) * 100)));

  function niceRange(values) {
    // vier gleich große Schritte mit runden Werten, Null liegt auf einer Linie
    const min = Math.min(0, ...values), max = Math.max(0, ...values);
    for (const step of [25, 50, 100, 200, 250, 500, 1000, 2000, 5000]) {
      const lo = Math.floor(min / step) * step;
      const hi = lo + 4 * step;
      if (hi >= max && hi - lo >= 100) return { lo, hi, step };
    }
    return { lo: 0, hi: 10000, step: 2500 };
  }

  class MaxxichargeCard extends HTMLElement {
    setConfig(config) {
      this._config = { hours: 3, pv_max: 4000, house_max: 3000, ccu_max: 2300, ...config };
      if (this._config.switcher === undefined) this._config.switcher = !this._config.device;
      this._sel = null;
      if (this._config.switcher) {
        try { this._sel = localStorage.getItem(this._selKey()) || null; } catch (e) { this._sel = null; }
      }
      if (!Array.isArray(this._config.modules) || !this._config.modules.length) this._config.modules = ALL_MODULES;
      if (!Array.isArray(this._config.tiles) || !this._config.tiles.length) this._config.tiles = ALL_TILES;
      this._built = false;
      this._hist = null;
      this._histAt = 0;
      if (this._hass) this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._built) this._render();
      this._update();
      this._maybeLoadHistory();
    }

    getCardSize() {
      return 7;
    }

    static getStubConfig() {
      return {};
    }

    static getConfigElement() {
      return document.createElement("maxxicharge-card-editor");
    }

    disconnectedCallback() {
      this._gone = true;
    }

    // ---------- Daten ----------
    _index() {
      const reg = this._hass.entities || {};
      if (this._regRef === reg && this._idx) return this._idx;
      const byDev = new Map(), byKey = new Map();
      for (const [id, e] of Object.entries(reg)) {
        if (e.platform !== "maxxicharge" || !e.translation_key) continue;
        byDev.set(`${e.device_id}|${e.translation_key}`, id);
        if (!byKey.has(e.translation_key)) byKey.set(e.translation_key, id);
      }
      this._regRef = reg;
      this._idx = { byDev, byKey };
      return this._idx;
    }
    _selKey() {
      return `maxxicharge-card-sel:${this._config.title || ""}:${this._config.device || ""}`;
    }
    _device() {
      if (this._sel) return this._sel === "total" ? undefined : this._sel;
      return this._config.device;
    }
    _devices() {
      const { byDev } = this._index(), ids = new Map();
      for (const key of byDev.keys()) {
        const [id, tk] = key.split("|");
        const d = ids.get(id) || { id, total: false };
        if (tk === "total_soc") d.total = true;
        ids.set(id, d);
      }
      const list = [...ids.values()].map((d) => {
        const dev = (this._hass.devices || {})[d.id] || {};
        return { ...d, name: dev.name_by_user || dev.name || (d.total ? "Gesamt" : "CCU") };
      });
      return list.sort((a, b) => (a.total === b.total ? a.name.localeCompare(b.name) : a.total ? -1 : 1));
    }
    _mode() {
      const dev = this._device();
      if (dev && !this._index().byDev.has(`${dev}|total_soc`)) return "ccu";
      return "total";
    }
    _entity(key) {
      const override = this._config.entities && this._config.entities[key];
      if (override) return override;
      const { byDev, byKey } = this._index();
      if (key === "lock") return byKey.get("write_lock") || null;
      if (this._mode() === "total") return byKey.get(TOTAL_KEYS[key]) || null;
      const tk = CCU_KEYS[key];
      return tk ? byDev.get(`${this._device()}|${tk}`) || null : null;
    }
    _raw(key) {
      const id = this._entity(key);
      const st = id && this._hass.states[id];
      return st ? st.state : null;
    }
    _rawNum(key) {
      const id = this._entity(key);
      const st = id && this._hass.states[id];
      if (!st || st.state === "unknown" || st.state === "unavailable") return null;
      let n = Number(st.state);
      if (Number.isNaN(n)) return null;
      if (key === "pvtoday") {  // Einheit der Entity beachten (CCU: Wh, Gesamt: kWh)
        const unit = st.attributes && st.attributes.unit_of_measurement;
        if (unit === "Wh") n /= 1000;
        else if (unit === "MWh") n *= 1000;
      }
      return n;
    }
    _state(key) {
      if (key === "fault" && this._mode() === "ccu") {
        const on = ["f1", "f2", "f3"].some((k) => this._raw(k) === "on");
        return this._raw("f1") === null ? null : on ? "on" : "off";
      }
      return this._raw(key);
    }
    _num(key) {
      if (this._mode() === "ccu") {
        if (key === "autarky") return null;
        if (key === "house") {  // Verbrauch = Netz + CCU-Abgabe - CCU-Aufnahme (nur mit Zähler an dieser CCU)
          const grid = this._rawNum("grid");
          return grid === null ? null : grid + (this._rawNum("feed") || 0) - (this._rawNum("draw") || 0);
        }
      }
      return this._rawNum(key);
    }
    _title() {
      if (this._config.title) return this._config.title;
      const dev = this._device(), d = dev && this._hass.devices && this._hass.devices[dev];
      return d ? d.name_by_user || d.name || "Maxxicharge" : "Maxxicharge";
    }

    async _maybeLoadHistory() {
      const now = Date.now();
      if (!this._built || this._loading || now - this._histAt < 120000 || !this._hass.callWS) return;
      const idGrid = this._entity("grid"), idFeed = this._entity("feed"), idDraw = this._entity("draw");
      if (!idFeed && !idDraw) return;
      const ids = [idGrid, idFeed, idDraw].filter(Boolean);
      this._loading = true;
      try {
        const hours = Number(this._config.hours) || 3;
        const end = new Date(), start = new Date(end.getTime() - hours * 3600 * 1000);
        const res = await this._hass.callWS({
          type: "history/history_during_period",
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          entity_ids: ids,
          minimal_response: true,
          no_attributes: true,
          significant_changes_only: false,
        });
        const N = 60, t0 = start.getTime() / 1000, dt = (hours * 3600) / N;
        const ser = (id) => {
          if (!id) return null;
          const rows = (res && res[id]) || [];
          const pts = rows
            .map((r) => ({ t: Number(r.lu ?? r.last_updated_ts ?? (r.last_updated ? Date.parse(r.last_updated) / 1000 : NaN)), v: Number(r.s ?? r.state) }))
            .filter((p) => !Number.isNaN(p.t) && !Number.isNaN(p.v));
          let i = 0, last = pts.length ? pts[0].v : null;
          const out = [];
          for (let b = 0; b <= N; b++) {
            const tb = t0 + b * dt;
            while (i < pts.length && pts[i].t <= tb) { last = pts[i].v; i++; }
            out.push(last);
          }
          return out;
        };
        const g = ser(idGrid), f = ser(idFeed), d = ser(idDraw);
        const base = f || d;
        this._hist = {
          grid: g || [],
          ccu: base.map((_, i) => {
            const fv = f ? f[i] : null, dv = d ? d[i] : null;
            return fv === null && dv === null ? null : (fv || 0) - (dv || 0);
          }),
        };
        this._histAt = Date.now();
        if (!this._gone) this._drawChart();
      } catch (err) {
        this._histAt = Date.now();
      } finally {
        this._loading = false;
      }
    }

    // ---------- Aufbau ----------
    _render() {
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      this.shadowRoot.innerHTML = `
        <style>
          :host { display:block; }
          ha-card { display:block; overflow:hidden; background:linear-gradient(180deg,#0a0e0d 0%,#0b1a12 100%); color:#e8eceb; padding:14px 14px 12px; border-radius:14px; }
          .top { display:flex; align-items:center; justify-content:space-between; min-height:30px; }
          .title { font-weight:600; font-size:1.05em; letter-spacing:.2px; }
          .badges { display:flex; gap:6px; }
          .chips { display:flex; gap:6px; flex-wrap:wrap; margin:6px 0 2px; }
          .chips:empty { display:none; }
          .chip { cursor:pointer; border:1px solid rgba(255,255,255,.2); background:rgba(255,255,255,.04); color:#cfd8d3; border-radius:14px; padding:3px 11px; font:inherit; font-size:.82em; }
          .chip.on { background:#34c759; border-color:#34c759; color:#06210f; font-weight:600; }
          .badge { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; background:#f2b705; color:#1b1b1b; }
          .badge.lock { background:#d9a21a; }
          .badge.off { background:#555; color:#ddd; }
          .scene { position:relative; margin-top:4px; }
          .scene.flat { display:grid; grid-template-columns:repeat(auto-fit,minmax(118px,1fr)); gap:8px; margin-top:10px; }
          .scene.flat .tile { position:static; width:auto; }
          .scene svg { width:100%; height:auto; display:block; }
          .tile { position:absolute; width:28.5%; min-width:0; overflow:hidden; box-sizing:border-box; background:linear-gradient(160deg,rgba(40,50,55,.92),rgba(20,26,29,.92)); border:1px solid rgba(255,255,255,.14); border-radius:12px; padding:7px 10px 8px; backdrop-filter:blur(4px); box-shadow:0 4px 14px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.06); }
          .tile .k { font-size:10.5px; color:#aeb9bd; display:flex; align-items:center; gap:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
          .tile .k .ic { font-size:12px; } .tile .ts { font-size:10px; color:#c4ced1; font-weight:600; min-height:12px; margin-top:1px; white-space:nowrap; }
          .tile .v { font-size:19px; font-weight:700; margin-top:2px; white-space:nowrap; letter-spacing:.2px; }
          .tile .v small { font-size:11px; font-weight:500; color:#aeb9bd; margin-right:4px; }
          .tile .v .u { font-size:12px; font-weight:600; color:#c4ced1; margin-left:2px; }
          .bar { height:4px; border-radius:2px; background:rgba(255,255,255,.12); margin-top:6px; overflow:hidden; }
          .bar i { display:block; height:100%; border-radius:2px; width:0; transition:width .6s; box-shadow:0 0 8px currentColor; }
          .t-pv { left:2%; top:9%; } .t-house { left:69.5%; top:2%; }
          .t-grid { left:2%; bottom:1%; } .t-ccu { left:35.75%; bottom:1%; } .t-store { left:69.5%; bottom:1%; }
          .sect { margin:10px 2px 2px; font-size:.78em; letter-spacing:1.3px; color:#9fb0a8; text-transform:uppercase; display:flex; align-items:center; gap:6px; }
          #chart { width:100%; height:auto; display:block; }
          .ax { font-size:9.5px; fill:#8da097; }
          .legend { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:6px; font-size:.78em; margin-top:2px; }
          .legend .col { display:flex; flex-direction:column; gap:3px; color:#b9c4c0; }
          .legend .col.r { align-items:flex-end; text-align:right; }
          .legend .dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
          .legend .r .dot { margin:0 0 0 5px; }
          .nums { display:flex; gap:18px; }
          .num { text-align:center; }
          .num .n { font-family:"Roboto Condensed","Arial Narrow",Roboto,sans-serif; font-size:2em; font-weight:700; line-height:1.05; }
          .num .cap { font-size:.78em; color:#9fb0a8; margin-top:1px; }
          .foot { display:grid; grid-template-columns:repeat(auto-fit,minmax(104px,1fr)); gap:8px; margin-top:12px; }
          .st { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.07); border-radius:10px; padding:7px 10px; }
          .st .sl { font-size:.72em; color:#9fb0a8; letter-spacing:.3px; } .st .sv { font-size:1.02em; font-weight:600; color:#eef2f1; margin-top:1px; }
          .msg { padding:18px 8px; color:#9fb0a8; }
          .flowdot { display:none; }
          .on .flowdot { display:inline; }
        </style>
        <ha-card>
          <div class="top"><div class="title"></div><div class="badges" id="badges"></div></div>
          <div class="chips" id="chips"></div>
          <div class="msg" id="msg" hidden>Keine Maxxicharge-Werte gefunden. Wähle im Karten-Editor ein Gerät aus oder richte „Maxxicharge Gesamt“ ein.</div>
          <div id="main">
            <div class="scene" id="scene">
              ${this._houseSvg()}
              <div class="tile t-pv" data-tile="pv"><div class="k"><span class="ic">☀️</span>PV-Leistung</div><div class="v" id="v-pv">–</div><div class="bar"><i id="b-pv" style="background:linear-gradient(90deg,#f5a623,#ff7a18);color:#ff9a2e"></i></div></div>
              <div class="tile t-house" data-tile="house"><div class="k"><span class="ic">🏠</span>Verbrauch</div><div class="v" id="v-house">–</div><div class="bar"><i id="b-house" style="background:${C.green};color:${C.green}"></i></div></div>
              <div class="tile t-grid" data-tile="grid"><div class="k"><span class="ic">⚡</span>Netz</div><div class="v" id="v-grid">–</div><div class="ts" id="s-grid"></div><div class="bar"><i id="b-grid" style="background:${C.blue};color:${C.blue}"></i></div></div>
              <div class="tile t-ccu" data-tile="ccu"><div class="k"><span class="ic">🔌</span>CCU-Abgabe</div><div class="v" id="v-ccu">–</div><div class="bar"><i id="b-ccu" style="background:${C.ccu};color:${C.ccu}"></i></div></div>
              <div class="tile t-store" data-tile="store"><div class="k"><span class="ic">🔋</span>Speicher</div><div class="v" id="v-soc">–</div><div class="ts" id="s-state"></div><div class="bar"><i id="b-soc" style="background:${C.green};color:${C.green}"></i></div></div>
            </div>
            <div id="m-chart">
            <div class="sect">⚡ Haushalt</div>
            ${this._chartSvg()}
            <div class="legend">
              <div class="col"><span><span class="dot" style="background:${C.grid}"></span>Netzbezug</span><span><span class="dot" style="background:#7a3050"></span>Einspeisung</span></div>
              <div class="nums"><div class="num"><div class="n" id="n-grid" style="color:${C.grid}">–</div><div class="cap" id="c-grid">Netzbezug</div></div><div class="num"><div class="n" id="n-ccu" style="color:${C.ccu}">–</div><div class="cap" id="c-ccu">CCU-Abgabe</div></div></div>
              <div class="col r"><span>CCU-Abgabe<span class="dot" style="background:${C.ccu}"></span></span><span>CCU-Aufnahme<span class="dot" style="background:${C.draw}"></span></span></div>
            </div>
            </div>
            <div class="foot" id="foot"></div>
          </div>
        </ha-card>`;
      this._built = true;
      this._applyLayout();
    }

    _renderChips() {
      const box = this.shadowRoot.getElementById("chips");
      if (!this._config.switcher) { box.innerHTML = ""; return; }
      const devs = this._devices();
      const current = this._sel || (this._config.device ? this._config.device : "total");
      const sig = `${current}|${devs.map((d) => d.id + d.name).join(",")}`;
      if (sig === this._chipSig) return;
      this._chipSig = sig;
      box.innerHTML = "";
      if (devs.length < 2) return;
      for (const d of devs) {
        const key = d.total ? "total" : d.id;
        const b = document.createElement("button");
        b.className = `chip${current === key || (d.total && current === "total") ? " on" : ""}`;
        b.textContent = d.name;
        b.onclick = () => this._select(key);
        box.appendChild(b);
      }
    }

    _select(key) {
      this._sel = key;
      try { localStorage.setItem(this._selKey(), key); } catch (e) { /* ohne Speicher weiter */ }
      this._hist = null;
      this._histAt = 0;
      this._chipSig = "";
      this._update();
      this._maybeLoadHistory();
    }

    _applyLayout() {
      const $ = (id) => this.shadowRoot.getElementById(id);
      const mods = new Set(this._config.modules), tiles = new Set(this._config.tiles);
      const art = mods.has("scene"), showTiles = mods.has("tiles");
      $("scene").style.display = art || showTiles ? "" : "none";
      $("scene").classList.toggle("flat", !art);
      $("house").style.display = art ? "" : "none";
      this.shadowRoot.querySelectorAll("[data-tile]").forEach((el) => {
        el.style.display = showTiles && tiles.has(el.dataset.tile) ? "" : "none";
      });
      this.shadowRoot.querySelectorAll("[data-t]").forEach((el) => {
        el.style.display = showTiles && tiles.has(el.dataset.t) ? "" : "none";
      });
      $("m-chart").style.display = mods.has("chart") ? "" : "none";
      $("foot").style.display = mods.has("stats") ? "" : "none";
    }

    _houseSvg() {
      // Schräge 3D-Ansicht (Kabinettprojektion): Frontwand, Seitenwand rechts, Satteldach mit Solarmodulen
      const A = [128, 112], B = [300, 112], R1 = [148, 57], R2 = [320, 57];
      const P = (u, v) => [A[0] + u * (B[0] - A[0]) + v * (R1[0] - A[0]), A[1] + u * (B[1] - A[1]) + v * (R1[1] - A[1])];
      const pt = (q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`;
      let panels = "";
      const cols = 8, rows = 3, gu = 0.012, gv = 0.03, mu = 0.045, mv = 0.09;
      const cw = (1 - 2 * mu - (cols - 1) * gu) / cols, ch = (1 - 2 * mv - (rows - 1) * gv) / rows;
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const u0 = mu + c * (cw + gu), v0 = mv + r * (ch + gv);
          const q = [P(u0, v0), P(u0 + cw, v0), P(u0 + cw, v0 + ch), P(u0, v0 + ch)];
          const shade = q.map((m) => [m[0] + 1.3, m[1] + 1.8]);  // Dicke: Schatten leicht versetzt dahinter
          panels += `<polygon points="${shade.map(pt).join(" ")}" fill="#070d13" opacity=".7"/>`;
          panels += `<polygon points="${q.map(pt).join(" ")}" fill="url(#gPanel)" stroke="#aebdc7" stroke-width=".9" stroke-linejoin="round"/>`;
          for (let k = 1; k < 4; k++) {  // Zellenlinien
            const a = P(u0 + (cw * k) / 4, v0), b = P(u0 + (cw * k) / 4, v0 + ch);
            panels += `<line x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${b[0].toFixed(1)}" y2="${b[1].toFixed(1)}" stroke="#4a6076" stroke-width=".45"/>`;
          }
          const m1 = P(u0, v0 + ch / 2), m2 = P(u0 + cw, v0 + ch / 2);
          panels += `<line x1="${m1[0].toFixed(1)}" y1="${m1[1].toFixed(1)}" x2="${m2[0].toFixed(1)}" y2="${m2[1].toFixed(1)}" stroke="#4a6076" stroke-width=".45"/>`;
        }
      }
      const sheen = [P(mu, mv), P(0.55, mv), P(0.28, 1 - mv), P(mu, 1 - mv)];
      const battery = (x) => `
        <polygon points="${x},158 ${x + 6},155 ${x + 22},155 ${x + 16},158" fill="#4a535a"/>
        <polygon points="${x + 16},158 ${x + 22},155 ${x + 22},201 ${x + 16},204" fill="#1d2225"/>
        <rect x="${x}" y="158" width="16" height="46" fill="#30373c" stroke="#505a62" stroke-width=".8"/>
        <rect x="${x + 3}" y="170" width="10" height="26" rx="1" fill="#22282c"/>`;
      return `
        <svg viewBox="0 0 400 316" id="house" role="img" aria-label="Haus mit PV und Speicher">
          <defs>
            <linearGradient id="gWall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b3c3cb"/><stop offset="1" stop-color="#8a9da7"/></linearGradient>
            <linearGradient id="gSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8396a0"/><stop offset="1" stop-color="#6c7e88"/></linearGradient>
            <linearGradient id="gRoof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8b9ea8"/><stop offset="1" stop-color="#6d808a"/></linearGradient>
            <linearGradient id="gPanel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34495f"/><stop offset=".55" stop-color="#1c2b3b"/><stop offset="1" stop-color="#121b26"/></linearGradient>
            <linearGradient id="gSheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".30"/><stop offset=".6" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
            <linearGradient id="gWin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#ff8a1f"/></linearGradient>
            <radialGradient id="gGlow"><stop offset="0" stop-color="#ffb347" stop-opacity=".55"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
            <radialGradient id="gSky"><stop offset="0" stop-color="#1f4a31" stop-opacity=".55"/><stop offset="1" stop-color="#1f4a31" stop-opacity="0"/></radialGradient>
            <radialGradient id="gSun"><stop offset="0" stop-color="#fff2b0" stop-opacity=".9"/><stop offset="1" stop-color="#ffd24d" stop-opacity="0"/></radialGradient>
          </defs>
          <ellipse cx="200" cy="150" rx="210" ry="140" fill="url(#gSky)"/>
          <ellipse cx="200" cy="224" rx="192" ry="20" fill="#0f1c15" opacity=".8"/>
          <!-- Bodenplatte -->
          <polygon points="14,200 392,200 392,214 14,214" fill="#6a7c86"/>
          <polygon points="14,200 392,200 380,194 26,194" fill="#7f929c"/>
          <!-- Seitenwand rechts und Giebel -->
          <polygon points="300,112 340,90 340,182 300,204" fill="url(#gSide)"/>
          <polygon points="300,112 340,90 320,57" fill="#a3b4bd" stroke="#8a9ba5" stroke-width=".8"/>
          <polygon points="316,150 332,141 332,167 316,176" fill="url(#gWin)" opacity=".5" stroke="#cdd9df" stroke-width="1.2"/>
          <!-- Frontwand -->
          <rect x="128" y="112" width="172" height="92" fill="url(#gWall)"/>
          <rect x="128" y="196" width="172" height="8" fill="#76888f"/>
          <!-- Dach: Vorderfläche mit Dachkante -->
          <polygon points="${pt(A)} ${pt(B)} ${pt(R2)} ${pt(R1)}" fill="url(#gRoof)" stroke="#9db0ba" stroke-width="1"/>
          <polygon points="${A[0] - 4},112 ${B[0] + 4},112 ${B[0] + 4},118 ${A[0] - 4},118" fill="#5f717b"/>
          <!-- Solarmodule -->
          <g id="panels">${panels}
            <polygon points="${sheen.map(pt).join(" ")}" fill="url(#gSheen)"/>
            <ellipse id="sun" cx="232" cy="84" rx="60" ry="30" fill="url(#gSun)" opacity="0"/>
          </g>
          <!-- Fenster und Tür -->
          <ellipse id="glow" cx="232" cy="152" rx="62" ry="46" fill="url(#gGlow)" opacity="0"/>
          <rect id="win" x="204" y="128" width="56" height="46" rx="3" fill="url(#gWin)" opacity=".18" stroke="#cfdbe1" stroke-width="2"/>
          <path d="M232 128V174M204 151H260" stroke="#cfdbe1" stroke-width="1.6"/>
          <rect x="150" y="140" width="32" height="56" rx="2" fill="#7b8d97" stroke="#9aaab3"/>
          <circle cx="176" cy="170" r="1.6" fill="#d7e0e5"/>
          <!-- Garage (vorne links) mit Oberseite -->
          <polygon points="20,150 128,150 150,139 42,139" fill="#8fa1ab"/>
          <rect x="20" y="150" width="108" height="54" fill="url(#gWall)"/>
          <rect x="20" y="150" width="108" height="6" fill="#7b8d97"/>
          <rect x="44" y="166" width="62" height="38" rx="2" fill="#aebdc5" stroke="#7a8c96"/>
          <path d="M44 174H106M44 182H106M44 190H106M44 198H106" stroke="#8ea0aa" stroke-width="1"/>
          <rect x="24" y="160" width="12" height="16" rx="2" fill="url(#gWin)" opacity=".9"/>
          <!-- Speicher mit 3D-Flächen -->
          <g id="batt">${battery(346)}${battery(368)}
            <circle id="led1" cx="354" cy="168" r="2.4" fill="#888"/><circle id="led2" cx="376" cy="168" r="2.4" fill="#888"/>
          </g>
          <!-- Leitlinien von den Kacheln zu den Teilen des Hauses -->
          <g data-t="pv"><path d="M116 56 L152 76" stroke="rgba(255,255,255,.32)" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle cx="152" cy="76" r="2" fill="rgba(255,255,255,.7)"/></g>
          <g data-t="house"><path d="M324 58 L316 80" stroke="rgba(255,255,255,.32)" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle cx="316" cy="80" r="2" fill="rgba(255,255,255,.7)"/></g>
          <g data-t="grid"><path d="M57 254 L57 210" stroke="rgba(255,255,255,.32)" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle cx="57" cy="210" r="2" fill="rgba(255,255,255,.7)"/></g>
          <g data-t="ccu"><path d="M200 254 L214 210" stroke="rgba(255,255,255,.32)" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle cx="214" cy="210" r="2" fill="rgba(255,255,255,.7)"/></g>
          <g data-t="store"><path d="M366 254 L366 208" stroke="rgba(255,255,255,.32)" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle cx="366" cy="208" r="2" fill="rgba(255,255,255,.7)"/></g>
          <!-- Leitungen -->
          <path id="p-pv" d="M322 72 L362 72 L362 150" fill="none" stroke="#51606a" stroke-width="2" opacity=".45"/>
          <path id="p-bat" d="M346 198 L330 198 L330 208 L214 208 L214 198" fill="none" stroke="#51606a" stroke-width="2" opacity=".45"/>
          <path id="p-grid" d="M128 190 L84 190 L84 208 L18 208" fill="none" stroke="#51606a" stroke-width="2" opacity=".45"/>
          <circle class="flowdot" id="d-pv" r="3.4" fill="${C.pv}"/>
          <circle class="flowdot" id="d-bat" r="3.4" fill="${C.green}"/>
          <circle class="flowdot" id="d-grid" r="3.4" fill="${C.blue}"/>
        </svg>`;
    }

    _chartSvg() {
      return `<svg id="chart" viewBox="0 0 400 124" role="img" aria-label="Verlauf Haushalt">
        <g id="grid-lines"></g>
        <path id="area-grid" fill="${C.grid}" opacity=".16"/>
        <path id="ln-grid" fill="none" stroke="${C.grid}" stroke-width="1.8" stroke-linejoin="round"/>
        <path id="ln-ccu" fill="none" stroke="${C.ccu}" stroke-width="1.8" stroke-linejoin="round"/>
        <circle id="dot-grid" r="3" fill="${C.grid}" display="none"/>
        <circle id="dot-ccu" r="3" fill="${C.ccu}" display="none"/>
        <text class="ax" id="t-none" x="200" y="62" text-anchor="middle"></text>
      </svg>`;
    }

    // ---------- Anzeige ----------
    _setDot(id, pathId, watts, forward, color) {
      const dot = this.shadowRoot.getElementById(id), path = this.shadowRoot.getElementById(pathId);
      const on = watts !== null && Math.abs(watts) >= 10;
      dot.style.display = on ? "inline" : "none";
      path.setAttribute("opacity", on ? ".95" : ".45");
      path.setAttribute("stroke", on ? color : "#51606a");
      if (!on) { dot.innerHTML = ""; dot.dataset.key = ""; return; }
      const key = `${forward}|${Math.round(Math.min(Math.abs(watts), 2300) / 400)}`;
      if (dot.dataset.key === key) return;
      dot.dataset.key = key;
      const dur = Math.max(1.4, 4.2 - Math.min(Math.abs(watts), 2300) / 800);
      dot.innerHTML = `<animateMotion dur="${dur}s" repeatCount="indefinite" keyPoints="${forward ? "0;1" : "1;0"}" keyTimes="0;1" calcMode="linear"><mpath href="#${pathId}"/></animateMotion>`;
    }

    _update() {
      if (!this._built || !this._hass) return;
      const $ = (id) => this.shadowRoot.getElementById(id);
      const pv = this._num("pv"), grid = this._num("grid"), house = this._num("house"), soc = this._num("soc");
      const ch = this._num("charge"), dis = this._num("discharge"), feed = this._num("feed"), draw = this._num("draw");
      this.shadowRoot.querySelector(".title").textContent = this._title();
      this._renderChips();
      const ok = [pv, grid, house, soc].some((v) => v !== null);
      $("msg").hidden = ok;
      $("main").style.display = ok ? "" : "none";

      $("b-pv").style.width = `${pct(pv, this._config.pv_max)}%`;
      $("b-house").style.width = `${pct(house, this._config.house_max)}%`;
      const ccu = feed === null && draw === null ? null : (feed || 0) - (draw || 0);
      const t = this._num("temp");
      const split = (txt) => (txt === "–" ? txt : txt.replace(/ (W|kW)$/, '<span class="u">$1</span>'));
      $("v-pv").innerHTML = split(fmtW(pv));
      $("v-house").innerHTML = split(fmtW(house));
      $("v-grid").innerHTML = split(fmtW(grid === null ? null : Math.abs(grid)));
      $("b-grid").style.width = `${pct(grid === null ? null : Math.abs(grid), this._config.house_max)}%`;
      $("s-grid").textContent = grid === null || Math.abs(grid) < 10 ? "" : grid > 0 ? "Bezug" : "Einspeisung";
      $("v-ccu").innerHTML = `${t !== null ? `<small>${Math.round(t)} °C ·</small>` : ""}${split(fmtW(ccu === null ? null : Math.max(ccu, 0)))}`;
      $("b-ccu").style.width = `${pct(ccu === null ? null : Math.max(ccu, 0), this._config.ccu_max)}%`;
      $("v-soc").textContent = soc === null ? "–" : `${Math.round(soc)} %`;
      $("b-soc").style.width = `${pct(soc, 100)}%`;
      $("s-state").textContent = (dis || 0) > 10 ? `↓ ${fmtW(dis)}` : (ch || 0) > 10 ? `↑ ${fmtW(ch)}` : "";

      // Haus: Fenster leuchtet bei Verbrauch, Speicher-LEDs zeigen Laden/Entladen
      const lit = house !== null && house > 30 ? Math.min(1, 0.45 + house / 3000) : 0.18;
      $("win").setAttribute("opacity", lit);
      $("glow").setAttribute("opacity", house !== null && house > 30 ? Math.min(0.9, lit) : 0);
      $("sun").setAttribute("opacity", pv !== null && pv > 20 ? Math.min(0.85, 0.25 + pv / 4000) : 0);
      const led = (dis || 0) > 10 ? C.green : (ch || 0) > 10 ? C.blue : "#888";
      $("led1").setAttribute("fill", led); $("led2").setAttribute("fill", led);

      // Leitungen mit wandernden Punkten: PV -> Speicher, Speicher <-> Haus, Netz <-> Haus
      this._setDot("d-pv", "p-pv", pv, true, C.pv);
      this._setDot("d-bat", "p-bat", ccu, (ccu || 0) >= 0, C.green);
      this._setDot("d-grid", "p-grid", grid, (grid || 0) < 0, C.blue);

      $("n-grid").textContent = fmtW(grid === null ? null : Math.abs(grid));
      $("n-ccu").textContent = fmtW(ccu === null ? null : Math.abs(ccu));
      $("c-grid").textContent = grid !== null && grid < 0 ? "Einspeisung" : "Netzbezug";
      $("c-ccu").textContent = ccu !== null && ccu < 0 ? "CCU-Aufnahme" : "CCU-Abgabe";

      const usable = this._num("usable"), runtime = this._num("runtime"), ttf = this._num("ttf");
      const autarky = this._num("autarky"), pvToday = this._num("pvtoday");
      const parts = [];
      const stat = (label, value) => `<div class="st"><div class="sl">${label}</div><div class="sv">${value}</div></div>`;
      if (pvToday !== null) parts.push(stat("PV heute", `${pvToday.toFixed(1).replace(".", ",")} kWh`));
      if (autarky !== null) parts.push(stat("Autarkie heute", `${Math.round(autarky)} %`));
      if (runtime !== null) parts.push(stat("Reicht noch", fmtH(runtime)));
      else if (ttf !== null) parts.push(stat("Voll in", fmtH(ttf)));
      if (usable !== null) parts.push(stat("Nutzbar", `${usable.toFixed(2).replace(".", ",")} kWh`));
      $("foot").innerHTML = parts.join("");

      const badges = [];
      if (this._state("online") === "off") badges.push(`<div class="badge off" title="CCU offline">☁</div>`);
      if (this._state("fault") === "on") badges.push(`<div class="badge" title="Störung">!</div>`);
      if (this._state("lock") === "on") badges.push(`<div class="badge lock" title="Schreibschutz">🔒</div>`);
      $("badges").innerHTML = badges.join("");
      this._drawChart();
    }

    _drawChart() {
      const $ = (id) => this.shadowRoot.getElementById(id);
      const none = $("t-none");
      if (!this._hist) { none.textContent = this._hass && this._hass.callWS ? "Verlauf wird geladen …" : ""; return; }
      none.textContent = "";
      const L = 46, R = 354, T = 8, B = 104, W = R - L, N = Math.max(this._hist.grid.length, this._hist.ccu.length) - 1;
      const gv = this._hist.grid.filter((v) => v !== null), cv = this._hist.ccu.filter((v) => v !== null);
      if (!gv.length && !cv.length) { none.textContent = "Keine Verlaufsdaten"; return; }
      const rg = niceRange(gv.length ? gv : [0]), rc = niceRange(cv.length ? cv : [0]);
      const y = (v, r) => T + (1 - (v - r.lo) / (r.hi - r.lo)) * (B - T);
      const path = (arr, r) => arr.map((v, i) => (v === null ? null : `${L + (i / N) * W},${y(v, r).toFixed(1)}`)).filter(Boolean).map((p, i) => (i ? "L" : "M") + p).join(" ");
      let grid = "";
      for (let k = 0; k <= 4; k++) {
        const yy = T + (k / 4) * (B - T);
        const vl = rg.hi - k * rg.step, vr = rc.hi - k * rc.step;
        grid += `<line x1="${L}" x2="${R}" y1="${yy}" y2="${yy}" stroke="rgba(255,255,255,.07)"/>`;
        grid += `<text class="ax" x="${L - 4}" y="${yy + 3}" text-anchor="end">${vl} W</text><text class="ax" x="${R + 4}" y="${yy + 3}">${vr} W</text>`;
      }
      const hours = Number(this._config.hours) || 3;
      for (let k = 0; k <= 3; k++) {
        const d = new Date(Date.now() - (hours * 3600 * 1000) * (1 - k / 3));
        grid += `<text class="ax" x="${L + (k / 3) * W}" y="${B + 14}" text-anchor="middle">${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}</text>`;
      }
      $("grid-lines").innerHTML = grid;
      const gp = path(this._hist.grid, rg);
      $("ln-grid").setAttribute("d", gp);
      $("area-grid").setAttribute("d", gp ? `${gp} L${R},${y(0, rg).toFixed(1)} L${L},${y(0, rg).toFixed(1)} Z` : "");
      $("ln-ccu").setAttribute("d", path(this._hist.ccu, rc));
      const endDot = (id, arr, r) => {
        let i = arr.length - 1;
        while (i >= 0 && arr[i] === null) i--;
        const el = $(id);
        if (i < 0) { el.setAttribute("display", "none"); return; }
        el.setAttribute("display", ""); el.setAttribute("cx", L + (i / N) * W); el.setAttribute("cy", y(arr[i], r));
      };
      endDot("dot-grid", this._hist.grid, rg);
      endDot("dot-ccu", this._hist.ccu, rc);
    }
  }

  // ---------- Karten-Editor (Gerät und Bausteine auswählen) ----------
  const LABELS = {
    title: "Titel (leer = Gerätename)",
    device: "Startgerät (leer = Maxxicharge Gesamt)",
    switcher: "Umschalter zwischen Geräten in der Karte anzeigen",
    modules: "Bausteine",
    tiles: "Kacheln",
    hours: "Verlauf in Stunden",
    pv_max: "PV-Balken Maximum (W)",
    house_max: "Verbrauchs-Balken Maximum (W)",
    ccu_max: "CCU-Balken Maximum (W)",
  };
  const SCHEMA = [
    { name: "device", selector: { device: { filter: [{ integration: "maxxicharge" }] } } },
    { name: "switcher", selector: { boolean: {} } },
    { name: "title", selector: { text: {} } },
    {
      name: "modules",
      selector: {
        select: {
          multiple: true,
          mode: "list",
          options: [
            { value: "scene", label: "Haus-Grafik" },
            { value: "tiles", label: "Kacheln" },
            { value: "chart", label: "Verlauf „Haushalt“" },
            { value: "stats", label: "Kennzahlen" },
          ],
        },
      },
    },
    {
      name: "tiles",
      selector: {
        select: {
          multiple: true,
          mode: "list",
          options: [
            { value: "pv", label: "PV-Leistung" },
            { value: "house", label: "Verbrauch" },
            { value: "grid", label: "Netz" },
            { value: "ccu", label: "CCU-Abgabe" },
            { value: "store", label: "Speicher" },
          ],
        },
      },
    },
    { name: "hours", selector: { number: { min: 1, max: 24, mode: "box" } } },
    {
      type: "grid",
      name: "",
      schema: [
        { name: "pv_max", selector: { number: { min: 500, max: 20000, step: 100, mode: "box" } } },
        { name: "house_max", selector: { number: { min: 500, max: 20000, step: 100, mode: "box" } } },
        { name: "ccu_max", selector: { number: { min: 500, max: 5000, step: 100, mode: "box" } } },
      ],
    },
  ];

  class MaxxichargeCardEditor extends HTMLElement {
    setConfig(config) {
      this._config = config;
      this._draw();
    }

    set hass(hass) {
      this._hass = hass;
      if (this._form) this._form.hass = hass;
    }

    _draw() {
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.computeLabel = (item) => LABELS[item.name] || item.name;
        this._form.addEventListener("value-changed", (ev) => {
          ev.stopPropagation();
          const value = { ...ev.detail.value, type: "custom:maxxicharge-card" };
          Object.keys(value).forEach((k) => (value[k] === "" || value[k] === undefined) && delete value[k]);
          this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: value }, bubbles: true, composed: true }));
        });
        this.appendChild(this._form);
      }
      this._form.hass = this._hass;
      this._form.schema = SCHEMA;
      this._form.data = {
        switcher: !this._config.device,
        modules: ALL_MODULES,
        tiles: ALL_TILES,
        hours: 3,
        pv_max: 4000,
        house_max: 3000,
        ccu_max: 2300,
        ...this._config,
      };
    }
  }

  if (!customElements.get("maxxicharge-card")) customElements.define("maxxicharge-card", MaxxichargeCard);
  if (!customElements.get("maxxicharge-card-editor")) customElements.define("maxxicharge-card-editor", MaxxichargeCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "maxxicharge-card",
    name: "Maxxicharge",
    description: "Haus mit PV und Speicher, Kacheln und Verlauf im Stil der Maxxisun-App, für die Gesamtübersicht oder eine einzelne CCU, modular einstellbar.",
  });
})();
