extends Node3D
## 2.5D Side-View Underwater Diving Showcase (Dave the Diver style, Mekong River theme).
## Matches PRD-0 gather coordinates: x in [0, 100], depth d in [0, 30] -> Godot (x, -d, 0).
## Visual-only showcase; does not affect headless Test Contract simulation.

var cam: Camera3D
var env: Environment
var diver_root: Node3D
var diver_visual: Node3D
var diver_skeleton: Skeleton3D
var bone_map: Dictionary = {}
var bone_rest_rot: Dictionary = {}
var hud_label: Label

var diver_pos := Vector2(18.0, 6.0) # [x, d]
var diver_vel := Vector2.ZERO
var facing_right := true
var cam_distance := 22.0
var time_acc := 0.0

var rng := RandomNumberGenerator.new()
var fish_nodes: Array = []
var ray_nodes: Array = []
var bubble_nodes: Array = []
var loaded_models := 0

const SHALLOW_FOG := Color("#6c8e58")
const DEEP_FOG := Color("#1e3120")
const SHALLOW_BG := Color("#648652")
const DEEP_BG := Color("#162618")

const PRD_NODES := [
	{"id": "N1", "kind": "bong_dien_dien", "pos": Vector2(12.0, 0.0)},
	{"id": "N2", "kind": "bong_dien_dien", "pos": Vector2(28.0, 0.0)},
	{"id": "N3", "kind": "bong_sung", "pos": Vector2(44.0, 0.0)},
	{"id": "N4", "kind": "bong_sung", "pos": Vector2(60.0, 0.0)},
	{"id": "N5", "kind": "keo_neo", "pos": Vector2(76.0, 0.0)},
	{"id": "N6", "kind": "keo_neo", "pos": Vector2(90.0, 0.0)},
]

const PRD_FISH := [
	{"id": "F1", "kind": "ca_linh", "pos": Vector2(15.0, 5.0)},
	{"id": "F2", "kind": "ca_loc", "pos": Vector2(30.0, 10.0)},
	{"id": "F3", "kind": "ca_linh", "pos": Vector2(45.0, 10.0)},
	{"id": "F4", "kind": "ca_loc", "pos": Vector2(60.0, 16.0)},
	{"id": "F5", "kind": "ca_linh", "pos": Vector2(75.0, 5.0)},
	{"id": "F6", "kind": "ca_loc", "pos": Vector2(90.0, 16.0)},
	{"id": "F7", "kind": "ca_keo", "pos": Vector2(35.0, 24.0)},
	{"id": "F8", "kind": "ca_keo", "pos": Vector2(72.0, 26.0)},
	{"id": "H1", "kind": "ca_ho", "pos": Vector2(52.0, 18.0)},
]


func _ready() -> void:
	rng.seed = 20261121
	_setup_environment()
	_build_water_surface_and_shore()
	_build_underwater_cliffs_and_seabed()
	_build_light_shafts_and_bubbles()
	_build_prd_nodes_and_fish()
	_build_diver()
	_setup_camera_and_hud()
	print("Dive Underwater 2.5D / imported models placed=", loaded_models)


func _asset(family: String, asset_id: String, at: Vector3, scale_v: Vector3 = Vector3.ONE, rot_deg: Vector3 = Vector3.ZERO, parent: Node3D = self) -> Node3D:
	var path := "res://assets/external/%s/%s.glb" % [family, asset_id]
	if not ResourceLoader.exists(path):
		var gltf_path := "res://assets/external/%s/%s.gltf" % [family, asset_id]
		if ResourceLoader.exists(gltf_path):
			path = gltf_path
		else:
			return null
	var packed = load(path)
	if not (packed is PackedScene):
		return null
	var inst: Node3D = packed.instantiate()
	inst.name = asset_id
	inst.position = at
	inst.rotation_degrees = rot_deg
	inst.scale = scale_v
	parent.add_child(inst)
	loaded_models += 1
	return inst


