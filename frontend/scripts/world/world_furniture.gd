extends Node2D
## Independent room furniture; the node origin is its ground-contact/Y-sort point.
var definition: Dictionary = {}

func configure(data: Dictionary) -> void:
    if definition==data: return
    definition=data.duplicate(true)
    position=Vector2(float(definition.get("x",0.0)),float(definition.get("y",560.0)))
    queue_redraw()

func _draw() -> void:
    var kind:=str(definition.get("kind","table"))
    var w:=float(definition.get("width",120.0))
    var h:=float(definition.get("height",56.0))
    var d:=float(definition.get("depth",54.0))
    var wood:=Color(str(definition.get("material","#76553b")))
    var trim:=Color(str(definition.get("accent","#c6a574")))
    match kind:
        "rug": _rug(w,d,wood,trim)
        "chair": _chair(w,h,d,wood,trim)
        "bookcase","shelf","bread_rack": _shelf(kind,w,h,wood,trim)
        "oven","hearth": _hearth(w,h,wood,trim)
        "barrel": _barrel(w,h,d,wood,trim)
        "plant": _plant(w,h,d,wood,trim)
        "basket": _basket(w,h,wood,trim)
        _: _table(kind,w,h,d,wood,trim)

func _table(kind:String,w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    for x in [-w*0.39,w*0.31]:
        draw_rect(Rect2(x,-h*0.48,9,h*0.48),wood.darkened(0.2))
    draw_rect(Rect2(-w*0.5,-h+d*0.22,w,h-d*0.22),wood.darkened(0.17))
    draw_colored_polygon(PackedVector2Array([Vector2(-w*0.5,-h+d*0.22),Vector2(-w*0.5+d*0.45,-h),Vector2(w*0.5+d*0.45,-h),Vector2(w*0.5,-h+d*0.22)]),wood.lightened(0.16))
    draw_colored_polygon(PackedVector2Array([Vector2(w*0.5,-h+d*0.22),Vector2(w*0.5+d*0.45,-h),Vector2(w*0.5+d*0.45,d*0.12),Vector2(w*0.5,0)]),wood.darkened(0.28))
    draw_line(Vector2(-w*0.46,-h+d*0.25),Vector2(w*0.46,-h+d*0.25),trim,2.0)
    if kind in ["desk","counter","bar_counter","workbench"]:
        for i in range(2):
            var dx:=-w*0.27+float(i)*w*0.48
            draw_rect(Rect2(dx,-h*0.55,w*0.20,h*0.16),wood.lightened(0.04))
            draw_circle(Vector2(dx+w*0.1,-h*0.47),2.0,trim)
    if kind=="table" or kind=="counter":
        _ellipse(Vector2(-w*0.18,-h-2),Vector2(9,4),trim)
        _ellipse(Vector2(w*0.16,-h-5),Vector2(7,3),Color("#e4d1a7"))

func _chair(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    draw_rect(Rect2(-w*0.38,-h*0.4,7,h*0.4),wood.darkened(0.2))
    draw_rect(Rect2(w*0.3,-h*0.4,7,h*0.4),wood.darkened(0.2))
    draw_rect(Rect2(-w*0.48,-h,w*0.96,h*0.62),wood.darkened(0.12))
    draw_rect(Rect2(-w*0.43,-h*0.94,w*0.86,h*0.48),wood)
    for i in range(3): draw_rect(Rect2(-w*0.32+float(i)*w*0.25,-h*0.9,w*0.12,h*0.36),trim.darkened(0.12))
    draw_colored_polygon(PackedVector2Array([Vector2(-w*0.48,-h*0.38),Vector2(-w*0.48+d*0.35,-h*0.55),Vector2(w*0.48+d*0.35,-h*0.55),Vector2(w*0.48,-h*0.38)]),wood.lightened(0.12))

func _shelf(kind:String,w:float,h:float,wood:Color,trim:Color)->void:
    _shadow(w,55)
    draw_rect(Rect2(-w*0.5,-h,w,h),wood.darkened(0.12))
    draw_rect(Rect2(-w*0.44,-h+6,w*0.88,h-12),Color("#493c35"))
    var rows:=2 if kind=="bread_rack" else 3
    for row in range(rows):
        var y:=-h+float(row+1)*h/float(rows+1)
        draw_rect(Rect2(-w*0.46,y,w*0.92,7),wood.lightened(0.12))
        var count:=maxi(int(w/30.0),2)
        for col in range(count):
            var x:=-w*0.4+float(col)*w*0.78/float(count)
            if kind=="bread_rack":
                _ellipse(Vector2(x+10,y-10),Vector2(11,6),Color("#b77b42"))
                draw_line(Vector2(x+5,y-11),Vector2(x+14,y-12),Color("#e5c38b"),1.2)
            else:
                draw_rect(Rect2(x,y-23,14,20),[trim,Color("#b66f53"),Color("#8b9b7a"),Color("#d5bd8d")][(row+col)%4])

func _hearth(w:float,h:float,wood:Color,trim:Color)->void:
    _shadow(w,75)
    draw_rect(Rect2(-w*0.5,-h,w,h),wood.darkened(0.18))
    draw_rect(Rect2(-w*0.42,-h+8,w*0.84,h-8),wood)
    draw_rect(Rect2(-w*0.28,-h*0.62,w*0.56,h*0.55),Color("#42352f"))
    draw_arc(Vector2(0,-h*0.3),w*0.28,PI,TAU,24,trim,5.0)
    draw_colored_polygon(PackedVector2Array([Vector2(-w*0.12,-h*0.12),Vector2(0,-h*0.52),Vector2(w*0.15,-h*0.12)]),Color("#e7a15d",0.9))
    draw_circle(Vector2(0,-h*0.28),w*0.09,Color("#f4c779",0.55))
    draw_rect(Rect2(-w*0.55,-8,w*1.1,8),wood.darkened(0.3))

func _barrel(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    draw_rect(Rect2(-w*0.42,-h,w*0.84,h),wood.darkened(0.12))
    _ellipse(Vector2(0,-h),Vector2(w*0.42,d*0.28),wood.lightened(0.15))
    for y in [-h*0.78,-h*0.24]: draw_line(Vector2(-w*0.4,y),Vector2(w*0.4,y),trim,4.0)

func _plant(w:float,h:float,d:float,wood:Color,trim:Color)->void:
    _shadow(w,d)
    draw_colored_polygon(PackedVector2Array([Vector2(-w*0.42,-h*0.32),Vector2(w*0.42,-h*0.32),Vector2(w*0.3,0),Vector2(-w*0.3,0)]),wood)
    draw_rect(Rect2(-w*0.46,-h*0.38,w*0.92,h*0.08),trim)
    for i in range(5):
        var x:=float(i-2)*w*0.12
        draw_line(Vector2(0,-h*0.34),Vector2(x,-h*0.7),Color("#4e7357"),3.0)
        _ellipse(Vector2(x,-h*0.74),Vector2(w*0.12,h*0.09),Color("#71906a"))

func _basket(w:float,h:float,wood:Color,trim:Color)->void:
    _shadow(w,45)
    draw_colored_polygon(PackedVector2Array([Vector2(-w*0.5,-h),Vector2(w*0.5,-h),Vector2(w*0.4,0),Vector2(-w*0.4,0)]),wood)
    for i in range(4): draw_line(Vector2(-w*0.4,-h+float(i)*h*0.22),Vector2(w*0.4,-h+float(i)*h*0.22),trim,2.0)
    draw_arc(Vector2(0,-h),w*0.32,PI,TAU,16,trim,3.0)

func _rug(w:float,d:float,wood:Color,trim:Color)->void:
    var p:=PackedVector2Array([Vector2(-w*0.5,-d*0.35),Vector2(-w*0.36,-d),Vector2(w*0.5,-d),Vector2(w*0.36,-d*0.35)])
    draw_colored_polygon(p,wood)
    draw_polyline(PackedVector2Array([p[0],p[1],p[2],p[3],p[0]]),trim,3.0,true)
    draw_line(Vector2(-w*0.25,-d*0.52),Vector2(w*0.25,-d*0.52),trim,2.0)

func _shadow(w:float,d:float)->void:
    _ellipse(Vector2(5,3),Vector2(w*0.58,d*0.32),Color("#403a32",0.17))

func _ellipse(center:Vector2,radius:Vector2,colour:Color)->void:
    var points:=PackedVector2Array()
    for i in range(24):
        var a:=TAU*float(i)/24.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
