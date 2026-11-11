extends Node2D
## Independent room furniture; node origin is the ground-contact/Y-sort point.
## Storybook style: every filled shape gets a warm crayon outline (see _rect/_poly),
## and manifest colours are graded a little brighter via StorybookStyle.vivid.
const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var definition: Dictionary = {}

func configure(data: Dictionary) -> void:
    if definition == data:
        return
    definition = data.duplicate(true)
    position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",560.0)))
    z_index = int(definition.get("z_index",0))
    queue_redraw()

func _colour(value: Variant,fallback: Color) -> Color:
    var colour: Color = value if value is Color else Color(str(value))
    return StorybookStyle.vivid(colour,0.8)

# Filled shapes with a crayon outline. Tiny details skip the outline so books,
# knobs and seams stay readable at game scale.
func _rect(rect: Rect2,colour: Color) -> void:
    draw_rect(rect,colour)
    if colour.a >= 0.99 and minf(rect.size.x,rect.size.y) >= 8.0:
        draw_rect(rect,StorybookStyle.OUTLINE,false,2.0)

func _poly(points: PackedVector2Array,colour: Color) -> void:
    draw_colored_polygon(points,colour)
    if colour.a >= 0.99:
        var edge := points.duplicate()
        edge.append(points[0])
        draw_polyline(edge,StorybookStyle.OUTLINE,2.0,true)

func _draw() -> void:
    var kind := str(definition.get("kind","table"))
    var w := maxf(float(definition.get("width",120.0)),24.0)
    var h := maxf(float(definition.get("height",56.0)),12.0)
    var d := maxf(float(definition.get("depth",54.0)),12.0)
    var wood := _colour(definition.get("material","#76553b"),Color("#76553b"))
    var trim := _colour(definition.get("accent","#c6a574"),Color("#c6a574"))
    var secondary := _colour(definition.get("secondary",wood.lightened(0.16)),wood.lightened(0.16))
    var upholstery := _colour(definition.get("upholstery","#a98a6e"),Color("#a98a6e"))
    var wear := clampf(float(definition.get("wear",0.12)),0.0,0.8)
    var finish := str(definition.get("finish","natural"))
    if str(definition.get("material_style","wood")) == "painted" and finish == "natural":
        finish = "painted"
    match kind:
        "rug": _rug(w,d,wood,trim,secondary)
        "chair","armchair","sofa": _seat(kind,w,h,d,wood,trim,upholstery)
        "stool": _stool(w,h,d,wood,trim,upholstery)
        "cabinet","sideboard": _cabinet(w,h,d,wood,trim,secondary)
        "floor_lamp": _floor_lamp(w,h,d,wood,trim)
        "coat_stand": _coat_stand(w,h,d,wood,trim)
        "bookcase","shelf","bread_rack": _shelf(kind,w,h,wood,trim,secondary)
        "oven","hearth": _hearth(w,h,wood,trim)
        "barrel": _barrel(w,h,d,wood,trim)
        "plant": _plant(w,h,d,wood,trim)
        "basket": _basket(w,h,wood,trim)
        _:
            _table(kind,w,h,d,wood,trim,secondary,wear,finish)

