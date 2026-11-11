extends Node2D
## Data-driven outdoor terrain, path and natural detail in the storybook style.

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var _manifest: Dictionary = {}
var _world_width := 3600.0

func configure(room_manifest: Dictionary,world_width: float) -> void:
    if _manifest == room_manifest and is_equal_approx(_world_width,world_width): return
    _manifest = room_manifest.duplicate(true)
    _world_width = world_width
    queue_redraw()

func _ground_edge(ground_y: float) -> PackedVector2Array:
    # Soft rolling lawn line instead of a hard horizon.
    var edge := PackedVector2Array()
    var x := 0.0
    while x < _world_width:
        edge.append(Vector2(x,ground_y+sin(x*0.0042)*11.0+sin(x*0.0113+1.3)*5.0))
        x += 120.0
    edge.append(Vector2(_world_width,ground_y+sin(_world_width*0.0042)*11.0+sin(_world_width*0.0113+1.3)*5.0))
    return edge

func _draw_interior_floor() -> void:
    # Rooms have no lawn: continue the wooden floor below the room shell, where
    # the observer and citizens walk, instead of falling back to default grass.
    var shell_bottom := 540.0
    var floor_colour := StorybookStyle.interior_floor_colour("")
    for building in _manifest.get("buildings",[]):
        if building is Dictionary and str(building.get("style","")).begins_with("interior_"):
            shell_bottom = float(building.get("y",150.0))+float(building.get("height",390.0))
            floor_colour = StorybookStyle.interior_floor_colour(str(building.get("style","")))
            break
    draw_rect(Rect2(0,shell_bottom,_world_width,720.0-shell_bottom),floor_colour)
    draw_rect(Rect2(0,shell_bottom,_world_width,46.0),StorybookStyle.tone(floor_colour,0.16))
    var seam := StorybookStyle.tone(floor_colour,-0.2)
    var row_y := shell_bottom+40.0
    while row_y < 720.0:
        StorybookStyle.crayon_line(self,Vector2(0,row_y),Vector2(_world_width,row_y),seam,2.0,int(row_y))
        row_y += 44.0
    var plank_x := 90.0
    while plank_x < _world_width:
        StorybookStyle.crayon_line(self,Vector2(plank_x,shell_bottom),Vector2(plank_x-26.0,720.0),seam,1.8,int(plank_x))
        plank_x += 210.0

func _draw() -> void:
    if str(_manifest.get("scene_kind","outdoor")) == "interior":
        _draw_interior_floor()
        return
    var data: Dictionary = _manifest.get("terrain",{})
    var ground_y := float(data.get("ground_y",560.0))
    var soil_y := float(data.get("soil_y",632.0))
    var grass := Color(str(data.get("grass_base","#82d35c")))
    var edge := _ground_edge(ground_y)

    # Base lawn, with a lighter sun-painted band along the top of the hills.
    var lawn := PackedVector2Array(edge)
    lawn.append(Vector2(_world_width,720))
    lawn.append(Vector2(0,720))
    draw_colored_polygon(lawn,grass)
    var band := PackedVector2Array(edge)
    for i in range(edge.size()-1,-1,-1):
        band.append(edge[i]+Vector2(0,46.0+sin(float(i)*1.9)*8.0))
    draw_colored_polygon(band,StorybookStyle.tone(grass,0.22))
    draw_polyline(StorybookStyle.wobble(edge,3,1.8,false,40.0),StorybookStyle.OUTLINE,4.0,true)

    # Foreground soil verge with a crayon edge.
    draw_rect(Rect2(0,soil_y,_world_width,720.0-soil_y),Color(str(data.get("soil","#d9a76a"))))
    draw_rect(Rect2(0,soil_y,_world_width,10.0),StorybookStyle.tone(Color(str(data.get("soil","#d9a76a"))),0.25))
    draw_polyline(StorybookStyle.wobble(PackedVector2Array([Vector2(0,soil_y),Vector2(_world_width,soil_y)]),5,1.6,false,40.0),StorybookStyle.OUTLINE,3.5,true)

    _draw_patches(data.get("patches",[]))
    _draw_path(data)
    _draw_stones(data.get("stones",[]))
    _draw_flowers(data.get("flower_beds",[]))
    var spacing := maxi(int(data.get("tuft_spacing",112)),40)
    var detail_seed := int(data.get("detail_seed",17))
    for x in range(24,int(_world_width),spacing):
        var y := ground_y+30.0+float((x*37+detail_seed*19)%54)
        var lean := sin(float(x)*0.031)*4.0
        for blade in range(3):
            var bx := float(x)+float(blade-1)*6.0
            var tip := Vector2(bx-4.0+lean+float(blade-1)*3.0,y-12.0-float(blade%2)*5.0)
            StorybookStyle.crayon_line(self,Vector2(bx,y),tip,StorybookStyle.LEAF_DEEP,2.6,x+blade)

