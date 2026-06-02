extends Node2D

var lion: CharacterBody2D
var camera: Camera2D
var world: Node2D
var current_steak: Area2D = null
var food_remaining: int = 0
var is_question_active: bool = false
var is_paused: bool = false
var sound_on: bool = true
var score: int = 0
var streak: int = 0

var canvas: CanvasLayer
var ui_score: Label
var ui_hint: Label
var ui_bg: ColorRect
var ui_panel: Panel
var ui_question: Label
var ui_input: LineEdit
var ui_submit: Button
var ui_feedback: Label
var ui_thankyou: Label
var ui_win: Label
var ui_restart_btn: Button
var ui_sound_btn: Button
var ui_pause_overlay: ColorRect
var ui_pause_panel: Panel
var ui_pause_title: Label
var ui_resume_btn: Button
var ui_pause_restart_btn: Button

var roar_player: AudioStreamPlayer
var music_player: AudioStreamPlayer
var correct_player: AudioStreamPlayer
var wrong_player: AudioStreamPlayer

func _ready():
	setup_input_map()
	build_world()
	spawn_lion()
	spawn_steaks(10)
	setup_ui()
	setup_audio()
	spawn_decorations()

func setup_input_map():
	for a in ["move_forward", "move_back", "move_left", "move_right", "restart"]:
		if not InputMap.has_action(a):
			InputMap.add_action(a)
	var key_map = {
		"move_forward": [KEY_W, KEY_UP],
		"move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
		"restart": [KEY_R],
	}
	for action in key_map:
		for key in key_map[action]:
			var ev = InputEventKey.new()
			ev.keycode = key
			InputMap.action_add_event(action, ev)

func build_world():
	world = Node2D.new()
	world.name = "World"
	add_child(world)
	var ground = ColorRect.new()
	ground.color = Color(0.22, 0.6, 0.12)
	ground.size = Vector2(1800, 1800)
	ground.position = Vector2(-900, -900)
	world.add_child(ground)

func spawn_decorations():
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	var tree_colors = [Color(0.08, 0.45, 0.08), Color(0.1, 0.5, 0.1), Color(0.12, 0.4, 0.06), Color(0.06, 0.5, 0.12)]
	var flower_colors = [Color(1, 0.2, 0.3), Color(1, 0.8, 0), Color(1, 0.4, 0.7), Color(0.8, 0.2, 1)]
	var trunk_c = Color(0.4, 0.2, 0.1)
	var rock_c = Color(0.5, 0.45, 0.4)

	for i in range(35):
		var x = rng.randf_range(-800, 800)
		var z = rng.randf_range(-800, 800)
		if abs(x) < 80 and abs(z) < 80: continue
		var s = rng.randf_range(0.6, 1.4)
		var t = Node2D.new()
		t.position = Vector2(x, z)
		var lc = tree_colors[rng.randi_range(0, tree_colors.size()-1)]
		t.draw.connect(func():
			t.draw_circle(Vector2(0, -20 * s), 18 * s, lc)
			t.draw_circle(Vector2(-10 * s, -14 * s), 14 * s, Color(lc.r * 0.9, lc.g * 0.9, lc.b * 0.9, 0.9))
			t.draw_circle(Vector2(10 * s, -14 * s), 14 * s, Color(lc.r * 0.9, lc.g * 0.9, lc.b * 0.9, 0.9))
			t.draw_rect(Rect2(-3 * s, 0, 6 * s, 18 * s), trunk_c)
		)
		add_child(t)
		t.queue_redraw()

	for i in range(15):
		var x = rng.randf_range(-750, 750)
		var z = rng.randf_range(-750, 750)
		if abs(x) < 80 and abs(z) < 80: continue
		var s = rng.randf_range(0.5, 1.0)
		var f = Node2D.new()
		f.position = Vector2(x, z)
		var fc = flower_colors[rng.randi_range(0, flower_colors.size()-1)]
		f.draw.connect(func():
			for j in range(5):
				var a = float(j) / 5.0 * TAU
				f.draw_circle(Vector2(cos(a) * 5 * s, sin(a) * 5 * s), 3 * s, fc)
			f.draw_circle(Vector2.ZERO, 2 * s, Color.YELLOW)
		)
		add_child(f)
		f.queue_redraw()

	for i in range(8):
		var x = rng.randf_range(-700, 700)
		var z = rng.randf_range(-700, 700)
		if abs(x) < 80 and abs(z) < 80: continue
		var s = rng.randf_range(0.7, 1.3)
		var r = Node2D.new()
		r.position = Vector2(x, z)
		r.draw.connect(func():
			r.draw_circle(Vector2.ZERO, 8 * s, rock_c)
			r.draw_circle(Vector2(-3 * s, 2 * s), 6 * s, Color(rock_c.r * 0.85, rock_c.g * 0.85, rock_c.b * 0.85))
		)
		add_child(r)
		r.queue_redraw()

