extends CharacterBody2D

var speed: float = 150.0
var walk_phase: float = 0.0
var facing_right: bool = true

func _ready():
	add_to_group("lion")
	var col = CollisionShape2D.new()
	col.shape = RectangleShape2D.new()
	col.shape.size = Vector2(36, 28)
	add_child(col)

func _physics_process(_delta):
	var input_dir = Vector2(
		Input.get_axis("move_left", "move_right"),
		Input.get_axis("move_forward", "move_back")
	)
	if input_dir.length() > 0.1:
		input_dir = input_dir.normalized()
		velocity = input_dir * speed
		walk_phase += _delta * 8.0
		if input_dir.x < 0 and facing_right:
			facing_right = false
			scale.x = -1
		elif input_dir.x > 0 and not facing_right:
			facing_right = true
			scale.x = 1
	else:
		velocity = Vector2.ZERO
		walk_phase = move_toward(walk_phase, 0.0, _delta * 15.0)
	move_and_slide()
	queue_redraw()

func _draw():
	var c_body = Color(0.85, 0.55, 0.1)
	var c_head = Color(0.9, 0.6, 0.15)
	var c_mane = Color(0.55, 0.3, 0.05)
	var c_leg = Color(0.75, 0.45, 0.1)
	var c_eye_w = Color.WHITE
	var c_eye_p = Color.BLACK
	var c_nose = Color(0.3, 0.15, 0.05)
	var c_tail_tip = Color(0.5, 0.25, 0.05)

	var ls = sin(walk_phase) * 5.0
	var bb = abs(sin(walk_phase * 2.0)) * 1.5
	var ly = 10 + bb

	draw_rect(Rect2(-18, -12 + bb, 36, 20), c_body)
	draw_circle(Vector2(20, -4 + bb), 9, c_head)
	for i in range(8):
		var a = float(i) / 8.0 * TAU
		draw_circle(Vector2(18 + cos(a) * 10, -4 + bb + sin(a) * 8), 4, c_mane)

	var leg_offsets = [[-12, ls], [-4, -ls], [4, ls], [12, -ls]]
	for lo in leg_offsets:
		draw_rect(Rect2(lo[0] - 2.5, ly, 5, 10), c_leg)

	draw_circle(Vector2(22, -6 + bb), 3, c_eye_w)
	draw_circle(Vector2(22, -6 + bb), 1.5, c_eye_p)
	draw_circle(Vector2(23, -3 + bb), 2, c_nose)
	draw_line(Vector2(-18, -2 + bb), Vector2(-30, -2 + bb), c_leg, 3)
	draw_circle(Vector2(-30, -2 + bb), 4, c_tail_tip)
