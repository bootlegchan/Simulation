extends Node2D
## Independently refreshed outdoor weather and sky atmosphere.
var _state: Dictionary = {}

func configure(state: Dictionary) -> void:
    _state = state.duplicate(true)
    var room: Dictionary = _state.get("room_manifest",{})
    var outdoors := str(room.get("scene_kind","outdoor")) != "interior"
    visible = outdoors
    set_process(outdoors)
    queue_redraw()

func _process(_delta: float) -> void:
    queue_redraw()

func _draw() -> void:
    var climate: Dictionary = _state.get("climate",{})
    var precipitation := str(climate.get("precipitation","CLEAR")).to_upper()
    var hour := int(_state.get("status",{}).get("hour",10))
    var width := float(_state.get("world_width",3600.0))
    var t := float(Time.get_ticks_msec()) / 1000.0

    # Time-of-day lighting is handled by WorldLighting/CanvasModulate. This pass
    # is reserved for atmosphere that belongs in front of the world geometry.
    if hour < 5 or hour >= 21:
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#17273c",0.12))
        for i in range(22):
            var sx := float((i*173+41)%int(maxf(width,1.0)))
            var sy := float((i*83+29)%310)
            draw_circle(Vector2(sx,sy),1.4,Color("#fff0c4",0.72))
        for i in range(12):
            var fx := float((i*277+int(t*16.0))%int(maxf(width,1.0)))
            var fy := 460.0+sin(t*1.7+float(i))*42.0
            draw_circle(Vector2(fx,fy),3.0,Color("#f4d98a",0.8))
            draw_circle(Vector2(fx,fy),7.0,Color("#f4d98a",0.14))
    elif hour < 8 or hour >= 17:
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#d98f72",0.06))
    elif hour >= 11 and hour <= 15:
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#fff1c9",0.02))

    # Slow drifting clouds and distant birds add gentle life to quiet scenes.
    for i in range(4):
        var cx := fposmod(float(i)*890.0+t*13.0,width+220.0)-110.0
        var cy := 110.0+float((i*43)%90)
        var cloud := Color("#fff8e8",0.34) if precipitation == "CLEAR" else Color("#d7ded8",0.28)
        _draw_ellipse(Vector2(cx,cy),Vector2(54,15),cloud)
        _draw_ellipse(Vector2(cx+34,cy-8),Vector2(38,18),cloud)
        _draw_ellipse(Vector2(cx+67,cy),Vector2(47,13),cloud)
    for i in range(5):
        var bx := fposmod(float(i)*710.0+t*27.0,width+80.0)-40.0
        var by := 190.0+sin(t*1.3+float(i))*16.0
        draw_arc(Vector2(bx,by),9.0,PI+0.25,TAU-0.25,8,Color("#46554d",0.58),1.8)
        draw_arc(Vector2(bx+15,by),9.0,PI+0.25,TAU-0.25,8,Color("#46554d",0.58),1.8)

    if precipitation in ["CLOUDY","OVERCAST"]:
        var cloud_tint := Color("#63727a",0.10) if precipitation == "CLOUDY" else Color("#4f5c65",0.20)
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),cloud_tint)
    if precipitation in ["RAIN","SLEET","SNOW","BLIZZARD"]:
        for i in range(120):
            var x := float((i*137+int(Time.get_ticks_msec()/22))%int(maxf(width,1.0)))
            var y := float((i*71+int(Time.get_ticks_msec()/13))%560)
            if precipitation == "SNOW" or precipitation == "BLIZZARD":
                draw_circle(Vector2(x,y),1.8,Color("#f1f3e8",0.78))
            else:
                draw_line(Vector2(x,y),Vector2(x-8,y+22),Color("#c5d4df",0.48),1.5)
    if precipitation == "FOG":
        draw_rect(Rect2(0,280,width,440),Color("#d8e0d9",0.30))
        for i in range(5):
            var fog_y := 360.0+float(i)*62.0+sin(t+float(i))*10.0
            draw_rect(Rect2(0,fog_y,width,34),Color("#e8e8dc",0.13))


func _draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(24):
        var angle := TAU*float(i)/24.0
        points.append(center+Vector2(cos(angle)*radius.x,sin(angle)*radius.y))
    draw_colored_polygon(points,colour)
