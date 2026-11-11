extends Node2D
## A building is an independent world object, not part of the background plate.
## Position, footprint, palette and silhouette come from the presentation manifest.
## Drawn in the shared storybook style: crayon outlines, warm flat fills, and
## chunky rounded details. Geometry and light occluders are unchanged.

const StorybookStyle = preload("res://scripts/style/storybook_style.gd")

var definition: Dictionary = {}
var _occluder: LightOccluder2D
var _seed := 0
var _room_theme: Dictionary = {}

func configure(data: Dictionary,room_theme: Dictionary = {}) -> void:
    if definition == data and _room_theme == room_theme:
        return
    definition = data.duplicate(true)
    _room_theme = room_theme.duplicate(true)
    _seed = absi(str(definition.get("id","")).hash())%1000
    var h := float(definition.get("height",260.0))
    var sort_y := float(definition.get("y",0.0))+h
    # Keep the interior shell just behind actors standing on its front edge.
    if str(definition.get("style","")).begins_with("interior_"):
        sort_y -= 1.0
    position = Vector2(float(definition.get("x",0.0)),sort_y)
    queue_redraw()
    _configure_occluder()

func _configure_occluder() -> void:
    if _occluder:
        _occluder.queue_free()
    if str(definition.get("style","")).begins_with("interior_"):
        return
    _occluder = LightOccluder2D.new()
    var polygon := OccluderPolygon2D.new()
    var w := float(definition.get("width",260.0))
    var h := float(definition.get("height",260.0))
    polygon.polygon = PackedVector2Array([
        Vector2(-w*0.08,-h*1.28),Vector2(0,-h*1.58),
        Vector2(w*0.5,-h*1.58),Vector2(w*1.08,-h*1.28),
        Vector2(w,0),Vector2(0,0)
    ])
    _occluder.occluder = polygon
    add_child(_occluder)

func _arch_points(x: float,top: float,width: float,height: float) -> PackedVector2Array:
    # Door or window with a rounded top, built from straight sides and an arc.
    var radius := width*0.5
    var points := PackedVector2Array()
    points.append(Vector2(x,top+height))
    points.append(Vector2(x,top+radius))
    for i in range(1,9):
        var a := PI+PI*float(i)/9.0
        points.append(Vector2(x+radius,top+radius)+Vector2(cos(a),sin(a))*radius)
    points.append(Vector2(x+width,top+radius))
    points.append(Vector2(x+width,top+height))
    return points

