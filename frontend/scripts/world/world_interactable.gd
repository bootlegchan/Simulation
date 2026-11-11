extends Node2D
## Manifest-driven environmental object visuals. Interaction semantics remain in the controller.
## Drawn in the shared storybook style (crayon outlines, warm flat fills).

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var definition: Dictionary = {}
var actual_state: Dictionary = {}
var simulation_hour := 10
var simulation_minute := 0
var _phase := 0.0
var _seed := 0

func configure(data: Dictionary,actual: Dictionary,status: Dictionary) -> void:
    var changed := definition != data or actual_state != actual or simulation_hour != int(status.get("hour",10)) or simulation_minute != int(status.get("tick",0))%60
    if not changed:
        return
    definition = data.duplicate(true)
    actual_state = actual.duplicate(true)
    simulation_hour = int(status.get("hour",10))
    simulation_minute = int(status.get("tick",0))%60
    _seed = absi(str(definition.get("id","")).hash())%1000
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
    var ink := StorybookStyle.OUTLINE
    _shadow(80.0,18.0)
    StorybookStyle.outlined_rect(self,Rect2(-8.0,-18.0,16.0,56.0),StorybookStyle.WOOD_DEEP,ink,2.8,_seed,0.6)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-38.0,-142.0,76.0,126.0),8.0,StorybookStyle.WOOD,ink,3.4,_seed+1,0.8)
    StorybookStyle.outlined_rect(self,Rect2(-28.0,-132.0,56.0,106.0),Color("#fff3d2"),ink,2.4,_seed+2,0.6)
    for i in range(3):
        var y := -118.0+float(i)*30.0
        var flutter := sin(_phase*2.0+float(i))*1.6
        var note := PackedVector2Array([Vector2(-20.0,y),Vector2(19.0,y+flutter),Vector2(17.0,y+18.0),Vector2(-19.0,y+17.0)])
        StorybookStyle.outlined_polygon(self,note,[Color("#ffd27a"),Color("#a8e6a0"),Color("#ffa9a0")][i],ink,2.0,_seed+i,0.4)
        StorybookStyle.crayon_line(self,Vector2(-13.0,y+8.0),Vector2(12.0,y+8.0+flutter),Color("#8a6a58"),1.8,i)
        StorybookStyle.outlined_circle(self,Vector2(-19.0,y+2.0),3.0,Color("#ff5b5b"),ink,1.4,_seed+i,0.1)
    StorybookStyle.outlined_rect(self,Rect2(-14.0,-24.0,28.0,8.0),StorybookStyle.tone(StorybookStyle.WOOD,0.2),ink,2.4,_seed+3,0.4)

func _draw_ledger() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(144.0,20.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-69.0,-81.0,138.0,77.0),8.0,StorybookStyle.TERRACOTTA,ink,3.4,_seed,0.8)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-60.0,-72.0),Vector2(-3.0,-68.0),Vector2(-3.0,-14.0),Vector2(-60.0,-19.0)]),Color("#fff6de"),ink,2.4,_seed+1,0.5)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(3.0,-68.0),Vector2(60.0,-72.0),Vector2(60.0,-19.0),Vector2(3.0,-14.0)]),Color("#fff0cc"),ink,2.4,_seed+2,0.5)
    for i in range(4):
        var y := -59.0+float(i)*10.0
        StorybookStyle.crayon_line(self,Vector2(-51.0,y),Vector2(-12.0,y+2.0),Color("#a58a74",0.85),1.8,i)
        StorybookStyle.crayon_line(self,Vector2(12.0,y+2.0),Vector2(51.0,y),Color("#a58a74",0.85),1.8,i+5)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-31.0,-115.0,62.0,44.0),6.0,Color("#fff3d2"),ink,2.8,_seed+3,0.6)
    StorybookStyle.outlined_rect(self,Rect2(-25.0,-109.0,50.0,32.0),Color("#ffe3a8"),ink,1.8,_seed+4,0.4)
    StorybookStyle.crayon_line(self,Vector2(-17.0,-99.0),Vector2(17.0,-99.0),ink,2.2,_seed)

