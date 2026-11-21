extends Node
## Cầu nối tới logic Python (`python -m chonoi.live`, mặc định --mode day):
## GET /state mỗi ~33 ms, POST /input khi phím đổi. Cảnh 3D chỉ ĐỌC `state`, không tự chạy luật.

signal state_updated(state: Dictionary)

const SERVER_URL := "http://127.0.0.1:8000"
const POLL_INTERVAL := 0.033

var state: Dictionary = {}
var connected := false
var _poll: HTTPRequest
var _send: HTTPRequest
var _poll_busy := false
var _poll_t := 0.0
var _last_payload := ""
var _queued: Array = []  # lệnh một lần (buy, restart)
var _send_busy := false


func _ready() -> void:
	_poll = HTTPRequest.new()
	add_child(_poll)
	_poll.request_completed.connect(_on_state)
	_send = HTTPRequest.new()
	add_child(_send)
	_send.request_completed.connect(func(_r, _c, _h, _b):
		_send_busy = false
		_flush_queue())


func phase() -> String:
	return str(state.get("phase", ""))


func buy(action: String) -> void:
	_queued.append({"path": "/input", "body": {"buy": action}})
	_flush_queue()


func restart() -> void:
	_queued.append({"path": "/restart", "body": {}})
	_flush_queue()


func _flush_queue() -> void:
	if _queued.is_empty() or _send_busy:
		return
	var job: Dictionary = _queued.pop_front()
	_send_busy = true
	_send.request(SERVER_URL + str(job["path"]), ["Content-Type: application/json"], HTTPClient.METHOD_POST,
		JSON.stringify(job["body"]))


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
	var payload := JSON.stringify({
		"move": [ix, iy],
		"interact": Input.is_key_pressed(KEY_E),
		"catch": Input.is_key_pressed(KEY_SPACE),
		"pause": Input.is_key_pressed(KEY_ESCAPE) or Input.is_key_pressed(KEY_P),
		"shop_done": Input.is_key_pressed(KEY_ENTER),
	})
	if connected and payload != _last_payload and _queued.is_empty() and not _send_busy:
		_last_payload = payload
		_send_busy = true
		_send.request(SERVER_URL + "/input", ["Content-Type: application/json"], HTTPClient.METHOD_POST, payload)

	_poll_t += delta
	if _poll_t >= POLL_INTERVAL and not _poll_busy:
		_poll_t = 0.0
		_poll_busy = true
		if _poll.request(SERVER_URL + "/state") != OK:
			_poll_busy = false


func _on_state(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	_poll_busy = false
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		connected = false
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	connected = true
	state = parsed
	state_updated.emit(state)