func _table(kind:String,w:float,h:float,d:float,wood:Color,trim:Color,secondary:Color,wear:float,finish:String)->void:
    _shadow(w,d)
    for x in [-w*0.39,w*0.31]:
        _rect(Rect2(x,-h*0.48,9,h*0.48),wood.darkened(0.2))
    _rect(Rect2(-w*0.5,-h+d*0.22,w,h-d*0.22),wood.darkened(0.17))
    _poly(PackedVector2Array([Vector2(-w*0.5,-h+d*0.22),Vector2(-w*0.5+d*0.45,-h),Vector2(w*0.5+d*0.45,-h),Vector2(w*0.5,-h+d*0.22)]),wood.lightened(0.16))
    _poly(PackedVector2Array([Vector2(w*0.5,-h+d*0.22),Vector2(w*0.5+d*0.45,-h),Vector2(w*0.5+d*0.45,d*0.12),Vector2(w*0.5,0)]),wood.darkened(0.28))
    draw_line(Vector2(-w*0.46,-h+d*0.25),Vector2(w*0.46,-h+d*0.25),trim,2.0)
    if finish != "painted":
        for grain in range(3):
            var gy := -h+8.0+float(grain)*maxf(d*0.08,3.0)
            draw_line(Vector2(-w*0.38,gy),Vector2(w*0.38,gy+1.5),secondary.darkened(wear*0.2),1.0)
    if kind in ["desk","counter","bar_counter","workbench"]:
        for i in range(2):
            var dx := -w*0.27+float(i)*w*0.48
            _rect(Rect2(dx,-h*0.55,w*0.20,h*0.16),wood.lightened(0.04))
            _rect(Rect2(dx+2.0,-h*0.54,w*0.16,h*0.10),wood.darkened(0.06))
            draw_circle(Vector2(dx+w*0.1,-h*0.47),2.0,trim)
    if kind in ["table","counter","side_table"]:
        _ellipse(Vector2(-w*0.18,-h-2),Vector2(9,4),trim)
        _ellipse(Vector2(w*0.16,-h-5),Vector2(7,3),Color("#e4d1a7"))

func _seat(kind:String,w:float,h:float,d:float,wood:Color,trim:Color,upholstery:Color)->void:
    _shadow(w,d)
    var back_height := h*0.72
    _rect(Rect2(-w*0.46,-h,w*0.92,back_height),wood.darkened(0.12))
    _rect(Rect2(-w*0.40,-h+6,w*0.80,back_height-12),upholstery.darkened(0.12))
    if kind == "sofa":
        _rect(Rect2(-w*0.50,-h*0.55,w*0.16,h*0.55),wood)
        _rect(Rect2(w*0.34,-h*0.55,w*0.16,h*0.55),wood)
        for cushion in range(2):
            var cx := -w*0.30+float(cushion)*w*0.30
            _poly(PackedVector2Array([Vector2(cx,-h*0.40),Vector2(cx+d*0.22,-h*0.55),Vector2(cx+w*0.28,-h*0.55),Vector2(cx+w*0.22,-h*0.40)]),upholstery.lightened(0.08))
            draw_line(Vector2(cx+w*0.12,-h*0.48),Vector2(cx+w*0.22,-h*0.48),upholstery.darkened(0.12),1.2)
    else:
        _poly(PackedVector2Array([Vector2(-w*0.40,-h*0.40),Vector2(-w*0.40+d*0.20,-h*0.55),Vector2(w*0.40+d*0.20,-h*0.55),Vector2(w*0.40,-h*0.40)]),upholstery)
        draw_line(Vector2(-w*0.24,-h*0.46),Vector2(w*0.24,-h*0.46),upholstery.lightened(0.15),1.0)
    for side in [-1.0,1.0]:
        _rect(Rect2(side*w*0.34-4.0,-h*0.38,8.0,h*0.34),wood.darkened(0.18))
        _rect(Rect2(side*w*0.34-5.0,-h*0.40,10.0,5.0),trim)
        _rect(Rect2(side*w*0.34-3.0,-h*0.12,6.0,h*0.12),wood.darkened(0.24))

func _stool(w:float,h:float,d:float,wood:Color,trim:Color,upholstery:Color)->void:
    _shadow(w,d)
    for side in [-1.0,1.0]:
        draw_line(Vector2(side*w*0.28,-h*0.42),Vector2(side*w*0.36,0),wood.darkened(0.22),6.0)
    _rect(Rect2(-w*0.43,-h*0.48,w*0.86,h*0.16),wood.darkened(0.14))
    _poly(PackedVector2Array([Vector2(-w*0.5,-h*0.48),Vector2(-w*0.36,-h*0.68),Vector2(w*0.36,-h*0.68),Vector2(w*0.5,-h*0.48)]),wood.lightened(0.16))
    draw_line(Vector2(-w*0.32,-h*0.53),Vector2(w*0.32,-h*0.53),trim,2.0)
    _ellipse(Vector2(0,-h*0.66),Vector2(w*0.31,d*0.12),upholstery)

