extends Node3D
## Game chính: nối logic (`chonoi.live`) với các cảnh 3D của nhóm.
##   gather -> res://scenes/DiveUnderwater.tscn   (lặn 2.5D, nhìn ngang)
##   quan / shop -> res://scenes/RestaurantNight.tscn (quán bè, góc nhìn thứ 3)
## Full styled HUD: rounded glass cards, ProgressBars (Oxy & Customer Patience),
## Vietnamese dish/state labels, warning alerts, freshness/spoiled tags & High Contrast mode (H).

const HUD_FONT := preload("res://assets/fonts/be-vietnam-pro/BeVietnamPro-Medium.ttf")
const CLOCK_FONT := preload("res://assets/fonts/bbh-bogle/BBHBogle-Regular.ttf")
const GLASS_SHADER := preload("res://shaders/hud_frosted_glass.gdshader")
const ALERT_AUDIO := preload("res://scripts/alert_audio.gd")
const SCENE_FOR_PHASE := {
	"gather": "res://scenes/DiveUnderwater.tscn",
	"quan": "res://scenes/RestaurantNight.tscn",
	"shop": "res://scenes/RestaurantNight.tscn",
}
const KIND_VI := {
	"ca_loc": "Cá lóc", "ca_linh": "Cá linh", "ca_keo": "Cá kèo",
	"bong_dien_dien": "Bông điên điển", "bong_sung": "Bông súng", "keo_neo": "Kèo nèo",
}
const KIND_SHORT := {
	"ca_loc": "Cá lóc", "ca_linh": "Cá linh", "ca_keo": "Cá kèo",
	"bong_dien_dien": "Điên điển", "bong_sung": "Bông súng", "keo_neo": "Kèo nèo",
}
const DISH_VI := {
	"ca_loc_nuong_trui": "Cá lóc nướng",
	"goi_bong_sung": "Gỏi bông súng",
	"lau_ca_linh_dien_dien": "Lẩu cá linh",
	"canh_chua_ca_loc": "Canh chua cá lóc",
	"ca_keo_nuong": "Cá kèo nướng",
	"lau_mam": "Lẩu mắm",
}
const STOVE_VI := {
	"idle": "Rảnh",
	"cooking": "Đang nấu",
	"ready": "Chín rồi!",
}
const CUST_VI := {
	"waiting": "Chờ món",
	"eating": "Đang ăn",
}
const RESERVATION_VI := {
	"scheduled": "Đã đặt", "holding": "Giữ bàn", "waiting": "Chờ món",
	"served": "Đã giao", "failed": "Lỡ đơn",
}
const CUE_SUBTITLES := {
	"monster": "[Âm trầm] Thủy quái đến gần",
	"oxygen": "[Bíp ngắn] Oxy sắp hết",
	"customer": "[Chuông báo] Khách sắp giận",
	"current": "[Hai tiếng báo] Dòng nước lũ sắp đến",
}

var link: Node
var world: Node3D
var world_viewport: SubViewport
var world_path := ""

# Styled HUD nodes
var top_panel: PanelContainer
var phase_badge: Label
var time_label: Label
var stats_label: Label
var contrast_btn: Button
var sound_btn: Button
var cue_audio: Node
var previous_cues: Dictionary = {}
var cue_run_id := -1
var subtitle_panel: PanelContainer
var subtitle_label: Label
var subtitle_seconds := 0.0

var left_panel: PanelContainer
var left_vbox: VBoxContainer
var reservation_panel: PanelContainer
var reservation_label: Label

var alert_panel: PanelContainer
var alert_label: Label
var monster_border: Array[ColorRect] = []

var bottom_panel: PanelContainer
var bottom_label: Label

var center_panel: PanelContainer
var center_label: Label
var continue_btn: Button
var menu_btn: Button
var quit_btn: Button
var shop_panel: PanelContainer
var shop_label: Label
var dim: ColorRect
var glass_cards: Dictionary = {}

var high_contrast := false
var blink_t := 0.0
var active_alert_monster := false
var active_alert_oxy := false
var active_alert_angry := false
# Ngưỡng cảnh báo từ meta.alerts (chonoi.live, Hà Anh); thiếu khóa thì dùng mặc định cũ
var alert_cfg: Dictionary = {}
var last_state: Dictionary = {}


func _ready() -> void:
	link = load("res://scripts/sim_link.gd").new()
	link.name = "SimLink"
	add_child(link)
	link.state_updated.connect(_on_state)
	cue_audio = ALERT_AUDIO.new()
	add_child(cue_audio)
	_build_world_viewport()
	_build_ui()
	_apply_contrast_theme()
	_show_world("res://scenes/DiveUnderwater.tscn")


func _build_world_viewport() -> void:
	var view := SubViewportContainer.new()
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	view.stretch = true
	add_child(view)
	world_viewport = SubViewport.new()
	world_viewport.own_world_3d = true
	view.add_child(world_viewport)


func _show_world(path: String) -> void:
	if path == world_path:
		return
	if is_instance_valid(world):
		world.queue_free()
	world_path = path
	world = load(path).instantiate()
	world.set("link", link)
	world_viewport.add_child(world)


