extends Node2D
## Foreground details are independently sorted against characters.
var _width := 3600.0
func configure(width: float) -> void:
    _width = width
    position = Vector2(0,650)
    queue_redraw()
func _draw() -> void:
    var t := float(Time.get_ticks_msec())/1000.0
    for i in range(0,int(_width),145):
        var x := float(i)
        var sway := sin(t*1.4+x*0.03)*5.0
        draw_line(Vector2(x,-60),Vector2(x-8+sway,-90),Color("#536d4e"),3.0)
        draw_line(Vector2(x+5,-58),Vector2(x+15+sway,-84),Color("#6e8759"),3.0)
        if i%435 == 0:
            draw_circle(Vector2(x-8+sway,-93),5.0,Color("#e8c58b"))
            draw_circle(Vector2(x-14+sway,-88),4.0,Color("#d88b76"))
    for i in range(0,int(_width),260):
        var x := float(i)+float((i/260)%2)*70.0
        draw_colored_polygon(PackedVector2Array([Vector2(x-30,24),Vector2(x-20,17),Vector2(x+14,17),Vector2(x+30,24),Vector2(x+12,29),Vector2(x-18,29)]),Color("#d4c4a4",0.72))
