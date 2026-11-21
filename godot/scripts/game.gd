extends Node3D
## Game chính: nối logic (`chonoi.live`) với các cảnh 3D của nhóm.
##   gather -> res://scenes/DiveUnderwater.tscn   (lặn 2.5D, nhìn ngang)
##   quan / shop -> res://scenes/RestaurantNight.tscn (quán bè, góc nhìn thứ 3)
## Cảnh chỉ hiển thị theo snapshot; HUD, Shop và pause vẽ ở đây.

const SCENE_FOR_PHASE := {
	"gather": "res://scenes/DiveUnderwater.tscn",
	"quan": "res://scenes/RestaurantNight.tscn",
	"shop": "res://scenes/RestaurantNight.tscn",
}
const KIND_VI := {
	"ca_loc": "Cá lóc", "ca_linh": "Cá linh", "ca_keo": "Cá kèo",
	"bong_dien_dien": "Bông điên điển", "bong_sung": "Bông súng", "keo_neo": "Kèo nèo",
}

var link: Node
var world: Node3D
var world_path := ""
var hud_top: Label
var hud_side: Label
var center: Label
var shop_panel: PanelContainer
var shop_label: Label
var dim: ColorRect


func _ready() -> void:
	link = load("res://scripts/sim_link.gd").new()
	link.name = "SimLink"
	add_child(link)
	link.state_updated.connect(_on_state)
	_build_ui()
	_show_world("res://scenes/DiveUnderwater.tscn")  # xem trước khi chưa kết nối


func _show_world(path: String) -> void:
	if path == world_path:
		return
	if is_instance_valid(world):
		world.queue_free()
	world_path = path
	world = load(path).instantiate()
	world.set("link", link)  # cảnh dùng link nếu có (không có thì chạy như bản trưng bày)
	add_child(world)


func _label(size: int, pos: Vector2, parent: Node) -> Label:
	var l := Label.new()
	l.position = pos
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color("#f4fbff"))
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	parent.add_child(l)
	return l


func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	canvas.layer = 10
	add_child(canvas)
	dim = ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.visible = false
	canvas.add_child(dim)
	hud_top = _label(20, Vector2(20, 14), canvas)
	hud_side = _label(18, Vector2(20, 54), canvas)
	center = _label(30, Vector2(0, 0), canvas)
	center.set_anchors_preset(Control.PRESET_CENTER)
	center.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	center.grow_horizontal = Control.GROW_DIRECTION_BOTH
	center.grow_vertical = Control.GROW_DIRECTION_BOTH
	shop_panel = PanelContainer.new()
	shop_panel.set_anchors_preset(Control.PRESET_CENTER)
	shop_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	shop_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	shop_panel.visible = false
	canvas.add_child(shop_panel)
	var box := VBoxContainer.new()
	shop_panel.add_child(box)
	shop_label = _label(20, Vector2.ZERO, box)
	for spec in [["1 · Mua Bình oxy", "oxygen"], ["2 · Mua Áo phao (+Máu)", "hp"]]:
		var b := Button.new()
		b.text = spec[0]
		b.add_theme_font_size_override("font_size", 20)
		var action: String = spec[1]
		b.pressed.connect(func(): link.buy(action))
		box.add_child(b)
	var hint := _label(18, Vector2.ZERO, box)
	hint.text = "Enter: Đóng Shop sang Ngày mới"


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.keycode == KEY_1 and link.phase() == "shop":
			link.buy("oxygen")
		elif ev.keycode == KEY_2 and link.phase() == "shop":
			link.buy("hp")
		elif ev.keycode == KEY_R and bool(link.state.get("finished", false)):
			link.restart()


func _process(_delta: float) -> void:
	if not link.connected:
		hud_top.text = "Chưa kết nối logic. Mở terminal ở thư mục repo và chạy:  python -m chonoi.live"
		hud_side.text = "(đang xem trước cảnh lặn của nhóm; kết nối xong game tự bắt đầu)"
		center.text = ""
		shop_panel.visible = false
		dim.visible = false