func _card_style(bg: Color, border: Color, radius := 12, pad_x := 14, pad_y := 8, border_w := 2) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(border_w)
	sb.set_corner_radius_all(radius)
	sb.content_margin_left = pad_x
	sb.content_margin_right = pad_x
	sb.content_margin_top = pad_y
	sb.content_margin_bottom = pad_y
	sb.shadow_color = Color(0, 0, 0, 0.18)
	sb.shadow_size = 4
	sb.shadow_offset = Vector2(0, 2)
	return sb


func _bar_style(col: Color, radius := 6) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(radius)
	return sb


func _mk_label(text: String, size: int, color := Color("#f5f7fa")) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", HUD_FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 2 if not high_contrast else 6)
	return l


func _mk_progress_bar(ratio: float, fill_col: Color, height := 14, width := 240) -> ProgressBar:
	var pb := ProgressBar.new()
	pb.min_value = 0.0
	pb.max_value = 100.0
	pb.value = clampf(ratio * 100.0, 0.0, 100.0)
	pb.show_percentage = false
	pb.custom_minimum_size = Vector2(width, height)
	pb.add_theme_stylebox_override("background", _bar_style(Color(0.67, 0.84, 0.80, 0.20), 4))
	pb.add_theme_stylebox_override("fill", _bar_style(fill_col, 4))
	return pb


