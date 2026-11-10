extends Node2D
## Data-driven outdoor terrain, path and natural detail.

var _manifest: Dictionary = {}
var _world_width := 3600.0

func configure(room_manifest: Dictionary,world_width: float) -> void:
    if _manifest == room_manifest and is_equal_approx(_world_width,world_width): return
    _manifest = room_manifest.duplicate(true)
    _world_width = world_width
    queue_redraw()

func _draw() -> void:
    var data: Dictionary = _manifest.get("terrain",{})
    var ground_y := float(data.get("ground_y",560.0))
    var soil_y := float(data.get("soil_y",632.0))
    draw_colored_polygon(PackedVector2Array([Vector2(0,ground_y+26),Vector2(_world_width*0.12,ground_y-5),Vector2(_world_width*0.34,ground_y+12),Vector2(_world_width*0.58,ground_y-7),Vector2(_world_width*0.82,ground_y+8),Vector2(_world_width,ground_y-4),Vector2(_world_width,720),Vector2(0,720)]),Color(str(data.get("grass_base","#a6a17a"))))
    draw_rect(Rect2(0,soil_y,_world_width,720.0-soil_y),Color(str(data.get("soil","#8b8069"))))
    draw_line(Vector2(0,soil_y),Vector2(_world_width,soil_y),Color("#d0c29f",0.68),3.0)
    _draw_patches(data.get("patches",[]))
    _draw_path(data)
    _draw_stones(data.get("stones",[]))
    _draw_flowers(data.get("flower_beds",[]))
    for x in range(24,int(_world_width),maxi(int(data.get("tuft_spacing",112)),40)):
        var y := ground_y+28.0+float((x*37+int(data.get("detail_seed",17))*19)%54)
        for blade in range(3):
            var bx := float(x)+float(blade-1)*5.0
            draw_line(Vector2(bx,y),Vector2(bx-4.0+sin(float(x)*0.031)*3.0,y-9.0-float(blade%2)*4.0),Color("#5e7956",0.72),1.8)

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
    draw_colored_polygon(polygon,Color(str(data.get("path_colour","#c4b18f"))))
    draw_polyline(left,Color("#e0d0ae",0.72),3.0,true)
    draw_polyline(right,Color("#a58f70",0.5),2.0,true)

func _draw_patches(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var p := Vector2(float(item.get("x",0.0)),float(item.get("y",580.0)))
        var r := Vector2(float(item.get("width",120.0))*0.5,float(item.get("height",30.0))*0.5)
        draw_ellipse(p+Vector2(0,3),r,Color("#657b58",0.10))
        draw_ellipse(p,r*0.82,Color(str(item.get("colour","#8f9a68")),0.30))

func _draw_stones(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var p := Vector2(float(item.get("x",0.0)),float(item.get("y",660.0)))
        var s := float(item.get("size",1.0))
        draw_ellipse(p+Vector2(2,3),Vector2(15,5)*s,Color("#514b40",0.14))
        draw_ellipse(p,Vector2(13,4)*s,Color("#d7c9ad",0.72))
        draw_line(p+Vector2(-6,-1)*s,p+Vector2(5,-2)*s,Color("#f0e4ca",0.72),1.2)

func _draw_flowers(items: Array) -> void:
    for item in items:
        if not item is Dictionary: continue
        var x := float(item.get("x",0.0))
        var y := float(item.get("y",580.0))
        for i in range(int(item.get("count",7))):
            var px := x+float(i)*float(item.get("spacing",13.0))
            var py := y+sin(float(i)*1.7)*4.0
            draw_line(Vector2(px,py+7),Vector2(px,py-3),Color("#617d59"),1.5)
            draw_circle(Vector2(px,py-5),3.1,Color(str(item.get("colour","#d7a27c"))))
            draw_circle(Vector2(px+2,py-6),1.2,Color("#f0d9a1"))

func draw_ellipse(center: Vector2,radius: Vector2,colour: Color) -> void:
    var points := PackedVector2Array()
    for i in range(20):
        var a := TAU*float(i)/20.0
        points.append(center+Vector2(cos(a)*radius.x,sin(a)*radius.y))
    draw_colored_polygon(points,colour)
