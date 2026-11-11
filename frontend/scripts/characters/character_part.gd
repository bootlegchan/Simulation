extends Node2D
## Independently replaceable character component, drawn in the storybook style:
## warm brown outlines, dot eyes, rosy cheeks, rounded limbs and bright flat fills.

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var component_type := ""
var appearance: Dictionary = {}
var _stride := 0.0
var _depth_stride := 0.0
var _blink := false
var _view_direction := "front"
var component_side := 0.0

func configure(kind: String,data: Dictionary,side: float = 0.0) -> void:
    component_type = kind
    component_side = side
    appearance = data.duplicate(true)
    queue_redraw()

func set_stride(value: float,depth_value: float = 0.0) -> void:
    # Idle characters pass the same values every frame; skip needless redraws.
    if is_equal_approx(_stride,value) and is_equal_approx(_depth_stride,depth_value):
        return
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
    var ink := StorybookStyle.OUTLINE
    var skin := Color(str(appearance.get("skin","#f6c298")))
    var hair := Color(str(appearance.get("hair","#5a3a2c")))
    var clothes := Color(str(appearance.get("clothes","#4fb286")))
    var eyes := Color(str(appearance.get("eyes","#3a2a26")))
    match component_type:
        "shadow": StorybookStyle.blob_shadow(self,Vector2.ZERO,25.0,0.24,0.26)
        "legs": _draw_legs(ink,clothes)
        "arm_back": _draw_arm(ink,skin.darkened(0.10),clothes.darkened(0.13),component_side)
        "body": _draw_body(ink,clothes)
        "garment": _draw_garment(ink,clothes)
        "arm_front": _draw_arm(ink,skin,clothes,component_side)
        "head": _draw_head(ink,skin)
        "hair": _draw_hair(ink,hair)
        "headwear": _draw_headwear(ink)
        "face": _draw_face(ink,skin,eyes)
        "accessory": _draw_accessory(ink)

func _draw_legs(ink: Color,clothes: Color) -> void:
    var shoe_colour := Color(str(appearance.get("shoes","#d2643f")))
    var pants := StorybookStyle.tone(clothes,-0.38)
    for side in [-1.0,1.0]:
        var swing := _stride*side
        var lift := maxf(swing,0.0)*0.46+maxf(_depth_stride*side,0.0)*0.34
        var hip := Vector2(side*7,-5)
        var knee := Vector2(side*8+swing,-1.0-lift*0.55)
        var foot := Vector2(side*12+swing,7.0+_depth_stride*side-lift)
        draw_line(hip,knee,ink,12.0,true)
        draw_line(knee,foot,ink,9.0,true)
        draw_line(hip,knee,pants,8.0,true)
        draw_line(knee,foot,pants,5.5,true)
        draw_ellipse(foot+Vector2(-1,1),Vector2(12.5,7.0),ink)
        draw_ellipse(foot+Vector2(-1,0.5),Vector2(10.0,5.0),shoe_colour)
        draw_ellipse(foot+Vector2(-3,-1),Vector2(4.0,1.8),Color("#ffb792",0.9))

func _draw_arm(ink: Color,skin: Color,clothes: Color,side: float) -> void:
    var swing := -_stride*0.72*side
    var depth_swing := _depth_stride*side
    var shoulder := Vector2(side*11.0,-29.0)
    var elbow := Vector2(side*16.0+swing*0.55,-17.0-depth_swing*0.25)
    var hand := Vector2(side*14.0+swing,-5.0-depth_swing*0.65)
    draw_line(shoulder,elbow,ink,11.0,true)
    draw_line(shoulder+Vector2(0,1),elbow+Vector2(0,1),clothes,7.5,true)
    draw_line(elbow,hand,ink,9.0,true)
    draw_line(elbow,hand-Vector2(0,1),skin,5.5,true)
    draw_circle(hand,5.6,ink)
    draw_circle(hand,4.2,skin)