func _draw() -> void:
    var w := float(definition.get("width",260.0))
    var h := float(definition.get("height",260.0))
    var wall := Color(str(definition.get("wall","#ffe6bd")))
    var roof := Color(str(definition.get("roof","#e2674a")))
    var ink := StorybookStyle.OUTLINE
    var style := str(definition.get("style","house"))
    draw_set_transform(Vector2(0.0,-h))
    if style.begins_with("interior_"):
        _draw_interior(w,h,style,wall,roof,_room_theme)
        draw_set_transform(Vector2.ZERO)
        return
    # A violet cast shadow plus a soft contact blob anchor the building to the lawn.
    draw_colored_polygon(PackedVector2Array([
        Vector2(-24,h+12),Vector2(w*0.5-5,-h*0.52+20),
        Vector2(w+42,h+20),Vector2(w+65,h+36),Vector2(-6,h+36)
    ]),Color(StorybookStyle.SHADOW_TINT,0.2))
    StorybookStyle.blob_shadow(self,Vector2(w*0.5,h+6),w*0.62,0.07,0.22)

    # Roof, then the return wall and roof plane that give the three-quarter view.
    var roof_shape := PackedVector2Array([
        Vector2(-24,8),Vector2(0,-h*0.28),Vector2(w*0.5,-h*0.58),
        Vector2(w+24,-h*0.28),Vector2(w+12,12)
    ])
    StorybookStyle.outlined_polygon(self,roof_shape,roof,ink,4.5,_seed,1.6)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([
        Vector2(w,0),Vector2(w+34,-h*0.12),Vector2(w+34,h-14),Vector2(w,h)
    ]),StorybookStyle.tone(wall,-0.24),ink,4.0,_seed+1,1.2)
    StorybookStyle.outlined_polygon(self,PackedVector2Array([
        Vector2(w*0.5,-h*0.58),Vector2(w+24,-h*0.28),
        Vector2(w+58,-h*0.40),Vector2(w*0.5+22,-h*0.70)
    ]),StorybookStyle.tone(roof,-0.18),ink,4.0,_seed+2,1.4)
    # Sun-lit ridge stripe and tile courses read as painted roof tiles.
    StorybookStyle.crayon_line(self,Vector2(6,-h*0.27),Vector2(w*0.5,-h*0.565),StorybookStyle.tone(roof,0.32),5.0,_seed)
    for seam in range(0,5):
        var seam_y := -h*0.40+float(seam)*h*0.075
        StorybookStyle.crayon_line(self,Vector2(22,seam_y),Vector2(w*0.5-10,seam_y-h*0.14),StorybookStyle.tone(roof,-0.16),2.4,_seed+seam)
        StorybookStyle.crayon_line(self,Vector2(w*0.5+10,seam_y-h*0.14),Vector2(w-14,seam_y),StorybookStyle.tone(roof,-0.22),2.2,_seed+seam+9)

    # Front wall with a warm shaded foot.
    StorybookStyle.outlined_rect(self,Rect2(0,0,w,h),wall,ink,4.5,_seed+3,1.6)
    draw_rect(Rect2(5,h-30,w-10,26),Color(StorybookStyle.SHADOW_TINT,0.14))
    StorybookStyle.dab(self,Vector2(w*0.2,h*0.5),Vector2(w*0.16,h*0.34),Color(StorybookStyle.CREAM,0.28))

    # Painted name plate.
    var plate := Rect2(24,26,w-48,38)
    StorybookStyle.outlined_rounded_rect(self,plate,9.0,StorybookStyle.tone(wall,0.35),ink,3.2,_seed+4,0.8)
    draw_string(ThemeDB.fallback_font,Vector2(plate.position.x,plate.position.y+26),str(definition.get("label","BUILDING")).to_upper(),HORIZONTAL_ALIGNMENT_CENTER,plate.size.x,17,ink)

    # Two bright windows with a glint, cross bars and a sill.
    for wx in [34.0,w-94.0]:
        StorybookStyle.outlined_rounded_rect(self,Rect2(wx-3,96,66,84),8.0,StorybookStyle.WOOD,ink,3.4,_seed+5,0.8)
        StorybookStyle.outlined_rect(self,Rect2(wx+5,104,50,66),Color("#9ee4ff"),ink,2.4,_seed+6,0.6)
        draw_colored_polygon(PackedVector2Array([Vector2(wx+11,108),Vector2(wx+27,108),Vector2(wx+13,150),Vector2(wx+8,150)]),Color("#ffffff",0.55))
        StorybookStyle.crayon_line(self,Vector2(wx+30,104),Vector2(wx+30,170),ink,2.6,_seed)
        StorybookStyle.crayon_line(self,Vector2(wx+5,137),Vector2(wx+55,137),ink,2.4,_seed+1)
        StorybookStyle.outlined_rect(self,Rect2(wx-8,178,76,9),StorybookStyle.tone(StorybookStyle.WOOD,0.2),ink,2.6,_seed+7,0.5)

    # Arched front door with a round window and a brass knob.
    var door_x := w*0.5-35
    StorybookStyle.outlined_polygon(self,_arch_points(door_x,h-122,70,122),StorybookStyle.WOOD_DEEP,ink,4.0,_seed+8,1.0)
    StorybookStyle.outlined_polygon(self,_arch_points(door_x+9,h-112,52,112),StorybookStyle.WOOD,ink,2.4,_seed+9,0.8)
    StorybookStyle.outlined_circle(self,Vector2(door_x+35,h-84),9.0,Color("#9ee4ff"),ink,2.2,_seed)
    StorybookStyle.outlined_circle(self,Vector2(door_x+52,h-52),4.2,Color("#ffd23f"),ink,1.8,_seed+1,0.3)
    StorybookStyle.outlined_rect(self,Rect2(door_x-10,h-4,90,8),StorybookStyle.STONE,ink,2.6,_seed+10,0.6)

    # Distinctive signatures keep each building recognisable.
    if style == "shop":
        StorybookStyle.outlined_rect(self,Rect2(-5,82,w+10,18),Color("#fff3d2"),ink,3.2,_seed+11,0.8)
        for awning_x in range(12,int(w)-12,42):
            var stripe := int(awning_x / 42) % 2 == 0
            StorybookStyle.outlined_polygon(self,PackedVector2Array([
                Vector2(float(awning_x),100),Vector2(float(awning_x+38),100),
                Vector2(float(awning_x+34),128),Vector2(float(awning_x+19),136),Vector2(float(awning_x+4),128)
            ]),Color("#ff6f59") if stripe else Color("#fff3d2"),ink,2.6,_seed+awning_x,0.8)
    elif style == "bakery":
        StorybookStyle.outlined_rect(self,Rect2(w-72,-h*0.58,34,86),StorybookStyle.tone(StorybookStyle.TERRACOTTA,-0.1),ink,3.6,_seed+12,1.0)
        StorybookStyle.outlined_rect(self,Rect2(w-78,-h*0.58-9,46,12),StorybookStyle.WOOD_DEEP,ink,3.2,_seed+13,0.8)
        for puff in range(3):
            StorybookStyle.outlined_circle(self,Vector2(w-55+float(puff)*7.0,-h*0.58-30.0-float(puff)*18.0),7.0+float(puff)*2.5,Color("#ffffff",0.9),Color("#c9d9ea"),1.8,_seed+puff,0.3)
        var bake_sign := Rect2(w*0.5-52,h-158,104,24)
        StorybookStyle.outlined_rounded_rect(self,bake_sign,8.0,StorybookStyle.TERRACOTTA,ink,3.0,_seed+14,0.7)
        draw_string(ThemeDB.fallback_font,Vector2(bake_sign.position.x,bake_sign.position.y+17),"BAKERY",HORIZONTAL_ALIGNMENT_CENTER,bake_sign.size.x,13,Color("#fff3d2"))
    elif style == "civic":
        for column_x in [48.0,w-62.0]:
            StorybookStyle.outlined_rect(self,Rect2(column_x,h-190,14,190),Color("#fff3d2"),ink,3.0,_seed+int(column_x),0.8)
            StorybookStyle.outlined_rect(self,Rect2(column_x-7,h-196,28,12),StorybookStyle.tone(wall,-0.1),ink,2.8,_seed+int(column_x)+1,0.6)
            StorybookStyle.outlined_rect(self,Rect2(column_x-7,h-10,28,12),StorybookStyle.tone(wall,-0.1),ink,2.8,_seed+int(column_x)+2,0.6)
        StorybookStyle.outlined_circle(self,Vector2(w*0.5,17),16.0,Color("#fff3d2"),ink,3.0,_seed+15,0.5)
        StorybookStyle.crayon_line(self,Vector2(w*0.5,17),Vector2(w*0.5,7),ink,2.2,_seed)
        StorybookStyle.crayon_line(self,Vector2(w*0.5,17),Vector2(w*0.5+8,21),ink,2.2,_seed+1)
    elif style == "tavern":
        var board := Rect2(w*0.5-66,72,132,48)
        StorybookStyle.outlined_rounded_rect(self,board,8.0,StorybookStyle.WOOD_DEEP,ink,3.4,_seed+16,0.8)
        StorybookStyle.outlined_rounded_rect(self,board.grow(-6),5.0,Color("#ffe3a8"),ink,2.0,_seed+17,0.5)
        draw_string(ThemeDB.fallback_font,Vector2(board.position.x,board.position.y+30),"THE TAVERN",HORIZONTAL_ALIGNMENT_CENTER,board.size.x,13,ink)
    _draw_facade_details(w,h,roof,ink)

    # Eaves and corner posts frame the facade.
    StorybookStyle.outlined_rect(self,Rect2(-10,6,w+20,12),StorybookStyle.tone(roof,-0.1),ink,3.6,_seed+18,0.8)
    draw_set_transform(Vector2.ZERO)