func spawn_lion():
	var ls = preload("res://lion.gd")
	lion = CharacterBody2D.new()
	lion.set_script(ls)
	lion.position = Vector2.ZERO
	add_child(lion)
	camera = Camera2D.new()
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 5.0
	add_child(camera)

func spawn_steaks(count: int):
	var ss = preload("res://steak.gd")
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	for i in range(count):
		var steak = Area2D.new()
		steak.set_script(ss)
		var pos = Vector2(rng.randf_range(-650, 650), rng.randf_range(-650, 650))
		var attempts = 0
		while pos.length() < 100 and attempts < 30:
			pos = Vector2(rng.randf_range(-650, 650), rng.randf_range(-650, 650))
			attempts += 1
		steak.position = pos
		add_child(steak)
		steak.triggered.connect(_on_steak_triggered)
		food_remaining += 1

func setup_ui():
	canvas = CanvasLayer.new()
	canvas.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	add_child(canvas)

	ui_score = Label.new()
	ui_score.text = "Steaks: 0/10  |  Streak: 0"
	ui_score.position = Vector2(10, 10)
	ui_score.add_theme_font_size_override("font_size", 22)
	ui_score.add_theme_color_override("font_color", Color.WHITE)
	ui_score.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	ui_score.add_theme_constant_override("outline_size", 2)
	canvas.add_child(ui_score)

	var ws = DisplayServer.window_get_size()
	ui_hint = Label.new()
	ui_hint.text = "WASD to move  |  R to restart  |  Esc to pause"
	ui_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_hint.position = Vector2(0, ws.y - 40)
	ui_hint.size = Vector2(ws.x, 30)
	ui_hint.add_theme_font_size_override("font_size", 16)
	ui_hint.add_theme_color_override("font_color", Color(1, 1, 1, 0.6))
	canvas.add_child(ui_hint)

	ui_sound_btn = Button.new()
	ui_sound_btn.text = "🔊"
	ui_sound_btn.position = Vector2(ws.x - 50, 10)
	ui_sound_btn.size = Vector2(40, 40)
	ui_sound_btn.add_theme_font_size_override("font_size", 22)
	ui_sound_btn.pressed.connect(_toggle_sound)
	canvas.add_child(ui_sound_btn)

	ui_bg = ColorRect.new()
	ui_bg.color = Color(0, 0, 0, 0.5)
	ui_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui_bg.hide()
	canvas.add_child(ui_bg)

	ui_panel = Panel.new()
	ui_panel.size = Vector2(420, 280)
	ui_panel.position = Vector2((ws.x - 420) / 2, (ws.y - 280) / 2)
	ui_panel.hide()
	canvas.add_child(ui_panel)

	var title = Label.new()
	title.text = "MATH QUESTION!"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(0, 20)
	title.size = Vector2(420, 40)
	title.add_theme_font_size_override("font_size", 32)
	title.add_theme_color_override("font_color", Color(1, 0.85, 0))
	ui_panel.add_child(title)

	ui_question = Label.new()
	ui_question.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_question.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ui_question.position = Vector2(0, 70)
	ui_question.size = Vector2(420, 50)
	ui_question.add_theme_font_size_override("font_size", 40)
	ui_question.add_theme_color_override("font_color", Color.WHITE)
	ui_panel.add_child(ui_question)

	ui_input = LineEdit.new()
	ui_input.position = Vector2(110, 135)
	ui_input.size = Vector2(200, 45)
	ui_input.add_theme_font_size_override("font_size", 28)
	ui_input.alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_input.placeholder_text = "Your answer"
	ui_input.text_submitted.connect(_on_answer_submitted)
	ui_panel.add_child(ui_input)

	ui_submit = Button.new()
	ui_submit.text = "Answer!"
	ui_submit.position = Vector2(150, 190)
	ui_submit.size = Vector2(120, 45)
	ui_submit.add_theme_font_size_override("font_size", 24)
	ui_submit.pressed.connect(_on_submit_pressed)
	ui_panel.add_child(ui_submit)

	ui_feedback = Label.new()
	ui_feedback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_feedback.position = Vector2(0, 240)
	ui_feedback.size = Vector2(420, 40)
	ui_feedback.add_theme_font_size_override("font_size", 26)
	ui_panel.add_child(ui_feedback)

	ui_thankyou = Label.new()
	ui_thankyou.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_thankyou.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ui_thankyou.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui_thankyou.add_theme_font_size_override("font_size", 40)
	ui_thankyou.add_theme_color_override("font_color", Color(1, 0.9, 0))
	ui_thankyou.add_theme_color_override("font_outline_color", Color(0.6, 0.3, 0))
	ui_thankyou.add_theme_constant_override("outline_size", 6)
	ui_thankyou.hide()
	canvas.add_child(ui_thankyou)

	ui_win = Label.new()
	ui_win.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_win.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ui_win.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui_win.add_theme_font_size_override("font_size", 50)
	ui_win.add_theme_color_override("font_color", Color(1, 0.7, 0))
	ui_win.add_theme_color_override("font_outline_color", Color(0.5, 0.2, 0))
	ui_win.add_theme_constant_override("outline_size", 8)
	ui_win.hide()
	canvas.add_child(ui_win)

	ui_restart_btn = Button.new()
	ui_restart_btn.text = "Play Again"
	ui_restart_btn.position = Vector2((ws.x - 200) / 2, ws.y / 2 + 80)
	ui_restart_btn.size = Vector2(200, 55)
	ui_restart_btn.add_theme_font_size_override("font_size", 26)
	ui_restart_btn.pressed.connect(_on_restart_pressed)
	ui_restart_btn.hide()
	canvas.add_child(ui_restart_btn)

	var instr = Label.new()
	instr.text = "Explore the jungle and find the steaks!\nSolve math problems to eat them!"
	instr.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	instr.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	instr.set_anchors_preset(Control.PRESET_FULL_RECT)
	instr.add_theme_font_size_override("font_size", 28)
	instr.add_theme_color_override("font_color", Color.WHITE)
	instr.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	instr.add_theme_constant_override("outline_size", 4)
	canvas.add_child(instr)
	var ft = create_tween()
	ft.tween_property(instr, "modulate:a", 0.0, 1.5).set_delay(4.0)
	ft.tween_callback(instr.queue_free)

	ui_pause_overlay = ColorRect.new()
	ui_pause_overlay.color = Color(0, 0, 0, 0.7)
	ui_pause_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui_pause_overlay.hide()
	canvas.add_child(ui_pause_overlay)

	ui_pause_panel = Panel.new()
	ui_pause_panel.size = Vector2(300, 250)
	ui_pause_panel.position = Vector2((ws.x - 300) / 2, (ws.y - 250) / 2)
	ui_pause_panel.hide()
	canvas.add_child(ui_pause_panel)

	ui_pause_title = Label.new()
	ui_pause_title.text = "PAUSED"
	ui_pause_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ui_pause_title.position = Vector2(0, 30)
	ui_pause_title.size = Vector2(300, 40)
	ui_pause_title.add_theme_font_size_override("font_size", 36)
	ui_pause_title.add_theme_color_override("font_color", Color(1, 0.85, 0))
	ui_pause_panel.add_child(ui_pause_title)

	ui_resume_btn = Button.new()
	ui_resume_btn.text = "Resume"
	ui_resume_btn.position = Vector2(75, 90)
	ui_resume_btn.size = Vector2(150, 45)
	ui_resume_btn.add_theme_font_size_override("font_size", 22)
	ui_resume_btn.pressed.connect(_resume_game)
	ui_pause_panel.add_child(ui_resume_btn)

	ui_pause_restart_btn = Button.new()
	ui_pause_restart_btn.text = "Restart"
	ui_pause_restart_btn.position = Vector2(75, 150)
	ui_pause_restart_btn.size = Vector2(150, 45)
	ui_pause_restart_btn.add_theme_font_size_override("font_size", 22)
	ui_pause_restart_btn.pressed.connect(_on_restart_pressed)
	ui_pause_panel.add_child(ui_pause_restart_btn)

