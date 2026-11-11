extends Node2D

signal world_clicked(world_position: Vector2)
signal interact_requested
signal close_requested

const WORLD_HEIGHT := 720.0
const PAPER := Color("#fff3d2")
const INK := Color("#5b3a2e")
const RUST := Color("#e6694b")
const StorybookStyle = preload("res://scripts/style/storybook_style.gd")
const ATMOSPHERE_SCRIPT = preload("res://scripts/world/world_atmosphere.gd")
const PAPER_SHADER = preload("res://shaders/storybook_paper.gdshader")
const CHARACTER_VISUAL_SCRIPT = preload("res://scripts/characters/character_visual.gd")
const BUILDING_SCRIPT = preload("res://scripts/world/world_building.gd")
const FURNITURE_SCRIPT = preload("res://scripts/world/world_furniture.gd")
const INTERACTABLE_SCRIPT = preload("res://scripts/world/world_interactable.gd")
const LIGHTING_SCRIPT = preload("res://scripts/world/world_lighting.gd")
const PROP_SCRIPT = preload("res://scripts/world/world_prop.gd")
const TERRAIN_SCRIPT = preload("res://scripts/world/world_terrain.gd")
const FOREGROUND_SCRIPT = preload("res://scripts/world/world_foreground.gd")
const HUD_SCRIPT = preload("res://scripts/ui/world_hud.gd")

var _state: Dictionary = {}
var _camera: Camera2D
var _npc_items: Array[Dictionary] = []
var _object_items: Array[Dictionary] = []
var _portal_items: Array[Dictionary] = []
var _building_nodes: Dictionary = {}
var _furniture_nodes: Dictionary = {}
var _interactable_nodes: Dictionary = {}
var _prop_nodes: Dictionary = {}
var _lighting: Node2D
var _character_nodes: Dictionary = {}
var _observer_visual: Node2D
var _last_observer_x := 500.0
var _camera_lead := 0.0
var _camera_initialized := false
var _camera_snap_pending := false
var _last_room_id := ""
var _transition_layer: CanvasLayer
var _transition_cover: ColorRect
var _transition_tween: Tween
var _camera_zoom_target := 1.0
var _hovered: Dictionary = {}
var _hover_signature := ""
var _foreground: Node2D
var _terrain: Node2D
var _hud: CanvasLayer
var _atmosphere: Node2D
var _post_layer: CanvasLayer

func _ready() -> void:
    # Sort independent world nodes by their ground contact point so trees,
    # buildings and people can overlap naturally as the camera moves.
    y_sort_enabled = true
    _camera = Camera2D.new()
    # Follow smoothing is handled by the custom dead-zone/look-ahead camera rig.
    _camera.position_smoothing_enabled = false
    add_child(_camera)
    _camera.make_current()
    _transition_layer = CanvasLayer.new()
    _transition_layer.layer = 100
    add_child(_transition_layer)
    _transition_cover = ColorRect.new()
    _transition_cover.color = Color(0.0,0.0,0.0,0.0)
    _transition_cover.visible = false
    _transition_cover.mouse_filter = Control.MOUSE_FILTER_STOP
    _transition_cover.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    _transition_layer.add_child(_transition_cover)
    _terrain = Node2D.new()
    _terrain.set_script(TERRAIN_SCRIPT)
    add_child(_terrain)
    _lighting = Node2D.new()
    _lighting.set_script(LIGHTING_SCRIPT)
    add_child(_lighting)
    _observer_visual = Node2D.new()
    _observer_visual.set_script(CHARACTER_VISUAL_SCRIPT)
    add_child(_observer_visual)
    _observer_visual.call("configure", {"id":"observer","name":"Observer"}, true)
    _foreground = Node2D.new()
    _foreground.set_script(FOREGROUND_SCRIPT)
    add_child(_foreground)
    _atmosphere = Node2D.new()
    _atmosphere.set_script(ATMOSPHERE_SCRIPT)
    add_child(_atmosphere)
    _hud = CanvasLayer.new()
    _hud.set_script(HUD_SCRIPT)
    add_child(_hud)
    # Whole-screen painted-paper finish. It sits above the world (layer 0) but
    # below the HUD (layer 20) and the room-transition fade (layer 100), and it
    # must never swallow mouse input.
    _post_layer = CanvasLayer.new()
    _post_layer.layer = 10
    add_child(_post_layer)
    var paper := ColorRect.new()
    paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
    paper.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var paper_material := ShaderMaterial.new()
    paper_material.shader = PAPER_SHADER
    paper.material = paper_material
    _post_layer.add_child(paper)

