extends Node2D
## Manifest-driven environmental object visuals. Interaction semantics remain in the controller.
var definition: Dictionary = {}
var actual_state: Dictionary = {}
var simulation_hour := 10
var simulation_minute := 0
var _phase := 0.0

func configure(data: Dictionary,actual: Dictionary,status: Dictionary) -> void:
    var changed := definition != data or actual_state != actual or simulation_hour != int(status.get("hour",10)) or simulation_minute != int(status.get("tick",0))%60
    if not changed:
        return
    definition = data.duplicate(true)
    actual_state = actual.duplicate(true)
    simulation_hour = int(status.get("hour",10))
    simulation_minute = int(status.get("tick",0))%60
    position = Vector2(float(definition.get("x",600.0)),float(definition.get("y",500.0)))
    set_process(str(definition.get("visual_kind",definition.get("kind","inspect"))) in ["noticeboard","clock","oven","hearth"])
    queue_redraw()

func _process(delta: float) -> void:
    _phase += delta
    queue_redraw()

func _draw() -> void:
    var visual_kind := str(definition.get("visual_kind",definition.get("kind","inspect")))
    match visual_kind:
        "noticeboard": _draw_noticeboard()
        "ledger": _draw_ledger()
        "clock": _draw_clock()
        "shop": _draw_shop()
        "oven": _draw_oven()
        "hearth": _draw_hearth()
        "game_table": _draw_game_table()
        "lawn_marker": _draw_lawn_marker()
        _: _draw_inspectable()

func _draw_noticeboard() -> void:
    _shadow(78.0,18.0)
    draw_rect(Rect2(-35.0,-139.0,70.0,122.0),Color("#594432"))
    draw_rect(Rect2(-30.0,-134.0,60.0,112.0),Color("#a47b52"))
    draw_rect(Rect2(-25.0,-129.0,50.0,101.0),Color("#eee3c9"))
    draw_rect(Rect2(-22.0,-126.0,44.0,95.0),Color("#e4d4b4"))
    for i in range(3):
        var y := -112.0+float(i)*27.0
        var flutter := sin(_phase*2.0+float(i))*1.4
        draw_colored_polygon(PackedVector2Array([Vector2(-16.0,y),Vector2(15.0,y+flutter),Vector2(13.0,y+13.0),Vector2(-15.0,y+12.0)]),[Color("#d5b58a"),Color("#b8c2a1"),Color("#d6a58a")][i])
        draw_line(Vector2(-11.0,y+5.0),Vector2(9.0,y+5.0+flutter),Color("#776b57",0.72),1.2)
        draw_circle(Vector2(-17.0,y+2.0),2.5,Color("#b66b48"))
    draw_rect(Rect2(-8.0,-18.0,16.0,54.0),Color("#70553c"))
    draw_rect(Rect2(-12.0,-22.0,24.0,6.0),Color("#c49b69"))

func _draw_ledger() -> void:
    _shadow(142.0,20.0)
    draw_rect(Rect2(-67.0,-79.0,134.0,75.0),Color("#654832"))
    draw_rect(Rect2(-61.0,-75.0,122.0,65.0),Color("#d2bd96"))
    draw_colored_polygon(PackedVector2Array([Vector2(-58.0,-72.0),Vector2(-3.0,-68.0),Vector2(-3.0,-15.0),Vector2(-58.0,-20.0)]),Color("#f0e5ce"))
    draw_colored_polygon(PackedVector2Array([Vector2(3.0,-68.0),Vector2(58.0,-72.0),Vector2(58.0,-20.0),Vector2(3.0,-15.0)]),Color("#e8dbc0"))
    draw_line(Vector2(0.0,-68.0),Vector2(0.0,-15.0),Color("#9b7c59"),2.0)
    for i in range(4):
        var y := -59.0+float(i)*10.0
        draw_line(Vector2(-50.0,y),Vector2(-12.0,y+2.0),Color("#9a8a70",0.72),1.2)
        draw_line(Vector2(12.0,y+2.0),Vector2(50.0,y),Color("#9a8a70",0.72),1.2)
    draw_rect(Rect2(-29.0,-113.0,58.0,42.0),Color("#e7ddc8"))
    draw_rect(Rect2(-25.0,-109.0,50.0,34.0),Color("#c9b18b"))
    draw_line(Vector2(-17.0,-99.0),Vector2(17.0,-99.0),Color("#6c5a43"),2.0)

