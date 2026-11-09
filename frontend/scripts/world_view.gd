extends Node2D

signal world_clicked(world_position: Vector2)
signal interact_requested
signal close_requested

const WORLD_HEIGHT := 720.0
const PAPER := Color("#eee5d2")
const INK := Color("#283a38")
const RUST := Color("#b66b48")

var _state: Dictionary = {}
var _camera: Camera2D
var _npc_items: Array[Dictionary] = []
var _object_items: Array[Dictionary] = []
var _portal_items: Array[Dictionary] = []
var _outdoor_background: Texture2D

func _ready() -> void:
    _outdoor_background = load("res://assets/backgrounds/village_square.svg") as Texture2D
    _camera = Camera2D.new()
    _camera.position_smoothing_enabled = true
    _camera.position_smoothing_speed = 5.0
    add_child(_camera)
    _camera.make_current()

func set_presentation_state(state: Dictionary) -> void:
    _state = state
    var width := float(_state.get("world_width",3600.0))
    if _camera:
        _camera.limit_left = 0
        _camera.limit_right = int(width)
        _camera.limit_top = 0
        _camera.limit_bottom = int(WORLD_HEIGHT)
    queue_redraw()

func _process(_delta: float) -> void:
    if _camera:
        _camera.position.x = lerpf(_camera.position.x,float(_state.get("observer_x",500.0)),0.12)

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
        world_clicked.emit(get_global_mouse_position())
        get_viewport().set_input_as_handled()
    elif event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_E:
            interact_requested.emit()
            get_viewport().set_input_as_handled()
        elif event.keycode == KEY_ESCAPE:
            close_requested.emit()
            get_viewport().set_input_as_handled()

func pick_target(position: Vector2) -> Dictionary:
    for portal in _portal_items:
        if absf(position.x-float(portal.get("x",0.0))) < float(portal.get("width",120.0))*0.5 and position.y > 260.0:
            return portal
    for item in _object_items:
        if position.distance_to(Vector2(float(item.get("x",0.0)),float(item.get("y",500.0)))) < 65.0:
            return item
    for actor in _npc_items:
        if position.distance_to(Vector2(float(actor.get("x",0.0)),float(actor.get("y",520.0)))) < 45.0:
            return actor
    return {}

func _draw() -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var scene_kind := str(room_manifest.get("scene_kind","outdoor"))
    var width := float(_state.get("world_width",3600.0))
    _npc_items.clear()
    _object_items.clear()
    _portal_items.clear()
    if scene_kind == "interior":
        _draw_interior(width,str(room_manifest.get("title","Interior")))
    else:
        _draw_outdoor(width)
    _draw_objects(room_manifest)
    _draw_portals(room_manifest)
    _draw_npcs()
    _draw_selection_prompt()
    _draw_observer()
    _draw_environment()
    _draw_inspection()
    _draw_connection_state()
    _draw_simulation_hud()

func _draw_outdoor(width: float) -> void:
    if _outdoor_background:
        draw_texture_rect(_outdoor_background, Rect2(0, 0, width, WORLD_HEIGHT), false)
        return
    var hour := int(_state.get("status",{}).get("hour",10))
    var sky := _sky_colour(hour)
    draw_rect(Rect2(0,0,width,WORLD_HEIGHT),sky)
    var sun_x := 280.0+float(hour)*125.0
    var sun_y := 115.0+absf(12.0-float(hour))*8.0
    var sun_colour := Color("#f4d79b") if hour >= 6 and hour < 19 else Color("#d9d9ce")
    draw_circle(Vector2(sun_x,sun_y),34.0,sun_colour)
    draw_set_transform(Vector2(_camera.position.x * 0.82 if _camera else 0.0,0))
    var ridge := PackedVector2Array([
        Vector2(0,390),Vector2(260,270),Vector2(520,350),Vector2(830,245),
        Vector2(1120,340),Vector2(1450,260),Vector2(1790,350),Vector2(2130,250),
        Vector2(2470,350),Vector2(2820,260),Vector2(3200,350),Vector2(width,300),
        Vector2(width,600),Vector2(0,600)
    ])
    draw_colored_polygon(ridge,Color("#82927d"))
    for tree_x in range(120,int(width),310):
        _draw_tree(float(tree_x),425.0,0.82)
    draw_set_transform(Vector2.ZERO)
    _draw_building(430.0,310.0,300.0,280.0,"TOWN HALL",Color("#d8c8a8"))
    _draw_building(1190.0,340.0,280.0,250.0,"GENERAL STORE",Color("#d6b98e"))
    _draw_building(2080.0,330.0,280.0,260.0,"BAKERY",Color("#d9c4a1"))
    _draw_building(3000.0,320.0,300.0,270.0,"THE TAVERN",Color("#b9b49c"))
    draw_rect(Rect2(0,560,width,160),Color("#a99b7b"))
    draw_rect(Rect2(0,590,width,130),Color("#8e846e"))
    draw_line(Vector2(0,590),Vector2(width,590),Color("#d3c5a5"),4.0)
    for stone_x in range(0,int(width),150):
        draw_line(Vector2(float(stone_x),620),Vector2(float(stone_x+95),620),Color("#a99d86"),2.0)
    draw_string(ThemeDB.fallback_font,Vector2(90,95),"OAKWOOD",HORIZONTAL_ALIGNMENT_LEFT,-1,18,Color("#f4eedf"))