func _draw_facade_details(w: float,h: float,roof: Color,ink: Color) -> void:
    # Optional facade treatments are manifest-driven so buildings can share
    # the same renderer without sharing the same architectural identity.
    var facade: Dictionary = definition.get("facade",{})
    if bool(facade.get("corner_stones",false)):
        var stone := Color(str(facade.get("stone_colour","#fff0d2")))
        for corner_x in [6.0,w-20.0]:
            for course in range(5):
                StorybookStyle.outlined_rect(self,Rect2(corner_x,82.0+float(course)*42.0,14,30),stone.darkened(0.03 if course%2==0 else 0.09),ink,2.2,_seed+course,0.5)
    if bool(facade.get("shutters",false)):
        var shutter := Color(str(facade.get("shutter_colour","#3fb59d")))
        for window_x in [34.0,w-94.0]:
            for side in [-1.0,1.0]:
                var sx := window_x-17.0 if side < 0.0 else window_x+66.0
                StorybookStyle.outlined_rect(self,Rect2(sx,98,13,82),shutter,ink,2.6,_seed+int(sx),0.6)
                for rail_y in [112.0,134.0,156.0]:
                    StorybookStyle.crayon_line(self,Vector2(sx+2,rail_y),Vector2(sx+11,rail_y),StorybookStyle.tone(shutter,0.3),1.8,int(rail_y))
    if bool(facade.get("window_boxes",false)):
        var box_colour := Color(str(facade.get("box_colour","#c47a4a")))
        var bloom_colour := Color(str(facade.get("bloom_colour","#ff8fb0")))
        for window_x in [34.0,w-94.0]:
            for flower_index in range(5):
                var flower_x := window_x+float(flower_index)*13.0+2.0
                StorybookStyle.crayon_line(self,Vector2(flower_x,184),Vector2(flower_x-2,172),StorybookStyle.LEAF_DEEP,2.2,flower_index)
                StorybookStyle.outlined_circle(self,Vector2(flower_x-2,167),5.0,bloom_colour,ink,1.6,flower_index+_seed,0.2)
                draw_circle(Vector2(flower_x-2,167),1.9,StorybookStyle.BLOOM_YELLOW)
            StorybookStyle.outlined_rect(self,Rect2(window_x-6,183,72,11),box_colour,ink,2.8,_seed+int(window_x),0.5)
    if bool(facade.get("roof_crest",false)):
        var crest_colour := Color(str(facade.get("crest_colour","#ffd23f")))
        StorybookStyle.outlined_polygon(self,PackedVector2Array([
            Vector2(w*0.5-24,-h*0.57),Vector2(w*0.5,-h*0.70),
            Vector2(w*0.5+24,-h*0.57),Vector2(w*0.5,-h*0.52)
        ]),crest_colour,ink,3.0,_seed+20,0.8)
        StorybookStyle.outlined_circle(self,Vector2(w*0.5,-h*0.60),6.0,StorybookStyle.tone(roof,-0.1),ink,2.2,_seed,0.3)
    var sign_text := str(facade.get("sign_text",""))
    if not sign_text.is_empty():
        var sign_width := minf(w-52.0,float(facade.get("sign_width",150.0)))
        var sign_x := (w-sign_width)*0.5
        var sign_y := float(facade.get("sign_y",70.0))
        var sign_fill := Color(str(facade.get("sign_colour","#fff3d2")))
        var sign_rect := Rect2(sign_x,sign_y,sign_width,30)
        StorybookStyle.outlined_rounded_rect(self,sign_rect,8.0,sign_fill,ink,3.0,_seed+21,0.7)
        draw_string(ThemeDB.fallback_font,Vector2(sign_x,sign_y+21),sign_text.to_upper(),HORIZONTAL_ALIGNMENT_CENTER,sign_width,11,ink)

