extends Node3D
## Game chính: nối logic (`chonoi.live`) với các cảnh 3D của nhóm.
##   gather -> res://scenes/DiveUnderwater.tscn   (lặn 2.5D, nhìn ngang)
##   quan / shop -> res://scenes/RestaurantNight.tscn (quán bè, góc nhìn thứ 3)
## Cảnh chỉ hiển thị theo snapshot; HUD cảnh báo, độ tươi, tương phản cao, Shop và pause vẽ ở đây.

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
var alert_label: Label
var center: Label
var hud_top_bg: ColorRect
var hud_side_bg: ColorRect
var alert_bg: ColorRect
var monster_border: Array[ColorRect] = []
var shop_panel: PanelContainer
var shop_label: Label
var contrast_btn: Button
var dim: ColorRect

var high_contrast := false
var blink_t := 0.0
var active_alert_monster := false
var active_alert_oxy := false
var active_alert_angry := false


func _ready() -> void:
	link = load("res://scripts/sim_link.gd").new()
	link.name = "SimLink"
	add_child(link)
	link.state_updated.connect(_on_state)
	_build_ui()
	_apply_contrast_theme()
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

	# 4-edge purple warning border when a monster (Ca Sau / Ran Ho May) is nearby
	var edge_defs := [
		[0.0, 0.0, 1.0, 0.0, 0, 0, 0, 12],
		[0.0, 1.0, 1.0, 1.0, 0, -12, 0, 0],
		[0.0, 0.0, 0.0, 1.0, 0, 0, 12, 0],
		[1.0, 0.0, 1.0, 1.0, -12, 0, 0, 0],
	]
	for e in edge_defs:
		var r := ColorRect.new()
		r.color = Color(0.68, 0.16, 0.92, 0.85)
		r.anchor_left = e[0]; r.anchor_top = e[1]; r.anchor_right = e[2]; r.anchor_bottom = e[3]
		r.offset_left = e[4]; r.offset_top = e[5]; r.offset_right = e[6]; r.offset_bottom = e[7]
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		r.visible = false
		canvas.add_child(r)
		monster_border.append(r)

	dim = ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.visible = false
	canvas.add_child(dim)

	hud_top_bg = ColorRect.new()
	hud_top_bg.position = Vector2(12, 10)
	hud_top_bg.size = Vector2(1256, 38)
	hud_top_bg.color = Color(0.03, 0.08, 0.12, 0.55)
	hud_top_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(hud_top_bg)

	hud_side_bg = ColorRect.new()
	hud_side_bg.position = Vector2(12, 52)
	hud_side_bg.size = Vector2(540, 230)
	hud_side_bg.color = Color(0.03, 0.08, 0.12, 0.45)
	hud_side_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(hud_side_bg)

	hud_top = _label(20, Vector2(20, 14), canvas)
	hud_side = _label(18, Vector2(20, 56), canvas)

	# High-visibility warning banner (Thuy quai / Oxy / Khach gian)
	alert_bg = ColorRect.new()
	alert_bg.anchor_left = 0.5; alert_bg.anchor_right = 0.5
	alert_bg.offset_left = -260; alert_bg.offset_right = 260
	alert_bg.offset_top = 56; alert_bg.offset_bottom = 102
	alert_bg.color = Color(0.55, 0.08, 0.12, 0.88)
	alert_bg.visible = false
	alert_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(alert_bg)

	alert_label = _label(24, Vector2.ZERO, alert_bg)
	alert_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	alert_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	alert_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER

	center = _label(30, Vector2(0, 0), canvas)
	center.set_anchors_preset(Control.PRESET_CENTER)
	center.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	center.grow_horizontal = Control.GROW_DIRECTION_BOTH
	center.grow_vertical = Control.GROW_DIRECTION_BOTH

	# High-contrast toggle button (top-right, also toggled via H key)
	contrast_btn = Button.new()
	contrast_btn.anchor_left = 1.0; contrast_btn.anchor_right = 1.0
	contrast_btn.offset_left = -230; contrast_btn.offset_right = -16
	contrast_btn.offset_top = 54; contrast_btn.offset_bottom = 88
	contrast_btn.add_theme_font_size_override("font_size", 16)
	contrast_btn.text = "H · Tương phản cao: TẮT"
	contrast_btn.pressed.connect(_toggle_high_contrast)
	canvas.add_child(contrast_btn)

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


func _toggle_high_contrast() -> void:
	high_contrast = not high_contrast
	_apply_contrast_theme()


