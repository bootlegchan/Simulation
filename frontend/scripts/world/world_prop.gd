extends Node2D
## Independent scenery assets with reusable species and prop variations.
var definition: Dictionary = {}
var _wind_phase := 0.0
var _base_rotation := 0.0

func configure(data: Dictionary) -> void:
    if definition == data: return
    definition = data.duplicate(true)
    position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",0.0)))
    _base_rotation = float(definition.get("rotation",0.0))
    _wind_phase = float(abs(definition.get("id","").hash())%1000)*0.01
    set_process(str(definition.get("kind","tree")) in ["tree","bush","flower"])
    rotation = _base_rotation
    queue_redraw()

func _process(delta: float) -> void:
    _wind_phase += delta*0.7
    rotation = _base_rotation+sin(_wind_phase)*0.018

func _draw() -> void:
    var kind := str(definition.get("kind","tree"))
    var s := float(definition.get("scale",1.0))
    match kind:
        "tree": _draw_tree(s,str(definition.get("species","oak")))
        "rock": _draw_rock(s)
        "bush": _draw_bush(s)
        "lamp": _draw_lamp(s)
        "flower": _draw_flower(s)
        "bench": _draw_bench(s)
        "planter": _draw_planter(s)

func _draw_tree(s: float,species: String) -> void:
    draw_ellipse(Vector2(8*s,4*s),Vector2(48*s,12*s),Color("#403a32",0.18))
    draw_colored_polygon(PackedVector2Array([Vector2(-13*s,0),Vector2(-10*s,-116*s),Vector2(10*s,-116*s),Vector2(16*s,0)]),Color("#70543e"))
    draw_line(Vector2(-1*s,-35*s),Vector2(-34*s,-108*s),Color("#806247"),7*s)
    draw_line(Vector2(5*s,-48*s),Vector2(39*s,-112*s),Color("#806247"),7*s)
    if species=="pine":
        for layer in range(4):
            var y := -92.0*s-float(layer)*32.0*s
            draw_colored_polygon(PackedVector2Array([Vector2(-55*s+float(layer)*5*s,y+24*s),Vector2(0,y-58*s),Vector2(55*s-float(layer)*5*s,y+24*s)]),[Color("#496b57"),Color("#55785e"),Color("#63836a"),Color("#719078")][layer])
    elif species=="cypress":
        draw_colored_polygon(PackedVector2Array([Vector2(-34*s,-35*s),Vector2(-22*s,-142*s),Vector2(0,-205*s),Vector2(22*s,-142*s),Vector2(34*s,-35*s)]),Color("#4f705b"))
        draw_colored_polygon(PackedVector2Array([Vector2(-17*s,-70*s),Vector2(-8*s,-150*s),Vector2(0,-184*s),Vector2(14*s,-140*s),Vector2(20*s,-70*s)]),Color("#708b6c"))
    else:
        var clusters := [{"p":Vector2(0,-153),"r":54,"c":"#58765a"},{"p":Vector2(-38,-124),"r":43,"c":"#6b8966"},{"p":Vector2(39,-126),"r":44,"c":"#4f7057"},{"p":Vector2(-10,-190),"r":39,"c":"#78916c"},{"p":Vector2(52,-166),"r":27,"c":"#66835f"},{"p":Vector2(-57,-164),"r":29,"c":"#7e966f"}]
        for cluster in clusters:
            draw_circle(cluster.p*s,float(cluster.r)*s,Color(cluster.c))
            draw_ellipse(cluster.p*s+Vector2(-8,-10)*s,Vector2(float(cluster.r)*0.64,float(cluster.r)*0.58)*s,Color("#a4ad7a",0.22))
    draw_line(Vector2(-8*s,-20*s),Vector2(8*s,-20*s),Color("#a08059",0.55),2*s)

func _draw_rock(s: float) -> void:
    draw_ellipse(Vector2(3*s,3*s),Vector2(29*s,8*s),Color("#403a32",0.16))
    draw_colored_polygon(PackedVector2Array([Vector2(-27*s,0),Vector2(-20*s,-20*s),Vector2(-5*s,-31*s),Vector2(17*s,-24*s),Vector2(31*s,-8*s),Vector2(27*s,0)]),Color("#777b70"))
    draw_colored_polygon(PackedVector2Array([Vector2(-20*s,-20*s),Vector2(-5*s,-31*s),Vector2(4*s,-18*s),Vector2(-9*s,-8*s)]),Color("#aeb09a"))

func _draw_bush(s: float) -> void:
    draw_ellipse(Vector2(0,3*s),Vector2(31*s,8*s),Color("#403a32",0.16))
    for p in [Vector2(-18,-4),Vector2(0,-16),Vector2(19,-5),Vector2(7,-25)]:
        draw_circle(p*s,19*s,Color("#55745a"))
        draw_circle((p+Vector2(-5,-6))*s,10*s,Color("#81936c"))
    for i in range(5): draw_circle(Vector2(float(i*9-18)*s,float(-18-(i%2)*8)*s),2.2*s,Color("#d6c68e"))

func _draw_lamp(s: float) -> void:
    draw_rect(Rect2(-4*s,-105*s,8*s,105*s),Color("#594a3b"))
    draw_rect(Rect2(-18*s,-113*s,36*s,14*s),Color("#594a3b"))
    draw_rect(Rect2(-13*s,-109*s,26*s,8*s),Color("#d2b47b"))
    draw_circle(Vector2(0,-100*s),10*s,Color("#f3d28a"))
    draw_circle(Vector2(0,-100*s),21*s,Color("#f3d28a",0.12))

func _draw_flower(s: float) -> void:
    draw_line(Vector2(0,0),Vector2(2*s,-23*s),Color("#577452"),2*s)
    var petal := Color(str(definition.get("flower_colour","#dcae78")))
    for i in range(5):
        var a := TAU*float(i)/5.0
        draw_circle(Vector2(cos(a)*6*s,-25*s+sin(a)*6*s),4*s,petal)
    draw_circle(Vector2(0,-25*s),3*s,Color("#e8d18f"))

func _draw_bench(s: float) -> void:
    draw_ellipse(Vector2(0,3*s),Vector2(43*s,7*s),Color("#403a32",0.16))
    draw_rect(Rect2(-39*s,-34*s,78*s,9*s),Color("#79583e"))
    draw_rect(Rect2(-39*s,-22*s,78*s,9*s),Color("#a17a50"))
    draw_rect(Rect2(-32*s,-12*s,7*s,24*s),Color("#594735"))
    draw_rect(Rect2(25*s,-12*s,7*s,24*s),Color("#594735"))

func _draw_planter(s: float) -> void:
    draw_colored_polygon(PackedVector2Array([Vector2(-23*s,-24*s),Vector2(23*s,-24*s),Vector2(18*s,0),Vector2(-18*s,0)]),Color("#a66f50"))
    draw_rect(Rect2(-25*s,-28*s,50*s,7*s),Color("#c18a63"))
    for x in [-12.0,0.0,12.0]:
        draw_line(Vector2(x*s,-27*s),Vector2((x-3)*s,-52*s),Color("#577452"),2*s)
        draw_circle(Vector2((x-3)*s,-53*s),7*s,Color("#6f8b65"))

func draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var a := TAU*float(i)/20.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
