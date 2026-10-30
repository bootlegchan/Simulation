import Phaser from "phaser";

const PALETTE = {
  sky: 0xb9dce0, grass: 0x9acb83, grassLight: 0xb7d99a,
  path: 0xe8d5a8, pathDark: 0xd5bd8d, wood: 0x9a6948,
  roof: 0xc77e61, leaf: 0x5d9a62, leaf2: 0x79ad68,
  cream: 0xfff1d6, ink: 0x435b4a
};

export default class WorldScene extends Phaser.Scene {
  constructor() {
    super("WorldScene");
    this.npcs = {};
    this.selectedId = null;
    this.onSelect = () => {};
    this.onInspect = () => {};
  }

  create() {
    this.cameras.main.setBackgroundColor(PALETTE.sky);
    this.drawLandscape();
    this.drawBuildings();
    this.drawLandmarks();
    this.input.on("gameobjectdown", (_pointer, object) => {
      if (object.getData("npcId")) {
        this.selectedId = object.getData("npcId");
        this.onSelect(this.npcs[this.selectedId]);
        this.refreshSelection();
      }
    });
    this.input.on("pointerdown", (pointer) => {
      if (pointer.downElement?.tagName === "CANVAS") this.onInspect(null);
    });
    this.scale.on("resize", () => this.drawLandscape());
    this.events.on("shutdown", () => this.input.removeAllListeners());
  }

  drawLandscape() {
    const w = this.scale.width, h = this.scale.height;
    if (this.landscape) this.landscape.destroy();
    this.landscape = this.add.graphics();
    const g = this.landscape;
    g.fillStyle(PALETTE.sky).fillRect(0, 0, w, h);
    g.fillStyle(0xa6d0d0).fillEllipse(w * .5, h * .82, w * 1.2, h * .5);
    g.fillStyle(PALETTE.grass).fillRect(0, h * .36, w, h * .64);
    g.fillStyle(PALETTE.grassLight).fillEllipse(w * .5, h * .54, w * 1.1, h * .36);
    // A winding village lane gives the world its side-scrolling storybook character.
    g.fillStyle(PALETTE.path).fillPoints([
      new Phaser.Math.Vector2(0, h*.76), new Phaser.Math.Vector2(0, h*.66),
      new Phaser.Math.Vector2(w*.24, h*.61), new Phaser.Math.Vector2(w*.48, h*.68),
      new Phaser.Math.Vector2(w*.72, h*.59), new Phaser.Math.Vector2(w, h*.63),
      new Phaser.Math.Vector2(w, h*.77), new Phaser.Math.Vector2(w*.7, h*.73),
      new Phaser.Math.Vector2(w*.48, h*.8), new Phaser.Math.Vector2(w*.23, h*.72)
    ], true);
    g.lineStyle(3, PALETTE.pathDark, .55).strokePoints([
      new Phaser.Math.Vector2(0,h*.72),new Phaser.Math.Vector2(w*.25,h*.67),
      new Phaser.Math.Vector2(w*.49,h*.74),new Phaser.Math.Vector2(w*.73,h*.66),
      new Phaser.Math.Vector2(w,h*.7)
    ]);
    for (let i=0;i<18;i++) {
      const x=(i*137+43)%Math.max(w,1), y=h*(.39+((i*31)%25)/100);
      g.fillStyle(i%2?0x78ad6b:0x8dbd78,.6).fillCircle(x,y,2+(i%3));
    }
    this.drawClouds(w,h);
  }

  drawClouds(w,h) {
    if (this.clouds) this.clouds.destroy();
    this.clouds=this.add.graphics();
    for (let i=0;i<5;i++) {
      const x=(w*.12+i*w*.22), y=h*(.12+(i%2)*.09);
      this.clouds.fillStyle(0xffffff,.7).fillEllipse(x,y,66,22);
      this.clouds.fillEllipse(x-17,y+2,28,19);
      this.clouds.fillEllipse(x+15,y-5,34,25);
    }
  }