func _draw_clock() -> void:
    _shadow(82.0,18.0)
    draw_rect(Rect2(-7.0,-26.0,14.0,58.0),Color("#70553c"))
    draw_circle(Vector2(0.0,-78.0),42.0,Color("#654c38"))
    draw_circle(Vector2(0.0,-78.0),36.0,Color("#e9dfc8"))
    draw_circle(Vector2(0.0,-78.0),31.0,Color("#f5edda"),false,1.2)
    for i in range(12):
        var a := TAU*float(i)/12.0
        var inner := Vector2(cos(a),sin(a))*25.0
        var outer := Vector2(cos(a),sin(a))*30.0
        draw_line(Vector2(0.0,-78.0)+inner,Vector2(0.0,-78.0)+outer,Color("#79664e"),1.8)
    var minute_angle := float(simulation_minute)/60.0*TAU-PI*0.5
    var hour_angle := (float(simulation_hour%12)+float(simulation_minute)/60.0)/12.0*TAU-PI*0.5
    draw_line(Vector2(0.0,-78.0),Vector2(cos(hour_angle)*15.0,sin(hour_angle)*15.0-78.0),Color("#3e4038"),3.0)
    draw_line(Vector2(0.0,-78.0),Vector2(cos(minute_angle)*26.0,sin(minute_angle)*26.0-78.0),Color("#a75e46"),2.0)
    draw_circle(Vector2(0.0,-78.0),3.0,Color("#b66b48"))

func _draw_shop() -> void:
    _shadow(166.0,22.0)
    draw_rect(Rect2(-78.0,-88.0,156.0,72.0),Color("#6e5039"))
    draw_rect(Rect2(-70.0,-81.0,140.0,57.0),Color("#d8c39d"))
    draw_rect(Rect2(-65.0,-74.0,130.0,16.0),Color("#876345"))
    for i in range(5):
        var x := -62.0+float(i)*25.0
        var stripe := Color("#b96f55") if i%2==0 else Color("#eee0c3")
        draw_colored_polygon(PackedVector2Array([Vector2(x,-74.0),Vector2(x+23.0,-74.0),Vector2(x+19.0,-57.0),Vector2(x+4.0,-57.0)]),stripe)
    draw_rect(Rect2(-66.0,-52.0,132.0,25.0),Color("#9b7958"))
    draw_rect(Rect2(-55.0,-44.0,110.0,10.0),Color("#d9bd8e"))
    draw_circle(Vector2(-38.0,-34.0),4.0,Color("#c68d58"))
    draw_circle(Vector2(0.0,-34.0),4.0,Color("#8b9b72"))
    draw_circle(Vector2(38.0,-34.0),4.0,Color("#b96f55"))

func _draw_oven() -> void:
    _shadow(128.0,24.0)
    draw_rect(Rect2(-66.0,-108.0,132.0,108.0),Color("#805a45"))
    draw_rect(Rect2(-59.0,-102.0,118.0,96.0),Color("#b66d50"))
    draw_arc(Vector2(0.0,-47.0),43.0,PI,TAU,24,Color("#e0b477"),5.0)
    draw_rect(Rect2(-36.0,-48.0,72.0,44.0),Color("#493b32"))
    var flame := 0.78+sin(_phase*5.0)*0.12+sin(_phase*8.1)*0.06
    draw_colored_polygon(PackedVector2Array([Vector2(-19.0,-9.0),Vector2(-7.0,-41.0*flame),Vector2(1.0,-17.0),Vector2(16.0,-38.0*flame),Vector2(22.0,-9.0)]),Color("#e99b51",0.9))
    draw_circle(Vector2(0.0,-24.0),11.0,Color("#f3cf83",0.58))
    draw_rect(Rect2(-72.0,-112.0,144.0,8.0),Color("#e1b77b"))

