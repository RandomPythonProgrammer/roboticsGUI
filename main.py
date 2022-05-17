import math

import pyglet
from pyglet.window import key
from enum import Enum
import os
import json


class ActionType(Enum):
    VOID = -1
    ROTATION = 0
    MOVEMENT = 1
    SLEEP = 2


class Direction(Enum):
    VOID = -1

    HORIZONTAL = 0
    VERTICAL = 1


class Movement:
    def __init__(self, action: ActionType, direction: Direction, amount: float, state: tuple):
        self.action = action
        self.direction = direction
        self.amount = round(amount, 4)
        self.state = state

    def __repr__(self):
        if self.action is ActionType.MOVEMENT:
            if self.direction is Direction.VERTICAL:
                if self.amount > 0:
                    return f"move forwards {abs(self.amount)}"
                elif self.amount < 0:
                    return f"move backwards {abs(self.amount)}"
            elif self.direction is Direction.HORIZONTAL:
                if self.amount > 0:
                    return f"move right {abs(self.amount)}"
                elif self.amount < 0:
                    return f"move left {abs(self.amount)}"

        elif self.action is ActionType.ROTATION:
            if self.amount > 0:
                return f"turn right {abs(self.amount)}"
            elif self.amount < 0:
                return f"turn left {abs(self.amount)}"
        elif self.action is ActionType.SLEEP:
            return f"wait {abs(self.amount)}"

        return "Error"

    def to_code(self):
        if self.action is ActionType.MOVEMENT:
            if self.direction is Direction.VERTICAL:
                if self.amount > 0:
                    return f".forwards({round(self.amount * 39.37, 4)})"
                elif self.amount < 0:
                    return f".back({round(abs(self.amount) * 39.37, 4)})"
            elif self.direction is Direction.HORIZONTAL:
                if self.amount > 0:
                    return f".strafeRight({round(self.amount * 39.37, 4)})"
                elif self.amount < 0:
                    return f".strafeLeft({round(abs(self.amount) * 39.37, 4)})"
        elif self.action is ActionType.ROTATION:
            return f".turn({-self.amount})"
        elif self.action is ActionType.SLEEP:
            return f".waitSeconds({self.amount})"

    def __add__(self, other):
        return Movement(self.action, self.direction, self.amount + other.amount, self.state)


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
        self.held_keys = key.KeyStateHandler()
        with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as config:
            self.settings = json.load(config)
        self.set_caption("RoboticsGUI")

        # initialize field variables
        self.speed = self.settings['robot_speed']
        self.rotation_speed = self.settings['robot_turn_speed']
        self.tileSize = 0.6096
        self.pixel_per_meter = self.height / (self.tileSize * 6)
        self.backgroundBatch = pyglet.graphics.Batch()
        self.foregroundBatch = pyglet.graphics.Batch()
        path = os.path.join(os.path.dirname(__file__), 'resources/field.png')
        self.background = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.backgroundBatch)
        self.field_size = round(self.tileSize * self.pixel_per_meter * 6)
        self.background.scale_x = self.field_size / self.background.width
        self.background.scale_y = self.field_size / self.background.height

        # initialize objects
        width = self.settings['robot_width'] * self.pixel_per_meter
        length = self.settings['robot_length'] * self.pixel_per_meter
        path = os.path.join(os.path.dirname(__file__), "resources/robot.png")
        image = pyglet.image.load(path)
        image.anchor_x, image.anchor_y = round(image.width / 2), round(image.height / 2)
        self.robot = pyglet.sprite.Sprite(image, self.field_size / 2, self.field_size / 2, batch=self.foregroundBatch)
        self.robot.scale_x, self.robot.scale_y = width / self.robot.width, length / self.robot.height
        self.robot.opacity = 200

        # storage variables
        self.movements = []
        self.console = pyglet.text.document.FormattedDocument()
        self.console_box = pyglet.text.layout.TextLayout(
            self.console,
            self.width - self.field_size, self.field_size,
            multiline=True,
            batch=self.foregroundBatch
        )
        self.console_box.x, self.console_box.y = self.field_size, 0

    def on_update(self, dt: float):
        if self.held_keys[key.LSHIFT] or self.held_keys[key.RSHIFT]:
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

        if self.held_keys[key.Q]:
            self.robot.rotation -= rotation
            action_type = ActionType.ROTATION
            direction = Direction.VOID
            amount = -rotation * math.pi / 180

        elif self.held_keys[key.E]:
            self.robot.rotation += rotation
            action_type = ActionType.ROTATION
            direction = Direction.VOID
            amount = rotation * math.pi / 180

        elif self.held_keys[key.W]:
            self.robot.x += distance * x_mult
            self.robot.y += distance * y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.VERTICAL
            amount = distance / self.pixel_per_meter

        elif self.held_keys[key.S]:
            self.robot.x -= distance * x_mult
            self.robot.y -= distance * y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.VERTICAL
            amount = -distance / self.pixel_per_meter

        elif self.held_keys[key.A]:
            self.robot.x -= distance * p_x_mult
            self.robot.y -= distance * p_y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.HORIZONTAL
            amount = -distance / self.pixel_per_meter

        elif self.held_keys[key.D]:
            self.robot.x += distance * p_x_mult
            self.robot.y += distance * p_y_mult
            action_type = ActionType.MOVEMENT
            direction = Direction.HORIZONTAL
            amount = distance / self.pixel_per_meter

        if amount is not 0:
            self.add_movement(amount, action_type, direction, (position, angle))

    def add_movement(self, amount: float, action_type: ActionType, direction: Direction, state: tuple):
        if self.setup:
            movement = Movement(action_type, direction, amount, state)
            if len(self.movements) > 0:
                previous = self.movements[-1]
                same_direction = previous.direction is direction
                if previous.action is action_type and same_direction:
                    movement = self.movements.pop(-1) + movement

            if movement.amount is not 0:
                self.movements.append(movement)
                self.update_console()

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_key_press(self, symbol, modifiers):
        self.held_keys[symbol] = True

    def get_code(self):
        header = """SampleMecanumDrive drive = new SampleMecanumDrive(hardwareMap);
drive.setPoseEstimate(new Pose2d());
TrajectorySequence trajectory = drive.trajectorySequenceBuilder(drive.getPoseEstimate())
    """

        code = []
        [
            code.append(movement.to_code())
            for movement in self.movements
            if movement.action != ActionType.VOID
        ]
        code.append(
            ".build();"
        )
        return header + "\n\t".join(code) + "\ndrive.followTrajectorySequence(trajectory);"

    def get_text(self):
        return [str(line) for line in self.movements if line.action is not ActionType.VOID]

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.console_box.x <= x <= self.console_box.x + self.console_box.width:
            self.console_box.y = min(max(self.console_box.y + scroll_y, 0),
                                     self.console_box.height - self.field_size / 4)

    def on_key_release(self, symbol, modifiers):
        self.held_keys[symbol] = False

        position = self.robot.position
        angle = self.robot.rotation

        if modifiers & key.MOD_SHIFT:
            radians = self.robot.rotation * math.pi / 180
            if symbol is key.Q:
                new_angle = round((radians - (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4) * 180 / math.pi
                self.add_movement(
                    -abs(angle - new_angle) * math.pi / 180,
                    ActionType.ROTATION, Direction.VOID, (position, angle)
                )
                self.robot.rotation = new_angle

            elif symbol is key.E:
                new_angle = round((radians + (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4) * 180 / math.pi
                self.add_movement(
                    abs(angle - new_angle) * math.pi / 180,
                    ActionType.ROTATION, Direction.VOID, (position, angle)
                )
                self.robot.rotation = new_angle

            elif symbol is key.R:
                self.add_movement(1, ActionType.SLEEP, Direction.VOID, (position, angle))

        else:
            if symbol is key.P and modifiers & key.MOD_ACCEL:
                print("--------------------------------------")
                print(self.get_code())
                print("--------------------------------------")

            elif symbol is key.Z and modifiers & key.MOD_ACCEL:
                if len(self.movements) > 0:
                    movement = self.movements.pop(-1)
                    self.robot.position, self.robot.rotation = movement.state
                    self.update_console()

            elif symbol is key.C and modifiers & key.MOD_ACCEL:
                if len(self.movements) > 0:
                    self.robot.position, self.robot.rotation = self.movements[0].state
                    self.robot.x = self.robot.y = self.field_size / 2
                    self.movements.clear()
                    self.setup = False
                    self.robot.opacity = 200
                    self.update_console()

            elif symbol is key.SPACE:
                self.movements.append(
                    Movement(ActionType.VOID, Direction.VOID, 0, (self.robot.position, self.robot.rotation))
                )

            elif symbol is key.ENTER:
                self.setup = True
                self.robot.opacity = 255

            elif symbol is key.R:
                self.add_movement(.1, ActionType.SLEEP, Direction.VOID, (position, angle))

    def update_console(self):
        lines = self.get_text()
        self.console.delete_text(0, len(self.console.text))
        text = ""
        for line in lines:
            index = lines.index(line)
            text += f"{index + 1}: {line}\n"
        self.console.insert_text(0, text, dict(
            color=(255, 255, 255, 255)
        ))


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
