extends CanvasLayer
## Camera-independent, minimal screen-space interface.
var _room: Label
var _clock: Label
var _population: Label
var _lifecycle: Label
var _prompt: PanelContainer
var _prompt_text: Label
var _inspection: PanelContainer
var _inspection_title: Label
var _inspection_body: Label
var _connection: Label

func _ready() -> void:
    layer = 20
    var root := Control.new()
    root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(root)
    var identity := _panel()
    identity.position = Vector2(24,20)
    identity.custom_minimum_size = Vector2(300,72)
    root.add_child(identity)
    var identity_stack := VBoxContainer.new()
    identity_stack.add_theme_constant_override("separation",3)
    identity.add_child(identity_stack)
    var title := Label.new()
    title.text = "OAKWOOD"
    title.add_theme_font_size_override("font_size",16)
    title.add_theme_color_override("font_color",Color("#293a35"))
    identity_stack.add_child(title)
    _room = Label.new()
    _room.add_theme_font_size_override("font_size",11)
    _room.add_theme_color_override("font_color",Color("#796b58"))
    identity_stack.add_child(_room)

    var status := _panel()
    status.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
    status.offset_left = -310
    status.offset_top = 20
    status.offset_right = -24
    status.offset_bottom = 96
    root.add_child(status)
    var stack := VBoxContainer.new()
    stack.add_theme_constant_override("separation",4)
    status.add_child(stack)
    _clock = Label.new()
    _clock.add_theme_font_size_override("font_size",17)
    _clock.add_theme_color_override("font_color",Color("#293a35"))
    stack.add_child(_clock)
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation",12)
    stack.add_child(row)
    _population = Label.new()
    _population.add_theme_font_size_override("font_size",11)
    _population.add_theme_color_override("font_color",Color("#796b58"))
    row.add_child(_population)
    _lifecycle = Label.new()
    _lifecycle.add_theme_font_size_override("font_size",10)
    _lifecycle.add_theme_color_override("font_color",Color("#58745e"))
    row.add_child(_lifecycle)

    _prompt = _panel()
    _prompt.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
    _prompt.offset_left = -190
    _prompt.offset_top = -68
    _prompt.offset_right = 190
    _prompt.offset_bottom = -18
    _prompt.visible = false
    root.add_child(_prompt)
    _prompt_text = Label.new()
    _prompt_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    _prompt_text.add_theme_font_size_override("font_size",13)
    _prompt_text.add_theme_color_override("font_color",Color("#293a35"))
    _prompt.add_child(_prompt_text)

    _inspection = _panel()
    _inspection.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
    _inspection.offset_left = -370
    _inspection.offset_top = -175
    _inspection.offset_right = -24
    _inspection.offset_bottom = 175
    _inspection.visible = false
    root.add_child(_inspection)
    var details := VBoxContainer.new()
    details.add_theme_constant_override("separation",10)
    _inspection.add_child(details)
    _inspection_title = Label.new()
    _inspection_title.add_theme_font_size_override("font_size",19)
    _inspection_title.add_theme_color_override("font_color",Color("#293a35"))
    details.add_child(_inspection_title)
    _inspection_body = Label.new()
    _inspection_body.custom_minimum_size = Vector2(290,220)
    _inspection_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    _inspection_body.add_theme_font_size_override("font_size",12)
    _inspection_body.add_theme_color_override("font_color",Color("#665c4d"))
    details.add_child(_inspection_body)

    _connection = Label.new()
    _connection.position = Vector2(26,102)
    _connection.add_theme_font_size_override("font_size",11)
    _connection.add_theme_color_override("font_color",Color("#9b5b43"))
    root.add_child(_connection)
    _make_pass_through(root)

func _make_pass_through(control: Control) -> void:
    control.mouse_filter = Control.MOUSE_FILTER_IGNORE
    for child in control.get_children():
        if child is Control:
            _make_pass_through(child)

func _panel() -> PanelContainer:
    var panel := PanelContainer.new()
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#f7f1e5",0.94)
    style.border_color = Color("#d8cbb5")
    style.set_border_width_all(1)
    style.set_corner_radius_all(12)
    style.content_margin_left = 14
    style.content_margin_right = 14
    style.content_margin_top = 10
    style.content_margin_bottom = 10
    panel.add_theme_stylebox_override("panel",style)
    return panel

func configure(state: Dictionary) -> void:
    if not is_node_ready():
        return
    var room: Dictionary = state.get("room_manifest",{})
    var status: Dictionary = state.get("status",{})
    _room.text = str(room.get("title",state.get("room_id","")))
    _clock.text = "%02d:%02d   ·   Day %s" % [int(status.get("hour",0)),int(status.get("tick",0))%60,str(status.get("day",1))]
    _population.text = "%s residents" % str(state.get("population",{}).get("alive",0))
    _lifecycle.text = "● "+str(status.get("lifecycle_state","CONNECTING")).capitalize()
    _connection.text = "" if bool(state.get("connected",false)) else str(state.get("error","Connecting…"))
    var selected: Dictionary = state.get("selected",{})
    _prompt.visible = not selected.is_empty() and state.get("inspection",{}).is_empty()
    if _prompt.visible:
        var kind := str(selected.get("kind",""))
        _prompt_text.text = "E   "+("ENTER LOCATION" if kind == "portal" else ("VIEW CITIZEN" if kind == "npc" else "INSPECT"))
    var inspection: Dictionary = state.get("inspection",{})
    _inspection.visible = not inspection.is_empty()
    if _inspection.visible:
        _inspection_title.text = str(inspection.get("title","Inspection"))
        var lines: Array = inspection.get("lines",[])
        if lines.is_empty() and inspection.has("data"):
            var data: Dictionary = inspection.get("data",{})
            lines = ["Occupation · %s" % data.get("occupation","—"),"Home · %s" % data.get("home_location_id","—"),"Work · %s" % data.get("work_location_id","—"),"Wealth · %s gold" % data.get("wealth_gold","—")]
        _inspection_body.text = "\n".join(PackedStringArray(lines))+"\n\nPress E or Esc to close"