func _draw_clock() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(84.0,18.0)
    StorybookStyle.outlined_rect(self,Rect2(-8.0,-26.0,16.0,60.0),StorybookStyle.WOOD_DEEP,ink,2.8,_seed,0.6)
    StorybookStyle.outlined_circle(self,Vector2(0.0,-78.0),44.0,StorybookStyle.WOOD,ink,3.6,_seed+1,0.8)
    StorybookStyle.outlined_circle(self,Vector2(0.0,-78.0),36.0,Color("#fff6de"),ink,2.4,_seed+2,0.6)
    for i in range(12):
        var a := TAU*float(i)/12.0
        var inner := Vector2(cos(a),sin(a))*26.0
        var outer := Vector2(cos(a),sin(a))*31.0
        StorybookStyle.crayon_line(self,Vector2(0.0,-78.0)+inner,Vector2(0.0,-78.0)+outer,Color("#8a5f49"),2.4,i)
    var minute_angle := float(simulation_minute)/60.0*TAU-PI*0.5
    var hour_angle := (float(simulation_hour%12)+float(simulation_minute)/60.0)/12.0*TAU-PI*0.5
    StorybookStyle.crayon_line(self,Vector2(0.0,-78.0),Vector2(cos(hour_angle)*16.0,sin(hour_angle)*16.0-78.0),ink,4.0,_seed)
    StorybookStyle.crayon_line(self,Vector2(0.0,-78.0),Vector2(cos(minute_angle)*27.0,sin(minute_angle)*27.0-78.0),StorybookStyle.TERRACOTTA,3.0,_seed+1)
    StorybookStyle.outlined_circle(self,Vector2(0.0,-78.0),4.0,StorybookStyle.BLOOM_YELLOW,ink,1.8,_seed,0.2)

func _draw_shop() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(168.0,22.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-78.0,-90.0,156.0,74.0),6.0,StorybookStyle.WOOD_DEEP,ink,3.4,_seed,0.8)
    StorybookStyle.outlined_rect(self,Rect2(-70.0,-82.0,140.0,58.0),Color("#ffe3a8"),ink,2.2,_seed+1,0.5)
    StorybookStyle.outlined_rect(self,Rect2(-67.0,-78.0,134.0,14.0),StorybookStyle.WOOD,ink,2.2,_seed+2,0.4)
    for i in range(5):
        var x := -64.0+float(i)*25.6
        var stripe := Color("#ff6f59") if i%2==0 else Color("#fff3d2")
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(x,-78.0),Vector2(x+25.0,-78.0),Vector2(x+21.0,-56.0),Vector2(x+12.0,-52.0),Vector2(x+4.0,-56.0)]),stripe,ink,2.2,_seed+i,0.4)
    StorybookStyle.outlined_rect(self,Rect2(-68.0,-50.0,136.0,26.0),StorybookStyle.tone(StorybookStyle.WOOD,0.1),ink,2.6,_seed+3,0.5)
    StorybookStyle.outlined_circle(self,Vector2(-40.0,-34.0),5.5,Color("#ff9f43"),ink,1.8,_seed+4,0.2)
    StorybookStyle.outlined_circle(self,Vector2(0.0,-34.0),5.5,Color("#7fd06a"),ink,1.8,_seed+5,0.2)
    StorybookStyle.outlined_circle(self,Vector2(40.0,-34.0),5.5,Color("#ff6f8f"),ink,1.8,_seed+6,0.2)

func _draw_oven() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(130.0,24.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-68.0,-110.0,136.0,110.0),10.0,StorybookStyle.TERRACOTTA,ink,3.8,_seed,0.9)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-58.0,-100.0,116.0,92.0),8.0,StorybookStyle.tone(StorybookStyle.TERRACOTTA,0.18),ink,2.4,_seed+1,0.6)
    draw_arc(Vector2(0.0,-47.0),43.0,PI,TAU,24,Color("#ffe08a"),5.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-37.0,-49.0,74.0,45.0),10.0,Color("#4a2f3a"),ink,3.0,_seed+2,0.6)
    var flame := 0.78+sin(_phase*5.0)*0.12+sin(_phase*8.1)*0.06
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-19.0,-9.0),Vector2(-7.0,-41.0*flame),Vector2(1.0,-17.0),Vector2(16.0,-38.0*flame),Vector2(22.0,-9.0)]),Color("#ffb347"),Color("#c4521f"),2.0,_seed+3,0.3)
    draw_circle(Vector2(0.0,-24.0),12.0,Color("#ffe08a",0.5))
    StorybookStyle.outlined_rect(self,Rect2(-74.0,-114.0,148.0,9.0),Color("#ffe08a"),ink,2.4,_seed+4,0.5)

