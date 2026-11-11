extends Node2D
## A building is an independent world object, not part of the background plate.
## Position, footprint, palette and silhouette come from the presentation manifest.

var definition: Dictionary = {}
var _room_theme: Dictionary = {}
var _occluder: LightOccluder2D

func configure(data: Dictionary,room_theme: Dictionary = {}) -> void:
    if definition == data and _room_theme == room_theme:
        return
    definition = data.duplicate(true)
    _room_theme = room_theme.duplicate(true)
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

func _draw() -> void:
    var w := float(definition.get("width",260.0))
    var h := float(definition.get("height",260.0))
    var wall := Color(str(definition.get("wall","#d8c8a8")))
    var roof := Color(str(definition.get("roof","#6e5949")))
    var ink := Color("#4f493e")
    var style := str(definition.get("style","house"))
    draw_set_transform(Vector2(0.0,-h))
    if style.begins_with("interior_"):
        _draw_interior(w,h,style,wall,roof,_room_theme)
        draw_set_transform(Vector2.ZERO)
        return
    # Contact shadow and an offset cast shadow anchor the silhouette to the ground.
    draw_colored_polygon(PackedVector2Array([
        Vector2(-24,h+12),Vector2(w*0.5-5,-h*0.52+20),
        Vector2(w+42,h+20),Vector2(w+65,h+36),Vector2(-6,h+36)
    ]),Color("#403a32",0.18))
    draw_colored_polygon(PackedVector2Array([
        Vector2(-24,8),Vector2(0,-h*0.28),Vector2(w*0.5,-h*0.58),
        Vector2(w+24,-h*0.28),Vector2(w+12,12)
    ]),roof)
    # The right return wall and roof plane establish a consistent three-quarter view.
    draw_colored_polygon(PackedVector2Array([
        Vector2(w,0),Vector2(w+34,-h*0.12),Vector2(w+34,h-14),Vector2(w,h)
    ]),wall.darkened(0.16))
    draw_colored_polygon(PackedVector2Array([
        Vector2(w*0.5,-h*0.58),Vector2(w+24,-h*0.28),
        Vector2(w+58,-h*0.40),Vector2(w*0.5+22,-h*0.70)
    ]),roof.darkened(0.12))
    draw_rect(Rect2(0,0,w,h),wall)
    draw_rect(Rect2(14,14,w-28,28),wall.lightened(0.12))
    draw_rect(Rect2(24,42,w-48,24),roof.darkened(0.08))
    draw_string(ThemeDB.fallback_font,Vector2(34,61),str(definition.get("label","BUILDING")).to_upper(),HORIZONTAL_ALIGNMENT_LEFT,w-68,16,ink)
    for wx in [34.0,w-94.0]:
        draw_rect(Rect2(wx,100,60,76),Color("#5b6f69"))
        draw_rect(Rect2(wx+6,106,48,64),Color("#c6d0b4"))
        draw_line(Vector2(wx+30,106),Vector2(wx+30,170),ink,3.0)
        draw_line(Vector2(wx+6,138),Vector2(wx+54,138),ink,2.0)
        draw_rect(Rect2(wx-5,174,70,7),roof)
    var door_x := w*0.5-35
    draw_rect(Rect2(door_x,h-118,70,118),Color("#614b3b"))
    draw_rect(Rect2(door_x+7,h-111,56,111),Color("#927253"))
    draw_circle(Vector2(door_x+50,h-58),4.0,Color("#d7b46f"))
    # Distinctive architectural signatures keep each building recognisable.
    if style == "shop":
        draw_rect(Rect2(-5,82,w+10,18),Color("#ead9b9"))
        for awning_x in range(12,int(w)-12,42):
            var stripe := int(awning_x / 42) % 2 == 0
            draw_colored_polygon(PackedVector2Array([
                Vector2(float(awning_x),100),Vector2(float(awning_x+38),100),
                Vector2(float(awning_x+32),130),Vector2(float(awning_x+5),130)
            ]),Color("#b96f55") if stripe else Color("#e8d8b8"))
    elif style == "bakery":
        draw_rect(Rect2(w-72,-h*0.58,34,86),Color("#8a6a52"))
        draw_rect(Rect2(w-78,-h*0.58-8,46,10),Color("#6c5545"))
        draw_rect(Rect2(w*0.5-52,h-154,104,22),Color("#a65f47"))
        draw_string(ThemeDB.fallback_font,Vector2(w*0.5-45,h-137),"BAKERY",HORIZONTAL_ALIGNMENT_CENTER,90,12,Color("#f6e8cf"))
    elif style == "civic":
        for column_x in [48.0,w-62.0]:
            draw_rect(Rect2(column_x,h-190,14,190),Color("#eee0c3"))
            draw_rect(Rect2(column_x-6,h-190,26,10),Color("#a18a6c"))
            draw_rect(Rect2(column_x-6,h-8,26,10),Color("#a18a6c"))
        draw_rect(Rect2(w*0.5-52,18,104,42),Color("#eee0c3"))
        draw_circle(Vector2(w*0.5,39),15.0,Color("#b58a58"),false,2.0)
    elif style == "tavern":
        draw_rect(Rect2(w*0.5-64,74,128,46),Color("#5a4334"))
        draw_rect(Rect2(w*0.5-58,80,116,34),Color("#d6bd91"))
        draw_string(ThemeDB.fallback_font,Vector2(w*0.5-52,102),"THE TAVERN",HORIZONTAL_ALIGNMENT_CENTER,104,12,Color("#514235"))
    _draw_facade_details(w,h,roof,ink)
    # Subtle roof seams and facade courses add readable material scale.
    for seam in range(0,5):
        var seam_y := -h*0.40+float(seam)*h*0.075
        draw_line(Vector2(20,seam_y),Vector2(w*0.5-8,seam_y-h*0.14),roof.lightened(0.12),1.4)
        draw_line(Vector2(w*0.5+8,seam_y-h*0.14),Vector2(w-12,seam_y),roof.darkened(0.08),1.2)
    for course in range(1,7):
        var course_y := float(course)*h/7.0
        draw_line(Vector2(12,course_y),Vector2(w-12,course_y),wall.darkened(0.07),1.0)
    # Roof eaves and corner timber add depth without baking the building into scenery.
    draw_rect(Rect2(-8,8,w+16,9),roof.darkened(0.12))
    draw_rect(Rect2(0,0,10,h),roof.darkened(0.12))
    draw_rect(Rect2(w-10,0,10,h),roof.darkened(0.12))
    draw_set_transform(Vector2.ZERO)