func _draw_body(ink: Color,clothes: Color) -> void:
    var shape := clampi(int(appearance.get("body_shape",0)),0,3)
    var hw := [12.0,15.0,13.0,17.0][shape]
    var h := [38.0,34.0,42.0,37.0][shape]
    draw_colored_polygon(PackedVector2Array([Vector2(-hw-1,-h-1),Vector2(-hw-8,-h+8),Vector2(-hw,-7),Vector2(hw,-7),Vector2(hw+8,-h+8),Vector2(hw+1,-h-1)]),ink)
    draw_colored_polygon(PackedVector2Array([Vector2(-hw+3,-h+4),Vector2(-hw-3,-h+11),Vector2(-hw+4,-11),Vector2(hw-4,-11),Vector2(hw+3,-h+11),Vector2(hw-3,-h+4)]),clothes)
    # A shaded side and a light shoulder dab keep the flat fill from looking dead.
    draw_colored_polygon(PackedVector2Array([Vector2(hw-6,-h+8),Vector2(hw+3,-h+11),Vector2(hw-4,-11),Vector2(hw-9,-11)]),Color(StorybookStyle.SHADOW_TINT,0.16))
    StorybookStyle.dab(self,Vector2(-hw+7,-h+13),Vector2(5,3),Color("#fff0c8",0.35))
    draw_line(Vector2(0,-h+12),Vector2(0,-12),clothes.darkened(0.22),1.6)
    draw_line(Vector2(-hw+5,-h+15),Vector2(-hw+7,-18),clothes.lightened(0.16),1.3)
    draw_colored_polygon(PackedVector2Array([Vector2(-7,-h+3),Vector2(0,-h+12),Vector2(7,-h+3),Vector2(3,-h-1),Vector2(-3,-h-1)]),StorybookStyle.CREAM)
    for i in range(3): draw_circle(Vector2(0,-h+19+float(i)*8),1.5,Color("#fff6e0"))

func _draw_head(ink: Color,skin: Color) -> void:
    var shape := clampi(int(appearance.get("head_shape",0)),0,3)
    var size := [21.0,23.0,20.0,22.0][shape]
    draw_circle(Vector2.ZERO,size+3.6,ink)
    draw_circle(Vector2(0,-1),size,skin)
    draw_circle(Vector2(-size+2,-2),5.0,skin.darkened(0.04))
    draw_circle(Vector2(size-2,-2),5.0,skin.darkened(0.04))
    draw_ellipse(Vector2(0,size*0.58),Vector2(size*0.62,size*0.26),Color(StorybookStyle.SHADOW_TINT,0.09))
    draw_ellipse(Vector2(-7,-12),Vector2(7,3),skin.lightened(0.16))

func _draw_hair(ink: Color,hair: Color) -> void:
    var style := int(appearance.get("hair_style",0))
    if style==1 or style==3:
        var points := [Vector2(-15,-13),Vector2(0,-17),Vector2(14,-12)] if style==1 else [Vector2(0,-17),Vector2(-12,-10),Vector2(12,-10)]
        for p in points:
            draw_circle(p,11.5,ink)
        for p in points:
            draw_circle(p+Vector2(0,-1),8.4,hair)
    elif style==2:
        draw_rect(Rect2(-24,-19,48,16),ink)
        draw_rect(Rect2(-20,-17,40,11),hair)
        draw_colored_polygon(PackedVector2Array([Vector2(-23,-6),Vector2(-12,-10),Vector2(-5,-4),Vector2(4,-10),Vector2(13,-4),Vector2(22,-7),Vector2(17,5),Vector2(-17,5)]),hair)
    elif style==4:
        draw_colored_polygon(PackedVector2Array([Vector2(-23,1),Vector2(-23,-19),Vector2(-10,-25),Vector2(0,-18),Vector2(11,-25),Vector2(23,-17),Vector2(21,4),Vector2(8,-2),Vector2(0,6),Vector2(-9,-2)]),ink)
        draw_colored_polygon(PackedVector2Array([Vector2(-19,-1),Vector2(-18,-16),Vector2(-9,-20),Vector2(0,-14),Vector2(10,-20),Vector2(18,-14),Vector2(17,0),Vector2(7,-5),Vector2(0,1),Vector2(-9,-5)]),hair)
    else:
        var cap := PackedVector2Array([Vector2(-21,5),Vector2(-22,-9),Vector2(-15,-20),Vector2(-5,-23),Vector2(3,-20),Vector2(12,-23),Vector2(22,-11),Vector2(21,5),Vector2(11,0),Vector2(3,4),Vector2(-5,0),Vector2(-13,5)])
        var outer := PackedVector2Array()
        for point in cap: outer.append(point*1.09)
        draw_colored_polygon(outer,ink)
        for i in range(cap.size()): cap[i]+=Vector2(1.5,1.5)
        draw_colored_polygon(cap,hair)
    draw_line(Vector2(-11,-19),Vector2(-3,-22),hair.lightened(0.28),2.2,true)
    draw_arc(Vector2(0,-7),18.0,PI+0.18,TAU-0.18,14,Color(ink,0.55),1.4)