func set_presentation_state(state: Dictionary) -> void:
    var incoming_room_id := str(state.get("room_id",""))
    if not _last_room_id.is_empty() and incoming_room_id != _last_room_id:
        _camera_snap_pending = true
        _camera_lead = 0.0
    _last_room_id = incoming_room_id
    if not _camera_initialized:
        _last_observer_x = float(state.get("observer_x",500.0))
    _state = state
    if _hud:
        _hud.call("configure",_state)
    if _foreground:
        _foreground.call("configure",float(_state.get("world_width",3600.0)))
    if _terrain:
        _terrain.call("configure",_state.get("room_manifest",{}),float(_state.get("world_width",3600.0)))
    _sync_character_nodes()
    _sync_building_nodes()
    _sync_furniture_nodes()
    _sync_interactable_nodes()
    _sync_prop_nodes()
    if _lighting:
        _lighting.call("configure",_state)
    if _atmosphere:
        _atmosphere.call("configure",_state)
    var width := float(_state.get("world_width",3600.0))
    if _camera:
        _camera.limit_left = 0
        _camera.limit_right = int(width)
        _camera.limit_top = 0
        _camera.limit_bottom = int(WORLD_HEIGHT)
    queue_redraw()

func _process(delta: float) -> void:
    var observer_x := float(_state.get("observer_x",500.0))
    if _camera:
        _update_camera_follow(observer_x,delta)
    if _observer_visual:
        _observer_visual.position = Vector2(observer_x,float(_state.get("observer_y",585.0)))
    var mouse_target := pick_target(get_global_mouse_position())
    var hover_signature := ""
    if not mouse_target.is_empty():
        hover_signature = "%s:%s" % [str(mouse_target.get("kind","")),str(mouse_target.get("id",""))]
    if hover_signature != _hover_signature:
        _hover_signature = hover_signature
        _hovered = mouse_target
        queue_redraw()
    if _camera:
        var zoom_weight := 1.0-exp(-3.0*delta)
        _camera.zoom = _camera.zoom.lerp(Vector2.ONE * _camera_zoom_target,zoom_weight)
    _last_observer_x = observer_x

func set_observer_motion(moving: bool, direction: Vector2 = Vector2.ZERO) -> void:
    if _observer_visual:
        _observer_visual.call("set_motion",moving,direction)

func begin_room_transition() -> void:
    if is_instance_valid(_transition_tween) and _transition_tween.is_running():
        _transition_tween.kill()
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var camera_config: Dictionary = room_manifest.get("camera",{})
    var duration := maxf(float(camera_config.get("transition_out_seconds",0.28)),0.05)
    _transition_cover.visible = true
    _transition_tween = create_tween()
    _transition_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    _transition_tween.tween_property(_transition_cover,"color",Color(0.035,0.045,0.04,0.97),duration)
    await _transition_tween.finished

func complete_room_transition() -> void:
    if is_instance_valid(_transition_tween) and _transition_tween.is_running():
        _transition_tween.kill()
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var camera_config: Dictionary = room_manifest.get("camera",{})
    var duration := maxf(float(camera_config.get("transition_in_seconds",0.42)),0.05)
    _transition_tween = create_tween()
    _transition_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    _transition_tween.tween_property(_transition_cover,"color",Color(0.035,0.045,0.04,0.0),duration)
    _transition_tween.tween_callback(func() -> void: _transition_cover.visible = false)

