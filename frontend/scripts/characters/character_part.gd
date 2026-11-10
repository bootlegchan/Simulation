extends Node2D
## Independently replaceable character component.

var component_type := ""
var appearance: Dictionary = {}
var _stride := 0.0
var _depth_stride := 0.0
var _blink := false
var _view_direction := "front"

func configure(kind: String,data: Dictionary) -> void:
    component_type = kind
    appearance = data.duplicate(true)
    queue_redraw()

func set_stride(value: float,depth_value: float = 0.0) -> void:
    _stride = value
    _depth_stride = depth_value
    queue_redraw()

func set_view_direction(value: String) -> void:
    if _view_direction == value: return
    _view_direction = value
    queue_redraw()

func set_blink(value: bool) -> void:
    if _blink==value: return
    _blink = value
    queue_redraw()

func _draw() -> void:
    var ink := Color("#493c35")
    var skin := Color(str(appearance.get("skin","#e9b994")))
    var hair := Color(str(appearance.get("hair","#49372f")))
    var clothes := Color(str(appearance.get("clothes","#718b79")))
    var eyes := Color(str(appearance.get("eyes","#302923")))
    match component_type:
        "shadow": draw_ellipse(Vector2.ZERO,Vector2(21,5),Color("#3e382f",0.22))
        "legs": _draw_legs(ink)
        "body": _draw_body(ink,clothes)
        "garment": _draw_garment(ink,clothes)
        "arms": _draw_arms(ink,skin,clothes)
        "head": _draw_head(ink,skin)
        "hair": _draw_hair(ink,hair)
        "headwear": _draw_headwear()
        "face": _draw_face(ink,skin,eyes)
        "accessory": _draw_accessory()

func _draw_legs(ink: Color) -> void:
    for side in [-1.0,1.0]:
        var swing := _stride*side
        var knee := Vector2(side*8+swing,-1)
        var foot := Vector2(side*12+swing,7+_depth_stride*side)
        draw_line(Vector2(side*7,-5),knee,ink,10.0)
        draw_line(knee,foot,ink,7.0)
        draw_ellipse(foot+Vector2(-1,1),Vector2(10,5),Color("#59483c"))
        draw_line(foot+Vector2(-4,-1),foot+Vector2(3,-1),Color("#c7b69c"),1.4)

func _draw_body(ink: Color,clothes: Color) -> void:
    var shape := clampi(int(appearance.get("body_shape",0)),0,3)
    var hw := [12.0,15.0,13.0,17.0][shape]
    var h := [38.0,34.0,42.0,37.0][shape]
    draw_colored_polygon(PackedVector2Array([Vector2(-hw,-h),Vector2(-hw-7,-h+8),Vector2(-hw+1,-8),Vector2(hw-1,-8),Vector2(hw+7,-h+8),Vector2(hw,-h)]),ink)
    draw_colored_polygon(PackedVector2Array([Vector2(-hw+3,-h+4),Vector2(-hw-3,-h+11),Vector2(-hw+4,-11),Vector2(hw-4,-11),Vector2(hw+3,-h+11),Vector2(hw-3,-h+4)]),clothes)
    draw_colored_polygon(PackedVector2Array([Vector2(-7,-h+3),Vector2(0,-h+12),Vector2(7,-h+3)]),Color("#f0e2c8"))
    draw_line(Vector2(0,-h+12),Vector2(0,-12),clothes.darkened(0.22),1.4)
    # Tailored seams and a small folded collar add readable costume detail at game scale.
    draw_line(Vector2(-hw+5,-h+15),Vector2(-hw+7,-18),clothes.lightened(0.16),1.1)
    draw_line(Vector2(hw-5,-h+15),Vector2(hw-7,-18),clothes.darkened(0.16),1.1)
    draw_colored_polygon(PackedVector2Array([Vector2(-7,-h+3),Vector2(0,-h+12),Vector2(7,-h+3),Vector2(3,-h-1),Vector2(-3,-h-1)]),Color("#f0e2c8"))
    for i in range(3): draw_circle(Vector2(0,-h+19+float(i)*8),1.25,Color("#ead9b8"))

func _draw_arms(ink: Color,skin: Color,clothes: Color) -> void:
    var swing := _stride*0.72
    for side in [-1.0,1.0]:
        var shoulder := Vector2(side*11,-29)
        var elbow := Vector2(side*16+swing*side,-16+_depth_stride*side*0.35)
        var hand := Vector2(side*15+swing*side*1.35,-5+_depth_stride*side*0.7)
        draw_line(shoulder,elbow,ink,9.0)
        draw_line(shoulder+Vector2(0,1),elbow+Vector2(0,1),clothes,6.5)
        draw_line(elbow,hand,ink,7.0)
        draw_line(elbow,hand-Vector2(0,1),skin,4.5)
        draw_circle(hand,3.8,skin)