func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	canvas.layer = 10
	add_child(canvas)

	# 4-edge pulsing purple border when a monster is close
	var edge_defs := [
		[0.0, 0.0, 1.0, 0.0, 0, 0, 0, 10],
		[0.0, 1.0, 1.0, 1.0, 0, -10, 0, 0],
		[0.0, 0.0, 0.0, 1.0, 0, 0, 10, 0],
		[1.0, 0.0, 1.0, 1.0, -10, 0, 0, 0],
	]
	for e in edge_defs:
		var r := ColorRect.new()
		r.color = Color(0.65, 0.25, 0.76, 0.52)
		r.anchor_left = e[0]; r.anchor_top = e[1]; r.anchor_right = e[2]; r.anchor_bottom = e[3]
		r.offset_left = e[4]; r.offset_top = e[5]; r.offset_right = e[6]; r.offset_bottom = e[7]
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		r.visible = false
		canvas.add_child(r)
		monster_border.append(r)

	dim = ColorRect.new()
	dim.color = Color(0, 0, 0, 0.58)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.visible = false
	canvas.add_child(dim)

	# 1. COMPACT TOP STATUS BAR
	top_panel = PanelContainer.new()
	top_panel.anchor_left = 0.0; top_panel.anchor_right = 1.0
	top_panel.offset_left = 14; top_panel.offset_right = -14
	top_panel.offset_top = 12; top_panel.offset_bottom = 50
	canvas.add_child(top_panel)

	var top_hbox := HBoxContainer.new()
	top_hbox.add_theme_constant_override("separation", 10)
	top_panel.add_child(top_hbox)

	phase_badge = _mk_label("Ngày 1 · Sông", 14, Color("#f2faf5"))
	top_hbox.add_child(phase_badge)

	var sp1 := Control.new()
	sp1.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_hbox.add_child(sp1)

	time_label = _mk_label("3:00", 16, Color("#ffffff"))
	time_label.add_theme_font_override("font", CLOCK_FONT)
	top_hbox.add_child(time_label)

	var sp2 := Control.new()
	sp2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_hbox.add_child(sp2)

	stats_label = _mk_label("0k  ·  Uy tín 3.0  ·  300 điểm", 12, Color("#d4e5df"))
	top_hbox.add_child(stats_label)

	contrast_btn = Button.new()
	contrast_btn.text = "H · Tương phản"
	contrast_btn.add_theme_font_override("font", HUD_FONT)
	contrast_btn.add_theme_font_size_override("font_size", 12)
	contrast_btn.pressed.connect(_toggle_high_contrast)
	top_hbox.add_child(contrast_btn)
	sound_btn = _make_button("M · Âm thanh", _toggle_mute)
	top_hbox.add_child(sound_btn)

	# 2. MINIMALIST LEFT INFO CARD
	left_panel = PanelContainer.new()
	left_panel.position = Vector2(14, 60)
	left_panel.custom_minimum_size = Vector2(238, 0)
	canvas.add_child(left_panel)

	left_vbox = VBoxContainer.new()
	left_vbox.add_theme_constant_override("separation", 5)
	left_panel.add_child(left_vbox)

	reservation_panel = PanelContainer.new()
	reservation_panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	reservation_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	reservation_panel.offset_left = -14
	reservation_panel.offset_right = -14
	reservation_panel.offset_top = 104
	reservation_panel.offset_bottom = 104
	reservation_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reservation_panel.hide()
	canvas.add_child(reservation_panel)
	reservation_label = _mk_label("", 13, Color.WHITE)
	reservation_panel.add_child(reservation_label)

	# 3. COMPACT TOP-CENTER WARNING PILL
	alert_panel = PanelContainer.new()
	alert_panel.anchor_left = 0.5; alert_panel.anchor_right = 0.5
	alert_panel.offset_left = -220; alert_panel.offset_right = 220
	alert_panel.offset_top = 60; alert_panel.offset_bottom = 96
	alert_panel.visible = false
	alert_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(alert_panel)

	alert_label = _mk_label("", 13, Color("#ffffff"))
	alert_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	alert_panel.add_child(alert_label)

	# 4. SLIM BOTTOM KEYBIND BAR
	bottom_panel = PanelContainer.new()
	bottom_panel.anchor_left = 0.5; bottom_panel.anchor_right = 0.5
	bottom_panel.anchor_top = 1.0; bottom_panel.anchor_bottom = 1.0
	bottom_panel.offset_left = -250; bottom_panel.offset_right = 250
	bottom_panel.offset_top = -36; bottom_panel.offset_bottom = -10
	bottom_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(bottom_panel)

	bottom_label = _mk_label("WASD Di chuyển  ·  E Tương tác  ·  Space Bắt cá  ·  Esc/P Tạm dừng  ·  H Tương phản", 12, Color("#d4e5df"))
	bottom_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bottom_panel.add_child(bottom_label)

	subtitle_panel = PanelContainer.new()
	subtitle_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	subtitle_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	subtitle_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	subtitle_panel.offset_top = -48
	subtitle_panel.offset_bottom = -48
	subtitle_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	subtitle_panel.visible = false
	canvas.add_child(subtitle_panel)
	subtitle_label = _mk_label("", 15, Color.WHITE)
	subtitle_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle_panel.add_child(subtitle_label)

	# 5. CENTER PAUSE / END CARD
	center_panel = PanelContainer.new()
	center_panel.set_anchors_preset(Control.PRESET_CENTER)
	center_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	center_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	center_panel.visible = false
	canvas.add_child(center_panel)

	var center_box := VBoxContainer.new()
	center_box.add_theme_constant_override("separation", 8)
	center_panel.add_child(center_box)
	center_label = _mk_label("", 20, Color("#fff3c4"))
	center_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	center_box.add_child(center_label)
	continue_btn = _make_button("Tiếp tục", func(): link.request_action("/continue"))
	menu_btn = _make_button("Về menu", func(): link.request_action("/menu"))
	quit_btn = _make_button("Thoát", func(): get_tree().quit())
	for button in [continue_btn, menu_btn, quit_btn]:
		center_box.add_child(button)

	# 6. COMPACT SHOP MODAL CARD
	shop_panel = PanelContainer.new()
	shop_panel.set_anchors_preset(Control.PRESET_CENTER)
	shop_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	shop_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	shop_panel.visible = false
	canvas.add_child(shop_panel)

	var sbox := VBoxContainer.new()
	sbox.add_theme_constant_override("separation", 6)
	shop_panel.add_child(sbox)
	shop_label = _mk_label("CỬA HÀNG NÂNG CẤP", 17, Color("#ffe394"))
	shop_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sbox.add_child(shop_label)
	for spec in [["1 · Bình oxy (+lặn lâu)", "oxygen"], ["2 · Áo phao (+1 Máu)", "hp"]]:
		var b := Button.new()
		b.text = spec[0]
		b.add_theme_font_override("font", HUD_FONT)
		b.add_theme_font_size_override("font_size", 15)
		var action: String = spec[1]
		b.pressed.connect(func(): link.buy(action))
		sbox.add_child(b)
	var shint := _mk_label("Enter: Đóng Shop sang Ngày mới", 13, Color("#cfe4f0"))
	shint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sbox.add_child(shint)

	_add_glass_card(canvas, top_panel, 13.0)
	_add_glass_card(canvas, left_panel, 14.0)
	_add_glass_card(canvas, bottom_panel, 13.0)
	_add_glass_card(canvas, center_panel, 16.0)
	_add_glass_card(canvas, shop_panel, 16.0)


func _make_button(title: String, action: Callable) -> Button:
	var button := Button.new()
	button.text = title
	button.add_theme_font_override("font", HUD_FONT)
	button.add_theme_font_size_override("font_size", 14)
	button.pressed.connect(action)
	return button


func _add_glass_card(canvas: CanvasLayer, panel: PanelContainer, radius: float) -> void:
	var card := ColorRect.new()
	card.z_index = -1
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var shader_material := ShaderMaterial.new()
	shader_material.shader = GLASS_SHADER
	shader_material.set_shader_parameter("scene_texture", world_viewport.get_texture())
	shader_material.set_shader_parameter("corner_radius", radius)
	card.material = shader_material
	canvas.add_child(card)
	glass_cards[panel] = card
	var sync := func():
		card.position = panel.position
		card.size = panel.size
		card.visible = panel.visible and not high_contrast
		shader_material.set_shader_parameter("panel_size", card.size)
	panel.item_rect_changed.connect(sync)
	panel.visibility_changed.connect(sync)
	sync.call()


func _toggle_high_contrast() -> void:
	high_contrast = not high_contrast
	_apply_contrast_theme()
	if not last_state.is_empty():
		_on_state(last_state)