func _update_camera_follow(observer_x: float, delta: float) -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var camera_config: Dictionary = room_manifest.get("camera",{})
    _camera_zoom_target = maxf(float(camera_config.get("zoom",1.0)),0.5)
    var selected: Dictionary = _state.get("selected",{})
    if str(selected.get("kind","")) == "portal":
        _camera_zoom_target = maxf(_camera_zoom_target,float(camera_config.get("portal_focus_zoom",1.07)))
    var viewport_width := get_viewport_rect().size.x / maxf(_camera.zoom.x,0.001)
    var anchor_ratio := clampf(float(camera_config.get("screen_anchor",0.42)),0.30,0.50)
    var follow_speed := maxf(float(camera_config.get("follow_speed",3.8)),0.1)
    var lead_distance := maxf(float(camera_config.get("look_ahead_distance",125.0)),0.0)
    var lead_response := maxf(float(camera_config.get("look_ahead_response",2.8)),0.1)
    var dead_zone_left := clampf(float(camera_config.get("dead_zone_left",0.34)),0.1,0.48)
    var dead_zone_right := clampf(float(camera_config.get("dead_zone_right",0.59)),0.52,0.9)
    var movement_speed := (observer_x-_last_observer_x) / maxf(delta,0.0001)
    var movement_strength := clampf(absf(movement_speed)/260.0,0.0,1.0)
    var desired_lead := signf(movement_speed)*lead_distance*movement_strength
    var lead_weight := 1.0-exp(-lead_response*delta)
    _camera_lead = lerpf(_camera_lead,desired_lead,lead_weight)

    var screen_x := observer_x-_camera.position.x+viewport_width*0.5
    var outside_dead_zone := screen_x < viewport_width*dead_zone_left or screen_x > viewport_width*dead_zone_right
    var anchor_offset := viewport_width*(0.5-anchor_ratio)
    var desired_x := observer_x+anchor_offset+_camera_lead
    if not outside_dead_zone and absf(_camera_lead) < 8.0 and not _camera_snap_pending:
        desired_x = _camera.position.x

    var world_width := float(_state.get("world_width",3600.0))
    var half_view := viewport_width*0.5
    desired_x = clampf(desired_x,half_view,maxf(half_view,world_width-half_view))
    if not _camera_initialized or _camera_snap_pending:
        _camera.position.x = desired_x
        _camera_initialized = true
        _camera_snap_pending = false
    else:
        var follow_weight := 1.0-exp(-follow_speed*delta)
        _camera.position.x = lerpf(_camera.position.x,desired_x,follow_weight)

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
        if position.distance_to(Vector2(float(item.get("x",0.0)),float(item.get("y",500.0)))) < float(item.get("interaction_radius",65.0)):
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
    if scene_kind != "interior":
        _draw_outdoor(width)
    _draw_objects(room_manifest)
    _draw_portals(room_manifest)
    _draw_npcs()
    _draw_hover_feedback()

func _draw_ridge(ridge: PackedVector2Array,fill: Color,line_colour: Color,line_width: float,seed_value: int,parallax: float) -> void:
    # One layer of distant hills: filled below, with a hand-drawn crayon ridge line.
    var camera_x := _camera.position.x if _camera else 0.0
    draw_set_transform(Vector2(camera_x*parallax,0))
    var body := PackedVector2Array(ridge)
    body.append(Vector2(ridge[ridge.size()-1].x,620))
    body.append(Vector2(ridge[0].x,620))
    draw_colored_polygon(body,fill)
    draw_polyline(StorybookStyle.wobble(ridge,seed_value,2.2,false,44.0),line_colour,line_width,true)
    draw_set_transform(Vector2.ZERO)

