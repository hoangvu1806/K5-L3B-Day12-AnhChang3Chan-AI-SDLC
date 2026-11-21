extends Node3D
# ART / asset check only; does not implement Test Contract gather physics.
const GOLD := Color("#ad945a")
var angle := 0.60
var pitch := 0.26
var radius := 24.0
var target := Vector3(0,-12,0)
var camera: Camera3D
var orbit := false

func block(p:Vector3,s:Vector3,c:Color)->void:
    var n=MeshInstance3D.new()
    var m=BoxMesh.new(); m.size=s;n.mesh=m;n.position=p
    var mat=StandardMaterial3D.new();mat.albedo_color=c;mat.roughness=0.96
    n.material_override=mat;add_child(n)

func _ready():
    var world=WorldEnvironment.new();var env=Environment.new()
    env.background_mode=Environment.BG_COLOR;env.background_color=Color("#1c5149")
    env.fog_enabled=true;env.fog_light_color=Color("#4c9488");env.fog_density=0.045
    env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color=Color("#84c6a7")
    env.ambient_light_energy=0.65;world.environment=env;add_child(world)
    var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-45,-25,0)
    sun.light_color=Color("#d6efcb");sun.light_energy=1.0;add_child(sun)
    var bottom=MeshInstance3D.new(); var ground=PlaneMesh.new();ground.size=Vector2(64,100)
    bottom.mesh=ground;bottom.position.y=-30
    var mud=StandardMaterial3D.new();mud.albedo_color=GOLD;mud.roughness=1
    bottom.material_override=mud;add_child(bottom)
    # Depth markers 0-30m and river bank geometry, actual 3D volume, not a 2D image
    for i in range(7):
        var d=float(i)*5.0
        block(Vector3(-21,-d,-5),Vector3(0.15,.08,2.0),Color("#f5d79c"))
    for i in range(32):
        var x=-17.0+float(i%8)*4.7
        var z=-22.0+float(i/8)*10.0
        var mudpile=MeshInstance3D.new();var cyl=CylinderMesh.new();cyl.top_radius=.45;cyl.bottom_radius=.85;cyl.height=.45
        mudpile.mesh=cyl;mudpile.position=Vector3(x,-29.75,z)
        var grass=StandardMaterial3D.new();grass.albedo_color=Color("#507c55");mudpile.material_override=grass;add_child(mudpile)
    for fish_id in ['fish_ca_loc','fish_ca_linh']:
        var p='res://assets/legacy/'+fish_id+'.glb'
        if ResourceLoader.exists(p):
            var scene=load(p)
            if scene is PackedScene:
                for i in range(3):
                    var n=scene.instantiate();n.position=Vector3(-10+i*6,-5-i*5,-3+i*5)
                    n.scale=Vector3.ONE*1.25;add_child(n)
    camera=Camera3D.new();camera.fov=57;camera.near=.05;camera.far=160;camera.current=true;add_child(camera)
    update_cam()
    var canvas=CanvasLayer.new();add_child(canvas)
    var label=Label.new();label.position=Vector2(16,14)
    label.text='LONG SONG 3D | ART PREVIEW | F1: SANG | F2: QUAN | F3: DUOI NUOC | RIGHT MOUSE/SCROLL: CAMERA'
    label.add_theme_color_override('font_color',Color.WHITE)
    canvas.add_child(label)

func update_cam():
    camera.position=target + Vector3(radius*cos(pitch)*sin(angle),radius*sin(pitch),radius*cos(pitch)*cos(angle))
    camera.look_at(target)

func _unhandled_input(event):
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode==KEY_F1:get_tree().change_scene_to_file('res://scenes/GatherRiver.tscn')
        elif event.keycode==KEY_F2:get_tree().change_scene_to_file('res://scenes/RestaurantNight.tscn')
        elif event.keycode==KEY_F3:get_tree().change_scene_to_file('res://scenes/UnderwaterRiver.tscn')
    elif event is InputEventMouseButton:
        if event.button_index==MOUSE_BUTTON_RIGHT:orbit=event.pressed
        elif event.pressed and event.button_index==MOUSE_BUTTON_WHEEL_UP:radius=max(5.0,radius*.88);update_cam()
        elif event.pressed and event.button_index==MOUSE_BUTTON_WHEEL_DOWN:radius=min(65.0,radius*1.12);update_cam()
    elif event is InputEventMouseMotion and orbit:
        angle-=event.relative.x*.008
        pitch=clampf(pitch+event.relative.y*.004,-.8,1.3);update_cam()
