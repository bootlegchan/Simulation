extends Node2D
## Lightweight animated foreground foliage and path-edge dressing.
var _width := 3600.0
var _time := 0.0
var _definition: Dictionary = {}

func configure(width: float,room_manifest: Dictionary = {}) -> void:
    _width = width
    _definition = room_manifest.duplicate(true)
    var outdoors := str(_definition.get("scene_kind","outdoor")) != "interior"
    visible = outdoors
    set_process(outdoors)
    position = Vector2(0,650)
    queue_redraw()

func _process(delta: float) -> void:
    _time += delta
    queue_redraw()

func _draw() -> void:
    var settings: Dictionary = _definition.get("foreground",{})
    var palette: Dictionary = settings.get("palette",{})
    var spacing := maxi(int(settings.get("spacing",145)),60)
    var stone_spacing := maxi(int(settings.get("stone_spacing",260)),80)
    var height := float(settings.get("height",34.0))
    var sway_amount := float(settings.get("sway",5.0))
    var seed := int(settings.get("seed",0))
    var dark_grass := Color(str(palette.get("grass_dark","#536d4e")))
    var light_grass := Color(str(palette.get("grass_light","#6e8759")))
    var cream_flower := Color(str(palette.get("flower_cream","#e8c58b")))
    var rust_flower := Color(str(palette.get("flower_rust","#d88b76")))
    var path_stone := Color(str(palette.get("path_stone","#d4c4a4")))
    for i in range(0,int(_width),spacing):
        var x := float(i)
        var phase := _time*1.4+x*0.03+float(seed)*0.17
        var sway := sin(phase)*sway_amount
        var blade_height := height+float((i+seed*13)%9)
        draw_line(Vector2(x,-blade_height*0.55),Vector2(x-8+sway,-blade_height),dark_grass,3.0)
        draw_line(Vector2(x+5,-blade_height*0.52),Vector2(x+15+sway,-blade_height*0.88),light_grass,3.0)
        if int(i/spacing)%3 == 0:
            draw_line(Vector2(x+10,-blade_height*0.45),Vector2(x+20+sway*0.65,-blade_height*0.72),dark_grass,2.0)
        if int(i/spacing)%4 == 0:
            draw_circle(Vector2(x-8+sway,-blade_height-3),5.0,cream_flower)
            draw_circle(Vector2(x-14+sway,-blade_height+2),4.0,rust_flower)
    for i in range(0,int(_width),stone_spacing):
        var x := float(i)+float((int(i/stone_spacing)+seed)%2)*70.0
        draw_colored_polygon(PackedVector2Array([Vector2(x-30,24),Vector2(x-20,17),Vector2(x+14,17),Vector2(x+30,24),Vector2(x+12,29),Vector2(x-18,29)]),path_stone)
        draw_line(Vector2(x-15,21),Vector2(x+8,21),path_stone.lightened(0.12),1.0)
