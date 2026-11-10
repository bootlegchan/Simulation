extends Node2D
## A building is an independent world object, not part of the background plate.
## Position, footprint, palette and silhouette come from the presentation manifest.

var definition: Dictionary = {}
var _occluder: LightOccluder2D

func configure(data: Dictionary) -> void:
    definition = data.duplicate(true)
    position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",0.0)))
    queue_redraw()
    _configure_occluder()

func _configure_occluder() -> void:
    if _occluder:
        _occluder.queue_free()
    if str(definition.get("style","")).begins_with("interior_"):
        return
    _occluder = LightOccluder2D.new()
    var polygon := OccluderPolygon2D.new()
    var w := float(definition.get("width",260.0))
    var h := float(definition.get("height",260.0))
    polygon.polygon = PackedVector2Array([
        Vector2(-w*0.08,-h*0.28),Vector2(0,-h*0.58),
        Vector2(w*0.5,-h*0.58),Vector2(w*1.08,-h*0.28),
        Vector2(w,h),Vector2(0,h)
    ])
    _occluder.occluder = polygon
    add_child(_occluder)

func _draw() -> void:
    var w := float(definition.get("width",260.0))
    var h := float(definition.get("height",260.0))
    var wall := Color(str(definition.get("wall","#d8c8a8")))
    var roof := Color(str(definition.get("roof","#6e5949")))
    var ink := Color("#4f493e")
    var style := str(definition.get("style","house"))
    if style.begins_with("interior_"):
        _draw_interior(w,h,style)
        return
    # Contact shadow and an offset cast shadow anchor the silhouette to the ground.
    draw_colored_polygon(PackedVector2Array([
        Vector2(-24,h+12),Vector2(w*0.5-5,-h*0.52+20),
        Vector2(w+42,h+20),Vector2(w+65,h+36),Vector2(-6,h+36)
    ]),Color("#403a32",0.18))
    draw_colored_polygon(PackedVector2Array([
        Vector2(-24,8),Vector2(0,-h*0.28),Vector2(w*0.5,-h*0.58),
        Vector2(w+24,-h*0.28),Vector2(w+12,12)
    ]),roof)
    draw_rect(Rect2(0,0,w,h),wall)
    draw_rect(Rect2(14,14,w-28,28),wall.lightened(0.12))
    draw_rect(Rect2(24,42,w-48,24),roof.darkened(0.08))
    draw_string(ThemeDB.fallback_font,Vector2(34,61),str(definition.get("label","BUILDING")).to_upper(),HORIZONTAL_ALIGNMENT_LEFT,w-68,16,ink)
    for wx in [34.0,w-94.0]:
        draw_rect(Rect2(wx,100,60,76),Color("#5b6f69"))
        draw_rect(Rect2(wx+6,106,48,64),Color("#c6d0b4"))
        draw_line(Vector2(wx+30,106),Vector2(wx+30,170),ink,3.0)
        draw_line(Vector2(wx+6,138),Vector2(wx+54,138),ink,2.0)
        draw_rect(Rect2(wx-5,174,70,7),roof)
    var door_x := w*0.5-35
    draw_rect(Rect2(door_x,h-118,70,118),Color("#614b3b"))
    draw_rect(Rect2(door_x+7,h-111,56,111),Color("#927253"))
    draw_circle(Vector2(door_x+50,h-58),4.0,Color("#d7b46f"))
    # Roof eaves and corner timber add depth without baking the building into scenery.
    draw_rect(Rect2(-8,8,w+16,9),roof.darkened(0.12))
    draw_rect(Rect2(0,0,10,h),roof.darkened(0.12))
    draw_rect(Rect2(w-10,0,10,h),roof.darkened(0.12))

func _draw_interior(w: float,h: float,style: String) -> void:
    var wood := Color("#76553b")
    if style == "interior_civic":
        draw_rect(Rect2(0,0,w,h),Color("#e8d9bd"))
        draw_rect(Rect2(70,170,480,24),wood)
        draw_rect(Rect2(100,194,20,130),wood)
        draw_rect(Rect2(500,194,20,130),wood)
        draw_rect(Rect2(650,40,220,180),wood)
        for row in range(3):
            for col in range(5):
                draw_rect(Rect2(665+float(col)*40,52+float(row)*52,28,42),Color("#d0b48a"))
    elif style == "interior_shop":
        draw_rect(Rect2(0,0,w,h),Color("#e8d9bd"))
        for row in range(3):
            draw_rect(Rect2(80,80+float(row)*90,w-160,12),wood)
            for col in range(12):
                draw_rect(Rect2(105+float(col)*65,38+float(row)*90,36,42),[Color("#c57d56"),Color("#d4b66f"),Color("#8da28a")][col%3])
        draw_rect(Rect2(280,270,500,32),wood)
    elif style == "interior_bakery":
        draw_rect(Rect2(0,0,w,h),Color("#e8d9bd"))
        draw_rect(Rect2(650,30,270,260),Color("#b66e4c"))
        draw_circle(Vector2(785,170),78,Color("#6e4838"))
        draw_circle(Vector2(785,170),55,Color("#292c2b"))
        draw_rect(Rect2(160,260,480,28),wood)
        for i in range(5):
            draw_circle(Vector2(220+float(i)*80,250),12,Color("#d8a65f"))
    else:
        draw_rect(Rect2(0,0,w,h),Color("#d8c9ae"))
        draw_rect(Rect2(620,40,300,250),wood)
        draw_rect(Rect2(650,90,240,200),Color("#292c2b"))
        draw_colored_polygon(PackedVector2Array([Vector2(700,290),Vector2(770,150),Vector2(840,290)]),Color("#e9a25f"))
        for x in [100.0,380.0]:
            draw_rect(Rect2(x,240,190,18),wood)
            draw_rect(Rect2(x+15,258,14,65),wood)
            draw_rect(Rect2(x+160,258,14,65),wood)