func _apply_contrast_theme() -> void:
	contrast_btn.text = "H · Tương phản cao: " + ("BẬT" if high_contrast else "TẮT")
	if high_contrast:
		hud_top_bg.color = Color(0.0, 0.0, 0.0, 0.96)
		hud_side_bg.color = Color(0.0, 0.0, 0.0, 0.94)
		hud_top.add_theme_color_override("font_color", Color("#ffff00"))
		hud_side.add_theme_color_override("font_color", Color("#ffffff"))
		hud_top.add_theme_font_size_override("font_size", 22)
		hud_side.add_theme_font_size_override("font_size", 20)
		hud_top.add_theme_constant_override("outline_size", 10)
		hud_side.add_theme_constant_override("outline_size", 10)
	else:
		hud_top_bg.color = Color(0.03, 0.08, 0.12, 0.55)
		hud_side_bg.color = Color(0.03, 0.08, 0.12, 0.45)
		hud_top.add_theme_color_override("font_color", Color("#f4fbff"))
		hud_side.add_theme_color_override("font_color", Color("#f4fbff"))
		hud_top.add_theme_font_size_override("font_size", 20)
		hud_side.add_theme_font_size_override("font_size", 18)
		hud_top.add_theme_constant_override("outline_size", 6)
		hud_side.add_theme_constant_override("outline_size", 6)


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.keycode == KEY_H:
			_toggle_high_contrast()
		elif ev.keycode == KEY_1 and link.phase() == "shop":
			link.buy("oxygen")
		elif ev.keycode == KEY_2 and link.phase() == "shop":
			link.buy("hp")
		elif ev.keycode == KEY_R and bool(link.state.get("finished", false)):
			link.restart()


func _process(delta: float) -> void:
	blink_t += delta
	var pulse := 0.55 + 0.45 * absf(sin(blink_t * 6.0))
	for r in monster_border:
		r.visible = active_alert_monster
		r.modulate.a = pulse
	if alert_bg.visible:
		alert_bg.modulate.a = 0.72 + 0.28 * absf(sin(blink_t * 7.0))

	if not link.connected:
		hud_top.text = "Chưa kết nối logic. Mở terminal ở thư mục repo và chạy:  python -m chonoi.live"
		hud_side.text = "(đang xem trước cảnh lặn của nhóm; kết nối xong game tự bắt đầu · H: Tương phản cao)"
		center.text = ""
		alert_bg.visible = false
		active_alert_monster = false
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

	active_alert_monster = false
	active_alert_oxy = false
	active_alert_angry = false
	var alerts: Array[String] = []

	if ph == "gather":
		var p: Dictionary = s.get("player", {})
		var oxy := float(p.get("oxygen_ticks", 0)) / maxf(1.0, float(p.get("oxygen_max_ticks", 1)))
		var pos: Array = p.get("pos", [0, 0])
		var oxy_txt := "Oxy %d%%" % int(round(oxy * 100.0))
		if oxy < 0.25:
			active_alert_oxy = true
			oxy_txt = "⚠ " + oxy_txt + (" — Hết hơi!" if oxy <= 0.0 else "")
			alerts.append("⚠ HẾT HƠI!" if oxy <= 0.0 else "⚠ OXY SẮP HẾT (%d%%)!" % int(round(oxy * 100.0)))

		# Detect nearby monsters (<= 10m or actively chasing)
		var pvec := Vector2(float(pos[0]), float(pos[1]))
		for m in s.get("monsters", []):
			var mp: Array = m.get("pos", [999, 999])
			var mdist := pvec.distance_to(Vector2(float(mp[0]), float(mp[1])))
			if mdist <= 10.0 or str(m.get("state", "")) == "chase":
				active_alert_monster = true
				break
		if active_alert_monster:
			alerts.append("⚠ THỦY QUÁI GẦN!")

		hud_top.text = "%sBuổi sáng · %s · Máu %s/%s · %s · Sâu %.1f m · %s" % [
			day_txt, time_txt, str(p.get("hp", 0)), str(p.get("hp_max", 0)), oxy_txt, float(pos[1]), common]
		hud_side.text = _hold_text(s) + "\nE: hái/cập bến · Space: bắt cá · Esc/P: tạm dừng · H: tương phản"
	elif ph == "quan":
		hud_top.text = "%sBuổi tối · %s · %s" % [day_txt, time_txt, common]
		hud_side.text = _quan_text(s) + "\nE: bếp/bưng/giao món · Esc/P: tạm dừng · H: tương phản"
		if active_alert_angry:
			alerts.append("⚠ KHÁCH SẮP GIẬN!")
	else:
		hud_top.text = "%sShop · tự đóng sau %ds · %s" % [day_txt, secs, common]
		hud_side.text = "1: Bình oxy · 2: Áo phao · Enter: Đóng Shop · H: tương phản"

	# Update top warning banner
	if alerts.size() > 0:
		alert_label.text = "   |   ".join(alerts)
		alert_bg.color = Color(0.50, 0.10, 0.72, 0.92) if active_alert_monster else Color(0.70, 0.12, 0.12, 0.92)
		alert_bg.visible = true
	else:
		alert_bg.visible = false

	shop_panel.visible = ph == "shop" and not bool(s.get("finished", false))
	if shop_panel.visible:
		shop_label.text = "SHOP NÂNG CẤP — Tiền %sk\nĐã mua: %s (áp dụng từ Ngày kế)" % [
			str(s.get("money", 0)), JSON.stringify(s.get("upgrades", {}))]
	var paused := str(s.get("state", "")) == "paused"
	dim.visible = paused
	if bool(s.get("finished", false)):
		center.text = "KẾT THÚC (%s)\nĐiểm %s · Tiền %sk\nR: chơi lại" % [str(s.get("reason", "")), str(s.get("score", 0)), str(s.get("money", 0))]
	elif paused:
		center.text = "TẠM DỪNG\nEsc/P: tiếp tục · H: tương phản cao"
	else:
		center.text = ""


