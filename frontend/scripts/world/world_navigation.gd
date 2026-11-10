extends RefCounted
## Grid pathfinding for the presentation-only observer.
const CELL := 44.0
const DIRS = [Vector2i(1,0),Vector2i(-1,0),Vector2i(0,1),Vector2i(0,-1)]

func build_path(start: Vector2, destination: Vector2, room: Dictionary, width: float) -> PackedVector2Array:
    var limits: Dictionary = room.get("navigation",{})
    var min_y := float(limits.get("min_y",450.0))
    var max_y := float(limits.get("max_y",680.0))
    var start_cell := _cell(start)
    var goal := _cell(Vector2(clampf(destination.x,32.0,width-32.0),clampf(destination.y,min_y,max_y)))
    start_cell = _nearest_open(start_cell,room,width,min_y,max_y)
    goal = _nearest_open(goal,room,width,min_y,max_y)
    var queue:Array[Vector2i] = [start_cell]
    var came:Dictionary = {}
    var seen:Dictionary = {start_cell:true}
    var cursor := 0
    while cursor < queue.size() and cursor < 1800:
        var current := queue[cursor]
        cursor += 1
        if current == goal:
            var cells:Array[Vector2i] = [current]
            while came.has(current):
                current = came[current]
                cells.push_front(current)
            var path := PackedVector2Array()
            for point in cells.slice(1):
                path.append(_world(point))
            return path
        for direction in DIRS:
            var next := current+direction
            if seen.has(next) or _blocked(next,room,width,min_y,max_y):
                continue
            seen[next] = true
            came[next] = current
            queue.append(next)
    return PackedVector2Array()

func _cell(point: Vector2) -> Vector2i:
    return Vector2i(roundi(point.x/CELL),roundi(point.y/CELL))

func _world(cell: Vector2i) -> Vector2:
    return Vector2((Vector2(cell)+Vector2(0.5))*CELL)

func _nearest_open(origin: Vector2i,room: Dictionary,width: float,min_y: float,max_y: float) -> Vector2i:
    if not _blocked(origin,room,width,min_y,max_y):
        return origin
    for radius in range(1,9):
        for dx in range(-radius,radius+1):
            for dy in range(-radius,radius+1):
                if maxi(absi(dx),absi(dy)) != radius:
                    continue
                var candidate := origin+Vector2i(dx,dy)
                if not _blocked(candidate,room,width,min_y,max_y):
                    return candidate
    return origin

func _blocked(cell: Vector2i,room: Dictionary,width: float,min_y: float,max_y: float) -> bool:
    var p := _world(cell)
    if p.x < 28.0 or p.x > width-28.0 or p.y < min_y or p.y > max_y:
        return true
    var ground := float(room.get("ground_y",590.0))
    for building in room.get("buildings",[]):
        if str(building.get("style","")).begins_with("interior_"):
            continue
        var left := float(building.get("x",0.0))-20.0
        var right := left+float(building.get("width",260.0))+40.0
        var top := float(building.get("y",0.0))+100.0
        var bottom := float(building.get("y",0.0))+float(building.get("height",260.0))+10.0
        if p.x >= left and p.x <= right and p.y >= top and p.y <= bottom:
            var key := str(building.get("id","")).trim_prefix("building_")
            for portal in room.get("portals",[]):
                if str(portal.get("id","")) == key:
                    var door := float(portal.get("door_x",portal.get("x",0.0)))
                    if absf(p.x-door) <= 42.0 and p.y >= ground-108.0 and p.y <= ground+22.0:
                        return false
            return true
    for prop in room.get("scenery",[]):
        if str(prop.get("kind","")) == "tree":
            var tree := Vector2(float(prop.get("x",0.0)),float(prop.get("y",0.0)))
            if p.distance_to(tree) < 25.0*float(prop.get("scale",1.0)):
                return true
    return false