func _setup_environment() -> void:
	var world := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = SHALLOW_BG
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#98b074")
	env.ambient_light_energy = 0.52
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = SHALLOW_FOG
	env.fog_light_energy = 0.85
	env.fog_density = 0.024
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.name = "UnderwaterSun"
	sun.rotation_degrees = Vector3(-66.0, -25.0, 0.0)
	sun.light_color = Color("#ffdca0")
	sun.light_energy = 0.85
	sun.shadow_enabled = true
	add_child(sun)

	var rim := DirectionalLight3D.new()
	rim.name = "DepthFillLight"
	rim.rotation_degrees = Vector3(25.0, 145.0, 0.0)
	rim.light_color = Color("#5b7844")
	rim.light_energy = 0.30
	add_child(rim)


func _build_water_surface_and_shore() -> void:
	# Shimmering water surface plane at y = 0 (visible from both above and below)
	var water := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(140.0, 44.0)
	pm.subdivide_width = 120
	pm.subdivide_depth = 24
	water.mesh = pm
	water.position = Vector3(50.0, 0.0, -14.0)
	var water_mat := ShaderMaterial.new()
	water_mat.shader = load("res://shaders/mekong_water.gdshader")
	water.material_override = water_mat
	add_child(water)

	# Underside warm sunlit alluvial water sheen
	var under_surface := MeshInstance3D.new()
	var upm := PlaneMesh.new()
	upm.size = Vector2(140.0, 44.0)
	under_surface.mesh = upm
	under_surface.position = Vector3(50.0, -0.08, -14.0)
	under_surface.rotation_degrees = Vector3(180.0, 0.0, 0.0)
	var us_mat := StandardMaterial3D.new()
	us_mat.albedo_color = Color(0.86, 0.80, 0.46, 0.36)
	us_mat.emission_enabled = true
	us_mat.emission = Color(0.76, 0.72, 0.38)
	us_mat.emission_energy_multiplier = 0.55
	us_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	us_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	under_surface.material_override = us_mat
	add_child(under_surface)

	# Floating dock at dock_pos = [2, 0] + sampan boat
	_asset("river_delta", "floating_docks", Vector3(2.0, 0.15, -1.5), Vector3.ONE * 1.15, Vector3(0.0, 90.0, 0.0))
	_asset("river_delta", "sampans", Vector3(5.8, 0.12, -2.0), Vector3.ONE * 0.85, Vector3(0.0, 12.0, 0.0))

	# Above-water Mekong background silhouettes along the far bank (z = -12..-18)
	for i in range(10):
		var bx := -5.0 + i * 12.5
		_asset("tropical", "coconut_tall" if i % 2 == 0 else "coconut_lean", Vector3(bx, 0.4, -14.0), Vector3.ONE * rng.randf_range(1.2, 1.7), Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))
		if i % 3 == 0:
			_asset("river_delta", "stilt_houses", Vector3(bx + 4.0, 0.2, -16.5), Vector3.ONE * 1.1, Vector3(0.0, 0.0, 0.0))
		else:
			_asset("tropical", "nipa_palm", Vector3(bx + 5.5, 0.1, -11.5), Vector3.ONE * 1.3, Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))


