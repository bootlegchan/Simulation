extends Node2D
## Modular character rig with independent limbs, face, hair and accessories.
## Proportions lean chibi: a large head group over a short, rounded body.

const PART_SCRIPT = preload("res://scripts/characters/character_part.gd")

# Head parts are drawn at a larger scale than the body for the storybook look.
const HEAD_SCALE := 1.3
const BODY_SCALE := 0.88
const HEAD_Y := -94.0
const HAIR_Y := HEAD_Y-20.0*HEAD_SCALE
const BODY_Y := -39.0

var _appearance: Dictionary = {}
var _parts: Dictionary = {}
var _phase := 0.0
var _moving := false
var _base_scale := 1.0
var _facing := 1.0
var _motion_direction := Vector2.ZERO
var _view_direction := "front"
var _blink_clock := 0.0
var _blink_left := 0.0
var _next_blink := 3.0

func configure(entity: Dictionary, is_observer: bool = false) -> void:
    var identity := str(entity.get("id",entity.get("name","citizen")))
    var seed_value := absi(identity.hash())
    var rng := RandomNumberGenerator.new()
    rng.seed = identity.hash()
    var skins := ["#ffd9b8","#f6c298","#e3a77a","#c98a62","#a86b4a","#7a4a36"]
    var hairs := ["#3b2a26","#5a3a2c","#8a5330","#c9852f","#e6b84a","#5d6d8a"]
    var clothes := ["#4fb286","#ff8a5c","#5b9bf0","#ffc233","#a58aef","#fff0d6","#37a8b0","#ee5c5c"]
    var generated := {"skin":skins[rng.randi_range(0,skins.size()-1)],"hair":hairs[rng.randi_range(0,hairs.size()-1)],"clothes":clothes[rng.randi_range(0,clothes.size()-1)],"eyes":"#3a2a26","head_shape":rng.randi_range(0,3),"body_shape":rng.randi_range(0,3),"hair_style":rng.randi_range(0,5),"face_style":rng.randi_range(0,4),"accessory":rng.randi_range(0,5),"outfit_style":rng.randi_range(0,5),"outfit_accent":clothes[rng.randi_range(0,clothes.size()-1)],"shoes":"#d2643f","headwear":rng.randi_range(0,5),"facial_hair":rng.randi_range(0,3),"scale":rng.randf_range(0.88,1.13)}
    var supplied: Variant = entity.get("appearance",{})
    if supplied is Dictionary:
        for key in supplied:
            if generated.has(key): generated[key] = supplied[key]
    _appearance = generated
    _base_scale = float(generated.get("scale",1.0))
    _phase = float(seed_value%628)*0.01
    _next_blink = 2.4+float(seed_value%230)*0.01
    _assemble()
    scale = Vector2(_base_scale,_base_scale)
    set_process(true)

func _assemble() -> void:
    for child in get_children(): child.queue_free()
    _parts.clear()
    _add_part("shadow",Vector2.ZERO)
    _add_part("legs",Vector2(0,-8))
    _add_part("arm_back",Vector2(0,BODY_Y),-1.0,BODY_SCALE)
    _add_part("body",Vector2(0,BODY_Y),0.0,BODY_SCALE)
    _add_part("garment",Vector2(0,BODY_Y),0.0,BODY_SCALE)
    _add_part("arm_front",Vector2(0,BODY_Y),1.0,BODY_SCALE)
    _add_part("head",Vector2(0,HEAD_Y),0.0,HEAD_SCALE)
    _add_part("hair",Vector2(0,HAIR_Y),0.0,HEAD_SCALE)
    _add_part("headwear",Vector2(0,HEAD_Y),0.0,HEAD_SCALE)
    _add_part("face",Vector2(0,HEAD_Y),0.0,HEAD_SCALE)
    _add_part("accessory",Vector2(0,BODY_Y),0.0,BODY_SCALE)

func _add_part(kind: String,offset: Vector2,side: float = 0.0,part_scale: float = 1.0) -> void:
    var part := Node2D.new()
    part.set_script(PART_SCRIPT)
    part.position = offset
    part.scale = Vector2(part_scale,part_scale)
    part.call("configure",kind,_appearance,side)
    add_child(part)
    _parts[kind] = part

func set_motion(moving: bool,direction: Vector2 = Vector2.ZERO) -> void:
    _moving = moving
    if direction.length_squared()>0.0025:
        _motion_direction = direction.normalized()
        if absf(direction.x)>absf(direction.y)*0.72:
            _view_direction = "side"
            _facing = signf(direction.x)
            scale = Vector2(_base_scale*_facing,_base_scale)
        elif direction.y>0.0:
            _view_direction = "front"
            scale = Vector2(_base_scale,_base_scale)
        else:
            _view_direction = "back"
            scale = Vector2(_base_scale,_base_scale)
        for key in _parts:
            _parts[key].call("set_view_direction",_view_direction)

func _process(delta: float) -> void:
    _phase += delta*(8.5 if _moving else 1.65)
    var bob := sin(_phase*2.0)*(1.7 if _moving else 0.65)
    var stride := sin(_phase)*5.2*absf(_motion_direction.x) if _moving else 0.0
    var depth_stride := sin(_phase)*3.8*absf(_motion_direction.y) if _moving else 0.0
    _parts["body"].position.y = BODY_Y+bob
    _parts["garment"].position.y = BODY_Y+bob
    _parts["accessory"].position.y = BODY_Y+bob
    _parts["body"].rotation = sin(_phase*0.5)*0.025 if _moving else sin(_phase*0.45)*0.012
    _parts["garment"].rotation = _parts["body"].rotation
    _parts["arm_back"].position.y = BODY_Y+bob
    _parts["arm_front"].position.y = BODY_Y+bob
    _parts["arm_back"].call("set_stride",stride,depth_stride)
    _parts["arm_front"].call("set_stride",stride,depth_stride)
    _parts["legs"].call("set_stride",stride,depth_stride)
    var torso_breath := sin(_phase*2.0)*(0.018 if _moving else 0.009)
    _parts["body"].scale = Vector2(BODY_SCALE,BODY_SCALE*(1.0+torso_breath))
    _parts["garment"].scale = _parts["body"].scale
    _parts["head"].position.y = HEAD_Y+bob*0.72
    _parts["head"].rotation = sin(_phase*0.65)*0.018
    _parts["hair"].position.y = HAIR_Y+bob*0.72
    _parts["hair"].rotation = sin(_phase*0.65+0.5)*0.025
    _parts["headwear"].position.y = HEAD_Y+bob*0.72
    _parts["headwear"].rotation = _parts["hair"].rotation*0.35
    _parts["face"].position.y = HEAD_Y+bob*0.72
    _blink_clock += delta
    if _blink_left>0.0:
        _blink_left = maxf(_blink_left-delta,0.0)
    elif _blink_clock>=_next_blink:
        _blink_left = 0.13
        _next_blink += 3.1+float((absi(str(_appearance.get("hair","").hash()))+int(_blink_clock*100.0))%240)*0.01
    _parts["face"].call("set_blink",_blink_left>0.0)