func _apply_contrast_theme() -> void:
	contrast_btn.text = "H · Tương phản" + (" ✓" if high_contrast else "")
	for panel in glass_cards:
		glass_cards[panel].visible = panel.visible and not high_contrast
	var subtitle_border := Color("#ffff00") if high_contrast else Color("#c6e6e3")
	subtitle_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.94), subtitle_border, 8))
	var reservation_bg := Color(0, 0, 0, 0.96) if high_contrast else Color(0.04, 0.10, 0.09, 0.74)
	reservation_panel.add_theme_stylebox_override("panel", _card_style(reservation_bg, subtitle_border, 10))
	if high_contrast:
		top_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.96), Color("#ffff00"), 8, 10, 4, 2))
		left_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.95), Color("#ffff00"), 8, 8, 6, 2))
		bottom_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.95), Color("#ffffff"), 6, 10, 3, 1))
		center_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.98), Color("#ffff00"), 10, 20, 14, 2))
		shop_panel.add_theme_stylebox_override("panel", _card_style(Color(0, 0, 0, 0.98), Color("#ffff00"), 10, 16, 12, 2))
		phase_badge.add_theme_color_override("font_color", Color("#ffff00"))
		time_label.add_theme_color_override("font_color", Color("#ffffff"))
		stats_label.add_theme_color_override("font_color", Color("#ffff00"))
		bottom_label.add_theme_color_override("font_color", Color("#ffffff"))
	else:
		var glass := Color(0.04, 0.10, 0.09, 0.58)
		var rim := Color(0.80, 0.93, 0.87, 0.42)
		top_panel.add_theme_stylebox_override("panel", _card_style(glass, rim, 13, 14, 4, 1))
		left_panel.add_theme_stylebox_override("panel", _card_style(glass, rim, 14, 12, 8, 1))
		bottom_panel.add_theme_stylebox_override("panel", _card_style(glass, rim, 13, 12, 4, 1))
		center_panel.add_theme_stylebox_override("panel", _card_style(glass, rim, 16, 26, 18, 1))
		shop_panel.add_theme_stylebox_override("panel", _card_style(glass, rim, 16, 22, 16, 1))
		phase_badge.add_theme_color_override("font_color", Color("#e6f4eb"))
		time_label.add_theme_color_override("font_color", Color("#ffffff"))
		stats_label.add_theme_color_override("font_color", Color("#e8f8ff"))
		bottom_label.add_theme_color_override("font_color", Color("#d4e4ee"))


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.keycode == KEY_H:
			_toggle_high_contrast()
		elif ev.keycode == KEY_M:
			_toggle_mute()
		elif last_state.get("presentation") != null:
			var screen: Dictionary = last_state["presentation"]
			if screen["name"] != "menu" or ev.keycode == KEY_ENTER:
				link.request_action("/continue")
		elif ev.keycode == KEY_1 and link.phase() == "shop":
			link.buy("oxygen")
		elif ev.keycode == KEY_2 and link.phase() == "shop":
			link.buy("hp")
		elif ev.keycode == KEY_R and _can_restart():
			link.restart()


func _can_restart() -> bool:
	# Chơi lại: khi đã kết thúc, hoặc đang tạm dừng (Esc/P rồi R) để tránh bấm nhầm giữa lượt.
	if not link.connected:
		return false
	var s: Dictionary = link.state
	return bool(s.get("finished", false)) or str(s.get("state", "")) == "paused"


func _clear_left_card() -> void:
	for c in left_vbox.get_children():
		c.queue_free()


func _process(delta: float) -> void:
	if subtitle_seconds > 0.0:
		subtitle_seconds = maxf(0.0, subtitle_seconds - delta)
		subtitle_panel.visible = subtitle_seconds > 0.0
	blink_t += delta
	var pulse := 0.55 + 0.45 * absf(sin(blink_t * 6.0))
	for r in monster_border:
		r.visible = active_alert_monster
		r.modulate.a = pulse
	if alert_panel.visible:
		alert_panel.modulate.a = 0.78 + 0.22 * absf(sin(blink_t * 7.0))

	if not link.connected:
		phase_badge.text = "CHỜ KẾT NỐI SERVER"
		time_label.text = "—"
		stats_label.text = "Chạy: python3 -m chonoi.live"
		alert_panel.visible = false
		active_alert_monster = false
		shop_panel.visible = false
		center_panel.visible = false
		dim.visible = false
		if left_vbox.get_child_count() == 0:
			left_vbox.add_child(_mk_label("Đang xem trước cảnh 3D.\nBật server logic để bắt đầu chơi.", 13, Color("#cfe4f0")))


func _al(key: String, fallback: float) -> float:
	return float(alert_cfg.get(key, fallback))


func _toggle_mute() -> void:
	cue_audio.toggle_mute()
	sound_btn.text = "M · Đã tắt tiếng" if cue_audio.muted else "M · Âm thanh"


