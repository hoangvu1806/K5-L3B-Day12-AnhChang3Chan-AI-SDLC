extends Node
## Tín hiệu ngắn được tạo trong Godot. Phụ đề do HUD hiển thị độc lập.

var muted := false
var players: Dictionary = {}

func _ready() -> void:
	var tones := {"monster": [170.0, 120.0], "oxygen": [430.0, 330.0],
		"customer": [370.0, 290.0], "current": [220.0, 330.0]}
	for key in tones:
		var player := AudioStreamPlayer.new()
		player.stream = _tone(tones[key])
		add_child(player)
		players[key] = player

func cue(key: String) -> void:
	if not muted:
		players[key].play()

func toggle_mute() -> void:
	muted = not muted
	if muted:
		for player in players.values():
			player.stop()

func _tone(frequencies: Array) -> AudioStreamWAV:
	var rate := 22050
	var note_length := 0.15
	var samples := int(rate * note_length)
	var pcm := PackedByteArray()
	pcm.resize(samples * frequencies.size() * 2)
	for note in range(frequencies.size()):
		for i in range(samples):
			var t := float(i) / rate
			var envelope := minf(t / 0.025, (note_length - t) / 0.05)
			var wave := sin(TAU * float(frequencies[note]) * t) * clampf(envelope, 0.0, 1.0)
			pcm.encode_s16((note * samples + i) * 2, int(wave * 4500.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.data = pcm
	return stream