func _draw_hearth() -> void:
    _shadow(120.0,24.0)
    draw_rect(Rect2(-61.0,-115.0,122.0,115.0),Color("#755c4b"))
    draw_rect(Rect2(-53.0,-106.0,106.0,99.0),Color("#b07a59"))
    draw_rect(Rect2(-40.0,-77.0,80.0,70.0),Color("#44372f"))
    draw_arc(Vector2(0.0,-7.0),40.0,PI,TAU,24,Color("#d8b17b"),5.0)
    var flame := 0.76+sin(_phase*4.6)*0.14+sin(_phase*7.2)*0.07
    draw_colored_polygon(PackedVector2Array([Vector2(-25.0,-8.0),Vector2(-13.0,-62.0*flame),Vector2(0.0,-24.0),Vector2(13.0,-58.0*flame),Vector2(26.0,-8.0)]),Color("#e89a53",0.9))
    draw_circle(Vector2(0.0,-31.0),14.0,Color("#f2c879",0.48))
    draw_rect(Rect2(-67.0,-7.0,134.0,9.0),Color("#514235"))

func _draw_game_table() -> void:
    _shadow(122.0,22.0)
    draw_rect(Rect2(-55.0,-58.0,110.0,58.0),Color("#614631"))
    draw_colored_polygon(PackedVector2Array([Vector2(-63.0,-58.0),Vector2(-48.0,-78.0),Vector2(63.0,-78.0),Vector2(49.0,-58.0)]),Color("#8a6747"))
    draw_colored_polygon(PackedVector2Array([Vector2(-48.0,-76.0),Vector2(48.0,-76.0),Vector2(55.0,-62.0),Vector2(-55.0,-62.0)]),Color("#66806a"))
    for i in range(3):
        var x := -23.0+float(i)*23.0
        draw_colored_polygon(PackedVector2Array([Vector2(x-7.0,-70.0),Vector2(x+7.0,-70.0),Vector2(x+8.0,-50.0),Vector2(x-6.0,-50.0)]),Color("#f1e6d0"))
        draw_circle(Vector2(x,-60.0),2.0,Color("#b66b48"))
    draw_rect(Rect2(-8.0,-48.0,16.0,6.0),Color("#c8a16d"))

func _draw_lawn_marker() -> void:
    _shadow(100.0,18.0)
    draw_ellipse(Vector2(0.0,-2.0),Vector2(60.0,12.0),Color("#7c9364",0.36))
    for i in range(3):
        var x := -27.0+float(i)*27.0
        draw_circle(Vector2(x,-12.0),7.0,[Color("#eee1c8"),Color("#c77d5b"),Color("#d7b77d")][i])
        draw_circle(Vector2(x-2.0,-14.0),2.0,Color("#fff6df",0.7))
    draw_line(Vector2(-53.0,-4.0),Vector2(53.0,-4.0),Color("#c1b48e",0.8),2.0)

func _draw_inspectable() -> void:
    _shadow(112.0,20.0)
    draw_rect(Rect2(-54.0,-66.0,108.0,52.0),Color("#886e51"))
    draw_rect(Rect2(-45.0,-58.0,90.0,36.0),Color("#c5a47a"))
    draw_rect(Rect2(-36.0,-50.0,72.0,5.0),Color("#e5d0a8",0.8))
    draw_circle(Vector2(0.0,-42.0),5.0,Color("#a75e46"))

func _shadow(width: float,depth: float) -> void:
    var points := PackedVector2Array()
    for i in range(24):
        var a := TAU*float(i)/24.0
        points.append(Vector2(0.0,2.0)+Vector2(cos(a)*width*0.5,sin(a)*depth*0.5))
    draw_colored_polygon(points,Color("#403a32",0.18))

func _draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var a := TAU*float(i)/20.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