func _current_warning(s: Dictionary) -> bool:
	var phase_tick := int(s.get("phase_tick", 0))
	var warning_ticks := int(s.get("meta", {}).get("current", {}).get("warning_ticks", 0))
	for event in s.get("events", []):
		if event.get("name") != "current_warning" or event.get("day") != s.get("day"):
			continue
		var starts_at := int(event["data"]["starts_at_phase_tick"])
		if phase_tick >= starts_at - warning_ticks and phase_tick < starts_at:
			return true
	return false


func _update_sound_cues(s: Dictionary, current_warning: bool) -> void:
	var run_id := int(s.get("run_id", 0))
	if run_id != cue_run_id:
		cue_run_id = run_id
		previous_cues.clear()
		subtitle_seconds = 0.0
		subtitle_panel.hide()
	var cues := {"monster": active_alert_monster, "oxygen": active_alert_oxy,
		"customer": active_alert_angry, "current": current_warning}
	var captions: Array[String] = []
	for key in cues:
		if cues[key] and not previous_cues.get(key, false):
			cue_audio.cue(key)
			captions.append(CUE_SUBTITLES[key])
	previous_cues = cues
	if not captions.is_empty():
		subtitle_label.text = "\n".join(captions)
		subtitle_seconds = 3.0
		subtitle_panel.show()


func _on_state(s: Dictionary) -> void:
	last_state = s
	var ph := str(s.get("phase", s.get("mode", "gather")))
	if SCENE_FOR_PHASE.has(ph):
		_show_world(SCENE_FOR_PHASE[ph])

	var secs := int(ceil(float(s.get("time_left_ticks", 0)) / 60.0))
	var day_num := int(round(float(s.get("day", 1))))
	var money_i := int(round(float(s.get("money", 0))))
	var rep_f := float(s.get("reputation", 3.0))
	var score_i := int(round(float(s.get("score", 0))))

	var ph_vi := "Sông" if ph == "gather" else ("Quán" if ph == "quan" else "Cửa hàng")
	phase_badge.text = ("Ngày %d · %s" % [day_num, ph_vi]) if s.has("day") else ph_vi

	# Ngưỡng cảnh báo lấy từ dữ liệu (meta.alerts do chonoi.live gửi, Hà Anh); thiếu thì dùng mặc định cũ
	alert_cfg = s.get("meta", {}).get("alerts", {})
	var low_time := secs <= int(_al("time_low_s", 30)) and ph != "shop"
	time_label.text = "%d:%02d" % [secs / 60, secs % 60]
	time_label.add_theme_color_override("font_color", Color("#ff6b6b") if low_time else Color("#ffffff"))
	stats_label.text = "%dk  ·  Uy tín %.1f  ·  %d điểm" % [money_i, rep_f, score_i]

	active_alert_monster = false
	active_alert_oxy = false
	active_alert_angry = false
	var alerts: Array[String] = []

	_clear_left_card()
	if ph == "gather":
		_build_gather_card(s, alerts)
		bottom_label.text = "WASD Bơi  ·  E Hái/Cập bến  ·  Space Bắt cá  ·  Esc Tạm dừng"
	elif ph == "quan":
		_build_quan_card(s, alerts)
		bottom_label.text = "WASD Đi lại  ·  E Nấu/Bưng/Giao  ·  Esc Tạm dừng"
	else:
		left_vbox.add_child(_mk_label("Mua nâng cấp cho Ngày kế tiếp.", 13, Color("#ffe394")))
		bottom_label.text = "1: Bình oxy  ·  2: Áo phao  ·  Enter: Đóng Shop  ·  H: Tương phản"

	var warning := ph == "gather" and _current_warning(s)
	if warning:
		alerts.append("≈ DÒNG NƯỚC LŨ SẮP ĐẾN")
	elif ph == "gather" and s.get("current") != null:
		var flow: Dictionary = s["current"]
		alerts.append("DÒNG NƯỚC LŨ " + ("→" if int(flow["direction"]) > 0 else "←"))
	_update_reservation_card(s.get("reservations", []))
	_update_sound_cues(s, warning)

	if alerts.size() > 0:
		alert_label.text = "   |   ".join(alerts)
		var bg := Color(0.50, 0.10, 0.74, 0.94) if active_alert_monster else Color(0.74, 0.14, 0.14, 0.94)
		var bd := Color("#e8a8ff") if active_alert_monster else Color("#ffcf6b")
		if high_contrast:
			bg = Color.BLACK
			bd = Color.YELLOW
		alert_label.add_theme_color_override("font_color", Color.YELLOW if high_contrast else Color.WHITE)
		alert_panel.add_theme_stylebox_override("panel", _card_style(bg, bd, 12, 18, 8, 2))
		alert_panel.visible = true
	else:
		alert_panel.visible = false

	var paused := str(s.get("state", "")) == "paused"
	shop_panel.visible = ph == "shop" and not bool(s.get("finished", false)) and not paused and s.get("presentation") == null
	if shop_panel.visible:
		shop_label.text = "CỬA HÀNG NÂNG CẤP — 💰 %dk\nĐã mua: %s (áp dụng từ Ngày kế)" % [
			money_i, JSON.stringify(s.get("upgrades", {}))]

	_update_center_card(s, day_num, paused, score_i, money_i, rep_f)


