import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Phaser from "phaser";
import WorldScene from "./game/WorldScene";

const API = import.meta.env.VITE_API_URL || "";
const initialWorld = {
  world_state:{virtual_time_iso:"—",current_tick:0,weather:"CLEAR",season:"SUMMER",time_of_day:"DAY",active_npc_count:0,total_wealth_gold:0,is_running:false},
  npcs:{},objects:{},events:[]
};
const titleCase = value => String(value||"").replaceAll("_"," ").toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());

export default function App(){
  const host=useRef(null), game=useRef(null), scene=useRef(null), socket=useRef(null);
  const [world,setWorld]=useState(initialWorld);
  const [selected,setSelected]=useState(null);
  const [tab,setTab]=useState("village");
  const [connected,setConnected]=useState(false);
  const [notice,setNotice]=useState("The village is waking up…");
  const [busy,setBusy]=useState(false);

  const selectNpc=useCallback(npc=>setSelected(npc?{...npc}:null),[]);
  useEffect(()=>{
    if(!host.current)return;
    const instance=new Phaser.Game({
      type:Phaser.AUTO,parent:host.current,width:1280,height:620,
      backgroundColor:"#b9dce0",render:{antialias:true,pixelArt:false},
      scale:{mode:Phaser.Scale.RESIZE,autoCenter:Phaser.Scale.CENTER_BOTH},
      scene:[WorldScene]
    });
    game.current=instance;
    instance.events.once("ready",()=>{});
    instance.scene.start("WorldScene");
    instance.events.on("step",()=>{});
    const attach=()=>{
      const s=instance.scene.getScene("WorldScene");
      if(s&&s.sys.isActive()){
        scene.current=s;s.onSelect=selectNpc;
        if(Object.keys(world.npcs).length)s.setWorld(world.npcs);
      }else requestAnimationFrame(attach);
    };
    attach();
    return()=>{instance.destroy(true);game.current=null;scene.current=null;};
  },[selectNpc]);

  const applyBatch=useCallback(batch=>{
    if(!batch)return;
    setWorld(prev=>({...prev,...batch,world_state:batch.world_state||prev.world_state}));
    if(scene.current&&batch.npcs)scene.current.setWorld(batch.npcs);
    setSelected(prev=>prev&&batch.npcs?.[prev.id]?{...batch.npcs[prev.id]}:prev);
  },[]);

  const refresh=useCallback(async()=>{
    try{
      const r=await fetch(`${API}/api/v1/simulation/status`);
      if(!r.ok)throw new Error("API unavailable");
      const status=await r.json();
      const [n,o,e]=await Promise.all([
        fetch(`${API}/api/v1/npcs`),fetch(`${API}/api/v1/objects`),fetch(`${API}/api/v1/events/history?limit=12`)
      ]);
      const batch={world_state:status,npcs:await n.json(),objects:await o.json(),events:await e.json()};
      applyBatch(batch);setConnected(true);setNotice("Connected to Oakwood simulation");
    }catch{setConnected(false);setNotice("Preview mode · start the Python server to connect");}
  },[applyBatch]);

  useEffect(()=>{
    refresh();
    const wsUrl=(API||window.location.origin).replace(/^http/,"ws")+"/api/v1/ws/bridge";
    const ws=new WebSocket(wsUrl);socket.current=ws;
    ws.onopen=()=>{setConnected(true);setNotice("Live connection established");};
    ws.onmessage=e=>{
      try{const msg=JSON.parse(e.data);if(msg.type==="SNAPSHOT"||msg.type==="TICK")applyBatch(msg.data);else if(msg.npcs&&msg.world_state)applyBatch(msg);}
      catch(err){console.warn("Ignored malformed simulation update",err);}
    };
    ws.onclose=()=>setConnected(false);
    ws.onerror=()=>setConnected(false);
    return()=>ws.close();
  },[refresh,applyBatch]);

  const npcs=useMemo(()=>Object.values(world.npcs||{}),[world.npcs]);
  const events=useMemo(()=>[...(world.events||[])].reverse().slice(0,8),[world.events]);
  const control=async action=>{
    setBusy(true);
    try{
      const r=await fetch(`${API}/api/v1/simulation/control`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action,step_ticks:1})});
      if(!r.ok)throw new Error("Control request failed");
      await refresh();
    }catch{setNotice("Could not reach the simulation server");}
    finally{setBusy(false);}
  };
  const forceAction=async action=>{
    if(!selected)return;
    try{
      const r=await fetch(`${API}/api/v1/mutate/npc/${encodeURIComponent(selected.id)}/action`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action_type:action})});
      if(!r.ok)throw new Error("Action rejected");
      setNotice(`${selected.name} · ${titleCase(action)} requested`);await refresh();
    }catch{setNotice("Action could not be sent");}
  };

  const state=world.world_state||initialWorld.world_state;
  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark">o</div><div><strong>oakwood</strong><span>A LITTLE WORLD, FULL OF LIFE</span></div></div>
      <nav className="main-nav">
        {["village","residents","stories","ledger"].map(item=><button key={item} className={tab===item?"nav-item active":"nav-item"} onClick={()=>{setTab(item);setSelected(null);}}>{item}</button>)}
      </nav>
      <div className="top-meta"><span className={connected?"live-dot":"live-dot offline"}></span><span>{connected?"WORLD CONNECTED":"PREVIEW MODE"}</span><div className="avatar">Z</div></div>
    </header>

    <section className="welcome-row">
      <div><p className="eyebrow">YOUR LITTLE CORNER OF THE WORLD</p><h1>{tab==="village"?"A lovely day in Oakwood":titleCase(tab)}</h1><p className="subline">A village with its own plans, friendships and little surprises.</p></div>
      <div className="weather-card"><div className="sun-icon">☀</div><div><b>{titleCase(state.weather||"Clear skies")}</b><span>{titleCase(state.season||"Summer")} · {titleCase(state.time_of_day||"Daytime")}</span></div><div className="weather-temp">24°</div></div>
    </section>

    {tab==="village"&&<section className="world-card">
      <div className="world-toolbar"><div><span className="live-pill"><i></i> {state.is_running?"LIVING WORLD":"WORLD AT REST"}</span><span className="day-label">DAY {Math.max(1,Math.floor((state.current_tick||0)/240)+1)} · TICK {state.current_tick||0}</span></div>
        <div className="world-controls"><button disabled={busy} onClick={()=>control(state.is_running?"pause":"resume")}>{state.is_running?"Ⅱ Pause":"▶ Start"}</button><button disabled={busy} onClick={()=>control("step")}>+ 1 moment</button><button className="icon-control" onClick={refresh}>↻</button></div>
      </div>
      <div className="world-canvas"><div className="canvas-host" ref={host}></div><div className="scene-caption"><span>⌖</span> OAKWOOD VILLAGE <b>·</b> THE MARKET LANE</div><div className="scene-hint">Tap a villager to say hello</div></div>
      <div className="world-footer"><div><b>{state.active_npc_count||npcs.length}</b><span> neighbours</span></div><div><b>{Object.keys(world.objects||{}).length}</b><span> little things</span></div><div><b>{Number(state.total_wealth_gold||0).toFixed(0)} ◈</b><span> village wealth</span></div><p>{notice}</p></div>
    </section>}

    {tab==="residents"&&<section className="content-card"><div className="section-heading"><div><p className="eyebrow">THE PEOPLE WHO MAKE THIS PLACE</p><h2>Oakwood neighbours</h2></div><span>{npcs.length} residents</span></div><div className="resident-grid">{npcs.map((n,i)=><button className="resident-card" key={n.id} onClick={()=>setSelected(n)}><div className="resident-avatar" style={{"--hue":i*47+"deg"}}>{(n.name||"?").slice(0,1)}</div><div><b>{n.name}</b><span>{titleCase(n.social_class)} · {titleCase(n.current_action)}</span></div><span className="chevron">›</span></button>)}</div></section>}

    {tab==="stories"&&<section className="content-card"><div className="section-heading"><div><p className="eyebrow">WHAT'S HAPPENING AROUND TOWN</p><h2>Village moments</h2></div><span>Recent activity</span></div><div className="story-list">{events.length?events.map((e,i)=><div className="story" key={e.event_id||i}><div className="story-icon">✿</div><div><b>{titleCase(e.event_type)}</b><p>{e.source_id||"The village"} · {e.timestamp_iso||"Just now"}</p></div><small>#{e.tick}</small></div>):<p className="empty-state">The village is quiet for now. Start the simulation and stories will unfold here.</p>}</div></section>}

    {tab==="ledger"&&<section className="content-card ledger"><p className="eyebrow">A GENTLE LOOK AT THE VILLAGE</p><h2>Village at a glance</h2><div className="ledger-grid"><div><span>Residents</span><b>{npcs.length}</b></div><div><span>Interactive objects</span><b>{Object.keys(world.objects||{}).length}</b></div><div><span>Village wealth</span><b>{Number(state.total_wealth_gold||0).toLocaleString()} ◈</b></div><div><span>Wealth distribution</span><b>{Math.round((state.gini_coefficient||0)*100)}%</b></div></div></section>}

    {selected&&<aside className="resident-drawer"><button className="close-drawer" onClick={()=>setSelected(null)}>×</button><div className="drawer-avatar">{selected.name?.slice(0,1)||"?"}</div><p className="eyebrow">A NEIGHBOUR OF OAKWOOD</p><h2>{selected.name}</h2><p className="resident-role">{titleCase(selected.social_class)} · {titleCase(selected.current_action||"Taking it easy")}</p>
      <div className="need-list"><Need label="Hunger" value={selected.needs_hunger??50} /><Need label="Energy" value={selected.needs_energy??50}/><Need label="Social" value={selected.needs_social??50}/></div>
      <div className="drawer-facts"><span>Currently</span><b>{titleCase(selected.current_action)}</b><span>Feeling</span><b>{titleCase(selected.dominant_feeling||selected.mood_icon||"Content")}</b><span>Coins</span><b>{Number(selected.wealth||0).toFixed(1)} ◈</b></div>
      <p className="drawer-label">A LITTLE NUDGE</p><div className="action-grid"><button onClick={()=>forceAction("SOCIALIZE")}>♡ Say hello</button><button onClick={()=>forceAction("EAT")}>☕ Have a bite</button><button onClick={()=>forceAction("SLEEP")}>☾ Take a rest</button><button onClick={()=>forceAction("WORK")}>✿ Get to work</button></div>
    </aside>}
    <footer className="bottom-note"><span>✿</span> Every neighbour has a story. Let it unfold. <span className="footer-right">OAKWOOD SOCIAL SIMULATION <b>·</b> SEED-DETERMINISTIC WORLD</span></footer>
  </main>;
}

function Need({label,value}){
  const amount=Math.max(0,Math.min(100,Number(value)||0));
  return <div className="need-row"><span>{label}</span><div className="need-track"><i style={{width:amount+"%"}}/></div><b>{Math.round(amount)}</b></div>;
}