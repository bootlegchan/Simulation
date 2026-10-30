import Phaser from "phaser";

const WORLD = { width: 2600, height: 700 };
const PALETTE = {
  sky: 0xb9dce0, distant: 0xa9c9ba, grass: 0x94c47f,
  grassLight: 0xb0d48e, path: 0xe8d5a8, pathEdge: 0xcbb98f,
  leaf: 0x5d9562, leafLight: 0x82ad70, trunk: 0x896548,
  cream: 0xfff2d9, ink: 0x435b4a
};

const hashText = value => Array.from(String(value || "")).reduce((sum, char) => (sum * 31 + char.charCodeAt(0)) >>> 0, 7);

export default class WorldScene extends Phaser.Scene {
  constructor() {
    super("WorldScene");
    this.npcs = {};
    this.sprites = new Map();
    this.buildingTargets = new Map();
    this.selectedId = null;
    this.onSelect = () => {};
    this.onBuilding = () => {};
  }

  create() {
    this.cameras.main.setBackgroundColor(PALETTE.sky);
    this.cameras.main.setBounds(0, 0, WORLD.width, WORLD.height);
    this.physics?.world?.setBounds?.(0, 0, WORLD.width, WORLD.height);
    this.drawLandscape();
    this.drawBuildings();
    this.drawLandmarks();
    this.setupCameraControls();

    this.input.on("gameobjectdown", (_pointer, object) => {
      const npcId = object.getData("npcId");
      const buildingId = object.getData("buildingId");
      if (npcId) {
        this.selectedId = npcId;
        this.onSelect(this.npcs[npcId] || null);
        this.refreshSelection();
      } else if (buildingId) {
        const building = this.buildingTargets.get(buildingId);
        this.onBuilding(building || { id: buildingId, name: buildingId });
      }
    });

    this.events.once("shutdown", () => {
      this.input.removeAllListeners();
      this.scale.removeAllListeners();
      this.tweens.killAll();
      this.time.removeAllEvents();
    });
  }

  setupCameraControls() {
    const camera = this.cameras.main;
    let dragging = false;
    let lastX = 0;
    this.input.on("pointerdown", pointer => {
      if (pointer.button !== 0) return;
      dragging = true;
      lastX = pointer.x;
    });
    this.input.on("pointerup", () => { dragging = false; });
    this.input.on("pointerupoutside", () => { dragging = false; });
    this.input.on("pointermove", pointer => {
      if (!dragging || !pointer.isDown) return;
      camera.scrollX -= (pointer.x - lastX) / camera.zoom;
      lastX = pointer.x;
    });
    this.input.on("wheel", (_pointer, _objects, _dx, dy) => {
      camera.scrollX = Phaser.Math.Clamp(camera.scrollX + dy * 0.9, 0, WORLD.width - this.scale.width);
    });
    this.cursors = this.input.keyboard?.createCursorKeys();
  }

  update(_time, delta) {
    if (!this.cursors) return;
    const speed = 420 * (delta / 1000);
    if (this.cursors.left.isDown) this.cameras.main.scrollX -= speed;
    if (this.cursors.right.isDown) this.cameras.main.scrollX += speed;
  }