func _update_reservation_card(orders: Array) -> void:
	reservation_panel.visible = not orders.is_empty()
	if orders.is_empty():
		return
	var rows := PackedStringArray(["ĐẶT TRƯỚC"])
	for order in orders:
		var dish := str(order["dish_id"])
		var seconds := int(ceil(float(order["arrival_tick"]) / 60.0))
		var words := "%s · %s · %d:%02d\n%s · %s" % [order["id"], order["table_id"],
			seconds / 60, seconds % 60, DISH_VI.get(dish, dish), RESERVATION_VI.get(order["state"], order["state"])]
		rows.append(words)
	reservation_label.text = "\n".join(rows)


func _update_center_card(s: Dictionary, day_num: int, paused: bool, score_i: int, money_i: int, rep_f: float) -> void:
	var screen = s.get("presentation")
	var screen_name := str(screen["name"]) if screen != null else ""
	continue_btn.visible = paused or screen != null
	continue_btn.text = "Chơi" if screen_name == "menu" else "Tiếp tục"
	menu_btn.visible = screen_name != "menu" and s.has("presentation") and (paused or bool(s.get("finished", false)))
	quit_btn.visible = screen_name == "menu"
	dim.visible = screen != null or paused or bool(s.get("finished", false))
	center_panel.visible = dim.visible
	if screen != null:
		match screen_name:
			"menu":
				center_label.text = "QUÁN ĂN CHỢ NỔI"
			"day_intro":
				var dishes := PackedStringArray()
				for dish in s.get("day_plan", {}).get("dishes", {}):
					var count: int = int(s["day_plan"]["dishes"][dish])
					dishes.append("%s ×%d" % [DISH_VI.get(dish, dish), count])
				center_label.text = "NGÀY %d · MÁ TƯ DẶN\n%s" % [day_num, "\n".join(dishes)]
			"evening_intro":
				var stock = s.get("stock", [])
				var available := _cookable_dishes(s, _available_stock(s))
				var names := PackedStringArray()
				for dish in available:
					names.append(DISH_VI.get(dish, dish))
				center_label.text = "MỞ QUÁN · NGÀY %d\nNhập kho %d nguyên liệu\n%s" % [day_num,
					stock.size(), " · ".join(names) if not names.is_empty() else "Chưa có món đủ nguyên liệu"]
			"day_result":
				var summary: Dictionary = s.get("shift_summary", {})
				center_label.text = "KẾT CA · NGÀY %d\nĐã phục vụ %d · Bỏ đi %d\nThu %dk · Boa %dk · Uy tín %+.1f" % [
					day_num, int(summary.get("served", 0)), int(summary.get("left", 0)),
					int(summary.get("earned", 0)), int(summary.get("tips", 0)), rep_f - float(summary.get("reputation_start", rep_f))]
		return
	if bool(s.get("finished", false)):
		var sales: Dictionary = s.get("dish_sales", {})
		var best := ""
		var best_count := 0
		var dishes := sales.keys()
		dishes.sort()
		for dish in dishes:
			if int(sales[dish]) > best_count:
				best = dish
				best_count = int(sales[dish])
		center_label.text = "TỔNG KẾT\nĐiểm %d · Tiền %dk · Uy tín %.1f\nMón bán chạy: %s\nNhấn R để chơi lại" % [
			score_i, money_i, rep_f, DISH_VI.get(best, "—")]
	elif paused:
		center_label.text = "TẠM DỪNG\nEsc / P: Tiếp tục   ·   R: Chơi lại từ đầu   ·   H: Tương phản cao"


