extends Node2D
## Independent, camera-space weather overlay. Simulation climate drives its state.

var _precipitation := "CLEAR"
var _intensity := 1.0
var _time := 0.0
var _viewport_size := Vector2(1280,720)

func configure(climate: Dictionary) -> void:
    _precipitation = str(climate.get("precipitation","CLEAR")).to_upper()
    _intensity = clampf(float(climate.get("precipitation_intensity",1.0)),0.0,2.0)
    queue_redraw()

func _process(delta: float) -> void:
    _time += delta
    if _precipitation in ["RAIN","SLEET","SNOW","BLIZZARD","FOG"]:
        queue_redraw()

func _draw() -> void:
    var count := int(90.0*_intensity)
    if _precipitation in ["RAIN","SLEET","BLIZZARD"]:
        for i in range(count):
            var x := fposmod(float(i*137)+_time*540.0,1280.0)
            var y := fposmod(float(i*71)+_time*720.0,720.0)
            draw_line(Vector2(x,y),Vector2(x-7,y+19),Color("#d7e4e9",0.48),1.4)
    elif _precipitation == "SNOW":
        for i in range(count):
            var x := fposmod(float(i*137)+sin(_time+float(i))*12.0,1280.0)
            var y := fposmod(float(i*71)+_time*45.0,720.0)
            draw_circle(Vector2(x,y),1.8,Color("#f1f3e8",0.78))
    elif _precipitation == "FOG":
        for i in range(6):
            var y := 300.0+float(i)*65.0+sin(_time*0.4+float(i))*12.0
            draw_rect(Rect2(0,y,1280,48),Color("#e8e8dc",0.12))
