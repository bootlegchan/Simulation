extends RefCounted
## Shared "storybook summer" art direction.
##
## Warm flat fills, thick brown crayon outlines with a little hand-drawn wobble,
## chunky rounded shapes, and shadows that shift toward violet instead of grey.
## Everything here is presentation-only and original artwork drawn from code.
## Tweak or replace this one file to restyle every renderer that uses it.

const OUTLINE := Color("#5b3a2e")
const OUTLINE_SOFT := Color("#8a5f49")
const SHADOW_TINT := Color("#5a3a66")
const CREAM := Color("#fff3d2")
const SUN := Color("#ffd85a")
const GRASS := Color("#82d35c")
const GRASS_DEEP := Color("#52b04c")
const LEAF_LIGHT := Color("#a4e46d")
const LEAF := Color("#62c650")
const LEAF_DEEP := Color("#3f9f47")
const WOOD := Color("#cf8f57")
const WOOD_DEEP := Color("#9c6241")
const TERRACOTTA := Color("#e6694b")
const BLOOM_PINK := Color("#ff8fb0")
const BLOOM_YELLOW := Color("#ffd23f")
const BLOOM_WHITE := Color("#fff8e8")
const STONE := Color("#d8cbb0")

# --- colour helpers -----------------------------------------------------------

static func tone(base: Color, shade: float) -> Color:
    # Negative shade pushes toward a warm violet-brown, positive toward cream,
    # so shadows and highlights both stay colourful rather than grey or white.
    if shade < 0.0:
        return base.lerp(Color("#6b3d5a"), clampf(-shade, 0.0, 1.0))
    return base.lerp(Color("#fff0c8"), clampf(shade, 0.0, 1.0))

static func vivid(base: Color, amount: float = 1.0) -> Color:
    # The storybook colour grade applied to colours that come from manifest data:
    # a little more saturation and a lift in value, so earthy data palettes still
    # read as warm and sunny without editing the data itself. amount 0 = unchanged.
    var s := clampf(base.s * (1.0 + 0.32 * amount) + 0.04 * amount, 0.0, 1.0)
    var v := clampf(base.v * (1.0 + 0.07 * amount) + 0.04 * amount, 0.0, 1.0)
    return Color.from_hsv(base.h, s, v, base.a)

static func sky_colors(hour: int) -> PackedColorArray:
    # Returns [top, horizon].
    if hour < 5 or hour >= 21:
        return PackedColorArray([Color("#2d3b7c"), Color("#7370b6")])
    if hour < 8:
        return PackedColorArray([Color("#82b9ea"), Color("#ffc9a2")])
    if hour < 17:
        return PackedColorArray([Color("#4aa9f0"), Color("#c4ecff")])
    if hour < 20:
        return PackedColorArray([Color("#7090e2"), Color("#ffb48c")])
    return PackedColorArray([Color("#3c4b8e"), Color("#8c7aba")])

static func interior_floor_colour(style: String) -> Color:
    if style == "interior_tavern":
        return Color("#c08a58")
    if style == "interior_shop":
        return Color("#ecc98d")
    if style == "interior_bakery":
        return Color("#f2d49c")
    return Color("#e8b97c")

static func ambient_colour(hour: int, interior: bool) -> Color:
    var result := Color("#fffbe8")
    if hour < 5 or hour >= 21:
        result = Color("#8089cc")
    elif hour < 8:
        result = Color("#ffdcbc")
    elif hour >= 17:
        result = Color("#ffbf91")
    if interior:
        result = result.lerp(Color("#fff0d0"), 0.35)
    return result

# --- geometry helpers ---------------------------------------------------------

static func ellipse_points(center: Vector2, radius: Vector2, segments: int = 24) -> PackedVector2Array:
    var points := PackedVector2Array()
    var count := maxi(segments, 8)
    for i in range(count):
        var a := TAU * float(i) / float(count)
        points.append(center + Vector2(cos(a) * radius.x, sin(a) * radius.y))
    return points

static func _circle_segments(radius: float) -> int:
    return clampi(int(radius * 0.7), 14, 40)

static func _noise(index: int, seed_value: int) -> float:
    # Deterministic, smooth-ish jitter in roughly [-1, 1]; never random per frame.
    var a := sin(float(index) * 1.7 + float(seed_value) * 0.37)
    var b := sin(float(index) * 3.1 + float(seed_value) * 0.91) * 0.5
    return (a + b) / 1.5

static func wobble(points: PackedVector2Array, seed_value: int = 0, amount: float = 1.4, closed: bool = true, step: float = 30.0) -> PackedVector2Array:
    # Subdivides long edges and nudges each point sideways so outlines look drawn
    # by hand. The same inputs always give the same line.
    var count := points.size()
    if count < 2:
        return points
    var out := PackedVector2Array()
    var index := 0
    var edges := count if closed else count - 1
    for i in range(edges):
        var a: Vector2 = points[i]
        var b: Vector2 = points[(i + 1) % count]
        var length := a.distance_to(b)
        var segments := maxi(int(length / step), 1)
        var normal := Vector2.ZERO
        if length > 0.001:
            var direction := (b - a) / length
            normal = Vector2(-direction.y, direction.x)
        for s in range(segments):
            var t := float(s) / float(segments)
            out.append(a.lerp(b, t) + normal * _noise(index, seed_value) * amount)
            index += 1
    if not closed:
        out.append(points[count - 1])
    return out

# --- outlined shapes ----------------------------------------------------------

