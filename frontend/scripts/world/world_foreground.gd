extends Node2D
## Lightweight animated foreground foliage and path-edge dressing, drawn as
## thick, rounded storybook grass blades with dark crayon edges.

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

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

func _blade(base: Vector2,tip: Vector2,dark: Color,light: Color,width: float) -> void:
    draw_line(base,tip,dark,width+3.0,true)
    draw_line(base,tip,light,width,true)
    draw_circle(tip,(width+3.0)*0.5,dark)
    draw_circle(tip,width*0.5,light)

func _draw() -> void:
    var settings: Dictionary = _definition.get("foreground",{})
    var palette: Dictionary = settings.get("palette",{})
    var spacing := maxi(int(settings.get("spacing",145)),60)
    var stone_spacing := maxi(int(settings.get("stone_spacing",260)),80)
    var height := float(settings.get("height",34.0))
    var sway_amount := float(settings.get("sway",5.0))
    var seed := int(settings.get("seed",0))
    var dark_grass := Color(str(palette.get("grass_dark","#3f9f47")))
    var light_grass := Color(str(palette.get("grass_light","#8fe05f")))
    var cream_flower := Color(str(palette.get("flower_cream","#fff3d2")))
    var rust_flower := Color(str(palette.get("flower_rust","#ff8fb0")))
    var path_stone := Color(str(palette.get("path_stone","#e6d8bb")))
    for i in range(0,int(_width),spacing):
        var x := float(i)
        var phase := _time*1.4+x*0.03+float(seed)*0.17
        var sway := sin(phase)*sway_amount
        var blade_height := height+float((i+seed*13)%9)
        _blade(Vector2(x,-blade_height*0.1),Vector2(x-8+sway,-blade_height),dark_grass,light_grass,4.0)
        _blade(Vector2(x+6,-blade_height*0.1),Vector2(x+15+sway,-blade_height*0.84),dark_grass,StorybookStyle.tone(light_grass,0.15),4.0)
        if int(i/spacing)%3 == 0:
            _blade(Vector2(x+12,-blade_height*0.1),Vector2(x+21+sway*0.65,-blade_height*0.62),dark_grass,light_grass,3.0)
        if int(i/spacing)%4 == 0:
            var f1 := Vector2(x-8+sway,-blade_height-4)
            var f2 := Vector2(x-15+sway,-blade_height+3)
            draw_circle(f1,7.0,StorybookStyle.OUTLINE)
            draw_circle(f1,5.0,cream_flower)
            draw_circle(f2,6.0,StorybookStyle.OUTLINE)
            draw_circle(f2,4.2,rust_flower)
            draw_circle(f1,1.8,StorybookStyle.BLOOM_YELLOW)
    for i in range(0,int(_width),stone_spacing):
        var x := float(i)+float((int(i/stone_spacing)+seed)%2)*70.0
        var stone := PackedVector2Array([Vector2(x-30,24),Vector2(x-20,16),Vector2(x+14,16),Vector2(x+30,24),Vector2(x+12,30),Vector2(x-18,30)])
        StorybookStyle.outlined_polygon(self,stone,path_stone,StorybookStyle.OUTLINE_SOFT,2.4,i,1.0)
        StorybookStyle.dab(self,Vector2(x-4,21),Vector2(14,2.2),Color("#fffaf0",0.8))