func _draw_facade_details(w: float,h: float,roof: Color,ink: Color) -> void:
    # Optional facade treatments are manifest-driven so buildings can share
    # the same renderer without sharing the same architectural identity.
    var facade: Dictionary = definition.get("facade",{})
    if bool(facade.get("corner_stones",false)):
        var stone := Color(str(facade.get("stone_colour","#e6d7b9")))
        for corner_x in [8.0,w-20.0]:
            for course in range(5):
                draw_rect(Rect2(corner_x,82.0+float(course)*42.0,12,28),stone.darkened(0.04 if course%2==0 else 0.10))
    if bool(facade.get("shutters",false)):
        var shutter := Color(str(facade.get("shutter_colour","#765b48")))
        for window_x in [34.0,w-94.0]:
            draw_rect(Rect2(window_x-13,99,10,80),shutter)
            draw_rect(Rect2(window_x+63,99,10,80),shutter)
            for rail_y in [112.0,136.0,160.0]:
                draw_line(Vector2(window_x-12,rail_y),Vector2(window_x-4,rail_y),shutter.lightened(0.18),1.2)
                draw_line(Vector2(window_x+64,rail_y),Vector2(window_x+72,rail_y),shutter.lightened(0.18),1.2)
    if bool(facade.get("window_boxes",false)):
        var box_colour := Color(str(facade.get("box_colour","#79583f")))
        var bloom_colour := Color(str(facade.get("bloom_colour","#d99b79")))
        for window_x in [34.0,w-94.0]:
            draw_rect(Rect2(window_x-5,181,70,9),box_colour)
            for flower_index in range(5):
                var flower_x := window_x+float(flower_index)*13.0+2.0
                draw_line(Vector2(flower_x,181),Vector2(flower_x-2,169),Color("#587653"),1.4)
                draw_circle(Vector2(flower_x-2,166),3.5,bloom_colour)
                draw_circle(Vector2(flower_x+2,168),2.5,Color("#e8d4a8"))
    if bool(facade.get("roof_crest",false)):
        var crest_colour := Color(str(facade.get("crest_colour","#d8bd8c")))
        draw_colored_polygon(PackedVector2Array([
            Vector2(w*0.5-24,-h*0.57),Vector2(w*0.5,-h*0.70),
            Vector2(w*0.5+24,-h*0.57),Vector2(w*0.5,-h*0.54)
        ]),crest_colour)
        draw_circle(Vector2(w*0.5,-h*0.60),5.0,roof.darkened(0.12))
    var sign_text := str(facade.get("sign_text",""))
    if not sign_text.is_empty():
        var sign_width := minf(w-52.0,float(facade.get("sign_width",150.0)))
        var sign_x := (w-sign_width)*0.5
        var sign_y := float(facade.get("sign_y",70.0))
        var sign_fill := Color(str(facade.get("sign_colour","#ead9b9")))
        draw_rect(Rect2(sign_x,sign_y,sign_width,28),roof.darkened(0.08))
        draw_rect(Rect2(sign_x+3,sign_y+3,sign_width-6,22),sign_fill)
        draw_string(ThemeDB.fallback_font,Vector2(sign_x+6,sign_y+21),sign_text.to_upper(),HORIZONTAL_ALIGNMENT_CENTER,sign_width-12,11,ink)

