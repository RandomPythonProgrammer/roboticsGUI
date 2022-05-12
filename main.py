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

    NORTH = 10
    EAST = 11
    SOUTH = 12
    WEST = 13

    CLOCKWISE = 20
    COUNTERCLOCKWISE = 21


class Movement:
    def __init__(self, action: ActionType, direction: Direction, amount: float):
        self.action = action
        self.direction = direction
        self.amount = amount

    def __repr__(self):
        if self.action is ActionType.MOVEMENT:
            return f"move({self.amount}, Direction.{self.direction.name})"
        elif self.action is ActionType.ROTATION:
            return f"turn({self.amount}, Direction.{self.direction.name})"
        elif self.action is ActionType.VOID:
            return None

    def __add__(self, other):
        return Movement(self.action, self.direction, self.amount + other.amount)


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
        self.robot = pyglet.sprite.Sprite(image, field_size/2, field_size/2, batch=self.foregroundBatch)
        self.robot.scale_x, self.robot.scale_y = size / self.robot.width, size / self.robot.height
        self.robot.opacity = 200

        # storage variables
        self.movements = []

    def on_update(self, dt: float):
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
            direction = Direction.RIGHTWARD
            amount = distance / self.pixel_per_meter

        elif self.held_keys[pyglet.window.key.D]:
            self.robot.x += distance * p_x_mult
            self.robot.y += distance * p_y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.LEFTWARD
            amount = distance / self.pixel_per_meter

        if self.setup and amount > 0:
            movement = Movement(action_type, direction, amount)
            has_previous = len(self.movements) > 0
            if has_previous and self.movements[-1].action is action_type and self.movements[-1].direction is direction:
                self.movements[-1] = self.movements[-1] + movement
            else:
                self.movements.append(movement)

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_key_press(self, symbol, modifiers):
        self.held_keys[symbol] = True
        if symbol is pyglet.window.key.C and modifiers & pyglet.window.key.MOD_ACCEL:
            for movement in self.movements:
                print(movement)
        if symbol is pyglet.window.key.SPACE:
            self.movements.append(Movement(ActionType.VOID, Direction.VOID, 0))

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.ENTER:
            self.setup = True
            self.robot.opacity = 255
        self.held_keys[symbol] = False


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
