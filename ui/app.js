/* Oakwood UI. All displayed simulation values come from the configured API.
   No sample world data is embedded in this application. */
(function () {
  "use strict";
  const BASE = String(window.OAKWOOD_API_BASE || "").replace(/\/$/, "");
  const $ = (selector, root) => (root || document).querySelector(selector);
  const state = { page: "overview", status: null, capabilities: null, health: null, selectedCitizen: null, citizenRows: [], refreshBusy: false };
  const pages = {
    overview: ["SIMULATION WORKSPACE", "Overview", "A live operational view of Oakwood and the systems shaping it."],
    citizens: ["POPULATION", "Citizens", "Inspect individual citizens, their condition, relationships and decision-making."],
    world: ["WORLD STRUCTURE", "World structure", "Browse settlements, buildings, rooms, occupancy and spatial connections."],
    economy: ["ECONOMIC SYSTEMS", "Economy", "Review currency, treasury, commodity reserves and household indicators."],
    society: ["SOCIAL SYSTEMS", "Society & justice", "Inspect factions, social tensions, municipal decrees and court activity."],
    climate: ["ENVIRONMENT", "Environment", "Review current climate conditions and the environmental state."],
    events: ["EVENT HISTORY", "Events", "Trace simulation events and inspect the activity history."],
    content: ["DECLARATIVE CONTENT", "Content", "Inspect scenarios, content packs and settings manifests."],
    diagnostics: ["OBSERVABILITY", "Diagnostics", "Review subsystem performance, world integrity and runtime health."]
  };
  const routes = {
    health: "/health",
    capabilities: "/capabilities",
    status: "/simulation/status",
    scenarios: "/scenarios",
    world: "/world/hierarchy",
    citizens: "/citizens",
    economy: "/economy/overview",
    society: "/society/overview",
    justice: "/justice/overview",
    climate: "/climate/status",
    events: "/events",
    packs: "/content/packs",
    performance: "/diagnostics/performance",
    integrity: "/diagnostics/integrity"
  };
  async function request(path, options) {
    if (!BASE) throw new Error("No API base URL is configured.");
    const response = await fetch(BASE + path, Object.assign({ headers: { "Accept": "application/json" } }, options || {}));
    const body = await response.text();
    let data = null;
    try { data = body ? JSON.parse(body) : null; } catch (_) { throw new Error("The API returned a non-JSON response."); }
    if (!response.ok) {
      const message = data && data.error && data.error.message ? data.error.message : "Request failed (" + response.status + ").";
      throw new Error(message);
    }
    return data;
  }
  const get = path => request(path);
  const post = (path, payload) => request(path, { method: "POST", headers: { "Accept": "application/json", "Content-Type": "application/json" }, body: JSON.stringify(payload || {}) });
  const esc = value => String(value == null ? "—" : value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
  const num = value => typeof value === "number" && Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—";
  const obj = value => value && typeof value === "object" ? value : {};
  const arr = value => Array.isArray(value) ? value : [];
  const keys = value => Object.keys(obj(value));
  function toast(message) {
    const node = $("#toast"); node.textContent = message; node.classList.add("show");
    window.clearTimeout(toast.timer); toast.timer = window.setTimeout(() => node.classList.remove("show"), 2600);
  }
  function empty(title, message, symbol) {
    return '<div class="card empty-state"><span class="empty-icon">' + esc(symbol || "⌁") + '</span><strong>' + esc(title) + '</strong><p>' + esc(message) + '</p></div>';
  }
  function errorBox(title, error) {
    return '<div class="card error-state"><strong>' + esc(title) + '</strong><p>' + esc(error && error.message ? error.message : error) + '</p></div>';
  }
  function metric(label, value, note, glyph) {
    return '<article class="card metric-card"><div class="metric-top"><span>' + esc(label) + '</span><span class="metric-icon">' + esc(glyph || "·") + '</span></div><div class="metric-value">' + esc(value) + '</div><div class="metric-foot">' + esc(note || "Live API value") + '</div></article>';
  }
  function field(label, value) {
    return '<div class="field"><small>' + esc(label) + '</small><strong>' + esc(value) + '</strong></div>';
  }
  function table(headers, rows, emptyTitle, emptyText) {
    if (!rows.length) return empty(emptyTitle || "No records returned", emptyText || "The connected API has not returned any records for this view.", "—");
    return '<div class="table-wrap"><table><thead><tr>' + headers.map(h => '<th>' + esc(h) + '</th>').join("") + '</tr></thead><tbody>' + rows.join("") + '</tbody></table></div>';
  }
  function setConnection(health, error) {
    state.health = health || null;
    const indicator = $("#connection-indicator");
    indicator.className = "connection-indicator" + (health ? " online" : error ? " error" : "");
    $("#connection-state").textContent = health ? "API connected" : "Not connected";
    $("#connection-detail").textContent = health ? "Local simulation interface" : (error ? "API connection unavailable" : "Waiting for local API");
    $("#api-version").textContent = state.capabilities && state.capabilities.api_version ? state.capabilities.api_version : "API —";
  }
  function setStatus(status) {
    state.status = status || null;
    if (!status) return;
    const time = status.virtual_time_iso || ("Tick " + num(status.tick));
    $("#sim-clock").textContent = "SIMULATION · " + time;
    const button = $("#run-button");
    button.disabled = false;
    button.textContent = status.is_paused || status.lifecycle_state !== "RUNNING" ? "Resume simulation" : "Pause simulation";
  }
  async function refreshCore() {
    try {
      const results = await Promise.all([get(routes.health), get(routes.capabilities), get(routes.status)]);
      setConnection(results[0], null); state.capabilities = results[1]; setStatus(results[2]);
      return true;
    } catch (error) {
      setConnection(null, error); state.capabilities = null; state.status = null;
      $("#sim-clock").textContent = "SIMULATION TIME —";
      $("#run-button").disabled = true;
      $("#run-button").textContent = "Start simulation";
      return false;
    }
  }
  function header() {
    const p = pages[state.page];
    $("#breadcrumb").textContent = p[1]; $("#page-eyebrow").textContent = p[0];
    $("#page-title").textContent = p[1]; $("#page-description").textContent = p[2];
    $("#page-actions").innerHTML = state.page === "citizens" ? '<button class="button button-secondary" id="citizen-refresh">Refresh directory</button>' : "";
    document.querySelectorAll(".nav-item").forEach(button => button.classList.toggle("active", button.dataset.page === state.page));
  }
  function showLoading() {
    $("#page-content").innerHTML = '<div class="loading-state"><span class="spinner"></span><span>Loading live simulation data…</span></div>';
  }
  function disconnected() {
    $("#page-content").innerHTML = '<div class="notice"><strong>Backend connection required.</strong> This interface does not use invented or preview simulation values. Connect a browser-facing adapter to the local Python facade to populate this screen.</div>' +
      empty("Simulation API unavailable", "The repository currently exposes LocalVisualAPI as in-process Python methods. It does not yet provide the HTTP routes this UI calls. See ui/API_CONNECTION_GAPS.md for the exact integration requirements.", "↔");
  }
  async function renderOverview() {
    const [economy, events, perf] = await Promise.allSettled([get(routes.economy), get(routes.events + "?limit=8"), get(routes.performance)]);
    const s = obj(state.status), e = economy.status === "fulfilled" ? obj(economy.value) : {};
    const pop = s.population != null ? s.population : s.alive_population;
    const eventRows = events.status === "fulfilled" ? arr(events.value).slice(-6).reverse().map(evt =>
      '<div class="activity-row"><span class="activity-icon">≋</span><div><strong>' + esc(evt.event_type || "Simulation event") + '</strong><p>' + esc(evt.source_id || "Unknown source") + ' · tick ' + esc(evt.tick) + '</p></div><time>' + esc(evt.timestamp || "") + '</time></div>'
    ).join("") : "";
    const performance = perf.status === "fulfilled" ? obj(perf.value) : {};
    $("#page-content").innerHTML =
      '<div class="metrics">' +
      metric("Population", num(pop), "From simulation status", "◎") +
      metric("Current tick", num(s.tick), "Virtual simulation clock", "◷") +
      metric("Total currency", e.total_currency_gold == null ? "—" : num(e.total_currency_gold) + " g", "Economy overview", "¤") +
      metric("Treasury", e.treasury_balance_gold == null ? "—" : num(e.treasury_balance_gold) + " g", "Municipal balance", "▤") +
      '</div><div class="content-grid">' +
      '<section class="card"><div class="card-head"><div><h2>Simulation state</h2><p>Live lifecycle and runtime information</p></div><span class="pill">' + esc(s.lifecycle_state || "Unknown") + '</span></div><div class="mini-card">' +
      '<div class="data-line"><span>Virtual time</span><strong>' + esc(s.virtual_time_iso || "—") + '</strong></div>' +
      '<div class="data-line"><span>Day</span><strong>' + esc(num(s.day)) + '</strong></div>' +
      '<div class="data-line"><span>Hour</span><strong>' + esc(num(s.hour)) + '</strong></div>' +
      '<div class="data-line"><span>Season</span><strong>' + esc(s.season || "—") + '</strong></div>' +
      '<div class="data-line"><span>Temperature</span><strong>' + (s.ambient_temperature_celsius == null ? "—" : esc(num(s.ambient_temperature_celsius) + " °C")) + '</strong></div>' +
      '</div></section>' +
      '<section class="card"><div class="card-head"><div><h2>Recent events</h2><p>Latest events retained by the event bus</p></div><button class="quiet-link" data-go="events">View all →</button></div><div class="activity-list">' +
      (eventRows || '<div class="empty-state"><strong>No event records</strong><p>Events will appear here when the event API is connected.</p></div>') + '</div></section></div>' +
      '<div class="lower-grid"><section class="card mini-card"><h3>Economy snapshot</h3>' +
      '<div class="data-line"><span>Gini coefficient</span><strong>' + esc(num(e.gini_coefficient)) + '</strong></div>' +
      '<div class="data-line"><span>Households</span><strong>' + esc(num(e.households_count)) + '</strong></div>' +
      '<div class="data-line"><span>Commodity types</span><strong>' + esc(num(keys(e.commodity_stocks).length)) + '</strong></div></section>' +
      '<section class="card mini-card"><h3>Runtime performance</h3>' +
      '<div class="data-line"><span>Average tick</span><strong>' + (performance.avg_tick_duration_ms == null ? "—" : esc(num(performance.avg_tick_duration_ms) + " ms")) + '</strong></div>' +
      '<div class="data-line"><span>Active subsystems</span><strong>' + esc(num(performance.active_subsystems_count)) + '</strong></div>' +
      '<div class="data-line"><span>Registered subsystems</span><strong>' + esc(num(performance.total_registered_subsystems)) + '</strong></div></section>' +
      '<section class="card mini-card"><h3>Quick access</h3>' +
      '<div class="data-line"><span>Citizen directory</span><button class="quiet-link" data-go="citizens">Open →</button></div>' +
      '<div class="data-line"><span>World structure</span><button class="quiet-link" data-go="world">Open →</button></div>' +
      '<div class="data-line"><span>Diagnostics</span><button class="quiet-link" data-go="diagnostics">Open →</button></div></section></div>';
  }
  async function renderCitizens() {
    const result = await get(routes.citizens);
    state.citizenRows = arr(result);
    const rows = state.citizenRows.map(n => '<tr data-citizen="' + esc(n.id) + '" class="' + (state.selectedCitizen === n.id ? "selected" : "") + '"><td class="primary-cell"><strong>' + esc(n.name) + '</strong><small>' + esc(n.id) + '</small></td><td>' + esc(n.occupation) + '</td><td>' + esc(n.location_id) + '</td><td>' + esc(n.current_action) + '</td><td>' + esc(num(n.wealth_gold)) + '</td><td><span class="pill ' + (n.is_alive ? "" : "warning") + '">' + (n.is_alive ? "Alive" : "Deceased") + '</span></td></tr>');
    $("#page-content").innerHTML = '<section class="card section-card"><div class="toolbar"><input class="search-input" id="citizen-search" placeholder="Search citizens by name, role or ID…" aria-label="Search citizens"><span class="pill">' + esc(state.citizenRows.length) + ' records</span></div>' +
      '<div id="citizen-table">' + table(["Citizen","Occupation","Current room","Current action","Wealth (g)","Status"], rows, "No citizens returned", "The API returned an empty citizen directory.") + '</div></section>' +
      '<div id="citizen-inspector">' + empty("Select a citizen", "Choose a row to inspect their profile, current state and decision explanation.", "◎") + '</div>';
    $("#citizen-search").addEventListener("input", filterCitizenTable);
    $("#citizen-refresh").addEventListener("click", () => loadPage());
    if (state.selectedCitizen) inspectCitizen(state.selectedCitizen);
  }
  function filterCitizenTable() {
    const term = $("#citizen-search").value.toLowerCase();
    const rows = state.citizenRows.filter(n => [n.name,n.id,n.occupation,n.location_id].some(v => String(v || "").toLowerCase().includes(term)));
    const html = rows.map(n => '<tr data-citizen="' + esc(n.id) + '"><td class="primary-cell"><strong>' + esc(n.name) + '</strong><small>' + esc(n.id) + '</small></td><td>' + esc(n.occupation) + '</td><td>' + esc(n.location_id) + '</td><td>' + esc(n.current_action) + '</td><td>' + esc(num(n.wealth_gold)) + '</td><td>' + (n.is_alive ? "Alive" : "Deceased") + '</td></tr>');
    $("#citizen-table").innerHTML = table(["Citizen","Occupation","Current room","Current action","Wealth (g)","Status"], html);
  }
  async function inspectCitizen(id) {
    state.selectedCitizen = id;
    const box = $("#citizen-inspector"); if (!box) return;
    box.innerHTML = '<div class="loading-state"><span class="spinner"></span><span>Loading citizen dossier…</span></div>';
    try {
      const results = await Promise.allSettled([
        get("/citizens/" + encodeURIComponent(id) + "/profile"),
        get("/citizens/" + encodeURIComponent(id) + "/state"),
        get("/citizens/" + encodeURIComponent(id) + "/relationships"),
        get("/citizens/" + encodeURIComponent(id) + "/decision")
      ]);
      const profile = results[0].status === "fulfilled" ? obj(results[0].value) : {};
      const current = results[1].status === "fulfilled" ? obj(results[1].value) : {};
      const relations = results[2].status === "fulfilled" ? obj(results[2].value) : {};
      const decision = results[3].status === "fulfilled" ? obj(results[3].value) : {};
      box.innerHTML = '<section class="card inspector"><div class="card-head"><div><h2>' + esc(profile.name || current.name || id) + '</h2><p>Citizen dossier · ' + esc(id) + '</p></div><span class="pill">Live record</span></div>' +
        '<div class="field-grid">' + field("Occupation",profile.occupation) + field("Social class",profile.social_class) + field("Wealth",profile.wealth_gold == null ? "—" : num(profile.wealth_gold) + " g") + field("Current action",current.current_action) + field("Location",current.location_id) + field("Home",profile.home_location_id) + '</div>' +
        '<div class="card-head"><div><h2>Needs & feelings</h2><p>Current state vectors</p></div></div><div class="field-grid">' +
        keys(current.needs).map(k => field(k,current.needs[k])).join("") + keys(current.feelings).map(k => field(k,current.feelings[k])).join("") + '</div>' +
        '<div class="card-head"><div><h2>Decision explanation</h2><p>Why this citizen selected their current action</p></div></div><div class="field-grid">' +
        field("Chosen drive",decision.chosen_drive) + field("Utility score",decision.chosen_utility_score) + field("Runner-up",decision.runner_up_drive) + field("Utility spread",decision.utility_spread) + '</div>' +
        '<div class="card-head"><div><h2>Relationships</h2><p>Social connections and affiliations</p></div></div><div class="field-grid">' +
        field("Romantic bond",obj(relations.romantic_bond).partner_name) + field("Social clubs",arr(relations.social_clubs).length) + field("Grudges",arr(relations.grudges_harbored).length) + field("Opinions tracked",keys(relations.opinions).length) + '</div></section>';
      if (results.some(r => r.status === "rejected")) box.insertAdjacentHTML("beforeend", '<div class="notice">Some dossier sections are not exposed by the current API adapter. Available sections are shown; unavailable sections are not replaced with sample values.</div>');
    } catch (error) { box.innerHTML = errorBox("Could not load citizen dossier", error); }
  }
  async function renderWorld() {
    const hierarchy = obj(await get(routes.world));
    const settlements = keys(hierarchy);
    if (!settlements.length) { $("#page-content").innerHTML = empty("No world hierarchy returned", "The API did not return settlement data.", "▦"); return; }
    let html = '<div class="split-view"><section class="card"><div class="card-head"><div><h2>Settlement hierarchy</h2><p>Settlements, buildings and rooms from the live world model</p></div></div><div class="tree-list">';
    settlements.forEach(sid => {
      const settlement = obj(hierarchy[sid]);
      html += '<div class="tree-item"><div class="tree-button"><span>⌂</span><strong>' + esc(settlement.name || sid) + '</strong><span class="tree-meta">' + esc(num(settlement.buildings_count)) + ' buildings</span></div>';
      keys(settlement.buildings).forEach(bid => {
        const building = obj(settlement.buildings[bid]);
        html += '<div class="tree-button" style="padding-left:22px"><span>▦</span><strong>' + esc(building.name || bid) + '</strong><span class="tree-meta">' + esc(building.category || "Building") + '</span></div><div class="tree-children">';
        keys(building.rooms).forEach(rid => {
          const room = obj(building.rooms[rid]);
          html += '<button class="tree-child" data-room="' + esc(rid) + '"><span>' + esc(room.name || rid) + '</span><span>' + esc(num(room.occupants_count)) + ' occupants · Inspect →</span></button>';
        });
        html += '</div>';
      });
      html += '</div>';
    });
    html += '</div></section><section id="room-inspector" class="card inspector">' + empty("Select a room", "Inspect occupants, objects, room connections and environmental details.", "⌂") + '</section></div>';
    $("#page-content").innerHTML = html;
  }
  async function inspectRoom(id) {
    const box = $("#room-inspector"); box.innerHTML = '<div class="loading-state"><span class="spinner"></span><span>Loading room…</span></div>';
    try {
      const r = obj(await get("/rooms/" + encodeURIComponent(id)));
      box.innerHTML = '<h2>' + esc(r.name || id) + '</h2><p class="inspector-subtitle">' + esc(r.room_id || id) + '</p><div class="field-grid">' +
        field("Archetype",r.archetype) + field("Building",r.building_name) + field("Occupants",r.occupants_count) + field("Temperature",r.ambient_temperature_celsius == null ? "—" : num(r.ambient_temperature_celsius) + " °C") +
        field("Objects",arr(r.objects).length) + field("Connected rooms",arr(r.connected_rooms).length) + '</div><div class="card-head"><h2>Occupants</h2></div>' +
        (arr(r.occupants).map(n => '<div class="data-line"><span>' + esc(n.name) + '</span><strong>' + esc(n.action) + '</strong></div>').join("") || '<p class="inspector-subtitle">No occupants reported.</p>') +
        '<div class="card-head"><h2>Objects</h2></div>' +
        (arr(r.objects).map(o => '<div class="data-line"><span>' + esc(o.name) + '</span><strong>' + esc(o.type) + '</strong></div>').join("") || '<p class="inspector-subtitle">No objects reported.</p>') + '</div>';
    } catch (error) { box.innerHTML = errorBox("Room inspection unavailable", error); }
  }
  async function renderEconomy() {
    const e = obj(await get(routes.economy)), stocks = obj(e.commodity_stocks), prices = obj(e.commodity_prices);
    const rows = keys(stocks).map(k => '<tr><td class="primary-cell"><strong>' + esc(k.replace(/_/g," ")) + '</strong><small>' + esc(k) + '</small></td><td>' + esc(num(stocks[k])) + '</td><td>' + esc(prices[k] == null ? "—" : num(prices[k]) + " g") + '</td></tr>');
    $("#page-content").innerHTML = '<div class="metrics">' +
      metric("Total currency",e.total_currency_gold == null ? "—" : num(e.total_currency_gold) + " g","Economy overview","¤") +
      metric("Treasury",e.treasury_balance_gold == null ? "—" : num(e.treasury_balance_gold) + " g","Municipal balance","▤") +
      metric("Gini coefficient",num(e.gini_coefficient),"Wealth distribution","◒") +
      metric("Households",num(e.households_count),"Registered households","⌂") +
      '</div><section class="card section-card"><div class="card-head"><div><h2>Commodity reserves</h2><p>Live stocks and market-clearing prices</p></div></div>' +
      table(["Commodity","Stock","Market price"],rows,"No commodity data","No live commodity stock or price records were returned.") + '</section>' +
      '<div class="notice">The current LocalVisualAPI exposes this economy overview and the commodity stock/price snapshots. Production history, demand, job records, tax receipts and household-level ledgers are not yet exposed through this facade.</div>';
  }
  async function renderSociety() {
    const results = await Promise.allSettled([get(routes.society),get(routes.justice)]);
    const s = results[0].status === "fulfilled" ? obj(results[0].value) : {};
    const j = results[1].status === "fulfilled" ? obj(results[1].value) : {};
    const factions = obj(s.factions);
    const factionRows = keys(factions).map(id => { const f=obj(factions[id]); return '<tr><td class="primary-cell"><strong>' + esc(f.name || id) + '</strong><small>' + esc(id) + '</small></td><td>' + esc(f.leader_id) + '</td><td>' + esc(num(f.member_count)) + '</td><td>' + esc(num(f.influence)) + '</td><td>' + (f.is_on_strike ? '<span class="pill warning">On strike</span>' : '<span class="pill">Active</span>') + '</td></tr>'; });
    const lawsuits = arr(j.pending_lawsuits).map(l => '<tr><td>' + esc(l.lawsuit_id || l.id) + '</td><td>' + esc(l.plaintiff_id) + '</td><td>' + esc(l.defendant_id) + '</td><td>' + esc(l.status || "Pending") + '</td></tr>');
    $("#page-content").innerHTML = '<div class="metrics">' +
      metric("Factions",num(keys(factions).length),"Political groups","◉") +
      metric("Active grudges",num(arr(s.active_grudges).length),"Unresolved grievances","!") +
      metric("Domestic tensions",num(arr(s.domestic_spats).length),"Elevated relationship friction","⌁") +
      metric("Pending lawsuits",num(arr(j.pending_lawsuits).length),"Court docket","§") +
      '</div><section class="card section-card"><div class="card-head"><div><h2>Political factions</h2><p>Membership, influence and strike status</p></div></div>' +
      table(["Faction","Leader","Members","Influence","Status"],factionRows,"No faction records","No political faction data was returned.") + '</section>' +
      '<section class="card section-card"><div class="card-head"><div><h2>Pending lawsuits</h2><p>Open municipal court cases</p></div></div>' +
      table(["Case","Plaintiff","Defendant","Status"],lawsuits,"No pending lawsuits","The court docket contains no pending cases or is unavailable.") + '</section>' +
      '<div class="notice">The current facade also exposes decrees, resolved lawsuits and probation records. Clubs, fraternal aid, information networks, life goals and recreation still need dedicated query methods.</div>';
  }
  async function renderClimate() {
    const c = obj(await get(routes.climate));
    $("#page-content").innerHTML = '<div class="metrics">' +
      metric("Season",c.season || "—","Current climate season","☼") +
      metric("Temperature",c.ambient_temperature_celsius == null ? "—" : num(c.ambient_temperature_celsius) + " °C","Ambient temperature","°") +
      metric("Humidity",c.humidity == null ? "—" : num(c.humidity * 100) + "%","Relative humidity","≈") +
      metric("Pressure",c.barometric_pressure_kpa == null ? "—" : num(c.barometric_pressure_kpa) + " kPa","Barometric pressure","⌁") +
      '</div><section class="card mini-card"><h3>Current conditions</h3>' +
      '<div class="data-line"><span>Precipitation</span><strong>' + esc(c.precipitation) + '</strong></div>' +
      '<div class="data-line"><span>Solar peak hour</span><strong>' + esc(num(c.solar_peak_hour)) + '</strong></div></section>' +
      '<div class="notice">The current facade provides a current climate snapshot only. Climate history, local room conditions over time, health incidents and mortality analytics are not exposed as UI queries.</div>';
  }
  async function renderEvents() {
    const events = arr(await get(routes.events + "?limit=200"));
    const rows = events.slice().reverse().map(e => '<tr><td>' + esc(num(e.tick)) + '</td><td class="primary-cell"><strong>' + esc(e.event_type) + '</strong><small>' + esc(e.source_id) + '</small></td><td>' + esc(e.timestamp) + '</td><td>' + esc(JSON.stringify(obj(e.payload))) + '</td></tr>');
    $("#page-content").innerHTML = '<section class="card section-card"><div class="toolbar"><input class="search-input" id="event-search" placeholder="Filter event type, source or payload…"><span class="pill">' + esc(events.length) + ' returned</span></div><div id="event-table">' +
      table(["Tick","Event / source","Timestamp","Payload"],rows,"No events retained","The event bus returned no matching records.") + '</div></section>' +
      '<div class="notice">The current EventBus keeps a bounded in-memory history. The browser-facing adapter should expose the retention limit and a reconnect cursor before enabling continuous streaming.</div>';
    $("#event-search").addEventListener("input", function () {
      const q=this.value.toLowerCase();
      const filtered=events.filter(e=>JSON.stringify(e).toLowerCase().includes(q)).reverse().map(e=>'<tr><td>'+esc(num(e.tick))+'</td><td class="primary-cell"><strong>'+esc(e.event_type)+'</strong><small>'+esc(e.source_id)+'</small></td><td>'+esc(e.timestamp)+'</td><td>'+esc(JSON.stringify(obj(e.payload)))+'</td></tr>');
      $("#event-table").innerHTML=table(["Tick","Event / source","Timestamp","Payload"],filtered);
    });
  }
  async function renderContent() {
    const results = await Promise.allSettled([get(routes.scenarios),get(routes.packs)]);
    const scenarios = results[0].status === "fulfilled" ? arr(results[0].value) : [];
    const packs = results[1].status === "fulfilled" ? arr(results[1].value) : [];
    const scenarioRows = scenarios.map(s=>'<tr><td class="primary-cell"><strong>'+esc(s.name || s.filename)+'</strong><small>'+esc(s.filename)+'</small></td><td>'+esc(s.description)+'</td><td>'+esc(s.settlement_id)+'</td></tr>');
    const packRows = packs.map(p=>'<tr><td class="primary-cell"><strong>'+esc(p.name || p.pack_id)+'</strong><small>'+esc(p.pack_id || p.id)+'</small></td><td>'+esc(p.version || "—")+'</td><td>'+esc(p.description || "—")+'</td></tr>');
    $("#page-content").innerHTML = '<section class="card section-card"><div class="card-head"><div><h2>Scenarios</h2><p>Available declarative simulation starting points</p></div></div>' +
      table(["Scenario","Description","Settlement"],scenarioRows,"No scenarios returned","The API did not return scenario manifests.") + '</section>' +
      '<section class="card section-card"><div class="card-head"><div><h2>Content packs</h2><p>Installed pack manifests</p></div></div>' +
      table(["Pack","Version","Description"],packRows,"No content packs returned","No pack manifests were returned by the connected API.") + '</section>' +
      '<div class="notice">The current facade supports scenario inspection, pack listing and settings-manifest inspection. Pack validation, dependency diagnostics, unmounting, safe reload and real merge-patch preview are not fully exposed.</div>';
  }
  async function renderDiagnostics() {
    const results = await Promise.allSettled([get(routes.performance),get(routes.integrity)]);
    const p = results[0].status === "fulfilled" ? obj(results[0].value) : {};
    const i = results[1].status === "fulfilled" ? obj(results[1].value) : {};
    const timings = obj(p.subsystem_timings_ms), counts = obj(p.subsystem_call_counts), errors = obj(p.subsystem_errors);
    const rows = keys(timings).map(id=>'<tr><td class="primary-cell"><strong>'+esc(id)+'</strong></td><td>'+esc(num(timings[id]))+' ms</td><td>'+esc(num(counts[id]))+'</td><td>'+esc(num(errors[id]))+'</td></tr>');
    const world = obj(i.world_integrity);
    $("#page-content").innerHTML = '<div class="metrics">' +
      metric("Average tick",p.avg_tick_duration_ms == null ? "—" : num(p.avg_tick_duration_ms)+" ms","Recent tick average","◷") +
      metric("Active subsystems",num(p.active_subsystems_count),"Enabled pipeline components","⌘") +
      metric("Registered subsystems",num(p.total_registered_subsystems),"Pipeline registry","▤") +
      metric("Pipeline time",p.total_pipeline_time_ms == null ? "—" : num(p.total_pipeline_time_ms)+" ms","Cumulative measured time","⌁") +
      '</div><section class="card section-card"><div class="card-head"><div><h2>Subsystem timings</h2><p>Accumulated execution duration, calls and errors</p></div></div>' +
      table(["Subsystem","Total time","Calls","Errors"],rows,"No profiling data","No subsystem performance profile was returned.") + '</section>' +
      '<section class="card mini-card"><h3>World integrity</h3><div class="data-line"><span>Integrity status</span><strong>' + (world.is_valid == null ? "Not reported" : (world.is_valid ? "Valid" : "Issues found")) + '</strong></div>' +
      '<div class="data-line"><span>Action entropy</span><strong>' + esc(num(obj(i.entropy).entropy)) + '</strong></div>' +
      '<div class="data-line"><span>Spatial coverage</span><strong>' + esc(num(obj(i.spatial_coverage).coverage)) + '</strong></div></section>' +
      '<div class="notice">The current API exposes pipeline timing and integrity audit calls. Health/uptime, structured logs, memory use, service-level status and telemetry history are not yet connected. Integrity output should be treated as authoritative only after its underlying auditor has been validated against real runs.</div>';
  }
  async function loadPage() {
    header(); showLoading();
    const connected = await refreshCore();
    if (!connected) { disconnected(); return; }
    try {
      const renderers = { overview:renderOverview, citizens:renderCitizens, world:renderWorld, economy:renderEconomy, society:renderSociety, climate:renderClimate, events:renderEvents, content:renderContent, diagnostics:renderDiagnostics };
      await renderers[state.page]();
    } catch (error) { $("#page-content").innerHTML = errorBox("Unable to load " + pages[state.page][1].toLowerCase(), error); }
  }
  function navigate(page) {
    if (!pages[page]) return;
    state.page=page; header(); loadPage();
  }
  async function simulationToggle() {
    if (!state.status) return;
    const paused = !!state.status.is_paused || state.status.lifecycle_state !== "RUNNING";
    try {
      const result = await post(paused ? "/simulation/start" : "/simulation/pause");
      setStatus(result); toast(paused ? "Simulation resumed" : "Simulation paused"); loadPage();
    } catch (error) { toast("Simulation control failed: " + error.message); }
  }
  function confirmAction(title,message,action) {
    const dialog=$("#confirm-dialog"); $("#dialog-title").textContent=title; $("#dialog-message").textContent=message;
    const confirm=$("#dialog-confirm");
    confirm.onclick=async function (event) {
      event.preventDefault(); dialog.close("confirm");
      try { await action(); toast("Simulation action completed"); await loadPage(); }
      catch(error){ toast("Action failed: "+error.message); }
    };
    dialog.showModal();
  }
  document.addEventListener("click", function (event) {
    const nav=event.target.closest("[data-page]"); if(nav){navigate(nav.dataset.page);return;}
    const go=event.target.closest("[data-go]"); if(go){navigate(go.dataset.go);return;}
    const citizen=event.target.closest("[data-citizen]"); if(citizen){inspectCitizen(citizen.dataset.citizen);return;}
    const room=event.target.closest("[data-room]"); if(room){inspectRoom(room.dataset.room);return;}
  });
  $("#refresh-button").addEventListener("click",loadPage);
  $("#run-button").addEventListener("click",simulationToggle);
  window.addEventListener("DOMContentLoaded",loadPage);
  if (document.readyState !== "loading") loadPage();
})();