func _theme_color(theme: Dictionary,key: String,fallback: Color) -> Color:
    var value: Variant = theme.get(key,fallback)
    if value is Color:
        return value
    return Color(str(value))

func _draw_interior(w: float,h: float,style: String,wall: Color,trim: Color,theme: Dictionary) -> void:
    var floor_y := h*0.70
    var wall_colour := _theme_color(theme,"wall_color",wall)
    var floor_colour := _theme_color(theme,"floor_color",Color("#c9b18b"))
    var trim_colour := _theme_color(theme,"trim_color",trim)
    if style == "interior_tavern" and not theme.has("floor_color"):
        floor_colour = Color("#9a795a")
    elif style == "interior_shop" and not theme.has("floor_color"):
        floor_colour = Color("#d1b98e")
    elif style == "interior_bakery" and not theme.has("floor_color"):
        floor_colour = Color("#d6bd94")
    var window_frame := _theme_color(theme,"window_frame_color",trim_colour.darkened(0.22))
    var window_glass := _theme_color(theme,"window_glass_color",Color("#9ab5ad"))
    var curtain := _theme_color(theme,"curtain_color",Color("#eee2ca"))
    var sconce := _theme_color(theme,"sconce_color",Color("#d6b47a"))
    var art_primary := _theme_color(theme,"art_primary_color",Color("#71836c"))
    var art_secondary := _theme_color(theme,"art_secondary_color",Color("#d6c39f"))
    var door := _theme_color(theme,"door_color",Color("#584638"))
    draw_rect(Rect2(0,0,w,floor_y),wall_colour)
    draw_rect(Rect2(0,floor_y,w,h-floor_y),floor_colour)
    draw_rect(Rect2(0,floor_y-14,w,14),trim_colour.darkened(0.08))
    draw_rect(Rect2(0,0,w,18),trim_colour.darkened(0.18))
    var wall_detail := str(theme.get("wall_detail","panel"))
    for beam_x in range(0,int(w),240):
        draw_rect(Rect2(float(beam_x),18,12,floor_y-18),wall_colour.darkened(0.10))
        if wall_detail == "panel":
            draw_line(Vector2(float(beam_x+15),floor_y+8),Vector2(float(beam_x+15),h-5),floor_colour.darkened(0.12),1.2)
    var window_positions: Array = theme.get("window_positions",[0.18,0.52,0.82])
    for ratio in window_positions:
        var wx := clampf(float(ratio),0.08,0.92)*w
        draw_rect(Rect2(wx-52,54,104,118),window_frame.darkened(0.22))
        draw_rect(Rect2(wx-44,62,88,102),window_glass.darkened(0.08))
        draw_rect(Rect2(wx-38,68,76,90),window_glass.lightened(0.16))
        draw_rect(Rect2(wx-35,72,70,82),window_glass)
        draw_rect(Rect2(wx-4,62,8,102),window_frame)
        draw_rect(Rect2(wx-44,108,88,6),window_frame)
        draw_rect(Rect2(wx-58,174,116,8),trim_colour.lightened(0.12))
        draw_rect(Rect2(wx-62,182,124,4),trim_colour.darkened(0.18))
        draw_colored_polygon(PackedVector2Array([Vector2(wx-39,68),Vector2(wx-27,72),Vector2(wx-28,154),Vector2(wx-39,160)]),curtain)
        draw_colored_polygon(PackedVector2Array([Vector2(wx+39,68),Vector2(wx+27,72),Vector2(wx+28,154),Vector2(wx+39,160)]),curtain)
        draw_line(Vector2(wx-30,78),Vector2(wx-31,150),curtain.darkened(0.16),1.2)
        draw_line(Vector2(wx+30,78),Vector2(wx+31,150),curtain.darkened(0.16),1.2)
    var panel_spacing := maxi(int(theme.get("panel_spacing",160)),80)
    for panel_x in range(80,int(w)-80,panel_spacing):
        draw_rect(Rect2(float(panel_x),floor_y-82,float(panel_spacing)-42,64),wall_colour.darkened(0.045),false,1.5)
        draw_line(Vector2(float(panel_x+8),floor_y-74),Vector2(float(panel_x)+float(panel_spacing)-42,floor_y-74),wall_colour.lightened(0.08),1.0)
    for sconce_x in [w*0.34,w*0.68]:
        draw_rect(Rect2(sconce_x-5,floor_y-142,10,22),trim_colour.darkened(0.2))
        draw_colored_polygon(PackedVector2Array([Vector2(sconce_x-12,floor_y-145),Vector2(sconce_x,floor_y-166),Vector2(sconce_x+12,floor_y-145)]),sconce)
        draw_circle(Vector2(sconce_x,floor_y-143),13.0,Color(sconce.r,sconce.g,sconce.b,0.10))
    for picture_x in [w*0.27,w*0.75]:
        draw_rect(Rect2(picture_x-25,floor_y-132,50,42),trim_colour.darkened(0.18))
        draw_rect(Rect2(picture_x-20,floor_y-127,40,32),art_secondary)
        draw_colored_polygon(PackedVector2Array([Vector2(picture_x-16,floor_y-101),Vector2(picture_x-4,floor_y-119),Vector2(picture_x+4,floor_y-108),Vector2(picture_x+15,floor_y-122),Vector2(picture_x+17,floor_y-101)]),art_primary)
    draw_rect(Rect2(28,floor_y-172,92,172),door.darkened(0.08))
    draw_rect(Rect2(35,floor_y-165,78,165),door)
    draw_rect(Rect2(42,floor_y-156,64,156),door.lightened(0.12))
    var hardware := _theme_color(theme,"hardware_color",Color("#d7b46f"))
    draw_circle(Vector2(99,floor_y-82),3.5,hardware)
    var floor_material := str(theme.get("floor_material",""))
    if floor_material.is_empty():
        floor_material = "tile" if style == "interior_shop" or style == "interior_bakery" else "plank"
    if floor_material == "tile" or floor_material == "stone":
        for tile in range(1,9):
            var tx := float(tile)*w/9.0
            draw_line(Vector2(tx,floor_y+2),Vector2(w*0.5+(tx-w*0.5)*1.7,h),floor_colour.darkened(0.12),1.0)
        for row in range(1,5):
            var ty := floor_y+float(row)*(h-floor_y)/5.0
            draw_line(Vector2(0,ty),Vector2(w,ty),floor_colour.darkened(0.10),1.0)
    else:
        for plank in range(1,10):
            var px := float(plank)*w/10.0
            draw_line(Vector2(px,floor_y+10),Vector2(px+18,h),floor_colour.darkened(0.10),1.2)
        for seam in range(1,6):
            var sy := floor_y+float(seam)*(h-floor_y)/6.0
            draw_line(Vector2(0,sy),Vector2(w,sy),floor_colour.darkened(0.08),0.9)
    draw_line(Vector2(0,h-3),Vector2(w,h-3),floor_colour.lightened(0.12),2.0)