func _build_underwater_cliffs_and_seabed() -> void:
	# Warm muddy alluvial riverbed floor at d = 30m (y = -30.5)
	var floor_mesh := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(145.0, 2.0, 50.0)
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color("#4a3a26")
	fmat.roughness = 0.96
	bm.material = fmat
	floor_mesh.mesh = bm
	floor_mesh.position = Vector3(50.0, -31.0, -14.0)
	add_child(floor_mesh)

	# Sloping muddy riverbank clay wall in the background (warm Mekong earth tones, NO ice cliffs!)
	var mud_wall := MeshInstance3D.new()
	var wbm := BoxMesh.new()
	wbm.size = Vector3(145.0, 32.0, 4.0)
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color("#4f4029")
	wmat.roughness = 0.95
	wbm.material = wmat
	mud_wall.mesh = wbm
	mud_wall.position = Vector3(50.0, -15.5, -24.0)
	mud_wall.rotation_degrees = Vector3(-12.0, 0.0, 0.0)
	add_child(mud_wall)

	# Wooden stilt-house pilings descending cleanly in the far background (z = -12..-18)
	var piling_mat := StandardMaterial3D.new()
	piling_mat.albedo_color = Color("#4a321d")
	piling_mat.roughness = 0.92
	for i in range(14):
		var px := 0.0 + i * 7.8 + rng.randf_range(-0.6, 0.6)
		var pz := rng.randf_range(-17.5, -12.0)
		var pile := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.18
		cm.bottom_radius = 0.24
		cm.height = 24.0
		cm.radial_segments = 8
		cm.material = piling_mat
		pile.mesh = cm
		pile.position = Vector3(px, -10.5, pz)
		pile.rotation_degrees = Vector3(rng.randf_range(-2.0, 2.0), 0.0, rng.randf_range(-2.0, 2.0))
		add_child(pile)

	# Mossy river-bank terraces & boulders anchored at the seabed (no mid-water floating rocks)
	for i in range(16):
		var rx := -4.0 + i * 6.8 + rng.randf_range(-1.2, 1.2)
		var ry := rng.randf_range(-29.8, -26.2)
		var rz := rng.randf_range(-17.0, -8.5)
		var rs := rng.randf_range(2.2, 4.0)
		var rock_id := "boulder_mossy" if i % 2 == 0 else "cliff_block"
		_asset("underwater", rock_id, Vector3(rx, ry, rz), Vector3(rs, rs * rng.randf_range(0.6, 0.95), rs), Vector3(rng.randf_range(-6.0, 6.0), rng.randf_range(-180.0, 180.0), rng.randf_range(-6.0, 6.0)))

	# Seabed flora (kelp forests, seaweed rocks, sunken driftwood & roots at y = -30)
	for i in range(24):
		var kx := -2.0 + i * 4.5 + rng.randf_range(-1.2, 1.2)
		var kz := rng.randf_range(-11.0, -2.5)
		var pick := i % 5
		if pick == 0:
			_asset("underwater", "kelp_forest", Vector3(kx, -30.0, kz), Vector3.ONE * rng.randf_range(1.6, 2.6), Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))
		elif pick == 1:
			_asset("underwater", "kelp_cluster", Vector3(kx, -30.0, kz), Vector3.ONE * rng.randf_range(1.8, 3.0), Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))
		elif pick == 2:
			_asset("underwater", "seaweed_rock", Vector3(kx, -29.8, kz), Vector3.ONE * rng.randf_range(1.4, 2.2), Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))
		elif pick == 3:
			_asset("underwater", "driftwood_rootball", Vector3(kx, -29.6, kz), Vector3.ONE * rng.randf_range(1.3, 2.1), Vector3(rng.randf_range(-10.0, 10.0), rng.randf_range(-180.0, 180.0), 0.0))
		else:
			_asset("underwater", "driftwood_log", Vector3(kx, -29.7, kz), Vector3.ONE * rng.randf_range(1.5, 2.4), Vector3(0.0, rng.randf_range(-180.0, 180.0), rng.randf_range(-12.0, 12.0)))

	# Subtle foreground framing rocks (z = +4.5..+6.5) at seabed for parallax depth
	for i in range(6):
		var fx := 8.0 + i * 18.0
		_asset("underwater", "boulder_mossy", Vector3(fx, -29.5, 5.2), Vector3.ONE * rng.randf_range(1.5, 2.3), Vector3(0.0, rng.randf_range(-180.0, 180.0), 0.0))
		_asset("underwater", "kelp_cluster", Vector3(fx + 2.5, -30.0, 4.8), Vector3.ONE * 1.4, Vector3(0.0, 0.0, 0.0))


func _build_light_shafts_and_bubbles() -> void:
	# Soft angled sunlight shafts spanning cleanly from surface to seabed
	for i in range(9):
		var ray := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(rng.randf_range(4.0, 7.0), 34.0)
		ray.mesh = qm
		var rmat := StandardMaterial3D.new()
		rmat.albedo_color = Color(1.0, 0.90, 0.56, 0.055)
		rmat.emission_enabled = true
		rmat.emission = Color(0.95, 0.84, 0.48)
		rmat.emission_energy_multiplier = 0.45
		rmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		rmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		rmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		rmat.cull_mode = BaseMaterial3D.CULL_DISABLED
		rmat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		ray.material_override = rmat
		ray.position = Vector3(6.0 + i * 11.5, -15.5, rng.randf_range(-9.0, -4.0))
		ray.rotation_degrees = Vector3(0.0, 0.0, -14.0)
		add_child(ray)
		ray_nodes.append({"node": ray, "phase": rng.randf_range(0.0, TAU), "base_x": ray.position.x})

	# Floating ambient bubbles / plankton particles
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.85, 0.98, 1.0, 0.72)
	bmat.emission_enabled = true
	bmat.emission = Color(0.75, 0.95, 1.0)
	bmat.emission_energy_multiplier = 0.6
	bmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	bmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

	for i in range(55):
		var b := MeshInstance3D.new()
		var sm := SphereMesh.new()
		var rad := rng.randf_range(0.05, 0.14)
		sm.radius = rad
		sm.height = rad * 2.0
		b.mesh = sm
		b.material_override = bmat
		b.position = Vector3(rng.randf_range(0.0, 100.0), rng.randf_range(-29.0, -0.5), rng.randf_range(-6.0, 2.5))
		add_child(b)
		bubble_nodes.append({"node": b, "speed": rng.randf_range(0.5, 1.5), "phase": rng.randf_range(0.0, TAU)})


