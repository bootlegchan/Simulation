extends Node2D
## Room ambient grading and practical point lights; all light placement is presentation data.
const StorybookStyle = preload("res://scripts/style/storybook_style.gd")
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
    var lighting: Dictionary = room.get("lighting",{})
    var signature := "%s:%s:%s:%s:%s" % [hour,str(room.get("scene_kind","outdoor")),str(room.get("title","")),JSON.stringify(room.get("lights",[])),JSON.stringify(lighting)]
    if signature == _last_signature:
        return
    _last_signature = signature
    var ambient_key := "ambient_day"
    if hour < 5 or hour >= 21:
        ambient_key = "ambient_night"
    elif hour < 8:
        ambient_key = "ambient_dawn"
    elif hour >= 17:
        ambient_key = "ambient_evening"
    # Manifest values win; the storybook palette only fills gaps. Either way the
    # result is graded a little brighter and more saturated for the painted look.
    var fallback := StorybookStyle.ambient_colour(hour,false)
    var ambient_value: Variant = lighting.get(ambient_key,fallback)
    var ambient_colour: Color = ambient_value if ambient_value is Color else Color(str(ambient_value))
    _ambient.color = StorybookStyle.vivid(ambient_colour,0.8)
    if str(room.get("scene_kind","outdoor")) == "interior":
        _ambient.color = _ambient.color.darkened(clampf(float(lighting.get("interior_dim",0.06)),0.0,0.25))
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
        var base_energy := float(definition.get("night_energy",definition.get("energy",0.7))) if is_night else float(definition.get("day_energy",0.0))
        if bool(definition.get("always_on",false)):
            base_energy = float(definition.get("energy",base_energy))
        light.energy = maxf(base_energy,0.0)
        light.texture = _make_light_texture()
        light.texture_scale = clampf(float(definition.get("radius",3.0)),0.4,5.0)
        light.shadow_enabled = bool(definition.get("shadow_enabled",true))
        light.shadow_filter = PointLight2D.SHADOW_FILTER_PCF5
        add_child(light)
        _lights.append(light)
        _light_effects.append({"node":light,"base_energy":base_energy,"flicker":clampf(float(definition.get("flicker",0.0)),0.0,0.18),"frequency":maxf(float(definition.get("flicker_frequency",3.0)),0.1),"phase":float(abs(str(definition.get("id","")).hash())%1000)*0.01})

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
