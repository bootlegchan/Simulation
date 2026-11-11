extends Node2D
## Independent scenery assets with reusable species and prop variations,
## drawn in the shared storybook style (crayon outlines, puffy rounded shapes).

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var definition: Dictionary = {}
var _wind_phase := 0.0
var _base_rotation := 0.0
var _seed := 0

func configure(data: Dictionary) -> void:
    if definition == data: return
    definition = data.duplicate(true)
    position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",0.0)))
    _base_rotation = float(definition.get("rotation",0.0))
    _seed = absi(str(definition.get("id","")).hash())%1000
    _wind_phase = float(_seed)*0.01
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
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(8*s,4*s),56*s)
    var trunk := PackedVector2Array([Vector2(-13*s,0),Vector2(-9*s,-112*s),Vector2(10*s,-112*s),Vector2(16*s,0)])
    StorybookStyle.outlined_polygon(self,trunk,Color("#c98a55"),ink,3.5,_seed,1.2)
    StorybookStyle.dab(self,Vector2(-3*s,-52*s),Vector2(3.5*s,40*s),Color("#e6b179",0.75))
    StorybookStyle.crayon_line(self,Vector2(-9*s,-18*s),Vector2(3*s,-24*s),Color("#8a5434",0.8),2.2,_seed)
    if species == "pine":
        for layer in range(4):
            var y := -92.0*s-float(layer)*32.0*s
            var tri := PackedVector2Array([Vector2(-55*s+float(layer)*5*s,y+24*s),Vector2(0,y-58*s),Vector2(55*s-float(layer)*5*s,y+24*s)])
            var fill := StorybookStyle.tone(StorybookStyle.LEAF_DEEP,float(layer)*0.09)
            StorybookStyle.outlined_polygon(self,tri,fill,ink,3.5,_seed+layer,1.4)
            StorybookStyle.dab(self,Vector2(-12*s,y-8*s),Vector2(16*s,6*s),Color(StorybookStyle.LEAF_LIGHT,0.55))
    elif species == "cypress":
        var flame := PackedVector2Array([Vector2(-34*s,-35*s),Vector2(-24*s,-120*s),Vector2(-9*s,-182*s),Vector2(0,-206*s),Vector2(10*s,-182*s),Vector2(24*s,-120*s),Vector2(34*s,-35*s)])
        StorybookStyle.outlined_polygon(self,flame,StorybookStyle.LEAF_DEEP,ink,3.5,_seed,1.5)
        StorybookStyle.dab(self,Vector2(-6*s,-112*s),Vector2(13*s,62*s),Color(StorybookStyle.LEAF_LIGHT,0.6))
        StorybookStyle.dab(self,Vector2(6*s,-84*s),Vector2(9*s,38*s),Color(StorybookStyle.LEAF,0.45))
    else:
        StorybookStyle.crayon_line(self,Vector2(-1*s,-35*s),Vector2(-34*s,-104*s),ink,6.0*s,_seed)
        StorybookStyle.crayon_line(self,Vector2(5*s,-48*s),Vector2(39*s,-108*s),ink,6.0*s,_seed+1)
        var lobes := [
            Vector3(0*s,-153*s,54*s),Vector3(-38*s,-124*s,43*s),Vector3(39*s,-126*s,44*s),
            Vector3(-10*s,-190*s,39*s),Vector3(52*s,-166*s,27*s),Vector3(-57*s,-164*s,29*s)
        ]
        StorybookStyle.puffs(self,lobes,StorybookStyle.LEAF,ink,4.0)
        for lobe in lobes:
            var v: Vector3 = lobe
            StorybookStyle.dab(self,Vector2(v.x-v.z*0.26,v.y-v.z*0.3),Vector2(v.z*0.5,v.z*0.36),Color(StorybookStyle.LEAF_LIGHT,0.8))
            StorybookStyle.dab(self,Vector2(v.x+v.z*0.3,v.y+v.z*0.36),Vector2(v.z*0.42,v.z*0.28),Color(StorybookStyle.LEAF_DEEP,0.5))
        for i in range(5):
            var bx := float(i-2)*22.0*s+sin(float(_seed+i))*8.0*s
            var by := -150.0*s+float((i*37)%60)*s
            draw_circle(Vector2(bx,by),3.4*s,StorybookStyle.BLOOM_WHITE)

func _draw_rock(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(3*s,3*s),32*s,0.26,0.22)
    var body := PackedVector2Array([Vector2(-27*s,0),Vector2(-21*s,-20*s),Vector2(-6*s,-32*s),Vector2(17*s,-25*s),Vector2(31*s,-9*s),Vector2(28*s,0)])
    StorybookStyle.outlined_polygon(self,body,Color("#b5b2a6"),ink,3.2,_seed,1.2)
    StorybookStyle.dab(self,Vector2(-8*s,-20*s),Vector2(11*s,6*s),Color("#eeeadb",0.85))
    StorybookStyle.dab(self,Vector2(14*s,-7*s),Vector2(10*s,5*s),Color(StorybookStyle.SHADOW_TINT,0.25))

