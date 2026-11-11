extends Node2D
## Independently refreshed outdoor weather and sky atmosphere, drawn in the
## shared storybook style (chunky outlined clouds, sparkle stars, soft weather).

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")
const WORLD_HEIGHT := 720.0

var _state: Dictionary = {}

func configure(state: Dictionary) -> void:
    _state = state.duplicate(true)
    var room: Dictionary = _state.get("room_manifest",{})
    var outdoors := str(room.get("scene_kind","outdoor")) != "interior"
    z_index = 50
    visible = outdoors
    set_process(outdoors)
    queue_redraw()

func _process(_delta: float) -> void:
    queue_redraw()

func _sparkle(center: Vector2,size: float,colour: Color) -> void:
    draw_colored_polygon(PackedVector2Array([
        center+Vector2(0,-size),center+Vector2(size*0.28,-size*0.28),
        center+Vector2(size,0),center+Vector2(size*0.28,size*0.28),
        center+Vector2(0,size),center+Vector2(-size*0.28,size*0.28),
        center+Vector2(-size,0),center+Vector2(-size*0.28,-size*0.28)
    ]),colour)

func _draw() -> void:
    var climate: Dictionary = _state.get("climate",{})
    var precipitation := str(climate.get("precipitation","CLEAR")).to_upper()
    var hour := int(_state.get("status",{}).get("hour",10))
    var width := float(_state.get("world_width",3600.0))
    var t := float(Time.get_ticks_msec()) / 1000.0

    # Time-of-day grading itself is handled by WorldLighting/CanvasModulate. This
    # pass only adds atmosphere that belongs in front of the world geometry.
    if hour < 5 or hour >= 21:
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#2a2f7a",0.1))
        for i in range(22):
            var sx := float((i*173+41)%int(maxf(width,1.0)))
            var sy := float((i*83+29)%240)+20.0
            var twinkle := 0.7+0.3*sin(t*2.0+float(i))
            _sparkle(Vector2(sx,sy),4.0+float(i%3)*1.6,Color("#fff3b0",twinkle))
        for i in range(12):
            var fx := float((i*277+int(t*16.0))%int(maxf(width,1.0)))
            var fy := 460.0+sin(t*1.7+float(i))*42.0
            draw_circle(Vector2(fx,fy),9.0,Color("#fff08a",0.18))
            draw_circle(Vector2(fx,fy),4.2,StorybookStyle.OUTLINE)
            draw_circle(Vector2(fx,fy),3.0,Color("#fff08a"))
    elif hour < 8 or hour >= 17:
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),Color("#ff9a70",0.07))

    # Big puffy clouds drift slowly; they dim and turn blue-grey in poor weather.
    var clear := precipitation == "CLEAR"
    var cloud_fill := Color("#ffffff") if clear else Color("#dfe7ef")
    var cloud_count := 5 if clear else 7
    for i in range(cloud_count):
        var cx := fposmod(float(i)*760.0+t*(11.0+float(i%3)*3.0),width+300.0)-150.0
        var cy := 105.0+float((i*43)%86)
        StorybookStyle.cloud(self,Vector2(cx,cy),1.0+float(i%3)*0.22,cloud_fill)
    for i in range(5):
        var bx := fposmod(float(i)*710.0+t*27.0,width+80.0)-40.0
        var by := 205.0+sin(t*1.3+float(i))*16.0
        var flap := 0.25+absf(sin(t*5.0+float(i)*1.7))*0.35
        draw_arc(Vector2(bx,by),10.0,PI+flap,TAU-flap,8,StorybookStyle.OUTLINE,2.6)
        draw_arc(Vector2(bx+17,by),10.0,PI+flap,TAU-flap,8,StorybookStyle.OUTLINE,2.6)

    if precipitation in ["CLOUDY","OVERCAST"]:
        var cloud_tint := Color("#7f93a8",0.12) if precipitation == "CLOUDY" else Color("#5f7288",0.24)
        draw_rect(Rect2(0,0,width,WORLD_HEIGHT),cloud_tint)
    if precipitation in ["RAIN","SLEET","SNOW","BLIZZARD"]:
        for i in range(120):
            var x := float((i*137+int(Time.get_ticks_msec()/22))%int(maxf(width,1.0)))
            var y := float((i*71+int(Time.get_ticks_msec()/13))%560)
            if precipitation == "SNOW" or precipitation == "BLIZZARD":
                draw_circle(Vector2(x,y),3.2,Color("#9fb4cc",0.7))
                draw_circle(Vector2(x,y),2.4,Color("#ffffff"))
            else:
                draw_line(Vector2(x,y),Vector2(x-8,y+22),Color("#5d86c4",0.55),3.2,true)
                draw_line(Vector2(x,y),Vector2(x-8,y+22),Color("#cfe6ff",0.9),1.6,true)
    if precipitation == "FOG":
        draw_rect(Rect2(0,280,width,440),Color("#e6efe9",0.34))
        for i in range(5):
            var fog_y := 360.0+float(i)*62.0+sin(t+float(i))*10.0
            draw_rect(Rect2(0,fog_y,width,34),Color("#fff8ea",0.16))
