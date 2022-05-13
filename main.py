import math

import pyglet
from enum import Enum
import os


class ActionType(Enum):
    VOID = -1
    ROTATION = 0
    MOVEMENT = 1
    FUNCTION = 2


class Direction(Enum):
    VOID = -1

    FORWARD = 0
    BACKWARD = 1
    RIGHTWARD = 2
    LEFTWARD = 3

    CLOCKWISE = 10
    COUNTERCLOCKWISE = 11


class Movement:
    def __init__(self, action: ActionType, direction: Direction, amount: float, state: tuple):
        self.action = action
        self.direction = direction
        self.amount = amount
        self.state = state

    def __repr__(self):
        if self.action is ActionType.MOVEMENT:
            return f"move({self.amount}, Direction.{self.direction.name})"
        elif self.action is ActionType.ROTATION:
            return f"turn({self.amount}, Direction.{self.direction.name})"
        elif self.action is ActionType.VOID:
            return None

    def __add__(self, other):
        if self.direction is other.direction:
            return Movement(self.action, self.direction, self.amount + other.amount, self.state)
        elif self.direction.value % 2 != other.direction.value % 2 and abs(
                self.direction.value - other.direction.value) is 1:
            if self.amount > other.amount:
                return Movement(self.action, self.direction, self.amount - other.amount, self.state)
            else:
                return Movement(self.action, other.direction, other.amount - self.amount, other.state)


class Application(pyglet.window.Window):
    def __init__(self):
        super(Application, self).__init__()
        # initialize window and application
        display = pyglet.canvas.Display().get_default_screen()
        x_mult, y_mult = display.width / 16, display.height / 9
        mult = round(min(x_mult, y_mult) * 0.75)
        self.set_size(16 * mult, 9 * mult)
        self.set_location(0, 0)
        self.dragging = False
        self.drag_direction = None
        self.setup = False
        self.held_keys = pyglet.window.key.KeyStateHandler()

        # initialize field variables
        self.speed = 1.5
        self.rotation_speed = 90
        self.tileSize = 0.6096
        self.pixel_per_meter = self.height / (self.tileSize * 6)
        self.backgroundBatch = pyglet.graphics.Batch()
        self.foregroundBatch = pyglet.graphics.Batch()
        path = os.path.join(os.getcwd(), "field.png")
        self.background = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.backgroundBatch)
        field_size = round(self.tileSize * self.pixel_per_meter * 6)
        self.background.scale_x = field_size / self.background.width
        self.background.scale_y = field_size / self.background.height

        # initialize objects
        size = 0.4572 * self.pixel_per_meter
        path = os.path.join(os.getcwd(), "robot.png")
        image = pyglet.image.load(path)
        image.anchor_x, image.anchor_y = round(image.width / 2), round(image.height / 2)
        self.robot = pyglet.sprite.Sprite(image, field_size / 2, field_size / 2, batch=self.foregroundBatch)
        self.robot.scale_x, self.robot.scale_y = size / self.robot.width, size / self.robot.height
        self.robot.opacity = 200

        # storage variables
        self.movements = []

    def on_update(self, dt: float):
        if self.held_keys[pyglet.window.key.LSHIFT] or self.held_keys[pyglet.window.key.RSHIFT]:
            return

        angle = self.robot.rotation
        position = self.robot.position

        rotation = self.robot.rotation * math.pi / 180
        x_mult = math.sin(rotation)
        y_mult = math.cos(rotation)

        p_rotation = rotation + math.pi / 2
        p_x_mult = math.sin(p_rotation)
        p_y_mult = math.cos(p_rotation)

        distance = self.speed * self.pixel_per_meter * dt
        rotation = self.rotation_speed * dt

        action_type = None
        direction = None
        amount = 0

        if self.held_keys[pyglet.window.key.Q]:
            self.robot.rotation -= rotation
            action_type = ActionType.ROTATION
            direction = Direction.COUNTERCLOCKWISE
            amount = rotation

        elif self.held_keys[pyglet.window.key.E]:
            self.robot.rotation += rotation
            action_type = ActionType.ROTATION
            direction = Direction.CLOCKWISE
            amount = rotation

        elif self.held_keys[pyglet.window.key.W]:
            self.robot.x += distance * x_mult
            self.robot.y += distance * y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.FORWARD
            amount = distance / self.pixel_per_meter

        elif self.held_keys[pyglet.window.key.S]:
            self.robot.x -= distance * x_mult
            self.robot.y -= distance * y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.BACKWARD
            amount = distance / self.pixel_per_meter

        elif self.held_keys[pyglet.window.key.A]:
            self.robot.x -= distance * p_x_mult
            self.robot.y -= distance * p_y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.LEFTWARD
            amount = distance / self.pixel_per_meter

        elif self.held_keys[pyglet.window.key.D]:
            self.robot.x += distance * p_x_mult
            self.robot.y += distance * p_y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.RIGHTWARD
            amount = distance / self.pixel_per_meter

        self.add_movement(amount, action_type, direction, (position, angle))

    def add_movement(self, amount: float, action_type: ActionType, direction: Direction, state: tuple):
        if self.setup and amount > 0:
            movement = Movement(action_type, direction, amount, state)
            has_previous = len(self.movements) > 0
            are_opposite = has_previous and direction.value % 2 != self.movements[-1].direction.value % 2
            same_group = abs(has_previous and direction.value - self.movements[-1].direction.value) is 1
            if has_previous and self.movements[-1].action is action_type or (are_opposite and same_group):
                new_movement = self.movements.pop(-1) + movement
                if new_movement.amount > 0:
                    self.movements.append(new_movement)
            else:
                self.movements.append(movement)

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_key_press(self, symbol, modifiers):
        self.held_keys[symbol] = True

    def get_code(self):
        return [movement for movement in self.movements if movement.action != ActionType.VOID and movement.amount > 0]

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.ENTER:
            self.setup = True
            self.robot.opacity = 255
        self.held_keys[symbol] = False

        if modifiers & pyglet.window.key.MOD_SHIFT:
            position = self.robot.position
            angle = self.robot.rotation

            radians = self.robot.rotation * math.pi / 180
            if symbol is pyglet.window.key.Q:
                new_angle = round((radians - (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4) * 180 / math.pi
                self.add_movement(
                    abs(angle - new_angle) * math.pi / 180,
                    ActionType.ROTATION, Direction.COUNTERCLOCKWISE, (position, angle)
                )
                self.robot.rotation = new_angle
            elif symbol is pyglet.window.key.E:
                new_angle = round((radians + (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4) * 180 / math.pi
                self.add_movement(
                    abs(angle - new_angle) * math.pi / 180,
                    ActionType.ROTATION, Direction.CLOCKWISE, (position, angle)
                )
                self.robot.rotation = new_angle

        if symbol is pyglet.window.key.P and modifiers & pyglet.window.key.MOD_ACCEL:
            for line in self.get_code():
                print(line)
            print("--------------------------------------")

        if symbol is pyglet.window.key.Z and modifiers & pyglet.window.key.MOD_ACCEL:
            if len(self.movements) > 0:
                movement = self.movements.pop(-1)
                self.robot.position, self.robot.rotation = movement.state

        if symbol is pyglet.window.key.SPACE:
            self.movements.append(
                Movement(ActionType.VOID, Direction.VOID, 0, (self.robot.position, self.robot.rotation))
            )


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