func _draw_outdoor(width: float) -> void:
    # The environment is a renderable stage, not a pre-painted village image.
    # Buildings and movable scenery are separate nodes sourced from the manifest.
    var hour := int(_state.get("status",{}).get("hour",10))
    var sky_colours := StorybookStyle.sky_colors(hour)
    draw_rect(Rect2(0,440,width,WORLD_HEIGHT-440),sky_colours[1])
    draw_polygon(PackedVector2Array([
        Vector2(0,0),Vector2(width,0),Vector2(width,440),Vector2(0,440)
    ]),PackedColorArray([sky_colours[0],sky_colours[0],sky_colours[1],sky_colours[1]]))

    # A round, friendly sun by day and a pale moon by night.
    var sun_x := 280.0+float(hour)*125.0
    var sun_y := 115.0+absf(12.0-float(hour))*8.0
    if hour >= 6 and hour < 19:
        var centre := Vector2(sun_x,sun_y)
        draw_circle(centre,82.0,Color(StorybookStyle.SUN,0.14))
        draw_circle(centre,60.0,Color(StorybookStyle.SUN,0.2))
        for ray in range(12):
            var angle := TAU*float(ray)/12.0
            var direction := Vector2(cos(angle),sin(angle))
            StorybookStyle.crayon_line(self,centre+direction*50.0,centre+direction*(64.0+float(ray%2)*12.0),Color("#ffb52e"),4.5,ray)
        StorybookStyle.outlined_circle(self,centre,40.0,StorybookStyle.SUN,Color("#e8902a"),4.0,7,1.0)
        StorybookStyle.dab(self,centre+Vector2(-12,-12),Vector2(13,9),Color("#fff6b8",0.8))
    else:
        var moon := Vector2(sun_x,sun_y)
        draw_circle(moon,56.0,Color("#fff3b0",0.14))
        StorybookStyle.outlined_circle(self,moon,32.0,Color("#fff6c9"),Color("#c9b878"),3.4,9,0.9)
        draw_circle(moon+Vector2(-9,-6),6.0,Color("#eadf9f"))
        draw_circle(moon+Vector2(10,9),4.0,Color("#eadf9f"))

    # Two layers of rolling hills; the far one is paler and moves more slowly.
    var far_ridge := PackedVector2Array([
        Vector2(-400,360),Vector2(300,290),Vector2(700,340),Vector2(1150,270),
        Vector2(1600,330),Vector2(2050,262),Vector2(2500,332),Vector2(2950,280),
        Vector2(3400,336),Vector2(width+400,300)
    ])
    _draw_ridge(far_ridge,Color("#9bdcb8"),Color("#5f9a86",0.8),3.0,21,0.1)
    var near_ridge := PackedVector2Array([
        Vector2(-200,390),Vector2(260,270),Vector2(520,350),Vector2(830,245),
        Vector2(1120,340),Vector2(1450,260),Vector2(1790,350),Vector2(2130,250),
        Vector2(2470,350),Vector2(2820,260),Vector2(3200,350),Vector2(width+200,300)
    ])
    _draw_ridge(near_ridge,Color("#6fcf7a"),StorybookStyle.OUTLINE,4.0,33,0.18)

    var title_pos := Vector2(90,95)
    draw_string_outline(ThemeDB.fallback_font,title_pos,"OAKWOOD",HORIZONTAL_ALIGNMENT_LEFT,-1,24,8,StorybookStyle.OUTLINE)
    draw_string(ThemeDB.fallback_font,title_pos,"OAKWOOD",HORIZONTAL_ALIGNMENT_LEFT,-1,24,Color("#fff3d2"))

func _sync_building_nodes() -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var definitions: Array = room_manifest.get("buildings",[])
    var visible_ids: Dictionary = {}
    for definition in definitions:
        var building_id := str(definition.get("id",""))
        if building_id.is_empty():
            continue
        visible_ids[building_id] = true
        var building: Node2D
        if _building_nodes.has(building_id):
            building = _building_nodes[building_id]
        else:
            building = Node2D.new()
            building.set_script(BUILDING_SCRIPT)
            add_child(building)
            _building_nodes[building_id] = building
        building.call("configure",definition,room_manifest.get("interior",{}))
    for existing_id in _building_nodes.keys():
        if not visible_ids.has(existing_id):
            var old_building: Node2D = _building_nodes[existing_id]
            old_building.queue_free()
            _building_nodes.erase(existing_id)

func _sync_furniture_nodes() -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var definitions: Array = room_manifest.get("furniture",[])
    var visible_ids: Dictionary = {}
    for definition in definitions:
        var furniture_id := str(definition.get("id",""))
        if furniture_id.is_empty(): continue
        visible_ids[furniture_id] = true
        var item: Node2D
        if _furniture_nodes.has(furniture_id):
            item = _furniture_nodes[furniture_id]
        else:
            item = Node2D.new()
            item.set_script(FURNITURE_SCRIPT)
            add_child(item)
            _furniture_nodes[furniture_id] = item
        item.call("configure",definition)
    for existing_id in _furniture_nodes.keys():
        if not visible_ids.has(existing_id):
            var old_item: Node2D = _furniture_nodes[existing_id]
            old_item.queue_free()
            _furniture_nodes.erase(existing_id)