func _play_loop_anim(node: Node3D, preferred: String) -> void:
	var ap := node.find_child("AnimationPlayer", true, false)
	if ap is AnimationPlayer:
		var player: AnimationPlayer = ap
		for aname in player.get_animation_list():
			var a: Animation = player.get_animation(aname)
			if a != null:
				a.loop_mode = Animation.LOOP_LINEAR
		if player.has_animation(preferred):
			player.play(preferred)
		elif player.get_animation_list().size() > 0:
			player.play(player.get_animation_list()[0])


func _build_prd_nodes_and_fish() -> void:
	# 6 PRD Phase 2 surface harvest nodes (N1-N2 bong_dien_dien, N3-N4 bong_sung, N5-N6 keo_neo)
	for n in PRD_NODES:
		var p: Vector2 = n["pos"]
		if n["kind"] == "bong_dien_dien":
			_asset("aquatic", "flower_yellow", Vector3(p.x, 0.05, 0.0), Vector3.ONE * 1.6, Vector3(0.0, 20.0, 0.0))
			_asset("aquatic", "lily_pads_swamp", Vector3(p.x, 0.02, -0.4), Vector3.ONE * 1.1, Vector3(0.0, 0.0, 0.0))
		elif n["kind"] == "bong_sung":
			_asset("aquatic", "lily_pads_blossom", Vector3(p.x, 0.04, 0.0), Vector3.ONE * 1.5, Vector3(0.0, 0.0, 0.0))
			_asset("aquatic", "lotus_clump", Vector3(p.x + 0.6, 0.04, -0.5), Vector3.ONE * 1.2, Vector3(0.0, 45.0, 0.0))
		else:
			_asset("aquatic", "keo_neo", Vector3(p.x, -0.05, 0.0), Vector3.ONE * 1.6, Vector3(0.0, 15.0, 0.0))

	# PRD Phase 2 fish schools (ca_linh, ca_loc, ca_keo, ca_ho)
	for f in PRD_FISH:
		var p: Vector2 = f["pos"]
		var kind: String = f["kind"]
		var count := 1 if kind == "ca_ho" else (2 if kind in ["ca_loc", "ca_keo"] else 4)
		for k in range(count):
			var offset := Vector3.ZERO if kind == "ca_ho" else Vector3(rng.randf_range(-1.4, 1.4), rng.randf_range(-0.7, 0.7), rng.randf_range(-1.2, 0.8))
			var base_pos := Vector3(p.x, -p.y, 0.0) + offset
			var f_id := "fish_perch"
			var sc := rng.randf_range(0.85, 1.1)
			if kind == "ca_loc":
				f_id = "fish_carp"
				sc = rng.randf_range(1.15, 1.45)
			elif kind == "ca_keo":
				f_id = "fish_ca_keo"
				sc = rng.randf_range(0.24, 0.30)
			elif kind == "ca_ho":
				f_id = "ca_ho"
				sc = 0.52
			var inst := _asset("aquatic", f_id, base_pos, Vector3.ONE * sc, Vector3(0.0, 90.0 if k % 2 == 0 else -90.0, 0.0))
			if inst != null:
				if kind in ["ca_keo", "ca_ho"]:
					_play_loop_anim(inst, "Swimming_Normal")
				fish_nodes.append({
					"node": inst,
					"origin": base_pos,
					"phase": rng.randf_range(0.0, TAU),
					"amp": rng.randf_range(0.7, 1.8) if kind != "ca_ho" else 3.0,
					"speed": rng.randf_range(1.0, 1.6) if kind != "ca_ho" else 0.7,
				})

	# Phase 2 Monsters: Ca Sau Nam Cheo (M1 [60,24]..[64,24]) & Ran Ho May (M3 [72,14]..[76,14])
	var croc := _asset("monsters", "ca_sau", Vector3(62.0, -24.0, 0.0), Vector3.ONE * 1.4, Vector3(0.0, 90.0, 0.0))
	if croc != null:
		fish_nodes.append({"node": croc, "origin": Vector3(62.0, -24.0, 0.0), "phase": 0.0, "amp": 2.5, "speed": 0.55})
	var snake := _asset("monsters", "ran_ho_may", Vector3(74.0, -14.0, 0.0), Vector3.ONE * 1.5, Vector3(0.0, 90.0, 0.0))
	if snake != null:
		fish_nodes.append({"node": snake, "origin": Vector3(74.0, -14.0, 0.0), "phase": 1.2, "amp": 2.5, "speed": 0.85})