  drawBuildings() {
    if (this.buildings) this.buildings.destroy();
    this.buildings=this.add.container(0,0);
    const w=this.scale.width,h=this.scale.height;
    const specs=[
      {x:.14,y:.47,s:1.05,roof:0xc77e61,label:"TOWN HALL"},
      {x:.37,y:.42,s:.9,roof:0xd49b59,label:"GENERAL STORE"},
      {x:.64,y:.45,s:1.05,roof:0x9d7caa,label:"THE TAVERN"},
      {x:.86,y:.43,s:.84,roof:0x7195a0,label:"APOTHECARY"}
    ];
    specs.forEach((b,i)=>{
      const x=w*b.x,y=h*b.y,s=b.s;
      const c=this.add.container(x,y);
      const g=this.add.graphics();
      g.fillStyle(0x000000,.12).fillEllipse(0,75*s,160*s,24*s);
      g.fillStyle(0xf1d8ad).fillRoundedRect(-65*s,-12*s,130*s,83*s,7*s);
      g.fillStyle(0xb9865c).fillRect(-9*s,28*s,20*s,43*s);
      g.fillStyle(0x8dc4c6).fillRoundedRect(-48*s,14*s,23*s,25*s,4*s);
      g.fillRoundedRect(25*s,14*s,23*s,25*s,4*s);
      g.fillStyle(b.roof).fillPoints([
        new Phaser.Math.Vector2(-77*s,-12*s),new Phaser.Math.Vector2(0,-65*s),
        new Phaser.Math.Vector2(77*s,-12*s)
      ],true);
      g.fillStyle(0xf5e8ca).fillRoundedRect(-26*s,-55*s,52*s,17*s,5*s);
      c.add(g);
      const label=this.add.text(0,88*s,b.label,{fontFamily:"Trebuchet MS",fontSize:"10px",fontStyle:"bold",color:"#526c55",letterSpacing:1}).setOrigin(.5);
      c.add(label);
      this.buildings.add(c);
    });
  }

  drawLandmarks() {
    if (this.landmarks) this.landmarks.destroy();
    this.landmarks=this.add.graphics();
    const w=this.scale.width,h=this.scale.height,g=this.landmarks;
    // Layered trees, shrubs and a small pond.
    for(let i=0;i<13;i++){
      const x=(i*173+75)%Math.max(w,1), y=h*(.38+((i*19)%23)/100);
      g.fillStyle(0x8a6546).fillRoundedRect(x-5,y+18,10,27,4);
      g.fillStyle(i%2?PALETTE.leaf:PALETTE.leaf2).fillCircle(x,y,22+(i%3)*5);
      g.fillStyle(0xa5cd83,.8).fillCircle(x-8,y-8,8);
    }
    g.fillStyle(0x6fb7c0).fillEllipse(w*.51,h*.91,180,48);
    g.lineStyle(3,0xd9f0df,.8).strokeEllipse(w*.51,h*.91,180,48);
    g.fillStyle(0xfff1c2).fillCircle(w*.78,h*.15,25);
  }

  setWorld(npcs) {
    this.npcs=npcs||{};
    Object.values(this.npcs).forEach((npc,index)=>{
      if(!npc._gameObject) {
        const p=this.positionFor(npc,index);
        npc._gameObject=this.makeVillager(npc,p.x,p.y,index);
      } else {
        const p=this.positionFor(npc,index);
        npc._gameObject.setPosition(p.x,p.y);
      }
      npc._gameObject.setData("npcId",npc.id);
    });
    Object.values(this.npcs).forEach(n=>n._gameObject?.setVisible(true));
    this.refreshSelection();
  }

  positionFor(npc,index) {
    const w=this.scale.width,h=this.scale.height;
    const hash=Array.from(npc.location_id||"").reduce((a,c)=>a+c.charCodeAt(0),0);
    return {x:w*(.07+((hash+index*17)%86)/100),y:h*(.64+((hash+index*7)%12)/100)};
  }

  makeVillager(npc,x,y,index) {
    const c=this.add.container(x,y);
    const g=this.add.graphics();
    const colors=[0xd98c69,0x7898bd,0xd4ae62,0x8baf87,0xb58db9,0xe0b6a0];
    const coat=colors[index%colors.length];
    g.fillStyle(0x000000,.16).fillEllipse(0,23,27,9);
    g.fillStyle(coat).fillRoundedRect(-10,-2,20,24,7);
    g.fillStyle(0xf1c9a4).fillCircle(0,-12,10);
    g.fillStyle(0x76513d).fillEllipse(0,-19,21,10);
    g.fillStyle(0x51483c).fillCircle(-3,-12,1.4);
    g.fillCircle(4,-12,1.4);
    g.lineStyle(1.5,0x9b5f52).beginPath().arc(1,-8,3,.2,2.5,false).strokePath();
    g.fillStyle(0x76513d).fillRoundedRect(-8,18,7,7,2);
    g.fillRoundedRect(2,18,7,7,2);
    c.add(g);
    const name=this.add.text(0,-38,npc.name.split(" ")[0],{
      fontFamily:"Trebuchet MS",fontSize:"11px",fontStyle:"bold",
      color:"#405b48",backgroundColor:"#fff8e8",padding:{x:5,y:3}
    }).setOrigin(.5);
    c.add(name);
    c.setSize(34,58).setInteractive(new Phaser.Geom.Rectangle(-17,-35,34,65),Phaser.Geom.Rectangle.Contains);
    c.setData("npcId",npc.id);
    return c;
  }

  refreshSelection() {
    Object.values(this.npcs).forEach(n=>{
      const active=n.id===this.selectedId;
      n._gameObject?.setScale(active?1.12:1);
      const label=n._gameObject?.list?.[1];
      if(label) label.setStyle({backgroundColor:active?"#f3d28c":"#fff8e8"});
    });
  }
}