func _draw_interior(width: float,title: String) -> void:
    draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#d5c8ad"))
    draw_rect(Rect2(0,0,width,515),Color("#d8cbb5"))
    draw_rect(Rect2(0,515,width,205),Color("#876f56"))
    draw_rect(Rect2(0,505,width,14),Color("#594c3e"))
    for x in range(90,int(width),300):
        draw_rect(Rect2(float(x),100,180,190),Color("#718779"))
        draw_rect(Rect2(float(x+12),112,156,166),Color("#b5c4ad"))
        draw_line(Vector2(float(x+90),112),Vector2(float(x+90),278),Color("#6a6856"),5.0)
    draw_rect(Rect2(0,0,width,80),Color("#5a5144"))
    draw_string(ThemeDB.fallback_font,Vector2(100,55),title.to_upper(),HORIZONTAL_ALIGNMENT_LEFT,-1,20,PAPER)
    for x in [380.0,1040.0,1680.0]:
        draw_rect(Rect2(x,420,240,28),Color("#604a38"))
        draw_rect(Rect2(x+20,448,18,110),Color("#604a38"))
        draw_rect(Rect2(x+200,448,18,110),Color("#604a38"))
    var room_id := str(_state.get("room_id",""))
    if room_id == "room_town_hall":
        draw_rect(Rect2(580,240,500,150),Color("#e6ddc8"))
        draw_rect(Rect2(610,260,440,110),Color("#9a805d"))
        draw_string(ThemeDB.fallback_font,Vector2(670,320),"CIVIC RECORDS",HORIZONTAL_ALIGNMENT_LEFT,-1,24,PAPER)
    elif room_id == "room_shop":
        for x in [420.0,780.0,1140.0]:
            draw_rect(Rect2(x,250,220,150),Color("#87694a"))
            for y in [280.0,335.0]:
                draw_rect(Rect2(x+12,y,196,8),Color("#d5bd91"))
                for j in range(4):
                    draw_circle(Vector2(x+35+j*48,y-14),12,Color("#b6a06f"))
    elif room_id == "room_bakery":
        draw_circle(Vector2(850,365),95,Color("#684a38"))
        draw_circle(Vector2(850,365),65,Color("#bd7950"))
        draw_circle(Vector2(850,365),35,Color("#e7c28d"))

func _draw_building(x: float,y: float,w: float,h: float,label: String,wall: Color) -> void:
    draw_rect(Rect2(x+10,y+12,w,h),Color("#574d40",0.25))
    draw_colored_polygon(PackedVector2Array([Vector2(x-25,y+10),Vector2(x+w*0.5,y-90),Vector2(x+w+25,y+10)]),Color("#6e5949"))
    draw_rect(Rect2(x,y,w,h),wall)
    draw_rect(Rect2(x+24,y+35,w-48,30),Color("#a28c6e"))
    draw_string(ThemeDB.fallback_font,Vector2(x+34,y+57),label,HORIZONTAL_ALIGNMENT_LEFT,-1,17,INK)
    for wx in [x+40,x+w-95]:
        draw_rect(Rect2(wx,y+100,55,70),Color("#64796f"))
        draw_rect(Rect2(wx+6,y+106,43,58),Color("#c6d0b4"))
        draw_line(Vector2(wx+27,y+106),Vector2(wx+27,y+164),INK,3.0)
    draw_rect(Rect2(x+w*0.5-34,y+h-105,68,105),Color("#614b3b"))
    draw_circle(Vector2(x+w*0.5+18,y+h-55),4,Color("#d7b46f"))