func _make_mat(hex: String, rough := 0.72) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(hex)
	m.roughness = rough
	return m


func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := _find_skeleton(child)
		if found != null:
			return found
	return null


func _cache_swim_bones(skel: Skeleton3D) -> void:
	skel.reset_bone_poses()
	for i in range(skel.get_bone_count()):
		var bname := skel.get_bone_name(i).to_lower()
		var is_left := bname.contains("left") or bname.ends_with(".l") or bname.ends_with("_l")
		var is_right := bname.contains("right") or bname.ends_with(".r") or bname.ends_with("_r")
		if bname.contains("head"):
			bone_map["head"] = i
		elif bname.contains("spine") and not bone_map.has("spine"):
			bone_map["spine"] = i
		elif (bname.contains("upperarm") or bname.contains("shoulder_arm") or (bname.contains("arm") and not bname.contains("fore") and not bname.contains("lower"))):
			if is_left and not bone_map.has("uarm_l"):
				bone_map["uarm_l"] = i
			elif is_right and not bone_map.has("uarm_r"):
				bone_map["uarm_r"] = i
		elif bname.contains("lowerarm") or bname.contains("forearm"):
			if is_left and not bone_map.has("larm_l"):
				bone_map["larm_l"] = i
			elif is_right and not bone_map.has("larm_r"):
				bone_map["larm_r"] = i
		elif bname.contains("upperleg") or bname.contains("thigh"):
			if is_left and not bone_map.has("uleg_l"):
				bone_map["uleg_l"] = i
			elif is_right and not bone_map.has("uleg_r"):
				bone_map["uleg_r"] = i
		elif bname.contains("lowerleg") or bname.contains("shin") or bname.contains("calf"):
			if is_left and not bone_map.has("lleg_l"):
				bone_map["lleg_l"] = i
			elif is_right and not bone_map.has("lleg_r"):
				bone_map["lleg_r"] = i
	for key in bone_map.keys():
		var idx: int = bone_map[key]
		bone_rest_rot[key] = skel.get_bone_pose_rotation(idx)


func _set_bone_euler(key: String, deg: Vector3) -> void:
	if not bone_map.has(key) or not is_instance_valid(diver_skeleton):
		return
	var idx: int = bone_map[key]
	var base_q: Quaternion = bone_rest_rot[key]
	var delta_q := Quaternion.from_euler(Vector3(deg_to_rad(deg.x), deg_to_rad(deg.y), deg_to_rad(deg.z)))
	diver_skeleton.set_bone_pose_rotation(idx, base_q * delta_q)