func _draw_hearth() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(122.0,24.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-63.0,-117.0,126.0,117.0),10.0,Color("#c98a6a"),ink,3.8,_seed,0.9)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-53.0,-107.0,106.0,100.0),8.0,Color("#e6a97f"),ink,2.4,_seed+1,0.6)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-41.0,-78.0,82.0,71.0),12.0,Color("#4a2f3a"),ink,3.0,_seed+2,0.6)
    draw_arc(Vector2(0.0,-7.0),40.0,PI,TAU,24,Color("#ffd98a"),5.0)
    var flame := 0.76+sin(_phase*4.6)*0.14+sin(_phase*7.2)*0.07
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-25.0,-8.0),Vector2(-13.0,-62.0*flame),Vector2(0.0,-24.0),Vector2(13.0,-58.0*flame),Vector2(26.0,-8.0)]),Color("#ffb347"),Color("#c4521f"),2.0,_seed+3,0.3)
    draw_circle(Vector2(0.0,-31.0),15.0,Color("#ffe08a",0.45))
    StorybookStyle.outlined_rect(self,Rect2(-69.0,-8.0,138.0,10.0),StorybookStyle.WOOD_DEEP,ink,2.6,_seed+4,0.5)

func _draw_game_table() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(124.0,22.0)
    StorybookStyle.outlined_rect(self,Rect2(-55.0,-58.0,110.0,58.0),StorybookStyle.WOOD_DEEP,ink,3.2,_seed,0.8)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-64.0,-58.0),Vector2(-49.0,-80.0),Vector2(64.0,-80.0),Vector2(50.0,-58.0)]),StorybookStyle.WOOD,ink,3.2,_seed+1,0.8)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-48.0,-77.0),Vector2(48.0,-77.0),Vector2(55.0,-62.0),Vector2(-55.0,-62.0)]),Color("#5fcf8a"),ink,2.2,_seed+2,0.6)
    for i in range(3):
        var x := -23.0+float(i)*23.0
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(x-8.0,-72.0),Vector2(x+8.0,-72.0),Vector2(x+9.0,-50.0),Vector2(x-7.0,-50.0)]),Color("#fff6de"),ink,2.0,_seed+i,0.3)
        StorybookStyle.outlined_circle(self,Vector2(x,-61.0),2.8,Color("#ff5b5b"),ink,1.2,_seed+i,0.1)
    StorybookStyle.outlined_rect(self,Rect2(-9.0,-48.0,18.0,7.0),Color("#ffd98a"),ink,2.0,_seed+4,0.3)

func _draw_lawn_marker() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(102.0,18.0)
    StorybookStyle.outlined_ellipse(self,Vector2(0.0,-2.0),Vector2(62.0,13.0),Color(StorybookStyle.LEAF_LIGHT,0.75),StorybookStyle.OUTLINE_SOFT,2.4,_seed,1.2)
    for i in range(3):
        var x := -27.0+float(i)*27.0
        var ball := [Color("#fff3d2"),Color("#ff7a59"),Color("#ffd23f")][i]
        StorybookStyle.outlined_circle(self,Vector2(x,-13.0),8.0,ball,ink,2.2,_seed+i,0.2)
        StorybookStyle.dab(self,Vector2(x-2.5,-16.0),Vector2(2.6,1.8),Color("#ffffff",0.85))
    StorybookStyle.crayon_line(self,Vector2(-54.0,-4.0),Vector2(54.0,-4.0),Color("#fff3d2"),2.4,_seed)

func _draw_inspectable() -> void:
    var ink := StorybookStyle.OUTLINE
    _shadow(114.0,20.0)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-56.0,-68.0,112.0,54.0),8.0,StorybookStyle.WOOD,ink,3.2,_seed,0.8)
    StorybookStyle.outlined_rect(self,Rect2(-46.0,-59.0,92.0,36.0),Color("#ffe3a8"),ink,2.0,_seed+1,0.5)
    StorybookStyle.dab(self,Vector2(0.0,-48.0),Vector2(34.0,3.0),Color("#fff6de",0.8))
    StorybookStyle.outlined_circle(self,Vector2(0.0,-42.0),5.5,StorybookStyle.TERRACOTTA,ink,1.8,_seed+2,0.2)

func _shadow(width: float,_depth: float) -> void:
    StorybookStyle.blob_shadow(self,Vector2(0.0,2.0),width*0.5,0.2,0.2)