func _draw_face(ink: Color,skin: Color,eyes: Color) -> void:
    if _view_direction == "back":
        return
    var style := int(appearance.get("face_style",0))
    var blush := Color("#ff7f9a",0.55)
    if _view_direction == "side":
        draw_circle(Vector2(8,-4),3.6,eyes)
        draw_circle(Vector2(9.2,-5.4),1.2,Color("#ffffff"))
        draw_line(Vector2(5,-13),Vector2(12,-12),ink,2.6,true)
        draw_ellipse(Vector2(10,8),Vector2(4.6,3.2),blush)
        draw_circle(Vector2(16,1),2.2,skin.darkened(0.1))
        draw_arc(Vector2(7,10),4.2,0.1,PI-0.2,8,ink,2.2)
        return
    draw_ellipse(Vector2(-14,9),Vector2(5.4,3.5),blush)
    draw_ellipse(Vector2(14,9),Vector2(5.4,3.5),blush)
    if _blink:
        draw_line(Vector2(-12,-5),Vector2(-4,-5),ink,2.8,true)
        draw_line(Vector2(4,-5),Vector2(12,-5),ink,2.8,true)
    elif style==1:
        draw_arc(Vector2(-8,-3),4.2,PI+0.3,TAU-0.3,8,ink,2.6)
        draw_arc(Vector2(8,-3),4.2,PI+0.3,TAU-0.3,8,ink,2.6)
    else:
        var radius := 4.2 if style==2 else 3.6
        draw_circle(Vector2(-8,-4),radius,eyes)
        draw_circle(Vector2(8,-4),radius,eyes)
        draw_circle(Vector2(-6.8,-5.4),1.3,Color("#ffffff"))
        draw_circle(Vector2(9.2,-5.4),1.3,Color("#ffffff"))
    draw_line(Vector2(-13,-12),Vector2(-4,-13.5),ink,2.6,true)
    draw_line(Vector2(4,-13.5),Vector2(13,-12),ink,2.6,true)
    draw_circle(Vector2(0,3),1.8,skin.darkened(0.1))
    if style%2==1:
        draw_ellipse(Vector2(0,11),Vector2(4.6,3.6),Color("#7a2f3a"))
        draw_ellipse(Vector2(0,12.6),Vector2(2.6,1.4),Color("#ff8a8a"))
    else:
        draw_arc(Vector2(0,9),5.2,0.15,PI-0.15,10,ink,2.2)

    var beard := int(appearance.get("facial_hair",0))
    var beard_colour := Color(str(appearance.get("hair","#5a3a2c")))
    if beard == 1:
        draw_arc(Vector2(0,9),10.0,0.15,PI-0.15,12,beard_colour,3.0)
    elif beard == 2:
        draw_colored_polygon(PackedVector2Array([Vector2(-10,7),Vector2(-8,16),Vector2(0,21),Vector2(8,16),Vector2(10,7)]),beard_colour)
    elif beard == 3:
        draw_line(Vector2(-13,4),Vector2(-5,10),beard_colour,3.0)
        draw_line(Vector2(13,4),Vector2(5,10),beard_colour,3.0)