static func outlined_polygon(canvas: CanvasItem, points: PackedVector2Array, fill: Color, line: Color = OUTLINE, width: float = 3.0, seed_value: int = 0, amount: float = 1.4) -> void:
    if points.size() < 3:
        return
    canvas.draw_colored_polygon(points, fill)
    if width <= 0.0:
        return
    var edge := wobble(points, seed_value, amount)
    edge.append(edge[0])
    canvas.draw_polyline(edge, line, width, true)

static func outlined_ellipse(canvas: CanvasItem, center: Vector2, radius: Vector2, fill: Color, line: Color = OUTLINE, width: float = 3.0, seed_value: int = 0, amount: float = 1.1) -> void:
    var segments := _circle_segments(maxf(radius.x, radius.y))
    outlined_polygon(canvas, ellipse_points(center, radius, segments), fill, line, width, seed_value, amount)

static func outlined_circle(canvas: CanvasItem, center: Vector2, radius: float, fill: Color, line: Color = OUTLINE, width: float = 3.0, seed_value: int = 0, amount: float = 1.0) -> void:
    outlined_ellipse(canvas, center, Vector2(radius, radius), fill, line, width, seed_value, amount)

static func outlined_rect(canvas: CanvasItem, rect: Rect2, fill: Color, line: Color = OUTLINE, width: float = 3.0, seed_value: int = 0, amount: float = 1.2) -> void:
    var points := PackedVector2Array([
        rect.position,
        Vector2(rect.end.x, rect.position.y),
        rect.end,
        Vector2(rect.position.x, rect.end.y)
    ])
    outlined_polygon(canvas, points, fill, line, width, seed_value, amount)

static func rounded_rect_points(rect: Rect2, radius: float, arc_steps: int = 5) -> PackedVector2Array:
    var r := minf(radius, minf(rect.size.x, rect.size.y) * 0.5)
    var points := PackedVector2Array()
    var corners := [
        [Vector2(rect.end.x - r, rect.position.y + r), -PI * 0.5],
        [Vector2(rect.end.x - r, rect.end.y - r), 0.0],
        [Vector2(rect.position.x + r, rect.end.y - r), PI * 0.5],
        [Vector2(rect.position.x + r, rect.position.y + r), PI]
    ]
    for corner in corners:
        var origin: Vector2 = corner[0]
        var start_angle: float = corner[1]
        for i in range(arc_steps + 1):
            var a := start_angle + (PI * 0.5) * float(i) / float(arc_steps)
            points.append(origin + Vector2(cos(a), sin(a)) * r)
    return points

static func outlined_rounded_rect(canvas: CanvasItem, rect: Rect2, radius: float, fill: Color, line: Color = OUTLINE, width: float = 3.0, seed_value: int = 0, amount: float = 0.9) -> void:
    outlined_polygon(canvas, rounded_rect_points(rect, radius), fill, line, width, seed_value, amount)

static func puffs(canvas: CanvasItem, lobes: Array, fill: Color, line: Color = OUTLINE, width: float = 3.5) -> void:
    # lobes: Array of Vector3(x, y, radius). All outlines are drawn first and all
    # fills second, so overlapping lobes share one continuous crayon silhouette.
    for outline_lobe in lobes:
        var o: Vector3 = outline_lobe
        var outer := Vector2(o.z + width, o.z + width)
        canvas.draw_colored_polygon(ellipse_points(Vector2(o.x, o.y), outer, _circle_segments(o.z)), line)
    for fill_lobe in lobes:
        var f: Vector3 = fill_lobe
        canvas.draw_colored_polygon(ellipse_points(Vector2(f.x, f.y), Vector2(f.z, f.z), _circle_segments(f.z)), fill)

static func crayon_line(canvas: CanvasItem, from: Vector2, to: Vector2, colour: Color, width: float = 3.0, seed_value: int = 0) -> void:
    var path := wobble(PackedVector2Array([from, to]), seed_value, 0.9, false, 40.0)
    canvas.draw_polyline(path, colour, width, true)
    canvas.draw_circle(from, width * 0.5, colour)
    canvas.draw_circle(to, width * 0.5, colour)

static func blob_shadow(canvas: CanvasItem, center: Vector2, radius_x: float, depth_ratio: float = 0.28, alpha: float = 0.24) -> void:
    var radius := Vector2(radius_x, radius_x * depth_ratio)
    canvas.draw_colored_polygon(ellipse_points(center, radius, 22), Color(SHADOW_TINT, alpha))
    canvas.draw_colored_polygon(ellipse_points(center, radius * 0.66, 18), Color(SHADOW_TINT, alpha * 0.8))

static func dab(canvas: CanvasItem, center: Vector2, radius: Vector2, colour: Color) -> void:
    # A soft highlight or shade patch with no outline, like a stroke of paint.
    canvas.draw_colored_polygon(ellipse_points(center, radius, 14), colour)

static func cloud(canvas: CanvasItem, center: Vector2, size: float, fill: Color) -> void:
    var lobes := [
        Vector3(center.x - 46.0 * size, center.y + 6.0 * size, 24.0 * size),
        Vector3(center.x - 14.0 * size, center.y - 8.0 * size, 32.0 * size),
        Vector3(center.x + 24.0 * size, center.y - 2.0 * size, 28.0 * size),
        Vector3(center.x + 52.0 * size, center.y + 8.0 * size, 21.0 * size)
    ]
    puffs(canvas, lobes, fill, Color("#7aa8d6", 0.85), 2.6)
    dab(canvas, Vector2(center.x - 20.0 * size, center.y + 12.0 * size), Vector2(46.0 * size, 9.0 * size), Color("#d7ecff", 0.7))