func _draw_head(ink: Color,skin: Color) -> void:
    var shape := clampi(int(appearance.get("head_shape",0)),0,3)
    var size := [21.0,23.0,20.0,22.0][shape]
    draw_circle(Vector2.ZERO,size+3.0,ink)
    draw_circle(Vector2(0,-1),size,skin)
    draw_circle(Vector2(-size+2,-2),5.0,skin.darkened(0.025))
    draw_circle(Vector2(size-2,-2),5.0,skin.darkened(0.025))
    draw_ellipse(Vector2(-7,-12),Vector2(7,3),skin.lightened(0.12))

func _draw_hair(ink: Color,hair: Color) -> void:
    var style := int(appearance.get("hair_style",0))
    if style==1 or style==3:
        var points := [Vector2(-15,-13),Vector2(0,-17),Vector2(14,-12)] if style==1 else [Vector2(0,-17),Vector2(-12,-10),Vector2(12,-10)]
        for p in points:
            draw_circle(p,10.0,ink)
            draw_circle(p+Vector2(0,-1),7.8,hair)
    elif style==2:
        draw_rect(Rect2(-23,-18,46,14),ink)
        draw_rect(Rect2(-20,-17,40,10),hair)
        draw_colored_polygon(PackedVector2Array([Vector2(-23,-6),Vector2(-12,-10),Vector2(-5,-4),Vector2(4,-10),Vector2(13,-4),Vector2(22,-7),Vector2(17,5),Vector2(-17,5)]),hair)
    elif style==4:
        draw_colored_polygon(PackedVector2Array([Vector2(-22,0),Vector2(-22,-18),Vector2(-10,-24),Vector2(0,-17),Vector2(11,-24),Vector2(22,-16),Vector2(20,3),Vector2(8,-2),Vector2(0,5),Vector2(-9,-2)]),ink)
        draw_colored_polygon(PackedVector2Array([Vector2(-19,-1),Vector2(-18,-16),Vector2(-9,-20),Vector2(0,-14),Vector2(10,-20),Vector2(18,-14),Vector2(17,0),Vector2(7,-5),Vector2(0,1),Vector2(-9,-5)]),hair)
    else:
        var cap := PackedVector2Array([Vector2(-21,5),Vector2(-22,-9),Vector2(-15,-20),Vector2(-5,-23),Vector2(3,-20),Vector2(12,-23),Vector2(22,-11),Vector2(21,5),Vector2(11,0),Vector2(3,4),Vector2(-5,0),Vector2(-13,5)])
        draw_colored_polygon(cap,ink)
        for i in range(cap.size()): cap[i]+=Vector2(1.5,1.5)
        draw_colored_polygon(cap,hair)
    draw_line(Vector2(-11,-19),Vector2(-3,-22),hair.lightened(0.22),1.4)
    draw_arc(Vector2(0,-7),18.0,PI+0.18,TAU-0.18,14,ink,1.2)

func _draw_face(ink: Color,skin: Color,eyes: Color) -> void:
    if _view_direction == "back":
        return
    var style := int(appearance.get("face_style",0))
    if _view_direction == "side":
        draw_ellipse(Vector2(7,-5),Vector2(2.7,4.2),Color("#fff8e9"))
        draw_circle(Vector2(8,-4),1.8,eyes)
        draw_line(Vector2(5,-13),Vector2(11,-12),ink,1.7)
        draw_line(Vector2(13,1),Vector2(17,4),skin.darkened(0.12),1.4)
        draw_arc(Vector2(7,10),4.0,0.1,PI-0.2,8,ink,1.4)
        return
    draw_ellipse(Vector2(-14,9),Vector2(4,2.5),Color("#df9180",0.48))
    if _blink:
        draw_line(Vector2(-11,-5),Vector2(-5,-5),ink,2.0)
        draw_line(Vector2(5,-5),Vector2(11,-5),ink,2.0)
    elif style==1:
        draw_line(Vector2(-10,-4),Vector2(-4,-4),ink,2.0)
        draw_line(Vector2(4,-4),Vector2(10,-4),ink,2.0)
    else:
        draw_ellipse(Vector2(-8,-5),Vector2(3,4.8),Color("#fff8e9"))
        draw_ellipse(Vector2(8,-5),Vector2(3,4.8),Color("#fff8e9"))
        draw_circle(Vector2(-7,-4),2.0,eyes)
        draw_circle(Vector2(9,-4),2.0,eyes)
    draw_line(Vector2(-12,-12),Vector2(-4,-13),ink,1.8)
    draw_line(Vector2(4,-13),Vector2(12,-12),ink,1.8)
    draw_circle(Vector2(0,3),1.6,skin.darkened(0.08))
    draw_arc(Vector2(0,10),5.0,0.15,PI-0.15,10,ink,1.7)

    var beard := int(appearance.get("facial_hair",0))
    var beard_colour := Color(str(appearance.get("hair","#49372f")))
    if beard == 1:
        draw_arc(Vector2(0,9),10.0,0.15,PI-0.15,12,beard_colour,3.0)
    elif beard == 2:
        draw_colored_polygon(PackedVector2Array([Vector2(-10,7),Vector2(-8,16),Vector2(0,21),Vector2(8,16),Vector2(10,7)]),beard_colour)
    elif beard == 3:
        draw_line(Vector2(-13,4),Vector2(-5,10),beard_colour,3.0)
        draw_line(Vector2(13,4),Vector2(5,10),beard_colour,3.0)