func _summarize_items(raw_items) -> Dictionary:
	# Supports BOTH v1.1 (Array[String] / Dict{kind: count}) and v1.2 (Array[{id, kind, fresh}])
	var stats := {}
	if typeof(raw_items) == TYPE_DICTIONARY:
		for k in raw_items.keys():
			stats[str(k)] = {"count": int(raw_items[k]), "spoiled": 0, "min_fresh": -1.0}
		return stats
	if typeof(raw_items) == TYPE_ARRAY:
		for entry in raw_items:
			if typeof(entry) == TYPE_DICTIONARY:
				var k := str(entry.get("kind", ""))
				var fr := float(entry.get("fresh", 100.0))
				if not stats.has(k):
					stats[k] = {"count": 0, "spoiled": 0, "min_fresh": fr}
				stats[k]["count"] += 1
				stats[k]["min_fresh"] = minf(stats[k]["min_fresh"], fr)
				if fr < 30.0:
					stats[k]["spoiled"] += 1
			else:
				var k := str(entry)
				if not stats.has(k):
					stats[k] = {"count": 0, "spoiled": 0, "min_fresh": -1.0}
				stats[k]["count"] += 1
	return stats


func _fresh_suffix(st: Dictionary) -> String:
	if float(st.get("min_fresh", -1.0)) < 0.0:
		return ""
	var sp := int(st.get("spoiled", 0))
	if sp > 0:
		return " [⚠ %d ươn, min %d%%]" % [sp, int(round(float(st["min_fresh"])))]
	return " [tươi %d%%]" % int(round(float(st["min_fresh"])))


func _hold_text(s: Dictionary) -> String:
	var stats := _summarize_items(s.get("hold", []))
	var lines := ["Giỏ %s/%s" % [str(s.get("hold_count", 0)), str(s.get("hold_capacity", 0))]]
	var need: Dictionary = s.get("day_plan", {}).get("ingredients", {})
	for k in need.keys():
		var st: Dictionary = stats.get(k, {"count": 0, "spoiled": 0, "min_fresh": -1.0})
		lines.append("  %s: %d/%d%s" % [KIND_VI.get(k, k), int(st["count"]), int(need[k]), _fresh_suffix(st)])
	for k in stats.keys():
		if not need.has(k):
			var st: Dictionary = stats[k]
			lines.append("  %s: %d%s" % [KIND_VI.get(k, k), int(st["count"]), _fresh_suffix(st)])
	return "\n".join(lines)


func _quan_text(s: Dictionary) -> String:
	var lines := []
	var stats := _summarize_items(s.get("stock", {}))
	var parts := []
	for k in stats.keys():
		var st: Dictionary = stats[k]
		parts.append("%s ×%d%s" % [KIND_VI.get(k, k), int(st["count"]), _fresh_suffix(st)])
	lines.append("Kho: " + (", ".join(parts) if parts.size() > 0 else "(trống)"))
	var hand = s.get("hand")
	lines.append("Đang cầm: " + (str(hand.get("dish_id", hand)) if typeof(hand) == TYPE_DICTIONARY else (str(hand) if hand != null else "—")))
	var patience_max := float(s.get("meta", {}).get("patience_s", 60)) * 60.0
	for c in s.get("customers", []):
		var ratio := float(c.get("patience_ticks_left", 0)) / maxf(1.0, patience_max)
		var is_angry := ratio < 0.25 and str(c.get("state", "")) == "waiting"
		if is_angry:
			active_alert_angry = true
		var mark := "⚠ SẮP GIẬN! " if is_angry else ""
		lines.append("  %s%s %s: %s (%s, %d%%)" % [mark, str(c.get("table_id", "")), str(c.get("id", "")),
			str(c.get("dish_id", "")), str(c.get("state", "")), int(round(ratio * 100.0))])
	for st in s.get("stoves", []):
		lines.append("  Bếp %s: %s %s" % [str(st.get("id", "")), str(st.get("state", "")),
			str(st.get("dish", "")) if st.get("dish") != null else ""])
	return "\n".join(lines)
