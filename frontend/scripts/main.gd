extends Node2D

const API_BASE := "http://127.0.0.1:8765/api/v1"
const MANIFEST_PATH := "res://data/presentation/oakwood.json"
const BRIDGE_SCRIPT := "res://../frontend_bridge/server.py"
const WALK_SPEED := 260.0

@onready var world_view: Node2D = $WorldView

var _http: HTTPRequest
var _poll_timer: Timer
var _manifest: Dictionary = {}
var _snapshot: Dictionary = {}
var _current_room_id := ""
var _observer_x := 500.0
var _target_x := 500.0
var _pending_room_id := ""
var _selected: Dictionary = {}
var _inspection: Dictionary = {}
var _request_kind := ""
var _connected := false
var _last_error := "Connecting to Oakwood simulation…"
var _bridge_pid := -1
var _bridge_launch_attempted := false
var _room_transition_busy := false

func _ready() -> void:
    _load_manifest()
    _http = HTTPRequest.new()
    _http.timeout = 4.0
    _http.max_redirects = 0
    add_child(_http)
    _http.request_completed.connect(_on_request_completed)

    _poll_timer = Timer.new()
    _poll_timer.wait_time = 1.0
    _poll_timer.timeout.connect(_refresh_snapshot)
    add_child(_poll_timer)

    world_view.world_clicked.connect(_on_world_clicked)
    world_view.interact_requested.connect(_on_interact)
    world_view.close_requested.connect(_close_inspection)

    _current_room_id = str(_manifest.get("start_room_id", "room_village_square"))
    var start_data: Dictionary = _room_manifest()
    _observer_x = float(start_data.get("observer_spawn_x", 500.0))
    _target_x = _observer_x

    # The game starts its own local simulation bridge. A separately started bridge
    # is detected by the first request and is never claimed or terminated by Godot.
    _refresh_snapshot()
    _poll_timer.start()

func _exit_tree() -> void:
    if _bridge_pid > 0:
        OS.kill(_bridge_pid)
        _bridge_pid = -1

func _process(delta: float) -> void:
    if absf(_target_x - _observer_x) > 1.0:
        _observer_x = move_toward(_observer_x, _target_x, WALK_SPEED * delta)
        if absf(_target_x - _observer_x) <= 1.0:
            _observer_x = _target_x
            if not _pending_room_id.is_empty():
                _enter_room(_pending_room_id)
    world_view.set_presentation_state(_build_view_state())

func _load_manifest() -> void:
    if not FileAccess.file_exists(MANIFEST_PATH):
        _last_error = "Presentation manifest is missing."
        return
    var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
    if parsed is Dictionary:
        _manifest = parsed
    else:
        _last_error = "Presentation manifest is invalid JSON."

func _room_manifest() -> Dictionary:
    var rooms: Dictionary = _manifest.get("rooms", {})
    return rooms.get(_current_room_id, {})

func _refresh_snapshot() -> void:
    if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        return
    _request_kind = "snapshot"
    var url := API_BASE + "/snapshot?room_id=" + _current_room_id.uri_encode()
    var error := _http.request(url)
    if error != OK:
        _connected = false
        _last_error = "Could not start the simulation connection."

func _request(path: String, kind: String) -> void:
    if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        return
    _request_kind = kind
    var error := _http.request(API_BASE + path)
    if error != OK:
        _last_error = "The local simulation request could not be started."

func _post(path: String, kind: String) -> void:
    if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        return
    _request_kind = kind
    var headers := PackedStringArray(["Content-Type: application/json"])
    var error := _http.request(API_BASE + path, headers, HTTPClient.METHOD_POST, "{}")
    if error != OK:
        _last_error = "The simulation command could not be started."

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
        _connected = false
        _last_error = "Simulation connection unavailable (HTTP %s)." % response_code
        if not _bridge_launch_attempted:
            _start_local_simulation()
        world_view.set_presentation_state(_build_view_state())
        if _room_transition_busy:
            _room_transition_busy = false
            world_view.call("complete_room_transition")
        return

    var payload = JSON.parse_string(body.get_string_from_utf8())
    if not payload is Dictionary:
        _connected = false
        _last_error = "The simulation returned an invalid response."
        if _room_transition_busy:
            _room_transition_busy = false
            world_view.call("complete_room_transition")
        return

    if _request_kind == "control":
        _refresh_snapshot()
    elif _request_kind == "snapshot":
        _snapshot = payload
        _connected = true
        _last_error = ""
        if _snapshot.get("active_room", {}).is_empty():
            _last_error = "This room is not available in the current simulation."
        world_view.set_presentation_state(_build_view_state())
        if _room_transition_busy:
            _room_transition_busy = false
            world_view.call("complete_room_transition")
    elif _request_kind == "profile":
        _inspection = {"title": str(payload.get("name", "Citizen")), "kind": "Citizen record", "data": payload}
        world_view.set_presentation_state(_build_view_state())

func _start_local_simulation() -> void:
    _bridge_launch_attempted = true
    var bridge_path := ProjectSettings.globalize_path(BRIDGE_SCRIPT)
    if not FileAccess.file_exists(bridge_path):
        _last_error = "Cannot find frontend_bridge/server.py. Open the Godot project from the Simulation repository."
        return

    var pid := OS.create_process("python3", [
        bridge_path,
        "--host", "127.0.0.1",
        "--port", "8765",
        "--seed", "42",
        "--ticks-per-second", "1"
    ], false)
    if pid <= 0:
        _last_error = "Could not start Python. Install Python 3 and the repository requirements, then restart the game."
        return

    _bridge_pid = pid
    _last_error = "Starting the Oakwood simulation…"