func _build_gather_card(s: Dictionary, alerts: Array[String]) -> void:
	var p: Dictionary = s.get("player", {})
	var hp := int(round(float(p.get("hp", 3))))
	var hp_max := maxi(1, int(round(float(p.get("hp_max", 3)))))
	var oxy := float(p.get("oxygen_ticks", 0)) / maxf(1.0, float(p.get("oxygen_max_ticks", 1)))
	var pos: Array = p.get("pos", [0, 0])

	# Compact HP hearts + Depth row
	var hearts := ""
	for i in range(hp_max):
		hearts += "♥" if i < hp else "♡"
	var top_row := HBoxContainer.new()
	top_row.add_child(_mk_label(hearts.strip_edges(), 17, Color("#ff5c6c")))
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(sp)
	top_row.add_child(_mk_label("Độ sâu: %.1f m" % float(pos[1]), 13, Color("#9ee8ff")))
	left_vbox.add_child(top_row)

	# Slim Oxygen bar
	var oxy_pct := int(round(oxy * 100.0))
	var oxy_col := Color("#36d6e8") if oxy >= 0.5 else (Color("#f5c242") if oxy >= _al("oxygen_low_ratio", 0.25) else Color("#ff4757"))
	var oxy_lbl := _mk_label("Oxy: %d%%" % oxy_pct, 13, oxy_col)
	left_vbox.add_child(oxy_lbl)
	left_vbox.add_child(_mk_progress_bar(oxy, oxy_col, 6, 210))

	if oxy < _al("oxygen_low_ratio", 0.25):
		active_alert_oxy = true
		alerts.append("⚠ HẾT HƠI!" if oxy <= 0.0 else "⚠ OXY SẮP HẾT (%d%%)!" % oxy_pct)

	# Monster proximity check
	var pvec := Vector2(float(pos[0]), float(pos[1]))
	var cooldown := int(p.get("catch_cd_ticks", 0))
	left_vbox.add_child(_mk_label("Bắt cá: sẵn sàng" if cooldown <= 0 else "Bắt cá: chờ %.1f giây" % (float(cooldown) / 60.0), 13, Color("#cfe4f0")))
	var meta: Dictionary = s.get("meta", {})
	if bool(p.get("at_surface", false)):
		var dock: Array = meta.get("dock_pos", [2, 0])
		if pvec.distance_to(Vector2(float(dock[0]), float(dock[1]))) <= float(meta.get("dock_radius", 3)):
			left_vbox.add_child(_mk_label("[E] Cập bến, mở quán", 13, Color("#ffe394")))
		else:
			for node in s.get("nodes", []):
				var node_pos: Array = node.get("pos", [999, 999])
				if bool(node.get("ready", false)) and pvec.distance_to(Vector2(float(node_pos[0]), float(node_pos[1]))) <= float(meta.get("interact_radius", 2)):
					left_vbox.add_child(_mk_label("[E] Hái " + str(KIND_VI.get(node.get("kind", ""), node.get("kind", ""))), 13, Color("#ffe394")))
					break
	for m in s.get("monsters", []):
		var mp: Array = m.get("pos", [999, 999])
		var near_m: Dictionary = alert_cfg.get("monster_near_m", {})
		var near_r := float(near_m.get(str(m.get("kind", "ca_sau")), 10.0))
		if pvec.distance_to(Vector2(float(mp[0]), float(mp[1]))) <= near_r or str(m.get("state", "")) == "chase":
			active_alert_monster = true
			break
	if active_alert_monster:
		alerts.append("⚠ THỦY QUÁI GẦN!")

	# Compact 2-column ingredient grid (half the height!)
	var hold_c := int(round(float(s.get("hold_count", 0))))
	var hold_cap := int(round(float(s.get("hold_capacity", 12))))
	left_vbox.add_child(_mk_label("Giỏ đồ: %d / %d ô" % [hold_c, hold_cap], 13, Color("#ffe394")))
	var stats := _summarize_items(s.get("hold", []))
	var need: Dictionary = s.get("day_plan", {}).get("ingredients", {})
	for k in need.keys():
		var st: Dictionary = stats.get(k, {"count": 0, "spoiled": 0, "min_fresh": -1.0})
		var got := int(st["count"])
		var req := int(round(float(need[k])))
		var col := Color("#7bed9f") if got >= req else Color("#f1f5f9")
		left_vbox.add_child(_mk_label("  • %s: %d/%d%s" % [KIND_VI.get(k, k), got, req, _fresh_suffix(st)], 13, col))
	for k in stats.keys():
		if not need.has(k):
			var st: Dictionary = stats[k]
			left_vbox.add_child(_mk_label("  • %s: %d%s" % [KIND_VI.get(k, k), int(st["count"]), _fresh_suffix(st)], 13, Color("#d4e4ee")))


