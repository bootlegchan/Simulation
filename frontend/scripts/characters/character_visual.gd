extends Node2D
## A reusable assembled NPC rig. Every part is an independent child component.
## Appearance is stable per entity ID and can later be overridden by an explicit
## appearance dictionary without changing the component architecture.

const PART_SCRIPT = preload("res://scripts/characters/character_part.gd")

var _appearance: Dictionary = {}
var _parts: Dictionary = {}
var _observer := false
var _phase := 0.0
var _is_moving := false

func configure(entity: Dictionary, is_observer: bool = false) -> void:
    _observer = is_observer
    var identity := str(entity.get("id",entity.get("name","citizen")))
    _appearance = _build_appearance(identity,entity.get("appearance",{}))
    _assemble()
    set_process(true)

func _build_appearance(identity: String, supplied: Variant) -> Dictionary:
    var rng := RandomNumberGenerator.new()
    rng.seed = int(identity.hash())
    var skin_tones := ["#f5d0ad","#e9b994","#d9a17e","#c98b6b","#a96f56","#754c3d"]
    var hair_colours := ["#302923","#49372f","#72503b","#a06d45","#c1a06d","#4b5555"]
    var clothing_colours := ["#718b79","#bd8060","#657c99","#c2a16b","#81738e","#d0bca0","#55716f","#a75e4c"]
    var eye_colours := ["#302923","#514438","#536b68"]
    var generated := {
        "skin":skin_tones[rng.randi_range(0,skin_tones.size()-1)],
        "hair":hair_colours[rng.randi_range(0,hair_colours.size()-1)],
        "clothes":clothing_colours[rng.randi_range(0,clothing_colours.size()-1)],
        "eyes":eye_colours[rng.randi_range(0,eye_colours.size()-1)],
        "head_shape":rng.randi_range(0,3),
        "body_shape":rng.randi_range(0,3),
        "hair_style":rng.randi_range(0,5),
        "face_style":rng.randi_range(0,4),
        "accessory":rng.randi_range(0,5),
        "scale":rng.randf_range(0.88,1.13)
    }
    if supplied is Dictionary:
        for key in supplied:
            if generated.has(key):
                generated[key] = supplied[key]
    return generated

func _assemble() -> void:
    for child in get_children():
        child.queue_free()
    _parts.clear()
    _add_part("shadow",Vector2(0,0))
    _add_part("legs",Vector2(0,-8))
    _add_part("body",Vector2(0,-39))
    _add_part("head",Vector2(0,-83))
    _add_part("hair",Vector2(0,-103))
    _add_part("face",Vector2(0,-83))
    _add_part("accessory",Vector2(0,-39))
    _apply_appearance()

func _add_part(part_type: String, offset: Vector2) -> void:
    var part := Node2D.new()
    part.set_script(PART_SCRIPT)
    part.position = offset
    part.call("configure",part_type,_appearance)
    add_child(part)
    _parts[part_type] = part

func _apply_appearance() -> void:
    for part in _parts.values():
        part.call("set_appearance",_appearance)

func set_motion(moving: bool) -> void:
    _is_moving = moving

func _process(delta: float) -> void:
    _phase += delta * (7.0 if _is_moving else 1.8)
    var bob := sin(_phase) * (1.2 if _is_moving else 0.45)
    var stride := sin(_phase * 0.72) * 3.0 if _is_moving else 0.0
    if _parts.has("body"):
        _parts["body"].position.y = -39.0 + bob
    if _parts.has("head"):
        _parts["head"].position.y = -83.0 + bob
    if _parts.has("hair"):
        _parts["hair"].position.y = -103.0 + bob
    if _parts.has("face"):
        _parts["face"].position.y = -83.0 + bob
    if _parts.has("legs"):
        _parts["legs"].call("set_stride",stride)