func _build_view_state() -> Dictionary:
    return {
        "room_id": _current_room_id,
        "room_manifest": _room_manifest(),
        "world_width": float(_manifest.get("world_width", 3600)),
        "active_room": _snapshot.get("active_room", {}),
        "npcs": _snapshot.get("npcs", []),
        "objects": _snapshot.get("objects", []),
        "status": _snapshot.get("status", {}),
        "climate": _snapshot.get("climate", {}),
        "economy": _snapshot.get("economy", {}),
        "population": _snapshot.get("population", {}),
        "observer_x": _observer_x,
        "selected": _selected,
        "inspection": _inspection,
        "connected": _connected,
        "error": _last_error
    }

func _on_world_clicked(world_position: Vector2) -> void:
    var target: Dictionary = world_view.pick_target(world_position)
    if target.is_empty():
        _selected = {}
        _pending_room_id = ""
        _target_x = clampf(world_position.x, 80.0, float(_manifest.get("world_width", 3600)) - 80.0)
    else:
        _selected = target
        _target_x = float(target.get("door_x", target.get("x", world_position.x)))
        _pending_room_id = str(target.get("target_room_id", "")) if target.get("kind") == "portal" else ""
    world_view.set_presentation_state(_build_view_state())

func _on_interact() -> void:
    if not _inspection.is_empty():
        _close_inspection()
        return
    if _selected.is_empty():
        return
    var kind := str(_selected.get("kind", ""))
    var entity_id := str(_selected.get("id", ""))
    if kind == "portal":
        _enter_room(str(_selected.get("target_room_id", "")))
        return
    if kind == "npc":
        _request("/citizens/" + entity_id.uri_encode() + "/profile", "profile")
        return

    if str(_selected.get("interaction", "")) == "clock":
        var lifecycle := str(_snapshot.get("status", {}).get("lifecycle_state", ""))
        _post("/simulation/resume" if lifecycle != "RUNNING" else "/simulation/pause", "control")
        return

    var active_room: Dictionary = _snapshot.get("active_room", {})
    var economy: Dictionary = _snapshot.get("economy", {})
    var object_data := _find_object(entity_id)
    var title := str(_selected.get("label", object_data.get("name", "Inspection")))
    var lines: Array[String] = []
    match str(_selected.get("interaction", "inspect")):
        "noticeboard":
            lines.append("PUBLIC NOTICES")
            var notices: Array = active_room.get("notice_board_atoms", [])
            if notices.is_empty():
                lines.append("The board is currently empty.")
            else:
                for notice in notices.slice(0, 8):
                    if notice is Dictionary:
                        lines.append(str(notice.get("content", notice.get("text", notice))))
                    else:
                        lines.append(str(notice))
        "ledger":
            lines.append("MUNICIPAL ACCOUNTS")
            lines.append("Treasury: %s gold" % economy.get("treasury_balance_gold", "—"))
            lines.append("Total currency: %s gold" % economy.get("total_currency_gold", "—"))
            lines.append("Households: %s" % economy.get("households_count", "—"))
        "shop":
            lines.append("MARKET COMMODITY DATA · READ ONLY")
            var stocks: Dictionary = economy.get("commodity_stocks", {})
            var prices: Dictionary = economy.get("commodity_prices", {})
            var count := 0
            for commodity in stocks.keys():
                lines.append("%s · %s · %s gold" % [str(commodity).capitalize(), stocks[commodity], prices.get(commodity, "—")])
                count += 1
                if count >= 9:
                    break
            lines.append("These are economy-wide values, not shop-specific inventory.")
            lines.append("Purchases are not enabled by the current backend command API.")
        _:
            lines.append("IN-WORLD OBJECT")
            lines.append("Name: %s" % object_data.get("name", title))
            lines.append("Room: %s" % active_room.get("name", _current_room_id))
            var capabilities: Array = object_data.get("capabilities", [])
            if not capabilities.is_empty():
                lines.append("Capabilities: %s" % str(capabilities))
            lines.append("Inspection only; no simulation state was changed.")
    _inspection = {"title": title, "kind": "World object", "lines": lines}
    world_view.set_presentation_state(_build_view_state())

func _find_object(object_id: String) -> Dictionary:
    for item in _snapshot.get("objects", []):
        if str(item.get("id", "")) == object_id:
            return item
    return {}

func _enter_room(room_id: String) -> void:
    if _room_transition_busy:
        return
    if room_id.is_empty() or not _manifest.get("rooms", {}).has(room_id):
        _last_error = "No presentation scene is mapped for that room yet."
        _pending_room_id = ""
        return
    _room_transition_busy = true
    await world_view.call("begin_room_transition")
    _current_room_id = room_id
    _selected = {}
    _inspection = {}
    var room_data: Dictionary = _room_manifest()
    _observer_x = float(room_data.get("observer_spawn_x", 140.0))
    _target_x = _observer_x
    _pending_room_id = ""
    world_view.set_presentation_state(_build_view_state())
    while _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        await get_tree().process_frame
    _refresh_snapshot()

func _close_inspection() -> void:
    _inspection = {}
    world_view.set_presentation_state(_build_view_state())