func setup_audio():
	roar_player = AudioStreamPlayer.new()
	roar_player.stream = _gen_roar()
	add_child(roar_player)

	music_player = AudioStreamPlayer.new()
	music_player.stream = _gen_music()
	music_player.autoplay = true
	add_child(music_player)

	correct_player = AudioStreamPlayer.new()
	correct_player.stream = _gen_correct()
	add_child(correct_player)

	wrong_player = AudioStreamPlayer.new()
	wrong_player.stream = _gen_wrong()
	add_child(wrong_player)

func gen_wav(sr: int, dur: float, gen: Callable) -> AudioStreamWAV:
	var ns = int(sr * dur)
	var data = PackedByteArray()
	data.resize(ns * 2)
	for i in range(ns):
		var s = gen.call(float(i) / sr)
		s = clamp(s, -1.0, 1.0)
		var val = int(s * 32767)
		data[i * 2] = val & 0xFF
		data[i * 2 + 1] = (val >> 8) & 0xFF
	var w = AudioStreamWAV.new()
	w.data = data
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = sr
	w.stereo = false
	return w

func _gen_roar() -> AudioStreamWAV:
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	return gen_wav(22050, 1.5, func(t):
		var s = sin(t * 40.0 * TAU) * 0.5
		s += sin(t * 70.0 * TAU) * 0.35
		s += sin(t * 110.0 * TAU) * 0.15
		s += sin(t * 55.0 * TAU) * 0.1
		var env = min(t * 8.0, 1.0) * exp(-t * 1.5)
		s *= env
		s += (rng.randf() - 0.5) * 0.06 * env
		return s * 1.2
	)