func _on_state(s: Dictionary) -> void:
	var ph := str(s.get("phase", "gather"))
	if SCENE_FOR_PHASE.has(ph):
		_show_world(SCENE_FOR_PHASE[ph])
	var secs := int(ceil(float(s.get("time_left_ticks", 0)) / 60.0))
	var time_txt := "%d:%02d" % [secs / 60, secs % 60]
	if secs <= 30 and ph != "shop":
		time_txt = "⚠ " + time_txt
	var day_txt := "Ngày %s · " % str(s["day"]) if s.has("day") else ""
	var common := "Tiền %sk · Uy tín %.1f · Điểm %s" % [str(s.get("money", 0)), float(s.get("reputation", 0)), str(s.get("score", 0))]

	if ph == "gather":
		var p: Dictionary = s.get("player", {})
		var oxy := float(p.get("oxygen_ticks", 0)) / maxf(1.0, float(p.get("oxygen_max_ticks", 1)))
		var pos: Array = p.get("pos", [0, 0])
		var oxy_txt := "Oxy %d%%" % int(round(oxy * 100.0))
		if oxy < 0.25:
			oxy_txt = "⚠ " + oxy_txt + (" — Hết hơi!" if oxy <= 0.0 else "")
		hud_top.text = "%sBuổi sáng · %s · Máu %s/%s · %s · Sâu %.1f m · %s" % [
			day_txt, time_txt, str(p.get("hp", 0)), str(p.get("hp_max", 0)), oxy_txt, float(pos[1]), common]
		hud_side.text = _hold_text(s) + "\nE: hái / cập bến · Space: bắt cá · Esc/P: tạm dừng"
	elif ph == "quan":
		hud_top.text = "%sBuổi tối · %s · %s" % [day_txt, time_txt, common]
		hud_side.text = _quan_text(s) + "\nE: bếp / bưng / giao món · Esc/P: tạm dừng"
	else:
		hud_top.text = "%sShop · tự đóng sau %ds · %s" % [day_txt, secs, common]
		hud_side.text = ""
	shop_panel.visible = ph == "shop" and not bool(s.get("finished", false))
	if shop_panel.visible:
		shop_label.text = "SHOP NÂNG CẤP — Tiền %sk\nĐã mua: %s (áp dụng từ Ngày kế)" % [
			str(s.get("money", 0)), JSON.stringify(s.get("upgrades", {}))]
	var paused := str(s.get("state", "")) == "paused"
	dim.visible = paused
	if bool(s.get("finished", false)):
		center.text = "KẾT THÚC (%s)\nĐiểm %s · Tiền %sk\nR: chơi lại" % [str(s.get("reason", "")), str(s.get("score", 0)), str(s.get("money", 0))]
	elif paused:
		center.text = "TẠM DỪNG\nEsc/P: tiếp tục"
	else:
		center.text = ""


func _hold_text(s: Dictionary) -> String:
	var counts := {}
	for k in s.get("hold", []):
		counts[k] = int(counts.get(k, 0)) + 1
	var lines := ["Giỏ %s/%s" % [str(s.get("hold_count", 0)), str(s.get("hold_capacity", 0))]]
	var need: Dictionary = s.get("day_plan", {}).get("ingredients", {})
	for k in need.keys():
		lines.append("  %s: %d/%d" % [KIND_VI.get(k, k), int(counts.get(k, 0)), int(need[k])])
	for k in counts.keys():
		if not need.has(k):
			lines.append("  %s: %d" % [KIND_VI.get(k, k), int(counts[k])])
	return "\n".join(lines)


func _quan_text(s: Dictionary) -> String:
	var lines := []
	var stock: Dictionary = s.get("stock", {})
	var parts := []
	for k in stock.keys():
		parts.append("%s ×%s" % [KIND_VI.get(k, k), str(stock[k])])
	lines.append("Kho: " + (", ".join(parts) if parts.size() > 0 else "(trống)"))
	var hand = s.get("hand")
	lines.append("Đang cầm: " + (str(hand.get("dish_id", hand)) if typeof(hand) == TYPE_DICTIONARY else (str(hand) if hand != null else "—")))
	var patience_max := float(s.get("meta", {}).get("patience_s", 60)) * 60.0
	for c in s.get("customers", []):
		var ratio := float(c.get("patience_ticks_left", 0)) / maxf(1.0, patience_max)
		var mark := "⚠ " if ratio < 0.25 and str(c.get("state", "")) == "waiting" else ""
		lines.append("  %s%s %s: %s (%s, %d%%)" % [mark, str(c.get("table_id", "")), str(c.get("id", "")),
			str(c.get("dish_id", "")), str(c.get("state", "")), int(round(ratio * 100.0))])
	for st in s.get("stoves", []):
		lines.append("  Bếp %s: %s %s" % [str(st.get("id", "")), str(st.get("state", "")),
			str(st.get("dish", "")) if st.get("dish") != null else ""])
	return "\n".join(lines)
