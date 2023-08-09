import json
import math
import os
import tkinter
from enum import Enum
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
import pyglet
from pyglet.window import key


class ActionType(Enum):
    VOID = -1
    ROTATION = 0
    MOVEMENT = 1
    SLEEP = 2
    FUNCTION = 3


class Direction(Enum):
    VOID = -1
    HORIZONTAL = 0
    VERTICAL = 1
    POSITIONAL = 10


class FunctionDialog(tkinter.Tk):
    def __init__(self, write: Connection):
        super(FunctionDialog, self).__init__()
        self.write = write
        self.func_label = tkinter.Label(text='Enter the name of the function to add:')
        self.func_label.pack()
        self.func_box = tkinter.Entry()
        self.func_box.pack()
        self.arg_label = tkinter.Label(text='Arguments, separated by commas')
        self.arg_label.pack()
        self.arg_box = tkinter.Entry()
        self.arg_box.pack()
        self.button = tkinter.Button(text="Add", command=self.on_stop)
        self.button.pack()

        self.func_box.focus()

        self.title('Add Function')
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'icon.jpg')
        self.iconphoto(False, tkinter.PhotoImage(file=path))

    def on_stop(self):
        self.write.send(self.func_box.get() + chr(23) + self.arg_box.get())
        self.destroy()

    @classmethod
    def run(cls, write: Connection):
        dialog = cls(write)
        dialog.mainloop()


class PositionDialog(tkinter.Tk):
    def __init__(self, write: Connection):
        super(PositionDialog, self).__init__()
        self.write = write
        self.pos_label = tkinter.Label(text='Position to travel to (x, y, rotation [optional]):')
        self.pos_label.pack()
        self.pos_box = tkinter.Entry()
        self.pos_box.pack()
        self.button = tkinter.Button(text="Add", command=self.on_stop)
        self.button.pack()

        self.pos_box.focus()

        self.title('Add Function')
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'icon.jpg')
        self.iconphoto(False, tkinter.PhotoImage(file=path))

    def on_stop(self):
        self.write.send(self.pos_box.get())
        self.destroy()

    @classmethod
    def run(cls, write: Connection):
        dialog = cls(write)
        dialog.mainloop()


class Movement:
    def __init__(self, action: ActionType, direction: Direction, amount: any, state: tuple, arguments=''):
        self.action = action
        self.direction = direction
        self.amount = amount
        self.arguments = arguments

        try:
            self.amount = round(amount, 4)
        except TypeError:
            pass

        self.state = state

    def __repr__(self):
        if self.action == ActionType.MOVEMENT:
            if self.direction == Direction.VERTICAL:
                if self.amount > 0:
                    return f"move forwards {round(abs(self.amount * 39.37), 4)}"
                elif self.amount < 0:
                    return f"move backwards {round(abs(self.amount * 39.37), 4)}"
            elif self.direction == Direction.HORIZONTAL:
                if self.amount > 0:
                    return f"move right {round(abs(self.amount * 39.37), 4)}"
                elif self.amount < 0:
                    return f"move left {round(abs(self.amount * 39.37), 4)}"
            elif self.direction == Direction.POSITIONAL:
                if len(self.amount) == 2:
                    return f"line to {round(self.amount[0] * 39.37, 4)}, {round(self.amount[1] * 39.37, 4)}"
                elif len(self.amount) == 3:
                    return f"line to {round(self.amount[0] * 39.37, 4)}, {round(self.amount[1] * 39.37, 4)}, heading {round(math.degrees(self.amount[2]), 4)}"

        elif self.action == ActionType.ROTATION:
            if self.amount > 0:
                return f"turn right {round(math.degrees(abs(self.amount)), 4)}"
            elif self.amount < 0:
                return f"turn left {round(math.degrees(abs(self.amount)), 4)}"

        elif self.action == ActionType.SLEEP:
            return f"wait {abs(self.amount)}"

        elif self.action == ActionType.FUNCTION:
            return f"execute {self.amount} ({self.arguments})"

        return "[Error]: " + str(self.amount)

    def to_code(self):
        if self.action == ActionType.MOVEMENT:
            if self.direction == Direction.VERTICAL:
                if self.amount > 0:
                    return f".forward({round(self.amount * 39.37, 4)})"
                elif self.amount < 0:
                    return f".back({round(abs(self.amount) * 39.37, 4)})"
            elif self.direction == Direction.HORIZONTAL:
                if self.amount > 0:
                    return f".strafeRight({round(self.amount * 39.37, 4)})"
                elif self.amount < 0:
                    return f".strafeLeft({round(abs(self.amount) * 39.37, 4)})"
            elif self.direction == Direction.POSITIONAL:
                if len(self.amount) == 2:
                    return f".lineTo(new Vector2d({self.amount}))"
                elif len(self.amount) == 3:
                    return f".lineToLinearHeading(new Pose2d{self.amount})"

        elif self.action == ActionType.ROTATION:
            return f".turn({-self.amount})"
        elif self.action == ActionType.SLEEP:
            return f".waitSeconds({self.amount})"
        elif self.action == ActionType.FUNCTION:
            return f".addDisplacementMarker(() -> {self.amount}({self.arguments}))"

    def __add__(self, other):
        return Movement(self.action, self.direction, self.amount + other.amount, self.state)