func _draw_tree(x: float,y: float,scale: float) -> void:
    draw_rect(Rect2(x-8*scale,y,16*scale,110*scale),Color("#705b43"))
    draw_circle(Vector2(x,y-35*scale),62*scale,Color("#617a61"))
    draw_circle(Vector2(x-28*scale,y-12*scale),42*scale,Color("#71866a"))
    draw_circle(Vector2(x+32*scale,y-10*scale),39*scale,Color("#536f59"))

func _draw_objects(room_manifest: Dictionary) -> void:
    var definitions: Array = room_manifest.get("objects",[])
    var actual_objects: Array = _state.get("objects",[])
    for definition in definitions:
        var object_id := str(definition.get("id",""))
        var actual := {}
        for item in actual_objects:
            if str(item.get("id","")) == object_id:
                actual = item
                break
        if actual.is_empty() and not bool(definition.get("presentation_only",false)):
            continue
        var x := float(definition.get("x",600.0))
        var y := 500.0
        var kind := str(definition.get("kind","inspect"))
        if kind == "noticeboard":
            draw_rect(Rect2(x-32,y-135,64,118),Color("#72533a"))
            draw_rect(Rect2(x-24,y-127,48,102),Color("#e8dfc7"))
            draw_line(Vector2(x-14,y-105),Vector2(x+14,y-105),RUST,3.0)
            draw_line(Vector2(x-14,y-85),Vector2(x+14,y-85),RUST,3.0)
            draw_rect(Rect2(x-7,y-18,14,55),Color("#70553c"))
        elif kind == "ledger":
            draw_rect(Rect2(x-65,y-80,130,75),Color("#70513a"))
            draw_rect(Rect2(x-32,y-113,64,48),Color("#e6ddc8"))
            draw_line(Vector2(x-20,y-98),Vector2(x+20,y-98),INK,2.0)
        elif kind == "clock":
            draw_circle(Vector2(x,y-70),38,Color("#e7dec8"))
            draw_circle(Vector2(x,y-70),31,Color("#6c5a43"),false,3.0)
            draw_line(Vector2(x,y-70),Vector2(x,y-91),INK,3.0)
            draw_line(Vector2(x,y-70),Vector2(x+18,y-58),INK,3.0)
            draw_rect(Rect2(x-6,y-18,12,50),Color("#70553c"))
        elif kind == "shop":
            draw_rect(Rect2(x-75,y-80,150,65),Color("#785b42"))
            draw_rect(Rect2(x-65,y-70,130,14),Color("#d4b98d"))
        else:
            draw_rect(Rect2(x-55,y-65,110,50),Color("#886e51"))
            draw_rect(Rect2(x-42,y-55,84,30),Color("#c5a47a"))
        _object_items.append({"kind":"object","interaction":kind,"id":object_id,"label":str(definition.get("label",actual.get("name",object_id))),"x":x,"y":y-60.0})
        draw_string(ThemeDB.fallback_font,Vector2(x-90,y+55),str(definition.get("label","")),HORIZONTAL_ALIGNMENT_LEFT,180,13,INK)

func _draw_portals(room_manifest: Dictionary) -> void:
    for portal in room_manifest.get("portals",[]):
        var x := float(portal.get("x",100.0))
        var width := float(portal.get("width",180.0))
        var door_x := float(portal.get("door_x",x+width*0.5))
        draw_rect(Rect2(door_x-35,465,70,125),Color("#5b4939"))
        draw_rect(Rect2(door_x-27,473,54,117),Color("#927253"))
        draw_string(ThemeDB.fallback_font,Vector2(x,445),str(portal.get("label","Exit")),HORIZONTAL_ALIGNMENT_LEFT,width,15,INK)
        _portal_items.append({"kind":"portal","id":str(portal.get("id","")),"label":str(portal.get("label","Exit")),"target_room_id":str(portal.get("target_room_id","")),"x":door_x,"width":width})

