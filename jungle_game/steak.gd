extends Area2D

signal triggered(question_text: String, correct_answer: int, node: Node2D)

var num1: int
var num2: int
var op: String
var collected: bool = false
var question_text: String
var correct_answer: int
var initial_y: float

func _ready():
	initial_y = position.y
	body_entered.connect(_on_body_entered)
	var col = CollisionShape2D.new()
	col.shape = RectangleShape2D.new()
	col.shape.size = Vector2(40, 30)
	add_child(col)
	generate_question()

func generate_question():
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	var diff = rng.randi_range(0, 2)
	if diff == 0:
		num1 = rng.randi_range(2, 5)
		num2 = rng.randi_range(1, num1 - 1)
		op = "-"
	elif diff == 1:
		num1 = rng.randi_range(5, 9)
		num2 = rng.randi_range(1, num1 - 1)
		op = "-"
	else:
		num1 = rng.randi_range(1, 5)
		num2 = rng.randi_range(1, 5)
		op = "+"
	if op == "-":
		correct_answer = num1 - num2
	else:
		correct_answer = num1 + num2
	question_text = "%d %s %d = ?" % [num1, op, num2]

func _process(_delta):
	position.y = initial_y + sin(Time.get_ticks_msec() * 0.003 + global_position.x * 0.5) * 2.0
	queue_redraw()

func _draw():
	var c_meat = Color(0.6, 0.15, 0.1)
	var c_fat = Color(0.9, 0.85, 0.75)
	var c_bone = Color(0.95, 0.9, 0.8)

	var pts = PackedVector2Array([
		Vector2(-16, -8), Vector2(-10, -12), Vector2(2, -13), Vector2(12, -10),
		Vector2(16, -4), Vector2(14, 4), Vector2(8, 10), Vector2(-2, 12),
		Vector2(-10, 10), Vector2(-16, 4)
	])
	draw_colored_polygon(pts, c_meat)
	draw_colored_polygon(PackedVector2Array([Vector2(12, -10), Vector2(18, -14), Vector2(20, -8), Vector2(16, -4)]), c_bone)
	draw_line(Vector2(-6, -2), Vector2(4, 4), c_fat, 2)
	draw_line(Vector2(-2, 4), Vector2(8, -2), c_fat, 2)
	draw_line(Vector2(-8, 4), Vector2(-2, 8), c_fat, 1.5)

func _on_body_entered(body):
	if body.is_in_group("lion") and not collected:
		collected = true
		triggered.emit(question_text, correct_answer, self)

func collect():
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector2.ZERO, 0.3)
	tween.tween_callback(queue_free)
