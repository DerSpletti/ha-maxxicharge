/* Maxxicharge-Karte im Stil der Maxxisun-App: Haus mit PV und Speicher, Kacheln, Verlauf „Haushalt“.
 * Eine Datei, keine Abhängigkeiten. Dashboard: type: custom:maxxicharge-card
 *
 * Optionen (alle optional):
 *   title: Maxxicharge        # Überschrift
 *   hours: 3                  # Zeitraum des Verlaufs in Stunden
 *   pv_max: 4000              # Skala des PV-Balkens in W
 *   house_max: 3000           # Skala des Verbrauchs-Balkens in W
 *   ccu_max: 2300             # Skala des CCU-Balkens in W
 *   entities: { pv: sensor.xxx, grid: sensor.xxx }   # Entities überschreiben (Schlüssel siehe KEYS)
 * Die Entities der Gesamtübersicht werden sonst automatisch gefunden.
 */
(() => {
  const KEYS = {
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
      this._config = { title: "Maxxicharge", hours: 3, pv_max: 4000, house_max: 3000, ccu_max: 2300, ...config };
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

    disconnectedCallback() {
      this._gone = true;
    }

    // ---------- Daten ----------
    _entity(key) {
      const override = this._config.entities && this._config.entities[key];
      if (override) return override;
      const registry = this._hass.entities || {};
      for (const [id, e] of Object.entries(registry)) {
        if (e.platform === "maxxicharge" && e.translation_key === KEYS[key]) return id;
      }
      return null;
    }
    _state(key) {
      const id = this._entity(key);
      const st = id && this._hass.states[id];
      return st ? st.state : null;
    }
    _num(key) {
      const s = this._state(key);
      if (s === null || s === "unknown" || s === "unavailable") return null;
      const n = Number(s);
      return Number.isNaN(n) ? null : n;
    }

    async _maybeLoadHistory() {
      const now = Date.now();
      if (!this._built || this._loading || now - this._histAt < 120000 || !this._hass.callWS) return;
      const ids = ["grid", "feed", "draw"].map((k) => this._entity(k));
      if (ids.some((i) => !i)) return;
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
        const series = ids.map((id) => {
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
        });
        this._hist = {
          grid: series[0],
          ccu: series[1].map((f, i) => (f === null && series[2][i] === null ? null : (f || 0) - (series[2][i] || 0))),
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
          .badge { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; background:#f2b705; color:#1b1b1b; }
          .badge.lock { background:#d9a21a; }
          .badge.off { background:#555; color:#ddd; }
          .scene { position:relative; margin-top:4px; }
          .scene svg { width:100%; height:auto; display:block; }
          .tile { position:absolute; background:rgba(26,32,36,.88); border:1px solid rgba(255,255,255,.13); border-radius:11px; padding:6px 9px 7px; min-width:84px; backdrop-filter:blur(3px); box-shadow:0 2px 10px rgba(0,0,0,.4); }
          .tile .k { font-size:10.5px; color:#b9c2c6; display:flex; justify-content:space-between; gap:8px; white-space:nowrap; }
          .tile .v { font-size:17px; font-weight:700; margin-top:1px; white-space:nowrap; }
          .tile .v small { font-size:11px; font-weight:500; color:#b9c2c6; margin-right:4px; }
          .bar { height:3px; border-radius:2px; background:rgba(255,255,255,.14); margin-top:5px; overflow:hidden; }
          .bar i { display:block; height:100%; border-radius:2px; width:0; transition:width .6s; }
          .t-pv { left:1%; top:8%; } .t-house { right:1%; top:8%; text-align:left; }
          .t-store { left:11%; bottom:1%; } .t-ccu { right:1%; bottom:1%; }
          .sect { margin:10px 2px 2px; font-size:.78em; letter-spacing:1.3px; color:#9fb0a8; text-transform:uppercase; display:flex; align-items:center; gap:6px; }
          #chart { width:100%; height:auto; display:block; }
          .ax { font-size:9.5px; fill:#8da097; }
          .legend { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:6px; font-size:.78em; margin-top:2px; }
          .legend .col { display:flex; flex-direction:column; gap:3px; }
          .legend .col.r { align-items:flex-end; text-align:right; }
          .legend .dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
          .legend .r .dot { margin:0 0 0 5px; }
          .legend .big { font-family:"Roboto Condensed","Arial Narrow",Roboto,sans-serif; font-size:1.7em; font-weight:700; display:flex; gap:12px; }
          .foot { display:flex; justify-content:space-around; flex-wrap:wrap; gap:4px 14px; margin-top:10px; padding-top:8px; border-top:1px solid rgba(255,255,255,.08); font-size:.8em; color:#9fb0a8; }
          .foot span { white-space:nowrap; } .foot b { color:#e8eceb; font-weight:600; }
          .msg { padding:18px 8px; color:#9fb0a8; }
          .flowdot { display:none; }
          .on .flowdot { display:inline; }
        </style>
        <ha-card>
          <div class="top"><div class="title"></div><div class="badges" id="badges"></div></div>
          <div class="msg" id="msg" hidden>Die Entities der Gesamtübersicht wurden nicht gefunden. Ist der Eintrag „Maxxicharge Gesamt“ eingerichtet?</div>
          <div id="main">
            <div class="scene">
              ${this._houseSvg()}
              <div class="tile t-pv"><div class="k">PV Maxxicharge</div><div class="v" id="v-pv">–</div><div class="bar"><i id="b-pv" style="background:linear-gradient(90deg,#f5a623,#ff7a18)"></i></div></div>
              <div class="tile t-house"><div class="k">Hausverbrauch</div><div class="v" id="v-house">–</div><div class="bar"><i id="b-house" style="background:${C.green}"></i></div></div>
              <div class="tile t-store"><div class="k"><span>Speicher</span><span id="s-state"></span></div><div class="v" id="v-soc">–</div><div class="bar"><i id="b-soc" style="background:${C.green}"></i></div></div>
              <div class="tile t-ccu"><div class="k">CCU AC-Abgabe</div><div class="v" id="v-ccu">–</div><div class="bar"><i id="b-ccu" style="background:${C.green}"></i></div></div>
            </div>
            <div class="sect">⚡ Haushalt</div>
            ${this._chartSvg()}
            <div class="legend">
              <div class="col"><span><span class="dot" style="background:${C.grid}"></span>Netzbezug</span><span><span class="dot" style="background:#7a3050"></span>Einspeisung</span></div>
              <div class="big"><span id="n-grid" style="color:${C.grid}">–</span><span id="n-ccu" style="color:${C.ccu}">–</span></div>
              <div class="col r"><span>CCU-Abgabe<span class="dot" style="background:${C.ccu}"></span></span><span>CCU-Aufnahme<span class="dot" style="background:${C.draw}"></span></span></div>
            </div>
            <div class="foot" id="foot"></div>
          </div>
        </ha-card>`;
      this.shadowRoot.querySelector(".title").textContent = this._config.title;
      this._built = true;
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
        <svg viewBox="0 0 400 292" id="house" role="img" aria-label="Haus mit PV und Speicher">
          <defs>
            <linearGradient id="gWall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b3c3cb"/><stop offset="1" stop-color="#8a9da7"/></linearGradient>
            <linearGradient id="gSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8396a0"/><stop offset="1" stop-color="#6c7e88"/></linearGradient>
            <linearGradient id="gRoof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8b9ea8"/><stop offset="1" stop-color="#6d808a"/></linearGradient>
            <linearGradient id="gPanel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34495f"/><stop offset=".55" stop-color="#1c2b3b"/><stop offset="1" stop-color="#121b26"/></linearGradient>
            <linearGradient id="gSheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".30"/><stop offset=".6" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
            <linearGradient id="gWin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#ff8a1f"/></linearGradient>
            <radialGradient id="gGlow"><stop offset="0" stop-color="#ffb347" stop-opacity=".55"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
            <radialGradient id="gSun"><stop offset="0" stop-color="#fff2b0" stop-opacity=".9"/><stop offset="1" stop-color="#ffd24d" stop-opacity="0"/></radialGradient>
          </defs>
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
      const ok = [pv, grid, house, soc].some((v) => v !== null);
      $("msg").hidden = ok;
      $("main").style.display = ok ? "" : "none";

      $("v-pv").textContent = fmtW(pv);
      $("b-pv").style.width = `${pct(pv, this._config.pv_max)}%`;
      $("v-house").textContent = fmtW(house);
      $("b-house").style.width = `${pct(house, this._config.house_max)}%`;
      const ccu = feed === null && draw === null ? null : (feed || 0) - (draw || 0);
      const t = this._num("temp");
      $("v-ccu").innerHTML = `${t !== null ? `<small>${Math.round(t)} °C ·</small>` : ""}${fmtW(ccu === null ? null : Math.max(ccu, 0))}`;
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

      const usable = this._num("usable"), runtime = this._num("runtime"), ttf = this._num("ttf");
      const autarky = this._num("autarky"), pvToday = this._num("pvtoday");
      const parts = [];
      if (pvToday !== null) parts.push(`<span>PV heute <b>${pvToday.toFixed(1).replace(".", ",")} kWh</b></span>`);
      if (autarky !== null) parts.push(`<span>Autarkie <b>${Math.round(autarky)} %</b></span>`);
      if (runtime !== null) parts.push(`<span>Reicht noch <b>${fmtH(runtime)}</b></span>`);
      else if (ttf !== null) parts.push(`<span>Voll in <b>${fmtH(ttf)}</b></span>`);
      if (usable !== null) parts.push(`<span>Nutzbar <b>${usable.toFixed(2).replace(".", ",")} kWh</b></span>`);
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
      const L = 46, R = 354, T = 8, B = 104, W = R - L, N = this._hist.grid.length - 1;
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
    }
  }

  if (!customElements.get("maxxicharge-card")) customElements.define("maxxicharge-card", MaxxichargeCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "maxxicharge-card",
    name: "Maxxicharge",
    description: "Haus mit PV und Speicher, Kacheln und Verlauf – im Stil der Maxxisun-App (Gesamtübersicht).",
  });
})();