func _sync_prop_nodes() -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var definitions: Array = room_manifest.get("scenery",[])
    var visible_ids: Dictionary = {}
    for definition in definitions:
        var prop_id := str(definition.get("id",""))
        if prop_id.is_empty():
            continue
        visible_ids[prop_id] = true
        var prop: Node2D
        if _prop_nodes.has(prop_id):
            prop = _prop_nodes[prop_id]
        else:
            prop = Node2D.new()
            prop.set_script(PROP_SCRIPT)
            add_child(prop)
            _prop_nodes[prop_id] = prop
        prop.call("configure",definition)
    for existing_id in _prop_nodes.keys():
        if not visible_ids.has(existing_id):
            var old_prop: Node2D = _prop_nodes[existing_id]
            old_prop.queue_free()
            _prop_nodes.erase(existing_id)

func _sync_interactable_nodes() -> void:
    var room_manifest: Dictionary = _state.get("room_manifest",{})
    var definitions: Array = room_manifest.get("objects",[])
    var actual_objects: Array = _state.get("objects",[])
    var status: Dictionary = _state.get("status",{})
    var visible_ids: Dictionary = {}
    for definition in definitions:
        var object_id := str(definition.get("id",""))
        if object_id.is_empty():
            continue
        var actual: Dictionary = {}
        for candidate in actual_objects:
            if str(candidate.get("id","")) == object_id:
                actual = candidate
                break
        if actual.is_empty() and not bool(definition.get("presentation_only",false)):
            continue
        visible_ids[object_id] = true
        var visual: Node2D
        if _interactable_nodes.has(object_id):
            visual = _interactable_nodes[object_id]
        else:
            visual = Node2D.new()
            visual.set_script(INTERACTABLE_SCRIPT)
            add_child(visual)
            _interactable_nodes[object_id] = visual
        visual.call("configure",definition,actual,status)
    for existing_id in _interactable_nodes.keys():
        if not visible_ids.has(existing_id):
            var old_visual: Node2D = _interactable_nodes[existing_id]
            old_visual.queue_free()
            _interactable_nodes.erase(existing_id)

func _draw_objects(room_manifest: Dictionary) -> void:
    var definitions: Array = room_manifest.get("objects",[])
    var actual_objects: Array = _state.get("objects",[])
    for definition in definitions:
        var object_id := str(definition.get("id",""))
        var actual: Dictionary = {}
        for candidate in actual_objects:
            if str(candidate.get("id","")) == object_id:
                actual = candidate
                break
        if actual.is_empty() and not bool(definition.get("presentation_only",false)):
            continue
        var x := float(definition.get("x",600.0))
        var y := 500.0
        var kind := str(definition.get("kind","inspect"))
        var label := str(definition.get("label",actual.get("name",object_id)))
        _object_items.append({
            "kind":"object",
            "interaction":kind,
            "id":object_id,
            "label":label,
            "x":x,
            "y":y-60.0,
            "interaction_radius":float(definition.get("interaction_radius",72.0))
        })

func _draw_portals(room_manifest: Dictionary) -> void:
    for portal in room_manifest.get("portals",[]):
        var x := float(portal.get("x",100.0))
        var width := float(portal.get("width",180.0))
        var door_x := float(portal.get("door_x",x+width*0.5))
        var door_seed := absi(str(portal.get("id","")).hash())%1000
        StorybookStyle.blob_shadow(self,Vector2(door_x,592),52.0,0.2,0.22)
        StorybookStyle.outlined_rounded_rect(self,Rect2(door_x-37,463,74,129),30.0,StorybookStyle.WOOD_DEEP,INK,4.0,door_seed,1.0)
        StorybookStyle.outlined_rounded_rect(self,Rect2(door_x-28,472,56,120),24.0,StorybookStyle.WOOD,INK,2.6,door_seed+1,0.8)
        StorybookStyle.crayon_line(self,Vector2(door_x,484),Vector2(door_x,588),StorybookStyle.WOOD_DEEP,2.4,door_seed)
        StorybookStyle.outlined_circle(self,Vector2(door_x+17,533),4.4,StorybookStyle.BLOOM_YELLOW,INK,1.8,door_seed+2,0.2)
        var portal_label := str(portal.get("label","Exit"))
        var tag_width := clampf(float(portal_label.length())*8.4+26.0,90.0,width)
        var tag := Rect2(door_x-tag_width*0.5,424,tag_width,26)
        StorybookStyle.outlined_rounded_rect(self,tag,9.0,StorybookStyle.CREAM,INK,3.0,door_seed+3,0.6)
        draw_string(ThemeDB.fallback_font,Vector2(tag.position.x,tag.position.y+18),portal_label,HORIZONTAL_ALIGNMENT_CENTER,tag_width,14,INK)
        _portal_items.append({"kind":"portal","id":str(portal.get("id","")),"label":str(portal.get("label","Exit")),"target_room_id":str(portal.get("target_room_id","")),"x":door_x,"width":width})