func _cabinet(w:float,h:float,d:float,wood:Color,trim:Color,secondary:Color)->void:
    _shadow(w,d)
    _rect(Rect2(-w*0.5,-h,w,h),wood.darkened(0.16))
    _rect(Rect2(-w*0.45,-h+7,w*0.90,h-14),wood)
    _rect(Rect2(-w*0.50,-h,w,8),trim)
    for door in range(2):
        var dx := -w*0.40+float(door)*w*0.42
        draw_rect(Rect2(dx,-h+18,w*0.38,h-38),secondary.darkened(0.10),false,2.0)
        draw_line(Vector2(dx+6,-h+25),Vector2(dx+w*0.38-6,-h+25),secondary,1.0)
        draw_circle(Vector2(dx+w*0.31,-h*0.52),2.4,trim)
    _rect(Rect2(-w*0.53,-h-5,w*1.06,7),wood.lightened(0.18))

func _floor_lamp(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    _ellipse(Vector2(0,-3),Vector2(w*0.42,d*0.18),wood.darkened(0.18))
    _rect(Rect2(-3.0,-h*0.72,6.0,h*0.68),wood)
    _poly(PackedVector2Array([Vector2(-w*0.48,-h*0.68),Vector2(-w*0.30,-h),Vector2(w*0.30,-h),Vector2(w*0.48,-h*0.68)]),trim)
    _ellipse(Vector2(0,-h*0.88),Vector2(w*0.17,5.0),Color("#f6dfa8",0.72))
    draw_line(Vector2(-w*0.30,-h*0.70),Vector2(w*0.30,-h*0.70),trim.darkened(0.18),1.2)

func _coat_stand(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    _ellipse(Vector2(0,-2),Vector2(w*0.44,d*0.18),wood.darkened(0.18))
    _rect(Rect2(-3.0,-h*0.82,6.0,h*0.82),wood)
    draw_line(Vector2(0,-h*0.82),Vector2(-w*0.42,-h*0.66),wood,5.0)
    draw_line(Vector2(0,-h*0.82),Vector2(w*0.42,-h*0.66),wood,5.0)
    draw_line(Vector2(0,-h*0.82),Vector2(0,-h),wood,5.0)
    for side in [-1.0,1.0]:
        draw_circle(Vector2(side*w*0.42,-h*0.66),4.0,trim)

func _shelf(kind:String,w:float,h:float,wood:Color,trim:Color,secondary:Color)->void:
    _shadow(w,55.0)
    _rect(Rect2(-w*0.5,-h,w,h),wood.darkened(0.12))
    _rect(Rect2(-w*0.44,-h+6,w*0.88,h-12),Color("#7a5238"))
    var rows := 2 if kind == "bread_rack" else 3
    for row in range(rows):
        var y := -h+float(row+1)*h/float(rows+1)
        _rect(Rect2(-w*0.46,y,w*0.92,7),wood.lightened(0.12))
        var count := maxi(int(w/30.0),2)
        for col in range(count):
            var x := -w*0.4+float(col)*w*0.78/float(count)
            if kind == "bread_rack":
                _ellipse(Vector2(x+10,y-10),Vector2(11,6),Color("#b77b42"))
                draw_line(Vector2(x+5,y-11),Vector2(x+14,y-12),Color("#e5c38b"),1.2)
            else:
                var colours := [trim,Color("#b66f53"),secondary,Color("#d5bd8d")]
                _rect(Rect2(x,y-23,14,20),colours[(row+col)%colours.size()])
                _rect(Rect2(x+2,y-21,10,3),Color("#fff1d6",0.55))

func _hearth(w:float,h:float,wood:Color,trim:Color)->void:
    _shadow(w,75.0)
    _rect(Rect2(-w*0.5,-h,w,h),wood.darkened(0.18))
    _rect(Rect2(-w*0.42,-h+8,w*0.84,h-8),wood)
    _rect(Rect2(-w*0.28,-h*0.62,w*0.56,h*0.55),Color("#6b4630"))
    draw_arc(Vector2(0,-h*0.3),w*0.28,PI,TAU,24,trim,5.0)
    _poly(PackedVector2Array([Vector2(-w*0.12,-h*0.12),Vector2(0,-h*0.52),Vector2(w*0.15,-h*0.12)]),Color("#e7a15d",0.9))
    draw_circle(Vector2(0,-h*0.28),w*0.09,Color("#f4c779",0.55))
    _rect(Rect2(-w*0.55,-8,w*1.1,8),wood.darkened(0.3))

func _barrel(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    _rect(Rect2(-w*0.42,-h,w*0.84,h),wood.darkened(0.12))
    _ellipse(Vector2(0,-h),Vector2(w*0.42,d*0.28),wood.lightened(0.15))
    for y in [-h*0.78,-h*0.24]:
        draw_line(Vector2(-w*0.4,y),Vector2(w*0.4,y),trim,4.0)

func _plant(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    _poly(PackedVector2Array([Vector2(-w*0.42,-h*0.32),Vector2(w*0.42,-h*0.32),Vector2(w*0.3,0),Vector2(-w*0.3,0)]),wood)
    _rect(Rect2(-w*0.46,-h*0.38,w*0.92,h*0.08),trim)
    for i in range(5):
        var x := float(i-2)*w*0.12
        draw_line(Vector2(0,-h*0.34),Vector2(x,-h*0.7),Color("#4e7357"),3.0)
        _ellipse(Vector2(x,-h*0.74),Vector2(w*0.12,h*0.09),Color("#71906a"))

func _basket(w:float,h:float,wood:Color,trim:Color)->void:
    _shadow(w,45.0)
    _poly(PackedVector2Array([Vector2(-w*0.5,-h),Vector2(w*0.5,-h),Vector2(w*0.4,0),Vector2(-w*0.4,0)]),wood)
    for i in range(4):
        draw_line(Vector2(-w*0.4,-h+float(i)*h*0.22),Vector2(w*0.4,-h+float(i)*h*0.22),trim,2.0)
    draw_arc(Vector2(0,-h),w*0.32,PI,TAU,16,trim,3.0)

func _rug(w:float,d:float,wood:Color,trim:Color,secondary:Color)->void:
    var p := PackedVector2Array([Vector2(-w*0.5,-d*0.35),Vector2(-w*0.36,-d),Vector2(w*0.5,-d),Vector2(w*0.36,-d*0.35)])
    _poly(p,wood)
    _poly(PackedVector2Array([Vector2(-w*0.40,-d*0.42),Vector2(-w*0.30,-d*0.90),Vector2(w*0.40,-d*0.90),Vector2(w*0.30,-d*0.42)]),secondary)
    draw_polyline(PackedVector2Array([p[0],p[1],p[2],p[3],p[0]]),trim,3.0,true)
    draw_line(Vector2(-w*0.25,-d*0.54),Vector2(w*0.25,-d*0.54),trim,2.0)
    for fringe in range(5):
        var x := -w*0.32+float(fringe)*w*0.16
        draw_line(Vector2(x,-d*0.96),Vector2(x+2.0,-d*1.04),trim,1.2)

func _shadow(w:float,d:float)->void:
    StorybookStyle.blob_shadow(self,Vector2(5,3),w*0.58,clampf(d*0.32/maxf(w*0.58,1.0),0.1,0.5),0.22)

func _ellipse(center:Vector2,radius:Vector2,colour:Color)->void:
    var points := StorybookStyle.ellipse_points(center,radius,24)
    draw_colored_polygon(points,colour)
    if colour.a >= 0.99 and minf(radius.x,radius.y) >= 4.0:
        var edge := points.duplicate()
        edge.append(points[0])
        draw_polyline(edge,StorybookStyle.OUTLINE,1.8,true)