func _build_diver() -> void:
	diver_root = Node3D.new()
	diver_root.name = "DiverUtSen"
	diver_root.position = Vector3(diver_pos.x, -diver_pos.y, 0.0)
	add_child(diver_root)

	# Petite 3D young girl Ut Sen (Quaternius CC0) with procedural skeletal swimming animation
	diver_visual = Node3D.new()
	diver_root.add_child(diver_visual)

	var pose_pivot := Node3D.new()
	pose_pivot.rotation_degrees = Vector3(0.0, 90.0, 0.0)
	diver_visual.add_child(pose_pivot)

	var girl := _asset("characters", "ut_sen_girl", Vector3(0.0, -0.15, -0.52), Vector3(0.28, 0.25, 0.28), Vector3(82.0, 0.0, 0.0), pose_pivot)
	if girl != null:
		var ap := girl.find_child("AnimationPlayer", true, false)
		if ap is AnimationPlayer:
			ap.stop()
		diver_skeleton = _find_skeleton(girl)
		if diver_skeleton != null:
			_cache_swim_bones(diver_skeleton)

	# Compact woven bamboo fish basket tucked neatly on her back
	var basket := MeshInstance3D.new()
	var bkm := CylinderMesh.new()
	bkm.top_radius = 0.11
	bkm.bottom_radius = 0.14
	bkm.height = 0.25
	bkm.material = _make_mat("#c9994a", 0.82)
	basket.mesh = bkm
	basket.position = Vector3(-0.04, 0.20, 0.0)
	basket.rotation_degrees = Vector3(0.0, 0.0, 82.0)
	diver_visual.add_child(basket)

	# Gentle warm dive-lamp light on diver
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("#ffe8b3")
	lamp.light_energy = 0.70
	lamp.omni_range = 7.5
	lamp.position = Vector3(0.6, 0.15, 1.0)
	diver_visual.add_child(lamp)


func _setup_camera_and_hud() -> void:
	cam = Camera3D.new()
	cam.name = "DiveCamera25D"
	cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	cam.fov = 52.0
	cam.near = 0.1
	cam.far = 220.0
	cam.position = Vector3(diver_pos.x, -diver_pos.y + 1.0, cam_distance)
	cam.current = true
	add_child(cam)

	var canvas := CanvasLayer.new()
	add_child(canvas)

	var bar := ColorRect.new()
	bar.color = Color(0.03, 0.14, 0.22, 0.72)
	bar.position = Vector2(14, 12)
	bar.size = Vector2(930, 44)
	canvas.add_child(bar)

	hud_label = Label.new()
	hud_label.position = Vector2(26, 22)
	hud_label.add_theme_font_size_override("font_size", 16)
	hud_label.add_theme_color_override("font_color", Color("#e6fbff"))
	hud_label.text = "LAN BAT CA 2.5D | WASD/Mui ten: Boi lan | Cuon: Zoom | F1: Song | F2: Quan toi | F3: Lan sau"
	canvas.add_child(hud_label)


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.keycode == KEY_F1:
			get_tree().change_scene_to_file("res://scenes/GatherRiver.tscn")
		elif ev.keycode == KEY_F2:
			get_tree().change_scene_to_file("res://scenes/RestaurantNight.tscn")
		elif ev.keycode == KEY_F3:
			get_tree().change_scene_to_file("res://scenes/DiveUnderwater.tscn")
	elif ev is InputEventMouseButton and ev.pressed:
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam_distance = maxf(11.0, cam_distance * 0.9)
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam_distance = minf(36.0, cam_distance * 1.1)


