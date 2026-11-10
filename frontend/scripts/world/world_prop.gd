extends Node2D
## Independent scenery prop. Prop placement is manifest data, not baked scenery.

var definition: Dictionary = {}
var _wind_phase := 0.0
var _base_rotation := 0.0

func configure(data: Dictionary) -> void:
    if definition == data:
        return
    definition = data.duplicate(true)
    position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",0.0)))
    _base_rotation = float(definition.get("rotation",0.0))
    _wind_phase = float(abs(definition.get("id","").hash()) % 1000) * 0.01
    set_process(kind_is_animated())
    rotation = _base_rotation
    queue_redraw()

func kind_is_animated() -> bool:
    return str(definition.get("kind","tree")) in ["tree","bush"]

func _process(delta: float) -> void:
    _wind_phase += delta * 0.7
    var strength := 0.012 if str(definition.get("kind","")) == "tree" else 0.006
    rotation = _base_rotation + sin(_wind_phase) * strength

func _draw() -> void:
    var kind := str(definition.get("kind","tree"))
    var scale_factor := float(definition.get("scale",1.0))
    if kind == "tree":
        _draw_tree(scale_factor)
    elif kind == "rock":
        draw_colored_polygon(PackedVector2Array([Vector2(-22,0),Vector2(-15,-18),Vector2(4,-25),Vector2(23,-10),Vector2(28,0)]),Color("#817d6c"))
        draw_line(Vector2(-13,-9),Vector2(4,-18),Color("#b5aa8e"),3.0)
    elif kind == "bush":
        for offset in [Vector2(-16,0),Vector2(0,-10),Vector2(17,0)]:
            draw_circle(offset*scale_factor,18.0*scale_factor,Color("#617a61"))
            draw_circle((offset+Vector2(-4,-4))*scale_factor,9.0*scale_factor,Color("#7c936e"))
    elif kind == "lamp":
        draw_rect(Rect2(-4,-92,8,92),Color("#554638"))
        draw_rect(Rect2(-17,-100,34,14),Color("#554638"))
        draw_circle(Vector2(0,-91),8,Color("#f3d28a"))
        draw_circle(Vector2(0,-91),14,Color("#f3d28a",0.18))

func _draw_tree(s: float) -> void:
    draw_colored_polygon(PackedVector2Array([
        Vector2(-8*s,0),Vector2(-6*s,-100*s),Vector2(6*s,-100*s),Vector2(9*s,0)
    ]),Color("#705b43"))
    draw_circle(Vector2(0,-132*s),62*s,Color("#617a61"))
    draw_circle(Vector2(-28*s,-112*s),42*s,Color("#71866a"))
    draw_circle(Vector2(32*s,-110*s),39*s,Color("#536f59"))
    draw_circle(Vector2(-13*s,-150*s),19*s,Color("#82936d",0.72))