func _draw_npcs() -> void:
    var npcs: Array = _state.get("npcs",[])
    var room_id := str(_state.get("room_id",""))
    var visible_index := 0
    for npc in npcs:
        if str(npc.get("location_id","")) != room_id or not bool(npc.get("is_alive",true)):
            continue
        var x := 360.0+float(visible_index)*72.0
        var y := 550.0+float((visible_index%3)*4)
        var colour_index := abs(str(npc.get("id","")).hash())%5
        var palette := [Color("#627b70"),Color("#a36d50"),Color("#65748a"),Color("#b39a70"),Color("#7b6c83")]
        _draw_character(x,y,palette[colour_index],false)
        if visible_index < 8 or absf(x-float(_state.get("observer_x",500.0))) < 240.0:
            draw_string(ThemeDB.fallback_font,Vector2(x-48,y-55),str(npc.get("name","Citizen")),HORIZONTAL_ALIGNMENT_CENTER,96,12,INK)
        _npc_items.append({"kind":"npc","id":str(npc.get("id","")),"label":str(npc.get("name","Citizen")),"x":x,"y":y-8.0})
        visible_index += 1

func _draw_character(x: float,y: float,clothes: Color,observer: bool) -> void:
    _draw_ellipse(Vector2(x,y+2),Vector2(19,6),Color("#403a32",0.22))
    draw_rect(Rect2(x-12,y-34,9,32),Color("#5a4b40"))
    draw_rect(Rect2(x+3,y-34,9,32),Color("#5a4b40"))
    draw_colored_polygon(PackedVector2Array([Vector2(x-19,y-76),Vector2(x+19,y-76),Vector2(x+15,y-30),Vector2(x-15,y-30)]),clothes)
    draw_circle(Vector2(x,y-91),19,Color("#d9b28c"))
    draw_arc(Vector2(x,y-93),19,PI,TAU,24,Color("#574538"),5.0)
    if observer:
        draw_circle(Vector2(x,y-118),5,Color("#f2d99d"))

func _draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var angle := TAU*float(i)/20.0
        points.append(center+Vector2(cos(angle)*radius.x,sin(angle)*radius.y))
    draw_colored_polygon(points,colour)

func _draw_selection_prompt() -> void:
    var selected: Dictionary = _state.get("selected",{})
    if selected.is_empty():
        return
    var x := float(selected.get("x",_state.get("observer_x",500.0)))
    var y := float(selected.get("y",500.0))-92.0
    var prompt := "E  ·  ENTER" if selected.get("kind") == "portal" else ("E  ·  INSPECT" if selected.get("kind") == "object" else "E  ·  MEET")
    draw_rect(Rect2(x-72,y-25,144,32),Color("#283a38",0.9))
    draw_string(ThemeDB.fallback_font,Vector2(x-61,y-4),prompt,HORIZONTAL_ALIGNMENT_LEFT,122,12,PAPER)

func _draw_observer() -> void:
    _draw_character(float(_state.get("observer_x",500.0)),585.0,Color("#d1b17d"),true)

func _draw_environment() -> void:
    var climate: Dictionary = _state.get("climate",{})
    var precipitation := str(climate.get("precipitation","CLEAR")).to_upper()
    var hour := int(_state.get("status",{}).get("hour",10))
    if precipitation in ["CLOUDY","OVERCAST"]:
        var cloud_tint := Color("#63727a",0.12) if precipitation == "CLOUDY" else Color("#4f5c65",0.22)
        draw_rect(Rect2(0,0,3600,WORLD_HEIGHT),cloud_tint)
        for cloud_x in range(220,3600,620):
            _draw_ellipse(Vector2(float(cloud_x),135.0),Vector2(95.0,25.0),Color("#e0e0d4",0.18))
    if precipitation in ["RAIN","SLEET","SNOW","BLIZZARD"]:
        for i in range(90):
            var x := float((i*137+int(Time.get_ticks_msec()/25))%3600)
            var y := float((i*71+int(Time.get_ticks_msec()/13))%560)
            var colour := Color("#dbe3e0",0.55) if precipitation == "SNOW" else Color("#c5d4d5",0.42)
            draw_line(Vector2(x,y),Vector2(x-7,y+18),colour,1.5)
    if hour >= 19 or hour < 6:
        draw_rect(Rect2(0,0,3600,WORLD_HEIGHT),Color("#18283a",0.34))