func _draw_bush(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(0,3*s),34*s,0.26,0.22)
    var lobes := [Vector3(-18*s,-4*s,19*s),Vector3(0,-16*s,21*s),Vector3(19*s,-5*s,19*s),Vector3(7*s,-26*s,16*s)]
    StorybookStyle.puffs(self,lobes,StorybookStyle.LEAF,ink,3.4)
    for lobe in lobes:
        var v: Vector3 = lobe
        StorybookStyle.dab(self,Vector2(v.x-v.z*0.25,v.y-v.z*0.3),Vector2(v.z*0.5,v.z*0.34),Color(StorybookStyle.LEAF_LIGHT,0.8))
    for i in range(5):
        var bp := Vector2(float(i*9-18)*s,float(-18-(i%2)*8)*s)
        StorybookStyle.outlined_circle(self,bp,3.0*s,StorybookStyle.BLOOM_PINK,ink,1.4,_seed+i,0.2)

func _draw_lamp(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(0,2*s),26*s,0.28,0.2)
    draw_circle(Vector2(0,-100*s),30*s,Color("#ffe29a",0.16))
    draw_circle(Vector2(0,-100*s),20*s,Color("#ffe29a",0.18))
    StorybookStyle.outlined_rect(self,Rect2(-4*s,-105*s,8*s,105*s),Color("#7a5a44"),ink,2.6,_seed,0.6)
    StorybookStyle.outlined_rounded_rect(self,Rect2(-17*s,-118*s,34*s,28*s),6.0*s,Color("#ffd86a"),ink,3.0,_seed,0.5)
    StorybookStyle.dab(self,Vector2(-4*s,-108*s),Vector2(6*s,8*s),Color("#fff6c7",0.9))
    StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(-21*s,-118*s),Vector2(0,-134*s),Vector2(21*s,-118*s)]),StorybookStyle.TERRACOTTA,ink,2.8,_seed,0.6)

func _draw_flower(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.crayon_line(self,Vector2(0,0),Vector2(2*s,-23*s),StorybookStyle.LEAF_DEEP,3.0*s,_seed)
    var petal := Color(str(definition.get("flower_colour","#ff8fb0")))
    for i in range(5):
        var a := TAU*float(i)/5.0
        StorybookStyle.outlined_circle(self,Vector2(cos(a)*7*s,-25*s+sin(a)*7*s),4.6*s,petal,ink,1.6,_seed+i,0.2)
    StorybookStyle.outlined_circle(self,Vector2(0,-25*s),3.8*s,StorybookStyle.BLOOM_YELLOW,ink,1.6,_seed,0.2)

func _draw_bench(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(0,3*s),46*s,0.22,0.2)
    StorybookStyle.outlined_rect(self,Rect2(-32*s,-12*s,7*s,24*s),StorybookStyle.WOOD_DEEP,ink,2.6,_seed,0.6)
    StorybookStyle.outlined_rect(self,Rect2(25*s,-12*s,7*s,24*s),StorybookStyle.WOOD_DEEP,ink,2.6,_seed+1,0.6)
    StorybookStyle.outlined_rect(self,Rect2(-40*s,-36*s,80*s,11*s),StorybookStyle.WOOD_DEEP,ink,2.8,_seed+2,0.7)
    StorybookStyle.outlined_rect(self,Rect2(-40*s,-23*s,80*s,11*s),StorybookStyle.WOOD,ink,2.8,_seed+3,0.7)
    StorybookStyle.dab(self,Vector2(-6*s,-18*s),Vector2(26*s,2.4*s),Color("#f4c999",0.8))

func _draw_planter(s: float) -> void:
    var ink := StorybookStyle.OUTLINE
    StorybookStyle.blob_shadow(self,Vector2(0,2*s),30*s,0.26,0.2)
    for x in [-12.0,0.0,12.0]:
        StorybookStyle.crayon_line(self,Vector2(x*s,-27*s),Vector2((x-3)*s,-50*s),StorybookStyle.LEAF_DEEP,3.0*s,int(x)+_seed)
        StorybookStyle.outlined_circle(self,Vector2((x-3)*s,-55*s),8.0*s,StorybookStyle.LEAF,ink,2.4,int(x)+_seed,0.4)
        StorybookStyle.dab(self,Vector2((x-5)*s,-58*s),Vector2(4*s,3*s),Color(StorybookStyle.LEAF_LIGHT,0.9))
    var pot := PackedVector2Array([Vector2(-24*s,-26*s),Vector2(24*s,-26*s),Vector2(18*s,0),Vector2(-18*s,0)])
    StorybookStyle.outlined_polygon(self,pot,StorybookStyle.TERRACOTTA,ink,3.0,_seed,0.8)
    StorybookStyle.outlined_rect(self,Rect2(-26*s,-31*s,52*s,9*s),StorybookStyle.tone(StorybookStyle.TERRACOTTA,0.2),ink,2.6,_seed,0.6)