func _draw_garment(ink: Color,base: Color) -> void:
    var style := int(appearance.get("outfit_style",0))
    var accent := Color(str(appearance.get("outfit_accent","#ffc233")))
    var hw := [12.0,15.0,13.0,17.0][clampi(int(appearance.get("body_shape",0)),0,3)]
    match style:
        0:
            draw_line(Vector2(-hw-2,-28),Vector2(hw+2,-28),accent.darkened(0.12),3.4)
            draw_rect(Rect2(-3,-31,6,6),accent)
        1:
            draw_colored_polygon(PackedVector2Array([Vector2(-hw-3,-37),Vector2(-hw-9,-27),Vector2(-7,-7),Vector2(0,-13),Vector2(7,-7),Vector2(hw+9,-27),Vector2(hw+3,-37)]),accent.darkened(0.08))
            draw_line(Vector2(-hw-2,-27),Vector2(-7,-9),accent.lightened(0.2),1.8)
            draw_line(Vector2(hw+2,-27),Vector2(7,-9),accent.lightened(0.2),1.8)
        2:
            draw_rect(Rect2(-hw-4,-35,hw*2+8,7),Color("#7a4a30"))
            draw_rect(Rect2(-4,-35,8,7),accent)
            draw_line(Vector2(-hw-2,-18),Vector2(hw+2,-18),base.lightened(0.2),2.4)
        3:
            draw_colored_polygon(PackedVector2Array([Vector2(-hw-3,-39),Vector2(-hw-8,-24),Vector2(-hw+1,-8),Vector2(hw-1,-8),Vector2(hw+8,-24),Vector2(hw+3,-39)]),accent)
            draw_line(Vector2(0,-34),Vector2(0,-10),accent.darkened(0.24),1.8)
        4:
            draw_rect(Rect2(-hw-2,-36,hw*2+4,10),StorybookStyle.CREAM)
            draw_rect(Rect2(-hw-2,-27,hw*2+4,4),accent)
            draw_line(Vector2(-hw,-20),Vector2(hw,-20),Color("#fff8e6"),1.6)
        5:
            draw_line(Vector2(-hw-5,-34),Vector2(-hw-8,-12),accent,5.5)
            draw_line(Vector2(hw+5,-34),Vector2(hw+8,-12),accent,5.5)
            draw_rect(Rect2(-hw-8,-35,hw*2+16,5),accent.darkened(0.18))

func _draw_headwear(ink: Color) -> void:
    var style := int(appearance.get("headwear",0))
    var accent := Color(str(appearance.get("outfit_accent","#ffc233")))
    if style == 1:
        StorybookStyle.outlined_rect(self,Rect2(-26,-16,52,8),Color("#9a5a3a"),ink,2.4,1,0.3)
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-18,-15),Vector2(-15,-28),Vector2(0,-34),Vector2(15,-28),Vector2(18,-15)]),Color("#e0a05e"),ink,2.4,2,0.4)
        draw_rect(Rect2(-17,-18,34,3),accent)
    elif style == 2:
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-25,-15),Vector2(-20,-31),Vector2(0,-38),Vector2(20,-31),Vector2(25,-15)]),Color("#4fb286"),ink,2.4,3,0.4)
        draw_rect(Rect2(-24,-17,48,4),accent)
    elif style == 3:
        draw_arc(Vector2(0,-16),23.0,PI,TAU,16,ink,8.6)
        draw_arc(Vector2(0,-16),23.0,PI,TAU,16,Color("#d08a50"),5.4)
        draw_line(Vector2(-23,-16),Vector2(23,-16),accent,2.6)
    elif style == 4:
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-20,-17),Vector2(-18,-35),Vector2(0,-42),Vector2(18,-35),Vector2(20,-17)]),Color("#5b82c8"),ink,2.4,4,0.4)
        draw_rect(Rect2(-20,-20,40,5),accent)
    elif style == 5:
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-12,-20),Vector2(-9,-36),Vector2(0,-41),Vector2(9,-36),Vector2(12,-20)]),Color("#f2d58e"),ink,2.4,5,0.4)
        StorybookStyle.outlined_ellipse(self,Vector2(0,-19),Vector2(21,5.5),Color("#f2d58e"),ink,2.4,6,0.4)
        draw_line(Vector2(-10,-21),Vector2(10,-21),accent,2.4)

func _draw_accessory(ink: Color) -> void:
    var item := int(appearance.get("accessory",0))
    if item==1:
        draw_arc(Vector2(0,-4),24.0,PI,TAU,16,ink,6.6)
        draw_arc(Vector2(0,-4),24.0,PI,TAU,16,Color("#d08a50"),4.0)
    elif item==2:
        draw_circle(Vector2(0,-20),6.4,ink)
        draw_circle(Vector2(0,-20),5.0,Color("#ffd23f"))
    elif item==3:
        draw_rect(Rect2(-25,-19,50,7),ink)
        draw_rect(Rect2(-24,-18,48,5),Color("#ffd23f"))
        draw_rect(Rect2(-4,-18,8,5),Color("#fff3d2"))
    elif item==4:
        draw_circle(Vector2(0,-18),5.4,ink)
        draw_circle(Vector2(0,-18),4.0,Color("#ff6f59"))
    elif item==5:
        draw_line(Vector2(-24,-1),Vector2(24,-1),ink,5.4)
        draw_line(Vector2(-24,-1),Vector2(24,-1),Color("#d08a50"),3.0)

func draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var a := TAU*float(i)/20.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
