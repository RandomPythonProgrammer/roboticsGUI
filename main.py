import pyglet
from pyglet.graphics import Batch
from enum import Enum
import os


class Direction(Enum):
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

    VERTICAL = 30
    HORIZONTAL = 31

    VOID = 40


class RectangularObject:
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple, batch: Batch = None):
        self.radius = ((width / 2) ** 2 + (height / 2) ** 2) ** 0.5
        coordinates = (
            [round(x - width / 2), round(y - height / 2)],
            [round(x - width / 2), round(y + height / 2)],
            [round(x + width / 2), round(y - height / 2)],
            [round(x + width / 2), round(y + height / 2)]
        )
        self.shape = pyglet.shapes.Polygon(*coordinates, color=color, batch=batch)

    @property
    def x(self):
        min_x = max_x = None
        for x, y in self.shape._coordinates:
            if min_x is None or min_x > x:
                min_x = x
            if max_x is None or max_x < x:
                max_x = x

        return (min_x + max_x) / 2

    @property
    def y(self):
        min_y = max_y = None
        for x, y in self.shape._coordinates:
            if min_y is None or min_y > y:
                min_y = y
            if max_y is None or max_y < y:
                max_y = y

        return (min_y + max_y) / 2

    def center(self, other):
        dx = other.x - self.x
        dy = other.y - self.x
        self.move(dx, dy)

    def move(self, dx, dy):
        self.shape._coordinates = [[x + dx, y + dy] for x, y in self.shape._coordinates]
        self.shape._update_position()


class Robot(RectangularObject):
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple, batch: Batch):
        super().__init__(x, y, width, height, color, batch)
        self.__rotation = 0

    @property
    def rotation(self) -> float:
        return self.__rotation

    @rotation.setter
    def rotation(self, rotation: float):
        self.__rotation = rotation


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

        # initialize field variables
        self.tileSize = 0.6096
        self.pixel_per_meter = self.height / (self.tileSize * 6)
        self.backgroundBatch = pyglet.graphics.Batch()
        self.foregroundBatch = pyglet.graphics.Batch()
        path = os.path.join(os.getcwd(), "field.png")
        self.background = None
        if os.path.exists(path):
            self.background = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.backgroundBatch)
            field_size = round(self.tileSize * self.pixel_per_meter * 6)
            self.background.scale_x = field_size / self.background.width
            self.background.scale_y = field_size / self.background.height

        # initialize objects
        size = self.tileSize * self.pixel_per_meter
        self.tiles = []
        for number in range(36):
            x, y = (number // 6 + 0.5) * size, (number % 6 + 0.5) * size
            if path is None:
                batch = self.backgroundBatch
            else:
                batch = None
            self.tiles.append(RectangularObject(x, y, size, size, (25, 25, 25), batch))
        size = 0.4572 * self.pixel_per_meter
        self.robot = Robot(0, 0, size, size, (255, 200, 200), self.foregroundBatch)
        self.robot.center(self.tiles[0])

        # storage variables
        self.movements = []

    def on_update(self, dt: float):
        pass

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if (abs(x - self.robot.x) ** 2 + abs(y - self.robot.y) ** 2) ** 0.5 < self.robot.radius:
            distance = 0
            direction = None
            if (self.drag_direction is None and abs(dy) > abs(dx)) or (self.drag_direction is Direction.VERTICAL):
                self.robot.move(0, dy)
                self.drag_direction = Direction.VERTICAL
            if (self.drag_direction is None and abs(dx) > abs(dy)) or self.drag_direction is Direction.HORIZONTAL:
                self.robot.move(dx, 0)
                self.drag_direction = Direction.HORIZONTAL
            self.movements.append((direction, distance))
        else:
            self.drag_direction = Direction.VOID

    def on_mouse_press(self, x, y, button, modifiers):
        for tile in self.tiles:
            if (abs(x - tile.x) ** 2 + abs(y - tile.y) ** 2) ** 0.5 < tile.radius:
                tile.shape.color = (255, 0, 0)
                break

    def on_mouse_release(self, x, y, button, modifiers):
        self.drag_direction = None


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
