extends Node3D
## Phase 4 Benchmark runner (bench_cmd):
##   bench_cmd --seed 42 --duration 30 --out bench.json
## Loads res://scenes/DiveUnderwater.tscn at 1280x720 with Ut Sen stationed at dock [2, 0],
## warms up for 3.0s, measures for --duration seconds, and writes JSON:
##   { avg_fps, p1_low_fps, frames, measured_s, load_ms }

const WARMUP_S := 3.0

var seed_val: int = 42
var duration_s: float = 30.0
var out_path: String = "bench.json"

var t_init_ms: int = 0
var load_ms: int = 0
var scene_ready_usec := 0
var sample_start_usec := 0
var last_frame_usec := 0
var measured_s: float = 0.0
var frames: int = 0
var frame_dts: Array[float] = []
var finished: bool = false
var status_label: Label


func _init() -> void:
	t_init_ms = Time.get_ticks_msec()


func _ready() -> void:
	_parse_args()
	DisplayServer.window_set_size(Vector2i(1280, 720))

	var scene_res := load("res://scenes/DiveUnderwater.tscn")
	if scene_res == null:
		push_error("Bench: failed to load res://scenes/DiveUnderwater.tscn")
		get_tree().quit(1)
		return

	var world: Node3D = scene_res.instantiate()
	world.set("diver_pos", Vector2(2.0, 0.0))
	world.set("scene_seed", seed_val)
	add_child(world)
	# Út Sen tự đứng yên ở bến [2, 0] khi không có phím; KHÔNG tắt _physics_process của cảnh lặn
	# vì nó còn chạy đàn cá, tia nắng, bọt khí và hoạt ảnh bơi -> tắt đi sẽ đo FPS trên cảnh đóng băng.
	if world.get("diver_root") is Node3D:
		world.diver_root.position = Vector3(2.0, 0.0, 0.0)
	if world.get("cam") is Camera3D:
		world.cam.position = Vector3(10.0, 1.2, 22.0)
		world.cam.look_at(Vector3(10.0, -2.0, -3.0), Vector3.UP)

	var canvas := CanvasLayer.new()
	canvas.layer = 20
	add_child(canvas)
	status_label = Label.new()
	status_label.position = Vector2(20, 68)
	status_label.add_theme_font_size_override("font_size", 20)
	status_label.add_theme_color_override("font_color", Color("#ffe97d"))
	status_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	status_label.add_theme_constant_override("outline_size", 6)
	canvas.add_child(status_label)

	load_ms = Time.get_ticks_msec() - t_init_ms
	scene_ready_usec = Time.get_ticks_usec()


func _parse_args() -> void:
	var args := OS.get_cmdline_user_args()
	var i := 0
	while i < args.size():
		var a := args[i]
		if a == "--seed" and i + 1 < args.size():
			seed_val = int(args[i + 1])
			i += 2
		elif a == "--duration" and i + 1 < args.size():
			duration_s = maxf(0.5, float(args[i + 1]))
			i += 2
		elif a == "--out" and i + 1 < args.size():
			out_path = args[i + 1]
			i += 2
		else:
			i += 1


func _process(_delta: float) -> void:
	if finished:
		return
	var now := Time.get_ticks_usec()
	if sample_start_usec == 0:
		var warmup_elapsed := float(now - scene_ready_usec) / 1000000.0
		if warmup_elapsed >= WARMUP_S:
			sample_start_usec = now
			last_frame_usec = now
		status_label.text = "BENCH WARMUP: %.1f / %.1f s (1280x720, seed=%d)" % [warmup_elapsed, WARMUP_S, seed_val]
		return

	measured_s = float(now - sample_start_usec) / 1000000.0
	frames += 1
	frame_dts.append(float(now - last_frame_usec) / 1000000.0)
	last_frame_usec = now
	status_label.text = "BENCH MEASURING: %.1f / %.1f s | frames=%d | fps=%.1f" % [
		measured_s, duration_s, frames, float(frames) / maxf(0.001, measured_s)]

	if measured_s >= duration_s:
		finished = true
		_write_report_and_quit()


func _write_report_and_quit() -> void:
	var avg_fps := float(frames) / maxf(0.001, measured_s)
	var sorted_dts := frame_dts.duplicate()
	sorted_dts.sort()
	var tail_count := maxi(1, int(ceil(float(sorted_dts.size()) * 0.01)))
	var sum_slow := 0.0
	for k in range(sorted_dts.size() - tail_count, sorted_dts.size()):
		sum_slow += sorted_dts[k]
	var mean_slow_dt := sum_slow / float(tail_count)
	var p1_low_fps := 1.0 / maxf(0.0001, mean_slow_dt)

	var report := {
		"avg_fps": snapped(avg_fps, 0.01),
		"p1_low_fps": snapped(p1_low_fps, 0.01),
		"frames": frames,
		"measured_s": snapped(measured_s, 0.001),
		"load_ms": load_ms,
	}

	var dir_path := out_path.get_base_dir()
	if not dir_path.is_empty():
		DirAccess.make_dir_recursive_absolute(dir_path)
	var tmp_path := out_path + ".tmp"
	var f := FileAccess.open(tmp_path, FileAccess.WRITE)
	if f == null:
		push_error("Bench: cannot write output file: " + tmp_path)
		get_tree().quit(1)
		return
	f.store_string(JSON.stringify(report, "  ") + "\n")
	f.close()
	if DirAccess.rename_absolute(tmp_path, out_path) != OK:
		push_error("Bench: cannot replace output file: " + out_path)
		get_tree().quit(1)
		return
	print("BENCH_OK ", JSON.stringify(report))
	get_tree().quit(0)