func _physics_process(delta: float) -> void:
	time_acc += delta

	# Read WASD + Arrow keys
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

	var move := Vector2(ix, iy)
	if move.length() > 1.0:
		move = move.normalized()

	var target_vel := move * 6.5
	diver_vel = diver_vel.lerp(target_vel, minf(1.0, delta * 8.0))
	diver_pos.x = clampf(diver_pos.x + diver_vel.x * delta, 0.0, 100.0)
	diver_pos.y = clampf(diver_pos.y + diver_vel.y * delta, 0.0, 29.0)

	if absf(diver_vel.x) > 0.2:
		facing_right = diver_vel.x > 0.0

	# Update diver transform & gentle swim bob
	var bob := sin(time_acc * 3.5) * 0.14
	diver_root.position = Vector3(diver_pos.x, -diver_pos.y + bob, 0.0)
	var target_yaw := 0.0 if facing_right else 180.0
	var target_tilt := clampf(-diver_vel.y * 5.0, -32.0, 32.0)
	diver_visual.rotation_degrees.y = lerpf(diver_visual.rotation_degrees.y, target_yaw, delta * 10.0)
	diver_visual.rotation_degrees.z = lerpf(diver_visual.rotation_degrees.z, target_tilt if facing_right else -target_tilt, delta * 8.0)

	# Real underwater breaststroke + flutter-kick skeletal swimming motion
	if is_instance_valid(diver_skeleton):
		var moving := diver_vel.length() > 0.5
		var freq := 6.5 if moving else 2.6
		var phase := time_acc * freq
		var kick_amp := 20.0 if moving else 9.0
		var stroke_amp := 38.0 if moving else 16.0
		var kick := sin(phase) * kick_amp
		var sweep := sin(phase * 0.65) * stroke_amp
		var reach := cos(phase * 0.65) * (stroke_amp * 0.55)
		# Head tilted slightly up to look forward along swim direction
		_set_bone_euler("head", Vector3(-34.0, 0.0, 0.0))
		# Gentle spine undulation
		_set_bone_euler("spine", Vector3(sin(phase) * 5.0, 0.0, 0.0))
		# Breaststroke arms: reaching forward and sweeping outward-back
		_set_bone_euler("uarm_l", Vector3(-115.0 + reach, 0.0, 32.0 + sweep))
		_set_bone_euler("uarm_r", Vector3(-115.0 + reach, 0.0, -32.0 - sweep))
		_set_bone_euler("larm_l", Vector3(-25.0 - absf(sweep) * 0.35, 0.0, 0.0))
		_set_bone_euler("larm_r", Vector3(-25.0 - absf(sweep) * 0.35, 0.0, 0.0))
		# Straight-ish flutter kick (not running knee bend!)
		_set_bone_euler("uleg_l", Vector3(kick, 0.0, 4.0))
		_set_bone_euler("uleg_r", Vector3(-kick, 0.0, -4.0))
		_set_bone_euler("lleg_l", Vector3(10.0 + maxf(0.0, kick * 0.45), 0.0, 0.0))
		_set_bone_euler("lleg_r", Vector3(10.0 + maxf(0.0, -kick * 0.45), 0.0, 0.0))

	# Smooth Dave-the-Diver depth fog color shift from sunlit shallow to deep abyss
	var depth_t := clampf(diver_pos.y / 28.0, 0.0, 1.0)
	env.fog_light_color = SHALLOW_FOG.lerp(DEEP_FOG, depth_t)
	env.background_color = SHALLOW_BG.lerp(DEEP_BG, depth_t)
	env.fog_density = lerpf(0.018, 0.032, depth_t)

	# Camera follows diver with gentle perspective look-ahead
	var cam_target := Vector3(clampf(diver_pos.x, 8.0, 92.0), clampf(-diver_pos.y + 1.2, -24.5, 3.0), cam_distance)
	cam.position = cam.position.lerp(cam_target, minf(1.0, delta * 5.0))
	cam.look_at(Vector3(clampf(diver_pos.x, 8.0, 92.0), clampf(-diver_pos.y, -26.0, 1.5), -3.0), Vector3.UP)

	# Animate fish schools
	for entry in fish_nodes:
		var fn: Node3D = entry["node"]
		var orig: Vector3 = entry["origin"]
		var ph: float = entry["phase"]
		var amp: float = entry["amp"]
		var sp: float = entry["speed"]
		var dx := sin(time_acc * sp + ph) * amp
		var dy := cos(time_acc * sp * 0.7 + ph) * 0.25
		fn.position = orig + Vector3(dx, dy, 0.0)
		fn.rotation.y = (PI * 0.5) if cos(time_acc * sp + ph) >= 0.0 else (-PI * 0.5)

	# Animate light shafts & rising bubbles
	for r in ray_nodes:
		var rn: MeshInstance3D = r["node"]
		rn.position.x = r["base_x"] + sin(time_acc * 0.6 + r["phase"]) * 0.8

	for b in bubble_nodes:
		var bn: MeshInstance3D = b["node"]
		bn.position.y += b["speed"] * delta
		bn.position.x += sin(time_acc * 2.0 + b["phase"]) * 0.15 * delta
		if bn.position.y > -0.2:
			bn.position.y = -29.2

	hud_label.text = "LAN BAT CA 2.5D | x=%.1fm  Do sau d=%.1fm | WASD/Mui ten: Boi | Cuon: Zoom | F1: Song | F2: Quan | F3: Lan" % [diver_pos.x, diver_pos.y]