class Application(pyglet.window.Window):
    def __init__(self, width: int, height: int):
        super(Application, self).__init__(width=width, height=height)

        # initialize window and application
        self.dragging = False
        self.drag_direction = None
        self.setup = False
        self.held_keys = key.KeyStateHandler()
        with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as config:
            self.settings = json.load(config)
        self.set_caption("RoboticsGUI")
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'icon.jpg')
        print(path)
        self.set_icon(pyglet.image.load(path))

        # initialize field variables
        self.speed = self.settings['robot_speed']
        self.rotation_speed = self.settings['robot_turn_speed']
        self.tileSize = 0.6096
        self.pixel_per_meter = self.height / (self.tileSize * 6)
        self.backgroundBatch = pyglet.graphics.Batch()
        self.foregroundBatch = pyglet.graphics.Batch()
        path = os.path.join(os.path.dirname(__file__), 'resources', 'field.png')
        self.background = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.backgroundBatch)
        self.field_size = round(self.tileSize * self.pixel_per_meter * 6)
        self.background.scale_x = self.field_size / self.background.width
        self.background.scale_y = self.field_size / self.background.height
        self.mouse_pos_mode = False
        self.mouse_pos = self.field_size / 2, self.field_size / 2
        mx, my = self.mouse_pos
        self.set_mouse_position(int(mx), int(my))

        # initialize objects
        width = self.settings['robot_width'] * self.pixel_per_meter / 39.37
        length = self.settings['robot_length'] * self.pixel_per_meter / 39.37
        path = os.path.join(os.path.dirname(__file__), 'resources', 'robot.png')
        image = pyglet.image.load(path)
        image.anchor_x, image.anchor_y = round(image.width / 2), round(image.height / 2)
        self.center_x = self.center_y = self.field_size / 2
        self.robot = pyglet.sprite.Sprite(image, self.center_x, self.center_y, batch=self.foregroundBatch)
        self.robot.scale_x, self.robot.scale_y = width / self.robot.width, length / self.robot.height
        self.robot.opacity = 200
        self.robot.rotation = 90
        self.starting_position = self.center_x, self.center_y, 0
        self.position_label = pyglet.text.Label(
            text=f"Pose: {self.calculate_position()}",
            font_size=self.settings['font_size'],
            x=0, y=0,
            color=(0, 100, 0, 255),
            bold=True
        )

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

        # Circles and lines
        self.mode = 0
        self.circles = []
        for line in self.settings['lines']:
            circle = pyglet.shapes.Circle(
                self.robot.x,
                self.robot.y,
                line['length'] / 39.37 * self.pixel_per_meter,
                color=line['color']
            )
            circle.opacity = 100
            self.circles.append(circle)
        radius = ((self.robot.width ** 2 + self.robot.height ** 2) ** 0.5) / 2
        turn_circle = pyglet.shapes.Circle(self.robot.x, self.robot.y, radius, color=(139, 54, 54))
        turn_circle.opacity = 150
        self.circles.append(turn_circle)

    def calculate_position(self):
        x, y = ((self.robot.x - self.center_x) / self.pixel_per_meter) * 39.37, (
                (self.robot.y - self.center_y) / self.pixel_per_meter) * 39.37
        rotation = math.radians(-self.robot.rotation + 90)
        return round(x, 4), round(y, 4), round(rotation % (math.pi * 2), 4)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = x, y

    def calculate_mouse_position(self):
        x, y = self.mouse_pos
        return round((x - self.field_size / 2) / self.pixel_per_meter * 39.37, 4), \
               round((y - self.field_size / 2) / self.pixel_per_meter * 39.37, 4)

    def on_update(self, dt: float):
        angle = self.robot.rotation
        position = self.robot.position

        rotation = math.radians(self.robot.rotation)
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

        shifted = self.held_keys[key.LSHIFT] or self.held_keys[key.RSHIFT]

        if shifted:
            distance *= 0.25
        else:
            if self.held_keys[key.Q]:
                self.robot.rotation -= rotation
                action_type = ActionType.ROTATION
                direction = Direction.VOID
                amount = -math.radians(rotation)

            elif self.held_keys[key.E]:
                self.robot.rotation += rotation
                action_type = ActionType.ROTATION
                direction = Direction.VOID
                amount = math.radians(rotation)

        if action_type != ActionType.ROTATION:
            if self.held_keys[key.W]:
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

        if amount != 0:
            self.add_movement(amount, action_type, direction, (position, angle))

    def add_movement(self, amount: float, action_type: ActionType, direction: Direction, state: tuple, arguments=''):
        if self.setup:
            movement = Movement(action_type, direction, amount, state, arguments)
            if direction != Direction.POSITIONAL:
                if len(self.movements) > 0:
                    previous = self.movements[-1]
                    same_direction = previous.direction == direction
                    if previous.action == action_type and same_direction and action_type != ActionType.FUNCTION:
                        movement = self.movements.pop(-1) + movement

            if movement.action == ActionType.FUNCTION or movement.amount != 0:
                self.movements.append(movement)
            self.update_console()

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        if self.mode > 0:
            if self.mode == 2:
                for circle in self.circles:
                    circle.position = self.robot.position
                    circle.draw()
            for line in self.settings['lines']:
                self.line_to(line['length'], line['angle'], line['width'], tuple(line['color'])).draw()
        self.foregroundBatch.draw()
        if self.mouse_pos_mode:
            self.position_label.text = f"Mouse Position: {self.calculate_mouse_position()}"
        else:
            self.position_label.text = f"Pose: {self.calculate_position()}"
        self.position_label.draw()

    def on_key_press(self, symbol, modifiers):
        self.held_keys[symbol] = True

    def get_code(self):
        x, y, rotation = self.starting_position
        x, y = ((x - self.center_x) / self.pixel_per_meter) * 39.37, (
                (y - self.center_y) / self.pixel_per_meter) * 39.37
        header = f"""SampleMecanumDrive drive = new SampleMecanumDrive(hardwareMap);
drive.setPoseEstimate(new Pose2d({x}, {y}, {math.radians(-rotation + 90)}));
TrajectorySequence trajectory = drive.trajectorySequenceBuilder(drive.getPoseEstimate())
    """
        code = [
            movement.to_code()
            for movement in self.movements
            if movement.action != ActionType.VOID
        ]

        code.append(
            ".build();"
        )

        return header + "\n\t".join(code) + "\ndrive.followTrajectorySequence(trajectory);"

    def get_text(self):
        return [str(line) for line in self.movements if line.action != ActionType.VOID]

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.console_box.x <= x <= self.console_box.x + self.console_box.width:
            self.console_box.y = min(max(self.console_box.y - scroll_y * self.settings['font_size'] * 1.5, 0),
                                     self.console_box.height - self.field_size / 4)

    def on_key_release(self, symbol, modifiers):
        self.held_keys[symbol] = False

        position = self.robot.position
        angle = self.robot.rotation

        if modifiers & key.MOD_SHIFT:
            radians = math.radians(self.robot.rotation)
            if symbol == key.Q:
                new_angle = math.degrees(round((radians - (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4))
                self.add_movement(
                    -math.radians(abs(angle - new_angle)),
                    ActionType.ROTATION, Direction.VOID, (position, angle)
                )
                self.robot.rotation = new_angle

            elif symbol == key.E:
                new_angle = math.degrees(round((radians + (math.pi / 4)) / (math.pi / 4)) * (math.pi / 4))
                self.add_movement(
                    math.radians(abs(angle - new_angle)),
                    ActionType.ROTATION, Direction.VOID, (position, angle)
                )
                self.robot.rotation = new_angle

            elif symbol == key.R:
                self.add_movement(1, ActionType.SLEEP, Direction.VOID, (position, angle))

        else:
            if symbol == key.P and modifiers & key.MOD_ACCEL:
                try:
                    line = "-" * os.get_terminal_size().columns
                except OSError:
                    line = "-" * 100

                print(line + "\n" + self.get_code() + "\n" + line)

            elif symbol == key.Z and modifiers & key.MOD_ACCEL:
                if len(self.movements) > 0:
                    movement = self.movements.pop(-1)
                    self.robot.position, self.robot.rotation = movement.state
                    self.update_console()

            elif symbol == key.C and modifiers & key.MOD_ACCEL:
                self.robot.rotation = 90
                self.robot.x = self.center_x
                self.robot.y = self.center_y
                self.movements.clear()
                self.setup = False
                self.robot.opacity = 200
                self.starting_position = self.center_x, self.center_y, 0
                self.update_console()

            elif symbol == key.SPACE:
                self.movements.append(
                    Movement(ActionType.VOID, Direction.VOID, 0, (self.robot.position, self.robot.rotation))
                )

            elif symbol == key.T and self.setup:
                read, write = Pipe()
                process = Process(target=PositionDialog.run, args=(write,))
                process.start()
                process.join()
                position = read.recv()
                read.close()
                write.close()
                if position:
                    items = position.replace(" ", "").split(",")
                    x = round(float(items[0]) / 39.37, 4)
                    y = round(float(items[1]) / 39.37, 4)
                    rx = self.field_size / 2 + x * self.pixel_per_meter
                    ry = self.field_size / 2 + y * self.pixel_per_meter
                    r = None
                    if len(items) == 3:
                        r = math.radians(float(items[2]))

                    self.robot.position = rx, ry
                    self.add_movement(
                        (x, y, r) if r is not None else (x, y),
                        ActionType.MOVEMENT, Direction.POSITIONAL,
                        (self.robot.position, self.robot.rotation)
                    )
                    if len(items) == 3:
                        self.robot.rotation = (-float(items[2])) + 90

            elif symbol == key.M:
                if self.mouse_pos_mode:
                    self.mouse_pos_mode = False
                    self.position_label.color = (0, 100, 0, 255)
                else:
                    self.mouse_pos_mode = True
                    self.position_label.color = (100, 0, 100, 255)

            elif symbol == key.ENTER:
                self.setup = True
                self.robot.opacity = 255
                self.starting_position = self.robot.x, self.robot.y, self.robot.rotation

            elif symbol == key.R:
                self.add_movement(.1, ActionType.SLEEP, Direction.VOID, (position, angle))

            elif symbol == key.F and self.setup:
                read, write = Pipe()
                process = Process(target=FunctionDialog.run, args=(write,))
                process.start()
                process.join()
                func_name, arguments = tuple(read.recv().split(chr(23)))
                read.close()
                write.close()
                if func_name:
                    self.add_movement(
                        func_name.replace(' ', ''),
                        ActionType.FUNCTION, Direction.VOID,
                        (self.robot.position, self.robot.rotation),
                        arguments
                    )

            elif symbol == key.C:
                self.mode += 1
                if self.mode > 2:
                    self.mode = 0

    def update_console(self):
        lines = self.get_text()
        self.console.delete_text(0, len(self.console.text))
        text = ""
        for line in lines:
            index = lines.index(line)
            text += f"{index + 1}: {line}\n"
        self.console.insert_text(0, text, dict(
            color=(255, 255, 255, 255), font_size=self.settings['font_size']
        ))

    def line_to(self, length: float, angle: float, width: float, color: tuple) -> pyglet.shapes.Line:
        total_angle = self.robot.rotation + angle
        pixel_length = length * self.pixel_per_meter
        x1, x2 = self.robot.x, self.robot.x + pixel_length * math.sin(math.radians(total_angle))
        y1, y2 = self.robot.y, self.robot.y + pixel_length * math.cos(math.radians(total_angle))
        return pyglet.shapes.Line(x1, y1, x2, y2, width, color)


if __name__ == '__main__':
    display = pyglet.canvas.Display().get_default_screen()
    x_mult, y_mult = display.width / 16, display.height / 9
    mult = round(min(x_mult, y_mult) * 0.75)
    app = Application(16 * mult, 9 * mult)

    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
