import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Phaser from "phaser";
import WorldScene from "./game/WorldScene";

const API = import.meta.env.VITE_API_URL || "";
const EMPTY_WORLD = {
  world_state: {
    virtual_time_iso: "", current_tick: 0, weather: "CLEAR", season: "SUMMER",
    time_of_day: "DAY", active_npc_count: 0, total_wealth_gold: 0, is_running: false
  },
  npcs: {}, objects: {}, events: []
};

const titleCase = value => String(value || "").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());

async function requestJson(path, options) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export default function App() {
  const host = useRef(null);
  const game = useRef(null);
  const scene = useRef(null);
  const worldRef = useRef(EMPTY_WORLD);
  const socket = useRef(null);
  const reconnectTimer = useRef(null);
  const [world, setWorld] = useState(EMPTY_WORLD);
  const [selected, setSelected] = useState(null);
  const [building, setBuilding] = useState(null);
  const [tab, setTab] = useState("village");
  const [connected, setConnected] = useState(false);
  const [notice, setNotice] = useState("The village is waking up…");
  const [busy, setBusy] = useState(false);

  const selectNpc = useCallback(npc => {
    setBuilding(null);
    setSelected(npc ? { ...npc } : null);
  }, []);

  const selectBuilding = useCallback(item => {
    setSelected(null);
    setBuilding(item || null);
  }, []);

  const applyBatch = useCallback(batch => {
    if (!batch || typeof batch !== "object") return;
    const merged = {
      ...worldRef.current,
      ...batch,
      world_state: batch.world_state || worldRef.current.world_state,
      npcs: batch.npcs || worldRef.current.npcs,
      objects: batch.objects || worldRef.current.objects,
      events: batch.events?.length ? [...worldRef.current.events, ...batch.events].slice(-100) : worldRef.current.events
    };
    worldRef.current = merged;
    setWorld(merged);
    if (scene.current && batch.npcs) scene.current.setWorld(batch.npcs);
    if (selected?.id && batch.npcs?.[selected.id]) setSelected({ ...batch.npcs[selected.id] });
  }, [selected?.id]);

  useEffect(() => {
    if (!host.current) return undefined;
    let cancelled = false;
    let frame = 0;
    const instance = new Phaser.Game({
      type: Phaser.AUTO,
      parent: host.current,
      width: 1280,
      height: 620,
      backgroundColor: "#b9dce0",
      render: { antialias: true, pixelArt: false },
      scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH },
      scene: [WorldScene]
    });
    game.current = instance;

    const attachScene = () => {
      if (cancelled) return;
      const activeScene = instance.scene.getScene("WorldScene");
      if (activeScene?.sys?.isActive()) {
        scene.current = activeScene;
        activeScene.onSelect = selectNpc;
        activeScene.onBuilding = selectBuilding;
        if (Object.keys(worldRef.current.npcs).length) activeScene.setWorld(worldRef.current.npcs);
        return;
      }
      frame = requestAnimationFrame(attachScene);
    };
    attachScene();

    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
      scene.current = null;
      instance.destroy(true);
      game.current = null;
    };
  }, [selectNpc, selectBuilding]);

  const refresh = useCallback(async () => {
    try {
      const [status, npcs, objects, events] = await Promise.all([
        requestJson("/api/v1/simulation/status"),
        requestJson("/api/v1/npcs"),
        requestJson("/api/v1/objects"),
        requestJson("/api/v1/events/history?limit=30")
      ]);
      const batch = { world_state: status, npcs, objects, events };
      worldRef.current = { ...EMPTY_WORLD, ...batch };
      setWorld(worldRef.current);
      scene.current?.setWorld(npcs);
      setSelected(current => current && npcs[current.id] ? { ...npcs[current.id] } : current);
      setConnected(true);
      setNotice("Connected to the Oakwood simulation");
      return true;
    } catch (error) {
      setConnected(false);
      setNotice("Preview mode · start the Python server to connect");
      return false;
    }
  }, []);

  useEffect(() => {
    let disposed = false;
    let retryDelay = 1000;

    const connect = () => {
      if (disposed) return;
      const base = API || window.location.origin;
      const wsUrl = base.replace(/^http/, "ws") + "/api/v1/ws/bridge";
      const ws = new WebSocket(wsUrl);
      socket.current = ws;

      ws.onopen = () => {
        retryDelay = 1000;
        setConnected(true);
        setNotice("Live connection established");
      };
      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "SNAPSHOT" || message.type === "TICK") applyBatch(message.data);
          else if (message.world_state && message.npcs) applyBatch(message);
        } catch (error) {
          console.warn("Ignored malformed simulation update", error);
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!disposed) {
          reconnectTimer.current = window.setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 15000);
        }
      };
      ws.onerror = () => ws.close();
    };

    refresh();
    connect();
    return () => {
      disposed = true;
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
      socket.current?.close();
    };
  }, [refresh, applyBatch]);

  const npcs = useMemo(() => Object.values(world.npcs || {}), [world.npcs]);
  const objects = useMemo(() => Object.values(world.objects || {}), [world.objects]);
  const events = useMemo(() => [...(world.events || [])].slice(-12).reverse(), [world.events]);
  const state = world.world_state || EMPTY_WORLD.world_state;

  const control = async action => {
    setBusy(true);
    try {
      const status = await requestJson("/api/v1/simulation/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, step_ticks: 1 })
      });
      applyBatch({ world_state: status });
      await refresh();
    } catch (error) {
      setNotice(`Control failed · ${error.message}`);
    } finally {
      setBusy(false);
    }
  };

  const forceAction = async action => {
    if (!selected) return;
    try {
      await requestJson(`/api/v1/mutate/npc/${encodeURIComponent(selected.id)}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: action })
      });
      setNotice(`${selected.name} · ${titleCase(action)} requested`);
      await refresh();
    } catch (error) {
      setNotice(`Action failed · ${error.message}`);
    }
  };

  const worldClock = state.virtual_time_iso
    ? new Date(state.virtual_time_iso).toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" })
    : "World not started";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">o</div>
          <div><strong>oakwood</strong><span>A LITTLE WORLD, FULL OF LIFE</span></div>
        </div>
        <nav className="main-nav" aria-label="Main navigation">
          {["village", "residents", "stories", "ledger"].map(item => (
            <button key={item} className={tab === item ? "nav-item active" : "nav-item"}
              onClick={() => { setTab(item); setSelected(null); setBuilding(null); }}>
              {item}
            </button>
          ))}
        </nav>
        <div className="top-meta">
          <span className={connected ? "live-dot" : "live-dot offline"} />
          <span>{connected ? "WORLD CONNECTED" : "PREVIEW MODE"}</span>
          <div className="avatar">O</div>
        </div>
      </header>

      <section className="welcome-row">
        <div>
          <p className="eyebrow">YOUR LITTLE CORNER OF THE WORLD</p>
          <h1>{tab === "village" ? "A lovely day in Oakwood" : titleCase(tab)}</h1>
          <p className="subline">A village with its own plans, friendships and little surprises.</p>
        </div>
        <div className="weather-card">
          <div className="sun-icon">{state.time_of_day === "NIGHT" ? "☾" : "☀"}</div>
          <div><b>{titleCase(state.weather || "Clear skies")}</b><span>{titleCase(state.season || "Summer")} · {titleCase(state.time_of_day || "Daytime")}</span></div>
          <div className="weather-temp">{worldClock}</div>
        </div>
      </section>

      {tab === "village" && (
        <section className="world-card">
          <div className="world-toolbar">
            <div>
              <span className="live-pill"><i />{state.is_running ? "LIVING WORLD" : "WORLD AT REST"}</span>
              <span className="day-label">TICK {state.current_tick || 0} · {worldClock}</span>
            </div>
            <div className="world-controls">
              {!state.is_running
                ? <><button disabled={busy} onClick={() => control("start")}>▶ Start</button><button disabled={busy} onClick={() => control("resume")}>↻ Resume</button></>
                : <button disabled={busy} onClick={() => control("pause")}>Ⅱ Pause</button>}
              <button disabled={busy} onClick={() => control("step")}>+ 1 moment</button>
              <button className="icon-control" onClick={refresh} aria-label="Refresh world">↻</button>
            </div>
          </div>
          <div className="world-canvas">
            <div className="canvas-host" ref={host} />
            <div className="scene-caption"><span>⌖</span> OAKWOOD VILLAGE <b>·</b> THE MARKET LANE</div>
            <div className="scene-hint">Drag or scroll to explore · click a neighbour or building</div>
          </div>
          <div className="world-footer">
            <div><b>{state.active_npc_count ?? npcs.length}</b><span> neighbours</span></div>
            <div><b>{state.active_object_count ?? objects.length}</b><span> little things</span></div>
            <div><b>{Number(state.total_wealth_gold || 0).toLocaleString()} ◈</b><span> village wealth</span></div>
            <p>{notice}</p>
          </div>
        </section>
      )}

      {tab === "residents" && (
        <section className="content-card">
          <div className="section-heading"><div><p className="eyebrow">THE PEOPLE WHO MAKE THIS PLACE</p><h2>Oakwood neighbours</h2></div><span>{npcs.length} residents</span></div>
          <div className="resident-grid">
            {npcs.map((npc, index) => (
              <button className="resident-card" key={npc.id} onClick={() => { setSelected(npc); setTab("village"); }}>
                <div className="resident-avatar" style={{ "--hue": `${index * 47}deg` }}>{(npc.name || "?").slice(0, 1)}</div>
                <div><b>{npc.name}</b><span>{titleCase(npc.social_class)} · {titleCase(npc.current_action)}</span></div>
                <span className="chevron">›</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {tab === "stories" && (
        <section className="content-card">
          <div className="section-heading"><div><p className="eyebrow">WHAT'S HAPPENING AROUND TOWN</p><h2>Village moments</h2></div><span>Recent activity</span></div>
          <div className="story-list">
            {events.length ? events.map((event, index) => (
              <div className="story" key={event.event_id || index}>
                <div className="story-icon">✿</div>
                <div><b>{titleCase(event.event_type)}</b><p>{event.source_id || "The village"} · {event.timestamp_iso || "Just now"}</p></div>
                <small>#{event.tick}</small>
              </div>
            )) : <p className="empty-state">The village is quiet for now. Start the simulation and stories will unfold here.</p>}
          </div>
        </section>
      )}

      {tab === "ledger" && (
        <section className="content-card ledger">
          <p className="eyebrow">A GENTLE LOOK AT THE VILLAGE</p><h2>Village at a glance</h2>
          <div className="ledger-grid">
            <div><span>Residents</span><b>{npcs.length}</b></div>
            <div><span>Interactive objects</span><b>{objects.length}</b></div>
            <div><span>Village wealth</span><b>{Number(state.total_wealth_gold || 0).toLocaleString()} ◈</b></div>
            <div><span>Wealth inequality</span><b>{Math.round((state.gini_coefficient || 0) * 100)}%</b></div>
          </div>
        </section>
      )}

      {selected && (
        <aside className="resident-drawer" aria-label={`${selected.name} resident details`}>
          <button className="close-drawer" onClick={() => setSelected(null)} aria-label="Close resident details">×</button>
          <div className="drawer-avatar">{selected.name?.slice(0, 1) || "?"}</div>
          <p className="eyebrow">A NEIGHBOUR OF OAKWOOD</p><h2>{selected.name}</h2>
          <p className="resident-role">{titleCase(selected.social_class)} · {titleCase(selected.current_action || "Taking it easy")}</p>
          <div className="need-list">
            <Need label="Hunger" value={selected.needs_hunger} />
            <Need label="Energy" value={selected.needs_energy} />
            <Need label="Social" value={selected.needs_social} />
          </div>
          <div className="drawer-facts">
            <span>Currently</span><b>{titleCase(selected.current_action)}</b>
            <span>Feeling</span><b>{titleCase(selected.dominant_feeling || selected.mood_icon || "Content")}</b>
            <span>Coins</span><b>{Number(selected.wealth || 0).toFixed(1)} ◈</b>
            <span>Location</span><b>{titleCase(selected.location_id)}</b>
          </div>
          <p className="drawer-label">A LITTLE NUDGE</p>
          <div className="action-grid">
            <button onClick={() => forceAction("SOCIALIZE")}>♡ Say hello</button>
            <button onClick={() => forceAction("EAT")}>☕ Have a bite</button>
            <button onClick={() => forceAction("SLEEP")}>☾ Take a rest</button>
            <button onClick={() => forceAction("WORK")}>✿ Get to work</button>
          </div>
        </aside>
      )}

      {building && (
        <aside className="resident-drawer building-drawer" aria-label={building.name}>
          <button className="close-drawer" onClick={() => setBuilding(null)} aria-label="Close building details">×</button>
          <div className="building-icon">⌂</div>
          <p className="eyebrow">A PLACE IN THE VILLAGE</p>
          <h2>{titleCase(building.name)}</h2>
          <p className="resident-role">A familiar Oakwood landmark.</p>
          <div className="building-note">Building interiors and their inventories will be connected to the simulation's actual settlement data in the next integration pass.</div>
          <button className="building-action" onClick={() => setBuilding(null)}>Back to the village</button>
        </aside>
      )}

      <footer className="bottom-note"><span>✿</span> Every neighbour has a story. Let it unfold. <span className="footer-right">OAKWOOD SOCIAL SIMULATION <b>·</b> SEED-DETERMINISTIC WORLD</span></footer>
    </main>
  );
}

function Need({ label, value }) {
  const amount = Math.max(0, Math.min(100, Number(value ?? 0)));
  return <div className="need-row"><span>{label}</span><div className="need-track"><i style={{ width: amount + "%" }} /></div><b>{Math.round(amount)}</b></div>;
}