func _sync_character_nodes() -> void:
    # NPC identity and simulation state remain authoritative in Python.
    # Godot only assembles a persistent visual rig from each NPC's stable ID.
    var visible_ids: Dictionary = {}
    var npcs: Array = _state.get("npcs",[])
    for npc in npcs:
        if str(npc.get("location_id","")) != str(_state.get("room_id","")):
            continue
        if not bool(npc.get("is_alive",true)):
            continue
        var npc_id := str(npc.get("id",""))
        if npc_id.is_empty():
            continue
        visible_ids[npc_id] = true
        if not _character_nodes.has(npc_id):
            var actor := Node2D.new()
            actor.set_script(CHARACTER_VISUAL_SCRIPT)
            add_child(actor)
            actor.call("configure",npc,false)
            _character_nodes[npc_id] = actor
    for existing_id in _character_nodes.keys():
        if not visible_ids.has(existing_id):
            var old_actor: Node2D = _character_nodes[existing_id]
            old_actor.queue_free()
            _character_nodes.erase(existing_id)

func _draw_npcs() -> void:
    var npcs: Array = _state.get("npcs",[])
    var room_id := str(_state.get("room_id",""))
    var visible_index := 0
    for npc in npcs:
        if str(npc.get("location_id","")) != room_id or not bool(npc.get("is_alive",true)):
            continue
        var npc_id := str(npc.get("id",""))
        if not _character_nodes.has(npc_id):
            continue
        # Stable slots prevent NPCs from drifting decoratively between snapshots.
        # Actual movement will be driven by authoritative activity/navigation data.
        var slot := visible_index % 32
        var row := int(visible_index / 32)
        var x := 360.0 + float(slot) * 82.0
        var y := 540.0 + float(row) * 58.0 + float((slot % 3) * 12)
        var actor: Node2D = _character_nodes[npc_id]
        actor.position = Vector2(x,y)
        actor.call("set_motion",false)
        if visible_index < 8 or absf(x-float(_state.get("observer_x",500.0))) < 240.0:
            var npc_name := str(npc.get("name","Citizen"))
            var name_width := clampf(float(npc_name.length())*7.4+20.0,64.0,140.0)
            var name_tag := Rect2(x-name_width*0.5,y-168,name_width,22)
            StorybookStyle.outlined_rounded_rect(self,name_tag,8.0,Color(StorybookStyle.CREAM,0.96),INK,2.4,visible_index,0.5)
            draw_string(ThemeDB.fallback_font,Vector2(name_tag.position.x,name_tag.position.y+16),npc_name,HORIZONTAL_ALIGNMENT_CENTER,name_width,12,INK)
        _npc_items.append({"kind":"npc","id":npc_id,"label":str(npc.get("name","Citizen")),"x":x,"y":y-8.0})
        visible_index += 1

func _draw_hover_feedback() -> void:
    var target: Dictionary = _hovered
    if target.is_empty():
        target = _state.get("selected",{})
    if target.is_empty():
        return
    var x := float(target.get("x",_state.get("observer_x",500.0)))
    var y := float(target.get("y",550.0))
    if str(target.get("kind","")) == "portal":
        y = 585.0
    var bounce := sin(float(Time.get_ticks_msec())/180.0)*2.0
    draw_arc(Vector2(x,y+8.0),32.0+bounce,0.0,TAU,32,INK,6.0,true)
    draw_arc(Vector2(x,y+8.0),32.0+bounce,0.0,TAU,32,StorybookStyle.SUN,3.2,true)
    var label := str(target.get("label",""))
    if not label.is_empty():
        var label_width := clampf(float(label.length())*8.4+30.0,100.0,260.0)
        var label_rect := Rect2(x-label_width*0.5,y-52.0,label_width,29.0)
        StorybookStyle.outlined_rounded_rect(self,label_rect,10.0,StorybookStyle.CREAM,INK,3.2,label.length(),0.6)
        draw_string(ThemeDB.fallback_font,Vector2(label_rect.position.x+10.0,label_rect.position.y+20.0),label,HORIZONTAL_ALIGNMENT_CENTER,label_width-20.0,13,INK)