func _sky_colour(hour: int) -> Color:
    if hour < 5 or hour >= 21:
        return Color("#27374b")
    if hour < 8:
        return Color("#c58e78")
    if hour < 17:
        return Color("#a9c1bd")
    if hour < 20:
        return Color("#cf9877")
    return Color("#48566a")

func _draw_inspection() -> void:
    var inspection: Dictionary = _state.get("inspection",{})
    if inspection.is_empty():
        return
    var camera_x := _camera.position.x if _camera else 640.0
    var panel := Rect2(camera_x-390,110,780,430)
    draw_rect(panel,Color("#403a32",0.22))
    draw_rect(Rect2(panel.position+Vector2(0,-5),panel.size),PAPER)
    draw_rect(Rect2(panel.position+Vector2(18,18),panel.size-Vector2(36,36)),Color("#d5c9b1"),false,2.0)
    draw_string(ThemeDB.fallback_font,panel.position+Vector2(42,58),str(inspection.get("title","Inspection")),HORIZONTAL_ALIGNMENT_LEFT,680,27,INK)
    draw_string(ThemeDB.fallback_font,panel.position+Vector2(42,88),str(inspection.get("kind","Record")).to_upper(),HORIZONTAL_ALIGNMENT_LEFT,680,12,RUST)
    var lines: Array = inspection.get("lines",[])
    if lines.is_empty() and inspection.has("data"):
        var data: Dictionary = inspection.get("data",{})
        lines = ["Occupation: %s" % data.get("occupation","—"),"Home: %s" % data.get("home_location_id","—"),"Work: %s" % data.get("work_location_id","—"),"Wealth: %s gold" % data.get("wealth_gold","—")]
    var line_y := panel.position.y+135
    for line in lines.slice(0,12):
        draw_string(ThemeDB.fallback_font,Vector2(panel.position.x+44,line_y),str(line),HORIZONTAL_ALIGNMENT_LEFT,680,16,INK)
        line_y += 25
    draw_string(ThemeDB.fallback_font,Vector2(panel.position.x+44,panel.end.y-28),"E / ESC  ·  CLOSE",HORIZONTAL_ALIGNMENT_LEFT,300,12,RUST)

func _draw_connection_state() -> void:
    if not bool(_state.get("connected",false)):
        var camera_x := _camera.position.x if _camera else 640.0
        draw_rect(Rect2(camera_x-180,24,360,42),Color("#282e2b",0.78))
        var error := str(_state.get("error",""))
        draw_string(ThemeDB.fallback_font,Vector2(camera_x-160,51),error if not error.is_empty() else "CONNECTING TO SIMULATION…",HORIZONTAL_ALIGNMENT_LEFT,320,13,PAPER)

func _draw_simulation_hud() -> void:
    var status: Dictionary = _state.get("status", {})
    if status.is_empty():
        return
    var camera_x := _camera.position.x if _camera else 640.0
    var lifecycle := str(status.get("lifecycle_state", "STARTING"))
    var tick := int(status.get("tick", 0))
    var day := int(status.get("day", 1))
    var hour := int(status.get("hour", 0))
    var population: Dictionary = _state.get("population", {})
    var clock_text := "%02d:%02d" % [hour, int(tick % 60)]
    draw_rect(Rect2(camera_x - 610, 24, 210, 54), Color("#f0e5ce", 0.92))
    draw_rect(Rect2(camera_x - 610, 24, 210, 54), Color("#76634b"), false, 2.0)
    draw_string(ThemeDB.fallback_font, Vector2(camera_x - 594, 46), "OAKWOOD  ·  DAY %d" % day, HORIZONTAL_ALIGNMENT_LEFT, 190, 12, INK)
    draw_string(ThemeDB.fallback_font, Vector2(camera_x - 594, 65), "%s   /   TICK %d" % [clock_text, tick], HORIZONTAL_ALIGNMENT_LEFT, 190, 14, INK)
    var state_colour := Color("#52785a") if lifecycle == "RUNNING" else Color("#a36d50")
    draw_circle(Vector2(camera_x + 580, 48), 5, state_colour)
    draw_string(ThemeDB.fallback_font, Vector2(camera_x + 594, 53), lifecycle, HORIZONTAL_ALIGNMENT_LEFT, 100, 12, INK)
