extends Node2D
## Modular character rig with independent limbs, face, hair and accessories.

const PART_SCRIPT = preload("res://scripts/characters/character_part.gd")
var _appearance: Dictionary = {}
var _parts: Dictionary = {}
var _phase := 0.0
var _moving := false
var _base_scale := 1.0
var _facing := 1.0
var _blink_clock := 0.0
var _blink_left := 0.0
var _next_blink := 3.0

func configure(entity: Dictionary, is_observer: bool = false) -> void:
    var identity := str(entity.get("id",entity.get("name","citizen")))
    var seed_value := absi(identity.hash())
    var rng := RandomNumberGenerator.new()
    rng.seed = identity.hash()
    var skins := ["#f5d0ad","#e9b994","#d9a17e","#c98b6b","#a96f56","#754c3d"]
    var hairs := ["#302923","#49372f","#72503b","#a06d45","#c1a06d","#4b5555"]
    var clothes := ["#718b79","#bd8060","#657c99","#c2a16b","#81738e","#d0bca0","#55716f","#a75e4c"]
    var generated := {"skin":skins[rng.randi_range(0,skins.size()-1)],"hair":hairs[rng.randi_range(0,hairs.size()-1)],"clothes":clothes[rng.randi_range(0,clothes.size()-1)],"eyes":"#302923","head_shape":rng.randi_range(0,3),"body_shape":rng.randi_range(0,3),"hair_style":rng.randi_range(0,5),"face_style":rng.randi_range(0,4),"accessory":rng.randi_range(0,5),"scale":rng.randf_range(0.88,1.13)}
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
    _add_part("body",Vector2(0,-39))
    _add_part("arms",Vector2(0,-39))
    _add_part("head",Vector2(0,-83))
    _add_part("hair",Vector2(0,-103))
    _add_part("face",Vector2(0,-83))
    _add_part("accessory",Vector2(0,-39))

func _add_part(kind: String,offset: Vector2) -> void:
    var part := Node2D.new()
    part.set_script(PART_SCRIPT)
    part.position = offset
    part.call("configure",kind,_appearance)
    add_child(part)
    _parts[kind] = part

func set_motion(moving: bool,direction: Vector2 = Vector2.ZERO) -> void:
    _moving = moving
    if direction.length_squared()>0.0025 and absf(direction.x)>absf(direction.y):
        _facing = signf(direction.x)
        scale = Vector2(_base_scale*_facing,_base_scale)

func _process(delta: float) -> void:
    _phase += delta*(8.5 if _moving else 1.65)
    var bob := sin(_phase*2.0)*(1.7 if _moving else 0.65)
    var stride := sin(_phase)*5.2 if _moving else 0.0
    _parts["body"].position.y = -39.0+bob
    _parts["body"].rotation = sin(_phase*0.5)*0.025 if _moving else sin(_phase*0.45)*0.012
    _parts["arms"].position.y = -39.0+bob
    _parts["arms"].call("set_stride",stride)
    _parts["legs"].call("set_stride",stride)
    _parts["head"].position.y = -83.0+bob*0.72
    _parts["head"].rotation = sin(_phase*0.65)*0.018
    _parts["hair"].position.y = -103.0+bob*0.72
    _parts["hair"].rotation = sin(_phase*0.65+0.5)*0.025
    _parts["face"].position.y = -83.0+bob*0.72
    _blink_clock += delta
    if _blink_left>0.0:
        _blink_left = maxf(_blink_left-delta,0.0)
    elif _blink_clock>=_next_blink:
        _blink_left = 0.13
        _next_blink += 3.1+float((absi(str(_appearance.get("hair","").hash()))+int(_blink_clock*100.0))%240)*0.01
    _parts["face"].call("set_blink",_blink_left>0.0)