func _draw_selection_prompt() -> void:
    var selected: Dictionary = _state.get("selected",{})
    if selected.is_empty():
        return
    var x := float(selected.get("x",_state.get("observer_x",500.0)))
    var y := float(selected.get("y",500.0))-112.0
    var prompt := "E  ·  GO INSIDE" if selected.get("kind") == "portal" else ("E  ·  TAKE A LOOK" if selected.get("kind") == "object" else "E  ·  SAY HELLO")
    # A little floating paper speech tag instead of a generic game button.
    draw_colored_polygon(PackedVector2Array([
        Vector2(x-75,y-30),Vector2(x+75,y-30),Vector2(x+75,y+5),
        Vector2(x+10,y+5),Vector2(x,y+17),Vector2(x-8,y+5),Vector2(x-75,y+5)
    ]),Color("#fff4dc"))
    draw_polyline(PackedVector2Array([
        Vector2(x-75,y-30),Vector2(x+75,y-30),Vector2(x+75,y+5),
        Vector2(x+10,y+5),Vector2(x,y+17),Vector2(x-8,y+5),Vector2(x-75,y+5),
        Vector2(x-75,y-30)
    ]),Color("#6e5743"),2.0)
    draw_string(ThemeDB.fallback_font,Vector2(x-65,y-7),prompt,HORIZONTAL_ALIGNMENT_CENTER,130,12,INK)

func _draw_inspection() -> void:
    var inspection: Dictionary = _state.get("inspection",{})
    if inspection.is_empty():
        return
    var camera_x := _camera.position.x if _camera else 640.0
    var panel := Rect2(camera_x-390,104,780,452)
    # Pinned journal page with a folded corner, ink outline and paper grain.
    draw_rect(Rect2(panel.position+Vector2(8,10),panel.size),Color("#443c34",0.24))
    draw_rect(panel,Color("#f5ecd7"))
    draw_rect(panel.grow(-9),Color("#fff8e8"),false,2.0)
    draw_rect(Rect2(panel.position.x+20,panel.position.y+18,7,panel.size.y-36),Color("#b66b55"))
    draw_rect(Rect2(panel.position.x+35,panel.position.y+20,4,panel.size.y-40),Color("#d9c9aa"))
    # Subtle ruled lines make the content feel like a page from a village ledger.
    for y in range(205,520,28):
        draw_line(Vector2(panel.position.x+58,float(y)),Vector2(panel.end.x-30,float(y)),Color("#c8bda7",0.42),1.0)
    # Folded page corner
    draw_colored_polygon(PackedVector2Array([
        Vector2(panel.end.x-48,panel.position.y),Vector2(panel.end.x,panel.position.y),
        Vector2(panel.end.x,panel.position.y+48)
    ]),Color("#dfd0b3"))
    draw_line(Vector2(panel.end.x-48,panel.position.y),Vector2(panel.end.x,panel.position.y+48),Color("#9a8468"),1.5)
    # Title plaque and category stamp
    draw_rect(Rect2(panel.position.x+58,panel.position.y+24,560,50),Color("#e6d8bb"))
    draw_string(ThemeDB.fallback_font,panel.position+Vector2(76,57),str(inspection.get("title","Inspection")),HORIZONTAL_ALIGNMENT_LEFT,520,25,INK)
    draw_string(ThemeDB.fallback_font,panel.position+Vector2(620,54),str(inspection.get("kind","Record")).to_upper(),HORIZONTAL_ALIGNMENT_RIGHT,100,10,RUST)
    var lines: Array = inspection.get("lines",[])
    if lines.is_empty() and inspection.has("data"):
        var data: Dictionary = inspection.get("data",{})
        lines = [
            "Occupation  ·  %s" % data.get("occupation","—"),
            "Home  ·  %s" % data.get("home_location_id","—"),
            "Work  ·  %s" % data.get("work_location_id","—"),
            "Wealth  ·  %s gold" % data.get("wealth_gold","—")
        ]
    var line_y := panel.position.y+132
    for line in lines.slice(0,11):
        draw_circle(Vector2(panel.position.x+68,line_y-5),3.0,RUST)
        draw_string(ThemeDB.fallback_font,Vector2(panel.position.x+84,line_y),str(line),HORIZONTAL_ALIGNMENT_LEFT,620,15,INK)
        line_y += 27
    draw_string(ThemeDB.fallback_font,Vector2(panel.position.x+60,panel.end.y-24),"PRESS E OR ESC TO CLOSE",HORIZONTAL_ALIGNMENT_LEFT,300,11,RUST)

