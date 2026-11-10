extends Node2D
## One independently replaceable layer in a CharacterVisual rig.

var component_type := ""
var appearance: Dictionary = {}
var _stride := 0.0

func configure(kind: String, data: Dictionary) -> void:
    component_type = kind
    appearance = data.duplicate(true)
    queue_redraw()

func set_appearance(data: Dictionary) -> void:
    appearance = data.duplicate(true)
    queue_redraw()

func set_stride(value: float) -> void:
    _stride = value
    queue_redraw()

func _draw() -> void:
    var ink := Color("#493c35")
    var skin := Color(str(appearance.get("skin","#e9b994")))
    var hair := Color(str(appearance.get("hair","#49372f")))
    var clothes := Color(str(appearance.get("clothes","#718b79")))
    var eyes := Color(str(appearance.get("eyes","#302923")))
    match component_type:
        "shadow":
            draw_ellipse(Vector2(0,0),Vector2(21,5),Color("#3e382f",0.22))
        "legs":
            _draw_legs(ink)
        "body":
            _draw_body(ink,skin,clothes)
        "head":
            _draw_head(ink,skin)
        "hair":
            _draw_hair(ink,hair)
        "face":
            _draw_face(ink,skin,eyes)
        "accessory":
            _draw_accessory(ink)

func _draw_legs(ink: Color) -> void:
    draw_line(Vector2(-7,-3),Vector2(-10+_stride,7),ink,9.0)
    draw_line(Vector2(7,-3),Vector2(10-_stride,7),ink,9.0)
    draw_line(Vector2(-7,-3),Vector2(-10+_stride,4),Color("#d9c9ae"),3.0)
    draw_line(Vector2(7,-3),Vector2(10-_stride,4),Color("#d9c9ae"),3.0)
    draw_ellipse(Vector2(-13+_stride,8),Vector2(10,5),ink)
    draw_ellipse(Vector2(13-_stride,8),Vector2(10,5),ink)

func _draw_body(ink: Color,skin: Color,clothes: Color) -> void:
    var shape := int(appearance.get("body_shape",0))
    var half_width := [12.0,15.0,13.0,17.0][shape]
    var height := [38.0,34.0,42.0,37.0][shape]
    var torso := PackedVector2Array([
        Vector2(-half_width,-height),Vector2(-half_width-7,-height+8),
        Vector2(-half_width+1,-8),Vector2(half_width-1,-8),
        Vector2(half_width+7,-height+8),Vector2(half_width,-height)
    ])
    draw_colored_polygon(torso,ink)
    var inner := PackedVector2Array([
        Vector2(-half_width+3,-height+4),Vector2(-half_width-3,-height+11),
        Vector2(-half_width+4,-11),Vector2(half_width-4,-11),
        Vector2(half_width+3,-height+11),Vector2(half_width-3,-height+4)
    ])
    draw_colored_polygon(inner,clothes)
    draw_colored_polygon(PackedVector2Array([Vector2(-7,-height+3),Vector2(0,-height+12),Vector2(7,-height+3)]),Color("#f0e2c8"))
    draw_line(Vector2(-half_width-2,-height+15),Vector2(-half_width-6,-14),skin,7.0)
    draw_line(Vector2(half_width+2,-height+15),Vector2(half_width+6,-14),skin,7.0)
    draw_circle(Vector2(-half_width-6,-13),4.0,skin)
    draw_circle(Vector2(half_width+6,-13),4.0,skin)

func _draw_head(ink: Color,skin: Color) -> void:
    var shape := int(appearance.get("head_shape",0))
    var size := [21.0,23.0,20.0,22.0][shape]
    draw_circle(Vector2(0,0),size+3.0,ink)
    draw_circle(Vector2(0,-1),size,skin)
    draw_circle(Vector2(-size+2,-2),5.0,skin)
    draw_circle(Vector2(size-2,-2),5.0,skin)