func _theme_color(theme: Dictionary,key: String,fallback: Color) -> Color:
    # Manifest colours win; the storybook grade only warms and brightens them.
    var value: Variant = theme.get(key,fallback)
    var colour: Color = value if value is Color else Color(str(value))
    return StorybookStyle.vivid(colour,0.8)

func _draw_interior(w: float,h: float,style: String,wall: Color,trim: Color,theme: Dictionary) -> void:
    # Architectural room shell only. Furniture is independently positioned and Y-sorted.
    var ink := StorybookStyle.OUTLINE
    var floor_y := h*0.70
    var wall_colour := _theme_color(theme,"wall_color",wall)
    var trim_colour := _theme_color(theme,"trim_color",trim)
    var floor_colour := _theme_color(theme,"floor_color",StorybookStyle.interior_floor_colour(style))
    var window_frame := _theme_color(theme,"window_frame_color",trim_colour)
    var window_glass := _theme_color(theme,"window_glass_color",Color("#9ee4ff"))
    var curtain := _theme_color(theme,"curtain_color",Color("#ff9fb3"))
    var sconce := _theme_color(theme,"sconce_color",Color("#ffd86a"))
    var art_primary := _theme_color(theme,"art_primary_color",StorybookStyle.LEAF)
    var art_secondary := _theme_color(theme,"art_secondary_color",Color("#bfeaff"))
    var door := _theme_color(theme,"door_color",StorybookStyle.WOOD_DEEP)
    var hardware := _theme_color(theme,"hardware_color",Color("#ffd23f"))
    draw_rect(Rect2(0,0,w,floor_y),wall_colour)
    draw_rect(Rect2(0,floor_y,w,h-floor_y),floor_colour)
    var wall_detail := str(theme.get("wall_detail","panel"))
    if wall_detail == "panel":
        # Wallpaper stripes give the long wall a cheerful rhythm.
        for stripe_x in range(60,int(w),120):
            draw_rect(Rect2(float(stripe_x),30,40,floor_y-60),Color(StorybookStyle.CREAM,0.25))
    draw_rect(Rect2(0,floor_y-14,w,14),trim_colour)
    StorybookStyle.crayon_line(self,Vector2(0,floor_y-14),Vector2(w,floor_y-14),ink,3.2,_seed)
    StorybookStyle.crayon_line(self,Vector2(0,floor_y),Vector2(w,floor_y),ink,3.6,_seed+1)
    draw_rect(Rect2(0,0,w,18),StorybookStyle.tone(trim_colour,-0.15))
    StorybookStyle.crayon_line(self,Vector2(0,18),Vector2(w,18),ink,3.2,_seed+2)
    for beam_x in range(0,int(w),240):
        StorybookStyle.outlined_rect(self,Rect2(float(beam_x),18,14,floor_y-32),StorybookStyle.tone(trim_colour,0.1),ink,2.6,_seed+beam_x,0.8)
        if wall_detail == "panel":
            StorybookStyle.crayon_line(self,Vector2(float(beam_x+16),floor_y+8),Vector2(float(beam_x+16),h-5),StorybookStyle.tone(floor_colour,-0.18),2.2,beam_x)
    var window_positions: Array = theme.get("window_positions",[0.18,0.52,0.82])
    for ratio in window_positions:
        var window_x := clampf(float(ratio),0.08,0.92)*w
        StorybookStyle.outlined_rounded_rect(self,Rect2(window_x-54,50,108,126),10.0,window_frame,ink,3.6,_seed+int(window_x),0.9)
        StorybookStyle.outlined_rect(self,Rect2(window_x-44,60,88,106),window_glass,ink,2.6,_seed+int(window_x)+1,0.6)
        draw_colored_polygon(PackedVector2Array([Vector2(window_x-34,64),Vector2(window_x-8,64),Vector2(window_x-30,120),Vector2(window_x-40,120)]),Color("#ffffff",0.5))
        StorybookStyle.crayon_line(self,Vector2(window_x,60),Vector2(window_x,166),ink,3.0,_seed)
        StorybookStyle.crayon_line(self,Vector2(window_x-44,112),Vector2(window_x+44,112),ink,3.0,_seed+1)
        StorybookStyle.outlined_rect(self,Rect2(window_x-62,174,124,10),StorybookStyle.tone(trim_colour,0.2),ink,2.8,_seed+int(window_x)+2,0.6)
        # Soft curtains tied back at both sides.
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(window_x-48,56),Vector2(window_x-24,62),Vector2(window_x-32,112),Vector2(window_x-28,166),Vector2(window_x-48,168)]),curtain,ink,2.4,_seed+int(window_x)+3,0.8)
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(window_x+48,56),Vector2(window_x+24,62),Vector2(window_x+32,112),Vector2(window_x+28,166),Vector2(window_x+48,168)]),curtain,ink,2.4,_seed+int(window_x)+4,0.8)
    var panel_spacing := maxi(int(theme.get("panel_spacing",160)),80)
    for panel_x in range(80,int(w)-80,panel_spacing):
        StorybookStyle.outlined_rounded_rect(self,Rect2(float(panel_x),floor_y-84,float(panel_spacing)-42.0,66),8.0,Color(StorybookStyle.CREAM,0.0),StorybookStyle.tone(wall_colour,-0.14),2.0,_seed+panel_x,0.5)
    # Wall lamps with a warm halo and framed pictures give the walls human scale.
    for sconce_x in [w*0.34,w*0.68]:
        draw_circle(Vector2(sconce_x,floor_y-143),20.0,Color(sconce,0.18))
        StorybookStyle.outlined_rect(self,Rect2(sconce_x-5,floor_y-142,10,22),StorybookStyle.tone(trim_colour,-0.2),ink,2.2,_seed+int(sconce_x),0.4)
        StorybookStyle.outlined_polygon(self,PackedVector2Array([Vector2(sconce_x-13,floor_y-145),Vector2(sconce_x,floor_y-168),Vector2(sconce_x+13,floor_y-145)]),sconce,ink,2.4,_seed+int(sconce_x)+1,0.5)
    for picture_x in [w*0.27,w*0.75]:
        StorybookStyle.outlined_rounded_rect(self,Rect2(picture_x-27,floor_y-134,54,44),5.0,StorybookStyle.WOOD,ink,2.8,_seed+int(picture_x),0.6)
        draw_rect(Rect2(picture_x-21,floor_y-128,42,32),art_secondary)
        draw_colored_polygon(PackedVector2Array([Vector2(picture_x-21,floor_y-96),Vector2(picture_x-8,floor_y-118),Vector2(picture_x+2,floor_y-106),Vector2(picture_x+12,floor_y-121),Vector2(picture_x+21,floor_y-96)]),art_primary)
        draw_circle(Vector2(picture_x+12,floor_y-118),4.5,StorybookStyle.SUN)
    # Arched exit door on the left wall.
    StorybookStyle.outlined_polygon(self,_arch_points(28,floor_y-176,92,176),StorybookStyle.tone(door,-0.1),ink,3.8,_seed+30,1.0)
    StorybookStyle.outlined_polygon(self,_arch_points(38,floor_y-164,72,164),StorybookStyle.tone(door,0.12),ink,2.4,_seed+31,0.8)
    StorybookStyle.outlined_circle(self,Vector2(99,floor_y-82),4.5,hardware,ink,1.8,_seed+32,0.3)
    var floor_material := str(theme.get("floor_material",""))
    if floor_material.is_empty():
        floor_material = "tile" if style == "interior_shop" or style == "interior_bakery" else "plank"
    if floor_material == "tile" or floor_material == "stone":
        # Perspective tile joints converge subtly toward the back wall.
        for tile in range(1,9):
            var tile_x := float(tile)*w/9.0
            StorybookStyle.crayon_line(self,Vector2(tile_x,floor_y+2),Vector2(w*0.5+(tile_x-w*0.5)*1.7,h),StorybookStyle.tone(floor_colour,-0.2),1.8,tile)
        for row in range(1,5):
            var tile_y := floor_y+float(row)*(h-floor_y)/5.0
            StorybookStyle.crayon_line(self,Vector2(0,tile_y),Vector2(w,tile_y),StorybookStyle.tone(floor_colour,-0.16),1.6,row)
    else:
        for plank in range(1,10):
            var plank_x := float(plank)*w/10.0
            StorybookStyle.crayon_line(self,Vector2(plank_x,floor_y+10),Vector2(plank_x+18,h),StorybookStyle.tone(floor_colour,-0.2),2.0,plank)
        for seam in range(1,6):
            var seam_y := floor_y+float(seam)*(h-floor_y)/6.0
            StorybookStyle.crayon_line(self,Vector2(0,seam_y),Vector2(w,seam_y),StorybookStyle.tone(floor_colour,-0.14),1.5,seam)
    StorybookStyle.crayon_line(self,Vector2(0,h-3),Vector2(w,h-3),ink,3.4,_seed+40)