  drawLandscape() {
    this.landscape?.destroy();
    this.landscape = this.add.graphics();
    const g = this.landscape;
    const w = WORLD.width, h = WORLD.height;

    g.fillStyle(PALETTE.sky).fillRect(0, 0, w, h);
    g.fillStyle(0xd6e8d8, 0.7).fillEllipse(w * 0.5, h * 0.38, w * 1.1, h * 0.48);
    g.fillStyle(PALETTE.distant).fillEllipse(w * 0.18, h * 0.47, 900, 250);
    g.fillStyle(0x9fc5a1).fillEllipse(w * 0.73, h * 0.45, 1100, 260);
    g.fillStyle(PALETTE.grass).fillRect(0, h * 0.48, w, h * 0.52);
    g.fillStyle(PALETTE.grassLight).fillEllipse(w * 0.48, h * 0.64, w * 1.05, h * 0.44);

    // Winding lane with a soft double edge.
    const road = [
      [0, 520], [0, 455], [360, 438], [690, 480], [1030, 430],
      [1370, 462], [1720, 420], [2070, 450], [2600, 410],
      [2600, 555], [2100, 560], [1730, 540], [1370, 580],
      [1030, 555], [690, 590], [360, 550]
    ].map(([x, y]) => new Phaser.Math.Vector2(x, y));
    g.fillStyle(PALETTE.pathEdge).fillPoints(road, true);
    const inner = road.map(p => new Phaser.Math.Vector2(p.x, p.y + (p.y < 500 ? 14 : -14)));
    g.fillStyle(PALETTE.path).fillPoints(inner, true);

    // Small meadow details add scale without overwhelming the characters.
    for (let i = 0; i < 160; i++) {
      const seed = hashText("meadow-" + i);
      const x = seed % w;
      const y = 350 + ((seed >>> 8) % 300);
      if (y > 430 && y < 585) continue;
      g.fillStyle(i % 3 ? 0x78a96d : 0xd5bd79, 0.65).fillCircle(x, y, 1 + (i % 3));
    }
    this.drawClouds();
  }