func _draw_hair(ink: Color,hair: Color) -> void:
    var style := int(appearance.get("hair_style",0))
    var cap := PackedVector2Array([
        Vector2(-21,5),Vector2(-22,-9),Vector2(-15,-20),
        Vector2(-5,-23),Vector2(3,-20),Vector2(12,-23),
        Vector2(22,-11),Vector2(21,5),Vector2(11,0),
        Vector2(3,4),Vector2(-5,0),Vector2(-13,5)
    ])
    if style == 1:
        draw_circle(Vector2(-15,-13),9.0,ink)
        draw_circle(Vector2(-15,-13),7.0,hair)
        draw_circle(Vector2(0,-17),11.0,ink)
        draw_circle(Vector2(0,-17),9.0,hair)
        draw_circle(Vector2(14,-12),9.0,ink)
        draw_circle(Vector2(14,-12),7.0,hair)
    elif style == 2:
        draw_rect(Rect2(-23,-18,46,14),ink)
        draw_rect(Rect2(-20,-17,40,10),hair)
        draw_colored_polygon(PackedVector2Array([Vector2(-23,-6),Vector2(-12,-10),Vector2(-5,-4),Vector2(4,-10),Vector2(13,-4),Vector2(22,-7),Vector2(17,5),Vector2(-17,5)]),hair)
    elif style == 3:
        draw_circle(Vector2(0,-17),11.0,ink)
        draw_circle(Vector2(0,-17),9.0,hair)
        draw_circle(Vector2(-12,-10),8.0,ink)
        draw_circle(Vector2(-12,-10),6.0,hair)
        draw_circle(Vector2(12,-10),8.0,ink)
        draw_circle(Vector2(12,-10),6.0,hair)
    elif style == 4:
        draw_colored_polygon(PackedVector2Array([Vector2(-22,0),Vector2(-22,-18),Vector2(-10,-24),Vector2(0,-17),Vector2(11,-24),Vector2(22,-16),Vector2(20,3),Vector2(8,-2),Vector2(0,5),Vector2(-9,-2)]),ink)
        draw_colored_polygon(PackedVector2Array([Vector2(-19,-1),Vector2(-18,-16),Vector2(-9,-20),Vector2(0,-14),Vector2(10,-20),Vector2(18,-14),Vector2(17,0),Vector2(7,-5),Vector2(0,1),Vector2(-9,-5)]),hair)
    else:
        draw_colored_polygon(cap,ink)
        cap[0] += Vector2(2,2)
        cap[1] += Vector2(2,2)
        cap[2] += Vector2(2,2)
        cap[3] += Vector2(2,2)
        cap[4] += Vector2(2,2)
        cap[5] += Vector2(2,2)
        cap[6] += Vector2(2,2)
        cap[7] += Vector2(2,2)
        draw_colored_polygon(cap,hair)

func _draw_face(ink: Color,skin: Color,eyes: Color) -> void:
    var style := int(appearance.get("face_style",0))
    draw_ellipse(Vector2(-14,9),Vector2(4,2.5),Color("#df9180",0.48))
    draw_ellipse(Vector2(14,9),Vector2(4,2.5),Color("#df9180",0.48))
    if style == 1:
        draw_line(Vector2(-10,-4),Vector2(-4,-4),ink,2.0)
        draw_line(Vector2(4,-4),Vector2(10,-4),ink,2.0)
    elif style == 2:
        draw_circle(Vector2(-8,-5),3.0,Color("#fff8e9"))
        draw_circle(Vector2(8,-5),3.0,Color("#fff8e9"))
        draw_circle(Vector2(-8,-5),1.8,eyes)
        draw_circle(Vector2(8,-5),1.8,eyes)
    else:
        draw_ellipse(Vector2(-8,-5),Vector2(3.0,4.8),Color("#fff8e9"))
        draw_ellipse(Vector2(8,-5),Vector2(3.0,4.8),Color("#fff8e9"))
        draw_circle(Vector2(-7,-4),2.0,eyes)
        draw_circle(Vector2(9,-4),2.0,eyes)
    draw_line(Vector2(-12,-12),Vector2(-4,-13),ink,1.8)
    draw_line(Vector2(4,-13),Vector2(12,-12),ink,1.8)
    draw_circle(Vector2(0,3),1.6,skin.darkened(0.08))
    if style == 3:
        draw_line(Vector2(-4,12),Vector2(4,12),ink,1.8)
    else:
        draw_arc(Vector2(0,10),5.0,0.15,PI-0.15,10,ink,1.7)

func _draw_accessory(ink: Color) -> void:
    var accessory := int(appearance.get("accessory",0))
    if accessory == 1:
        draw_arc(Vector2(0,-4),24.0,PI,TAU,16,Color("#a87845"),4.0)
    elif accessory == 2:
        draw_circle(Vector2(0,-20),5.0,Color("#d8b36e"))
    elif accessory == 3:
        draw_rect(Rect2(-24,-18,48,5),Color("#d8b36e"))
        draw_rect(Rect2(-4,-18,8,5),Color("#f0dfbd"))
    elif accessory == 4:
        draw_circle(Vector2(0,-18),4.0,Color("#b66b48"))
    elif accessory == 5:
        draw_line(Vector2(-24,-1),Vector2(24,-1),Color("#a87845"),3.0)

func draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var angle := TAU * float(i) / 20.0
        points.append(center + Vector2(cos(angle) * radius.x,sin(angle) * radius.y))
    draw_colored_polygon(points,colour)
