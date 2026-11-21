extends Node
## Cầu nối tới logic Python (`python -m chonoi.live`, mặc định --mode day):
## GET /state mỗi ~33 ms, POST /input khi phím đổi. Cảnh 3D chỉ ĐỌC `state`, không tự chạy luật.

signal state_updated(state: Dictionary)

const SERVER_URL := "http://127.0.0.1:8000"
const POLL_INTERVAL := 0.033

var state: Dictionary = {}
var connected := false
var server_url := OS.get_environment("CHONOI_SERVER_URL")
var _poll: HTTPRequest
var _send: HTTPRequest
var _poll_busy := false
var _poll_t := 0.0
var _last_payload := ""
var _queued: Array = []  # lệnh một lần (buy, restart)
var _send_busy := false
var _block_game_buttons := false


func _ready() -> void:
	if server_url.is_empty():
		server_url = SERVER_URL
	_poll = HTTPRequest.new()
	add_child(_poll)
	_poll.request_completed.connect(_on_state)
	_send = HTTPRequest.new()
	add_child(_send)
	_send.request_completed.connect(func(result, code, _h, _b):
		_send_busy = false
		if result != HTTPRequest.RESULT_SUCCESS or code != 200:
			_last_payload = ""
		_flush_queue())


func phase() -> String:
	return str(state.get("phase", state.get("mode", "")))


func buy(action: String) -> void:
	_queued.append({"path": "/input", "body": {"buy": action}})
	_flush_queue()


func restart() -> void:
	request_action("/restart")


func request_action(path: String) -> void:
	_queued.append({"path": path, "body": {}})
	_flush_queue()


func _flush_queue() -> void:
	if _queued.is_empty() or _send_busy:
		return
	var job: Dictionary = _queued.pop_front()
	_send_busy = true
	if _send.request(server_url + str(job["path"]), ["Content-Type: application/json"], HTTPClient.METHOD_POST,
		JSON.stringify(job["body"])) != OK:
		_send_busy = false


func _physics_process(delta: float) -> void:
	var ix := 0.0
	var iy := 0.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		ix += 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		ix -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		iy += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		iy -= 1.0
	# gather: [x, d] (S = lặn xuống); quan: [x, z] (W = đi về phía bếp, z giảm theo màn hình)
	var interact := Input.is_key_pressed(KEY_E)
	var catching := Input.is_key_pressed(KEY_SPACE)
	var pause := Input.is_key_pressed(KEY_ESCAPE) or Input.is_key_pressed(KEY_P)
	var shop_done := Input.is_key_pressed(KEY_ENTER)
	var in_screen: bool = state.get("presentation") != null
	var any_button := interact or catching or pause or shop_done
	_block_game_buttons = any_button and (_block_game_buttons or in_screen)
	var payload := JSON.stringify({
		"move": [ix, iy],
		"interact": interact and not _block_game_buttons,
		"catch": catching and not _block_game_buttons,
		"pause": pause and not _block_game_buttons,
		"shop_done": shop_done and not _block_game_buttons,
	})
	if connected and payload != _last_payload and _queued.is_empty() and not _send_busy:
		_last_payload = payload
		_send_busy = true
		if _send.request(server_url + "/input", ["Content-Type: application/json"], HTTPClient.METHOD_POST, payload) != OK:
			_send_busy = false
			_last_payload = ""

	_poll_t += delta
	if _poll_t >= POLL_INTERVAL and not _poll_busy:
		_poll_t = 0.0
		_poll_busy = true
		if _poll.request(server_url + "/state") != OK:
			_poll_busy = false


func _on_state(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	_poll_busy = false
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		connected = false
		_last_payload = ""
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		connected = false
		_last_payload = ""
		return
	connected = true
	state = parsed
	state_updated.emit(state)