func _draw_path(data: Dictionary) -> void:
    var points := PackedVector2Array()
    for p in data.get("path_points",[]):
        if p is Dictionary: points.append(Vector2(float(p.get("x",0.0)),float(p.get("y",650.0))))
    if points.size()<2: return
    var half_width := float(data.get("path_width",150.0))*0.5
    var left := PackedVector2Array()
    var right := PackedVector2Array()
    for i in range(points.size()):
        var tangent := (points[mini(i+1,points.size()-1)]-points[maxi(i-1,0)]).normalized()
        var normal := Vector2(-tangent.y,tangent.x)
        left.append(points[i]+normal*half_width)
        right.append(points[i]-normal*half_width)
    var polygon := PackedVector2Array()
    for p in left: polygon.append(p)
    for i in range(right.size()-1,-1,-1): polygon.append(right[i])
    var path_colour := Color(str(data.get("path_colour","#f1d9a0")))
    draw_colored_polygon(polygon,path_colour)
    # A lighter stripe down the middle of the lane, like a worn trail.
    var core := PackedVector2Array()
    for i in range(points.size()):
        var tangent_c := (points[mini(i+1,points.size()-1)]-points[maxi(i-1,0)]).normalized()
        core.append(points[i]+Vector2(-tangent_c.y,tangent_c.x)*half_width*0.45)
    for i in range(points.size()-1,-1,-1):
        var tangent_d := (points[mini(i+1,points.size()-1)]-points[maxi(i-1,0)]).normalized()
        core.append(points[i]-Vector2(-tangent_d.y,tangent_d.x)*half_width*0.45)
    draw_colored_polygon(core,StorybookStyle.tone(path_colour,0.28))
    draw_polyline(StorybookStyle.wobble(left,11,2.0,false,36.0),StorybookStyle.OUTLINE_SOFT,4.0,true)
    draw_polyline(StorybookStyle.wobble(right,17,2.0,false,36.0),StorybookStyle.OUTLINE_SOFT,4.0,true)

func _draw_patches(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var p := Vector2(float(item.get("x",0.0)),float(item.get("y",580.0)))
        var r := Vector2(float(item.get("width",120.0))*0.5,float(item.get("height",30.0))*0.5)
        StorybookStyle.dab(self,p+Vector2(0,4),r,Color(StorybookStyle.GRASS_DEEP,0.28))
        StorybookStyle.dab(self,p,r*0.82,Color(str(item.get("colour","#a4e46d")),0.55))

func _draw_stones(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var p := Vector2(float(item.get("x",0.0)),float(item.get("y",660.0)))
        var s := float(item.get("size",1.0))
        StorybookStyle.blob_shadow(self,p+Vector2(2,4),16.0*s,0.3,0.2)
        StorybookStyle.outlined_ellipse(self,p,Vector2(14,6)*s,StorybookStyle.STONE,StorybookStyle.OUTLINE_SOFT,2.2,int(p.x))
        StorybookStyle.dab(self,p+Vector2(-3,-2)*s,Vector2(7,2.4)*s,Color("#fff6e0",0.8))

func _draw_flowers(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var x := float(item.get("x",0.0))
        var y := float(item.get("y",580.0))
        var bloom := Color(str(item.get("colour","#ff8fb0")))
        for i in range(int(item.get("count",7))):
            var px := x+float(i)*float(item.get("spacing",13.0))
            var py := y+sin(float(i)*1.7)*4.0
            StorybookStyle.crayon_line(self,Vector2(px,py+8),Vector2(px,py-4),StorybookStyle.LEAF_DEEP,2.2,i)
            for petal in range(5):
                var a := TAU*float(petal)/5.0
                draw_circle(Vector2(px+cos(a)*4.2,py-8.0+sin(a)*4.2),3.4,bloom)
            draw_circle(Vector2(px,py-8.0),2.6,StorybookStyle.BLOOM_YELLOW)