func _draw_garment(ink: Color,base: Color) -> void:
    var style := int(appearance.get("outfit_style",0))
    var accent := Color(str(appearance.get("outfit_accent","#c9a36d")))
    var hw := [12.0,15.0,13.0,17.0][clampi(int(appearance.get("body_shape",0)),0,3)]
    match style:
        0:
            draw_line(Vector2(-hw-2,-28),Vector2(hw+2,-28),accent.darkened(0.12),3.0)
            draw_rect(Rect2(-2,-30,4,4),accent)
        1:
            draw_colored_polygon(PackedVector2Array([Vector2(-hw-3,-37),Vector2(-hw-9,-27),Vector2(-7,-7),Vector2(0,-13),Vector2(7,-7),Vector2(hw+9,-27),Vector2(hw+3,-37)]),accent.darkened(0.08))
            draw_line(Vector2(-hw-2,-27),Vector2(-7,-9),accent.lightened(0.18),1.4)
            draw_line(Vector2(hw+2,-27),Vector2(7,-9),accent.lightened(0.18),1.4)
        2:
            draw_rect(Rect2(-hw-4,-35,hw*2+8,7),Color("#594638"))
            draw_rect(Rect2(-4,-35,8,7),accent)
            draw_line(Vector2(-hw-2,-18),Vector2(hw+2,-18),base.lightened(0.18),2.0)
        3:
            draw_colored_polygon(PackedVector2Array([Vector2(-hw-3,-39),Vector2(-hw-8,-24),Vector2(-hw+1,-8),Vector2(hw-1,-8),Vector2(hw+8,-24),Vector2(hw+3,-39)]),accent)
            draw_line(Vector2(0,-34),Vector2(0,-10),accent.darkened(0.24),1.5)
        4:
            draw_rect(Rect2(-hw-2,-36,hw*2+4,10),Color("#f0e2c8"))
            draw_rect(Rect2(-hw-2,-27,hw*2+4,4),accent)
            draw_line(Vector2(-hw,-20),Vector2(hw,-20),Color("#fff0d7"),1.3)
        5:
            draw_line(Vector2(-hw-5,-34),Vector2(-hw-8,-12),accent,5.0)
            draw_line(Vector2(hw+5,-34),Vector2(hw+8,-12),accent,5.0)
            draw_rect(Rect2(-hw-8,-35,hw*2+16,5),accent.darkened(0.18))

func _draw_headwear() -> void:
    var style := int(appearance.get("headwear",0))
    var accent := Color(str(appearance.get("outfit_accent","#c9a36d")))
    if style == 1:
        draw_rect(Rect2(-25,-15,50,7),Color("#5c4938"))
        draw_colored_polygon(PackedVector2Array([Vector2(-18,-15),Vector2(-15,-28),Vector2(0,-34),Vector2(15,-28),Vector2(18,-15)]),Color("#a17b53"))
        draw_rect(Rect2(-18,-17,36,3),accent)
    elif style == 2:
        draw_colored_polygon(PackedVector2Array([Vector2(-25,-15),Vector2(-20,-31),Vector2(0,-38),Vector2(20,-31),Vector2(25,-15)]),Color("#536d5c"))
        draw_rect(Rect2(-24,-16,48,4),accent)
    elif style == 3:
        draw_arc(Vector2(0,-16),23.0,PI,TAU,16,Color("#9b704c"),5.0)
        draw_line(Vector2(-23,-16),Vector2(23,-16),accent,2.0)
    elif style == 4:
        draw_colored_polygon(PackedVector2Array([Vector2(-20,-17),Vector2(-18,-35),Vector2(0,-42),Vector2(18,-35),Vector2(20,-17)]),Color("#3f5149"))
        draw_rect(Rect2(-20,-19,40,5),accent)
    elif style == 5:
        draw_ellipse(Vector2(0,-19),Vector2(20,5),Color("#d2b88a"))
        draw_colored_polygon(PackedVector2Array([Vector2(-12,-20),Vector2(-9,-36),Vector2(0,-41),Vector2(9,-36),Vector2(12,-20)]),Color("#d2b88a"))
        draw_line(Vector2(-10,-21),Vector2(10,-21),accent,2.0)

func _draw_accessory() -> void:
    var item := int(appearance.get("accessory",0))
    if item==1: draw_arc(Vector2(0,-4),24.0,PI,TAU,16,Color("#a87845"),4.0)
    elif item==2: draw_circle(Vector2(0,-20),5.0,Color("#d8b36e"))
    elif item==3:
        draw_rect(Rect2(-24,-18,48,5),Color("#d8b36e"))
        draw_rect(Rect2(-4,-18,8,5),Color("#f0dfbd"))
    elif item==4: draw_circle(Vector2(0,-18),4.0,Color("#b66b48"))
    elif item==5: draw_line(Vector2(-24,-1),Vector2(24,-1),Color("#a87845"),3.0)

func draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var a := TAU*float(i)/20.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