func _gen_music() -> AudioStreamWAV:
	var sr = 22050
	var dur = 4.0
	var ns = int(sr * dur)
	var data = PackedByteArray()
	data.resize(ns * 2)
	var notes = {
		"C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.00,
		"A4": 440.00, "C5": 523.25, "D5": 587.33, "E5": 659.25,
	}
	var melody = ["C4", "E4", "G4", "A4", "G4", "E4", "D4", "C4",
		"E4", "G4", "A4", "C5", "A4", "G4", "E4", "D4"]
	var note_len = dur / melody.size()
	for i in range(ns):
		var t = float(i) / sr
		var ni = int(t / note_len)
		if ni >= melody.size(): ni = melody.size() - 1
		var nt = (t - ni * note_len) / note_len
		var env = min(nt * 30.0, 1.0) * exp(-nt * 5.0)
		var freq = notes[melody[ni]]
		var s = sin(t * freq * TAU) * 0.12 * env
		s += sin(t * 130.81 * TAU) * 0.04
		s += sin(t * 261.63 * TAU) * 0.03
		s += sin(t * 329.63 * TAU) * 0.03
		s += sin(t * 392.00 * TAU) * 0.03
		s = clamp(s, -1.0, 1.0)
		var val = int(s * 16000)
		data[i * 2] = val & 0xFF
		data[i * 2 + 1] = (val >> 8) & 0xFF
	var w = AudioStreamWAV.new()
	w.data = data
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = sr
	w.stereo = false
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_begin = 0
	w.loop_end = ns
	return w

func _gen_correct() -> AudioStreamWAV:
	return gen_wav(22050, 0.3, func(t):
		var f = 523.25 + t * 1000.0
		var env = min(t * 30.0, 1.0) * exp(-t * 6.0)
		return sin(t * f * TAU) * 0.3 * env
	)

func _gen_wrong() -> AudioStreamWAV:
	return gen_wav(22050, 0.3, func(t):
		var env = min(t * 30.0, 1.0) * exp(-t * 6.0)
		return (sin(t * 100.0 * TAU) + sin(t * 120.0 * TAU)) * 0.15 * env
	)

func _process(_delta):
	if lion and camera:
		camera.global_position = camera.global_position.lerp(lion.global_position, _delta * 5.0)