func _draw_connection_state() -> void:
    if not bool(_state.get("connected",false)):
        var camera_x := _camera.position.x if _camera else 640.0
        draw_rect(Rect2(camera_x-180,24,360,42),Color("#282e2b",0.78))
        var error := str(_state.get("error",""))
        draw_string(ThemeDB.fallback_font,Vector2(camera_x-160,51),error if not error.is_empty() else "CONNECTING TO SIMULATION…",HORIZONTAL_ALIGNMENT_LEFT,320,13,PAPER)

func _draw_simulation_hud() -> void:
    var status: Dictionary = _state.get("status",{})
    if status.is_empty():
        return
    var camera_x := _camera.position.x if _camera else 640.0
    var lifecycle := str(status.get("lifecycle_state","STARTING"))
    var tick := int(status.get("tick",0))
    var day := int(status.get("day",1))
    var hour := int(status.get("hour",0))
    var minute := tick % 60
    var season := str(status.get("season","SPRING")).capitalize()
    var temperature := float(status.get("ambient_temperature_celsius",18.0))
    var people := int(_state.get("population",{}).get("alive",0))
    var clock_text := "%02d:%02d" % [hour,minute]

    # The time display is styled as a small village notice plaque, not a HUD bar.
    draw_rect(Rect2(camera_x-616,22,264,76),Color("#584637",0.96))
    draw_rect(Rect2(camera_x-610,27,252,66),Color("#e9d9b8"))
    draw_rect(Rect2(camera_x-604,32,240,56),Color("#f6ecd5"),false,2.0)
    draw_circle(Vector2(camera_x-582,60),21.0,Color("#a77a51"))
    draw_circle(Vector2(camera_x-582,60),16.0,Color("#fff2d4"))
    draw_line(Vector2(camera_x-582,60),Vector2(camera_x-582,49),INK,2.0)
    draw_line(Vector2(camera_x-582,60),Vector2(camera_x-573,65),INK,2.0)
    draw_circle(Vector2(camera_x-582,60),2.0,INK)
    draw_string(ThemeDB.fallback_font,Vector2(camera_x-552,49),"OAKWOOD  ·  DAY %d" % day,HORIZONTAL_ALIGNMENT_LEFT,174,12,INK)
    draw_string(ThemeDB.fallback_font,Vector2(camera_x-552,70),clock_text+"  ·  "+season,HORIZONTAL_ALIGNMENT_LEFT,174,17,INK)
    draw_string(ThemeDB.fallback_font,Vector2(camera_x-552,85),"%d neighbours  ·  %.0f°C" % [people,temperature],HORIZONTAL_ALIGNMENT_LEFT,174,10,Color("#80664d"))

    # A tiny hanging status tag gives the running state a physical, diegetic feel.
    var tag_colour := Color("#6d8a68") if lifecycle == "RUNNING" else Color("#b66b48")
    draw_colored_polygon(PackedVector2Array([
        Vector2(camera_x+474,22),Vector2(camera_x+614,22),
        Vector2(camera_x+604,88),Vector2(camera_x+484,88)
    ]),Color("#604a39"))
    draw_colored_polygon(PackedVector2Array([
        Vector2(camera_x+480,27),Vector2(camera_x+608,27),
        Vector2(camera_x+600,82),Vector2(camera_x+488,82)
    ]),tag_colour)
    draw_circle(Vector2(camera_x+544,39),3.0,Color("#f1dfbf"))
    draw_string(ThemeDB.fallback_font,Vector2(camera_x+496,61),"VILLAGE",HORIZONTAL_ALIGNMENT_CENTER,96,11,Color("#fff4df"))
    draw_string(ThemeDB.fallback_font,Vector2(camera_x+496,76),lifecycle,HORIZONTAL_ALIGNMENT_CENTER,96,10,Color("#fff4df"))
