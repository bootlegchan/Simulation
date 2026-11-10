extends Node2D
## Time-of-day ambient grading and practical point lights.
## Buildings contribute occluder polygons; this node owns the light sources.

var _ambient: CanvasModulate
var _lights: Array[PointLight2D] = []
var _light_effects: Array[Dictionary] = []
var _last_signature := ""
var _elapsed := 0.0

func _ready() -> void:
    _ambient = CanvasModulate.new()
    add_child(_ambient)

func _process(delta: float) -> void:
    _elapsed += delta
    for effect in _light_effects:
        var light: PointLight2D = effect.get("node")
        if not is_instance_valid(light):
            continue
        var amount := float(effect.get("flicker",0.0))
        var phase := float(effect.get("phase",0.0))
        var frequency := float(effect.get("frequency",3.0))
        var pulse := sin(_elapsed*frequency+phase)*0.65+sin(_elapsed*frequency*1.71+phase*0.7)*0.35
        light.energy = maxf(float(effect.get("base_energy",0.0))*(1.0+pulse*amount),0.0)

func configure(state: Dictionary) -> void:
    var status: Dictionary = state.get("status",{})
    var hour := int(status.get("hour",10))
    var room: Dictionary = state.get("room_manifest",{})
    var signature := "%s:%s:%s:%s" % [hour,str(room.get("scene_kind","outdoor")),str(room.get("title","")),JSON.stringify(room.get("lights",[]))]
    if signature == _last_signature:
        return
    _last_signature = signature
    if hour < 5 or hour >= 21:
        _ambient.color = Color("#53627d")
    elif hour < 8 or hour >= 17:
        _ambient.color = Color("#f0c2a0")
    elif hour >= 11 and hour <= 15:
        _ambient.color = Color("#fff4dc")
    else:
        _ambient.color = Color("#e4e6d4")
    if str(room.get("scene_kind","outdoor")) == "interior":
        _ambient.color = _ambient.color.darkened(0.08)
    _rebuild_lights(room,hour)

func _rebuild_lights(room: Dictionary,hour: int) -> void:
    for light in _lights:
        light.queue_free()
    _lights.clear()
    _light_effects.clear()
    var definitions: Array = room.get("lights",[])
    var is_night := hour < 6 or hour >= 18
    for definition in definitions:
        var light := PointLight2D.new()
        light.position = Vector2(float(definition.get("x",0.0)),float(definition.get("y",300.0)))
        light.color = Color(str(definition.get("color","#f2c77e")))
        var base_energy := float(definition.get("energy",0.7)) if is_night or bool(definition.get("always_on",false)) else 0.0
        light.energy = base_energy
        light.texture = _make_light_texture()
        light.texture_scale = float(definition.get("radius",3.0))
        light.shadow_enabled = true
        light.shadow_filter = PointLight2D.SHADOW_FILTER_PCF5
        add_child(light)
        _lights.append(light)
        _light_effects.append({
            "node":light,
            "base_energy":base_energy,
            "flicker":clampf(float(definition.get("flicker",0.0)),0.0,0.18),
            "frequency":maxf(float(definition.get("flicker_frequency",3.0)),0.1),
            "phase":float(abs(str(definition.get("id","")).hash())%1000)*0.01
        })

func _make_light_texture() -> Texture2D:
    var gradient := Gradient.new()
    gradient.set_color(0,Color(1,1,1,0.72))
    gradient.add_point(0.28,Color(1,1,1,0.36))
    gradient.set_color(1,Color(1,1,1,0))
    var texture := GradientTexture2D.new()
    texture.gradient = gradient
    texture.width = 256
    texture.height = 256
    texture.fill = GradientTexture2D.FILL_RADIAL
    texture.fill_from = Vector2(0.5,0.5)
    texture.fill_to = Vector2(0.5,0.0)
    return texture