func _input(event):
	if event.is_action_pressed("ui_cancel"):
		if is_question_active: return
		if is_paused: _resume_game()
		else: _pause_game()
	if event.is_action_pressed("restart"):
		_on_restart_pressed()

func _pause_game():
	is_paused = true
	get_tree().paused = true
	ui_pause_overlay.show()
	ui_pause_panel.show()

func _resume_game():
	is_paused = false
	get_tree().paused = false
	ui_pause_overlay.hide()
	ui_pause_panel.hide()

func _toggle_sound():
	sound_on = not sound_on
	ui_sound_btn.text = "🔊" if sound_on else "🔇"
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), not sound_on)

func _on_steak_triggered(qtext: String, answer: int, node: Node2D):
	if is_question_active: return
	is_question_active = true
	current_steak = node
	ui_question.text = qtext
	ui_feedback.text = ""
	ui_input.text = ""
	ui_submit.disabled = false
	ui_input.editable = true
	ui_bg.show()
	ui_panel.show()
	ui_input.grab_focus()
	get_tree().paused = true

func _on_submit_pressed(): check_answer()
func _on_answer_submitted(_text): check_answer()

func check_answer():
	if not current_steak or not is_question_active: return
	var text = ui_input.text.strip_edges()
	if text.is_empty(): return
	if text.to_int() == current_steak.correct_answer:
		on_correct_answer()
	else:
		on_wrong_answer()

func on_correct_answer():
	is_question_active = false
	ui_submit.disabled = true
	ui_input.editable = false
	ui_feedback.add_theme_color_override("font_color", Color(0, 1, 0))
	ui_feedback.text = "Correct!"
	food_remaining -= 1
	score += 1
	streak += 1
	update_score()

	correct_player.play()
	roar_player.volume_db = 10.0
	roar_player.play()
	spawn_particles()

	await get_tree().create_timer(0.5).timeout
	ui_bg.hide()
	ui_panel.hide()
	get_tree().paused = false

	ui_thankyou.text = "Thank you Titus Hank Naidoo!"
	ui_thankyou.show()
	if DisplayServer.tts_is_speaking(): DisplayServer.tts_stop()
	DisplayServer.tts_speak("Thank you Titus Hank Naidoo", "en-US", 150)

	await get_tree().create_timer(3.0, false).timeout
	ui_thankyou.hide()

	ui_submit.disabled = false
	ui_input.editable = true
	if current_steak: current_steak.call("collect")

	if food_remaining <= 0:
		ui_win.text = "AMAZING!\nYou ate all the steaks!"
		ui_win.show()
		ui_restart_btn.show()
		DisplayServer.tts_speak("Amazing! You ate all the steaks!", "en-US")

func on_wrong_answer():
	streak = 0
	update_score()
	ui_feedback.add_theme_color_override("font_color", Color(1, 0.3, 0.3))
	ui_feedback.text = "Oops, try again!"
	ui_input.text = ""
	ui_input.grab_focus()
	wrong_player.play()

func update_score():
	ui_score.text = "Steaks: %d/10  |  Streak: %d" % [score, streak]

func spawn_particles():
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	var colors = [Color(1, 0.8, 0), Color(1, 0.4, 0), Color(0.2, 1, 0.2), Color(0.3, 0.6, 1), Color(1, 0.2, 0.5)]
	var ws = DisplayServer.window_get_size()
	for i in range(18):
		var p = ColorRect.new()
		p.color = colors[rng.randi_range(0, colors.size()-1)]
		p.size = Vector2(6, 6)
		p.position = Vector2(ws.x/2 + rng.randf_range(-60, 60), ws.y/2 + rng.randf_range(-60, 60))
		canvas.add_child(p)
		var target = p.position + Vector2(rng.randf_range(-180, 180), rng.randf_range(-180, 180))
		var tw = create_tween()
		tw.set_parallel(true)
		tw.tween_property(p, "position", target, 0.7).set_ease(Tween.EASE_OUT)
		tw.tween_property(p, "modulate:a", 0.0, 0.7)
		tw.tween_callback(p.queue_free)

func _on_restart_pressed():
	get_tree().paused = false
	get_tree().reload_current_scene()