func _build_quan_card(s: Dictionary, alerts: Array[String]) -> void:
	# Compact carrying row
	var hand = s.get("hand")
	var hand_id := str(hand.get("dish_id", "")) if typeof(hand) == TYPE_DICTIONARY else (str(hand) if hand != null else "")
	var hand_txt: String = str(DISH_VI.get(hand_id, hand_id)) if not hand_id.is_empty() else "Tay trống"
	left_vbox.add_child(_mk_label("🍽 Đang cầm: " + hand_txt, 14, Color("#7bed9f") if not hand_id.is_empty() else Color("#b8cad6")))

	# Compact stock summary
	var stats := _summarize_items(s.get("stock", {}))
	var parts := []
	for k in stats.keys():
		var st: Dictionary = stats[k]
		if int(st["count"]) > 0:
			parts.append("%s ×%d%s" % [KIND_VI.get(k, k), int(st["count"]), _fresh_suffix(st)])
	var stock_lbl := _mk_label("📦 Kho: " + (" · ".join(parts) if parts.size() > 0 else "Trống"), 13, Color("#ffe394"))
	stock_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stock_lbl.custom_minimum_size = Vector2(210, 0)
	left_vbox.add_child(stock_lbl)

	# A customer only arrives when an eligible dish can be made from unreserved,
	# unspoiled ingredients. Explain this instead of leaving an empty restaurant.
	var available := _available_stock(s)
	var cookable := _cookable_dishes(s, available)
	if cookable.is_empty():
		var no_dish := _mk_label("Chưa có món cho khách mới: nguyên liệu thiếu, đã ươn hoặc đang giữ cho khách khác.", 13, Color("#ffcf6b"))
		no_dish.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		no_dish.custom_minimum_size = Vector2(210, 0)
		left_vbox.add_child(no_dish)
	else:
		var dishes := []
		for id in cookable:
			dishes.append(str(DISH_VI.get(id, id)))
		var menu_lbl := _mk_label("Có thể gọi: " + " · ".join(dishes), 13, Color("#b9eec9"))
		menu_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		menu_lbl.custom_minimum_size = Vector2(210, 0)
		left_vbox.add_child(menu_lbl)
	var free_parts := []
	for kind in available:
		if int(available[kind]) > 0:
			free_parts.append("%s ×%d" % [KIND_VI.get(kind, kind), int(available[kind])])
	var free_lbl := _mk_label("Kho khả dụng: " + (" · ".join(free_parts) if not free_parts.is_empty() else "Trống"), 13, Color("#cfe4f0"))
	free_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	free_lbl.custom_minimum_size = Vector2(210, 0)
	left_vbox.add_child(free_lbl)

	# Stoves row
	var stove_row := HBoxContainer.new()
	stove_row.add_theme_constant_override("separation", 8)
	for st in s.get("stoves", []):
		var sid := str(st.get("id", "B1"))
		var st_state := str(st.get("state", "idle"))
		var st_col := Color("#7bed9f") if st_state == "ready" else (Color("#ffa502") if st_state == "cooking" else Color("#9aaeb8"))
		stove_row.add_child(_mk_label("🔥 %s: %s" % [sid, STOVE_VI.get(st_state, st_state)], 13, st_col))
	left_vbox.add_child(stove_row)

	# Compact customers with slim 6px patience bars
	var customers: Array = s.get("customers", [])
	if customers.is_empty():
		left_vbox.add_child(_mk_label("Chờ khách đến..." if not cookable.is_empty() else "Chưa có khách ngồi bàn.", 13, Color("#9aaeb8")))
	else:
		var patience_max := float(s.get("meta", {}).get("patience_s", 60)) * 60.0
		for c in customers:
			var tid := str(c.get("table_id", ""))
			var did := str(c.get("dish_id", ""))
			var cstate := str(c.get("state", "waiting"))
			var ratio := float(c.get("patience_ticks_left", 0)) / maxf(1.0, patience_max)
			var is_angry: bool = ratio < _al("patience_low_ratio", 0.25) and cstate == "waiting"
			if is_angry:
				active_alert_angry = true
			var bar_col := Color("#2ed573") if ratio >= 0.5 else (Color("#ffa502") if ratio >= _al("patience_low_ratio", 0.25) else Color("#ff4757"))
			if cstate == "eating":
				bar_col = Color("#70a1ff")
			var line := "%s · %s" % [tid, str(DISH_VI.get(did, did))]
			if is_angry:
				line = "⚠ " + line
			left_vbox.add_child(_mk_label(line, 13, Color("#ff6b6b") if is_angry else Color("#f5f7fa")))
			left_vbox.add_child(_mk_progress_bar(ratio, bar_col, 6, 210))

	if active_alert_angry:
		alerts.append("⚠ KHÁCH SẮP GIẬN!")


func _available_stock(s: Dictionary) -> Dictionary:
	var raw = s.get("stock", [])
	var available := {}
	var held_ids := {}
	for customer in s.get("customers", []):
		var reserved = customer.get("reserved", [])
		if typeof(reserved) == TYPE_ARRAY:
			for id in reserved:
				held_ids[str(id)] = true
	if typeof(raw) == TYPE_ARRAY:
		var threshold := float(s.get("meta", {}).get("spoiled_below", 30))
		for item in raw:
			if typeof(item) != TYPE_DICTIONARY or held_ids.has(str(item.get("id", ""))) or float(item.get("fresh", 100)) < threshold:
				continue
			var kind := str(item.get("kind", ""))
			available[kind] = int(available.get(kind, 0)) + 1
	elif typeof(raw) == TYPE_DICTIONARY:
		available = raw.duplicate()
		for customer in s.get("customers", []):
			var reserved = customer.get("reserved", {})
			if typeof(reserved) == TYPE_DICTIONARY:
				for kind in reserved:
					available[kind] = int(available.get(kind, 0)) - int(reserved[kind])
	return available


func _cookable_dishes(s: Dictionary, available: Dictionary) -> Array:
	var menu: Dictionary = s.get("meta", {}).get("menu", {})
	var planned: Dictionary = s.get("day_plan", {}).get("dishes", {})
	var result := []
	for id in menu:
		if s.has("day_plan") and not planned.has(id):
			continue
		var recipe: Dictionary = menu[id].get("recipe", {})
		var enough := not recipe.is_empty()
		for kind in recipe:
			if int(available.get(kind, 0)) < int(recipe[kind]):
				enough = false
				break
		if enough:
			result.append(id)
	result.sort()
	return result


func _summarize_items(raw_items) -> Dictionary:
	var stats := {}
	if typeof(raw_items) == TYPE_DICTIONARY:
		for k in raw_items.keys():
			stats[str(k)] = {"count": int(round(float(raw_items[k]))), "spoiled": 0, "min_fresh": -1.0}
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
		return " [⚠ %d ươn]" % sp
	return " [%d%%]" % int(round(float(st["min_fresh"])))