  drawClouds() {
    this.clouds?.destroy();
    this.clouds = this.add.container(0, 0);
    for (let i = 0; i < 9; i++) {
      const x = 120 + i * 300, y = 75 + (i % 3) * 48;
      const cloud = this.add.graphics();
      cloud.fillStyle(0xffffff, 0.68).fillEllipse(x, y, 100, 27);
      cloud.fillEllipse(x - 25, y + 2, 42, 26);
      cloud.fillEllipse(x + 22, y - 7, 54, 36);
      this.clouds.add(cloud);
      this.tweens.add({ targets: cloud, x: 35, duration: 24000 + i * 1700, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    }
  }

  drawBuildings() {
    this.buildings?.destroy();
    this.buildings = this.add.container(0, 0);
    const specs = [
      { id: "town_hall", x: 260, y: 340, scale: 1.12, roof: 0xc77e61, label: "TOWN HALL", tint: 0xf1d8ad },
      { id: "general_store", x: 770, y: 325, scale: 0.98, roof: 0xd49b59, label: "GENERAL STORE", tint: 0xf3dfb5 },
      { id: "tavern", x: 1300, y: 337, scale: 1.08, roof: 0x9d7caa, label: "THE TAVERN", tint: 0xe9d7bb },
      { id: "apothecary", x: 1830, y: 325, scale: 0.92, roof: 0x7195a0, label: "APOTHECARY", tint: 0xf0dfc0 },
      { id: "bakery", x: 2290, y: 342, scale: 1.02, roof: 0xd18b75, label: "THE BAKERY", tint: 0xf4d9b8 }
    ];
    specs.forEach((b, index) => {
      const s = b.scale;
      const c = this.add.container(b.x, b.y);
      const g = this.add.graphics();
      g.fillStyle(0x526d52, 0.15).fillEllipse(0, 90 * s, 190 * s, 26 * s);
      g.fillStyle(b.tint).fillRoundedRect(-70 * s, -12 * s, 140 * s, 94 * s, 8 * s);
      g.fillStyle(0xb9865c).fillRoundedRect(-11 * s, 35 * s, 23 * s, 47 * s, 4 * s);
      g.fillStyle(0x8dc4c6).fillRoundedRect(-53 * s, 13 * s, 26 * s, 29 * s, 4 * s);
      g.fillRoundedRect(27 * s, 13 * s, 26 * s, 29 * s, 4 * s);
      g.fillStyle(b.roof).fillPoints([
        new Phaser.Math.Vector2(-83 * s, -12 * s),
        new Phaser.Math.Vector2(0, -72 * s),
        new Phaser.Math.Vector2(83 * s, -12 * s)
      ], true);
      g.fillStyle(0xfff1d8).fillRoundedRect(-29 * s, -60 * s, 58 * s, 19 * s, 6 * s);
      c.add(g);
      const label = this.add.text(0, 105 * s, b.label, {
        fontFamily: "Nunito, Trebuchet MS, sans-serif", fontSize: "12px",
        fontStyle: "bold", color: "#526c55", letterSpacing: 1,
        backgroundColor: "#fff8e8", padding: { x: 8, y: 5 }
      }).setOrigin(0.5);
      c.add(label);
      c.setSize(180 * s, 190 * s).setInteractive(new Phaser.Geom.Rectangle(-90 * s, -78 * s, 180 * s, 190 * s), Phaser.Geom.Rectangle.Contains);
      c.setData("buildingId", b.id);
      this.buildingTargets.set(b.id, { id: b.id, name: b.label, kind: "building" });
      this.buildings.add(c);
      this.tweens.add({ targets: c, y: b.y - 2, duration: 2600 + index * 190, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    });
  }

  drawLandmarks() {
    this.landmarks?.destroy();
    this.landmarks = this.add.container(0, 0);
    const g = this.add.graphics();
    for (let i = 0; i < 42; i++) {
      const seed = hashText("tree-" + i);
      const x = 55 + (seed % (WORLD.width - 110));
      const y = 335 + ((seed >>> 9) % 150);
      const size = 18 + (seed % 15);
      g.fillStyle(PALETTE.trunk).fillRoundedRect(x - 5, y + 13, 10, 30, 4);
      g.fillStyle(i % 2 ? PALETTE.leaf : PALETTE.leafLight).fillCircle(x, y, size);
      g.fillStyle(0xa9cc82, 0.75).fillCircle(x - 8, y - 8, size * 0.38);
    }
    // Pond at the far edge of the village.
    g.fillStyle(0x6fb7c0).fillEllipse(2460, 625, 260, 72);
    g.lineStyle(4, 0xd9f0df, 0.85).strokeEllipse(2460, 625, 260, 72);
    g.fillStyle(0xfff1c2).fillCircle(2200, 100, 28);
    this.landmarks.add(g);
  }

  positionFor(npc, index) {
    // The Python runner projects each room to stable 3D coordinates.
    // Keep that projection authoritative so residents share locations in the
    // visual world instead of being scattered by a frontend-only hash.
    const hasProjection = Number.isFinite(Number(npc.x_3d)) && Number.isFinite(Number(npc.y_3d));
    if (hasProjection) {
      return {
        x: Phaser.Math.Clamp(105 + Number(npc.x_3d) * 11.2, 55, WORLD.width - 55),
        y: Phaser.Math.Clamp(430 + Number(npc.y_3d) * 0.62 + (index % 3) * 5, 430, 585)
      };
    }

    const location = hashText(npc.location_id || npc.id);
    const xBase = 130 + (location % 2250);
    const yBase = 475 + ((location >>> 9) % 70);
    return {
      x: Phaser.Math.Clamp(xBase + (index % 7) * 15, 40, WORLD.width - 40),
      y: Phaser.Math.Clamp(yBase + (index % 3) * 8, 430, 590)
    };
  }

  setWorld(npcs) {
    const next = npcs || {};
    this.npcs = next;
    const activeIds = new Set(Object.keys(next));

    for (const [id, sprite] of this.sprites.entries()) {
      if (!activeIds.has(id)) {
        sprite.destroy();
        this.sprites.delete(id);
      }
    }

    Object.values(next).forEach((npc, index) => {
      const position = this.positionFor(npc, index);
      let sprite = this.sprites.get(npc.id);
      if (!sprite) {
        sprite = this.makeVillager(npc, position.x, position.y, index);
        this.sprites.set(npc.id, sprite);
      } else {
        const previousLocation = sprite.getData("lastLocation");
        const locationChanged = previousLocation && previousLocation !== npc.location_id;
        const distance = Phaser.Math.Distance.Between(sprite.x, sprite.y, position.x, position.y);
        if (locationChanged && distance > 8) {
          if (sprite.getData("moveTween")) sprite.getData("moveTween").stop();
          const duration = Phaser.Math.Clamp(distance * 5, 500, 2600);
          const tween = this.tweens.add({
            targets: sprite,
            x: position.x,
            y: position.y,
            duration,
            ease: "Sine.easeInOut",
            onComplete: () => sprite.setData("moveTween", null)
          });
          sprite.setData("moveTween", tween);
        } else if (distance > 140) {
          sprite.setPosition(position.x, position.y);
        }
      }

      sprite.setData("npcId", npc.id);
      sprite.setData("npc", npc);
      sprite.setData("lastLocation", npc.location_id);
      const label = sprite.getByName("name");
      if (label) label.setText(String(npc.name || "Neighbour").split(" ")[0]);

      const speech = sprite.getByName("speech");
      if (npc.speech_bubble) {
        if (speech) speech.setText(String(npc.speech_bubble).slice(0, 42));
        else {
          const bubble = this.add.text(0, -68, String(npc.speech_bubble).slice(0, 42), {
            name: "speech",
            fontFamily: "Nunito, Trebuchet MS, sans-serif",
            fontSize: "10px",
            color: "#52634d",
            backgroundColor: "#fffdf2",
            padding: { x: 7, y: 5 },
            wordWrap: { width: 150 }
          }).setOrigin(0.5);
          bubble.setName("speech");
          sprite.add(bubble);
        }
      } else if (speech) {
        speech.destroy();
      }
    });
    this.refreshSelection();
  }

  makeVillager(npc, x, y, index) {
    const sprite = this.add.container(x, y);
    const body = this.add.container(0, 0);
    const g = this.add.graphics();
    const coats = [0xd98c69, 0x7898bd, 0xd4ae62, 0x8baf87, 0xb58db9, 0xe0b6a0, 0x6f9c9a];
    const coat = coats[index % coats.length];

    g.fillStyle(0x000000, 0.15).fillEllipse(0, 25, 29, 9);
    g.fillStyle(coat).fillRoundedRect(-11, -1, 22, 26, 8);
    g.fillStyle(0xf1c9a4).fillCircle(0, -13, 11);
    g.fillStyle(0x76513d).fillEllipse(0, -21, 23, 11);
    g.fillStyle(0x51483c).fillCircle(-4, -13, 1.5);
    g.fillCircle(4, -13, 1.5);
    g.lineStyle(1.5, 0x9b5f52).beginPath().arc(0, -9, 3.5, 0.2, 2.5, false).strokePath();
    g.fillStyle(0x76513d).fillRoundedRect(-9, 20, 7, 8, 2);
    g.fillRoundedRect(2, 20, 7, 8, 2);
    body.add(g);
    sprite.add(body);

    const name = this.add.text(0, -43, String(npc.name || "Neighbour").split(" ")[0], {
      fontFamily: "Nunito, Trebuchet MS, sans-serif",
      fontSize: "12px",
      fontStyle: "bold",
      color: "#405b48",
      backgroundColor: "#fff8e8",
      padding: { x: 6, y: 4 }
    }).setOrigin(0.5);
    name.setName("name");
    sprite.add(name);

    sprite.setSize(38, 68).setInteractive(
      new Phaser.Geom.Rectangle(-19, -39, 38, 70),
      Phaser.Geom.Rectangle.Contains
    );
    sprite.setData("npcId", npc.id);
    sprite.setData("npc", npc);
    sprite.setData("lastLocation", npc.location_id);

    // Bob only the body, leaving the world-position container free to walk.
    this.tweens.add({
      targets: body,
      y: -2,
      duration: 850 + (index % 5) * 120,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut"
    });
    return sprite;
  }

  refreshSelection() {
    for (const [id, sprite] of this.sprites.entries()) {
      const active = id === this.selectedId;
      sprite.setScale(active ? 1.13 : 1);
      const label = sprite.getByName("name");
      if (label) label.setStyle({ backgroundColor: active ? "#f3d28c" : "#fff8e8" });
    }
  }
}
