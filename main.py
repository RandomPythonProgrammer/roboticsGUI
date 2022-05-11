import pyglet
from pyglet.graphics import Batch
from enum import Enum


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


class RectangularObject:
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple, batch: Batch):
        self.shape = pyglet.shapes.Rectangle(x, y, width, height, color, batch)
        self.shape.anchor_x, self.shape.anchor_y = width / 2, height / 2

    def center(self, other):
        center_x, center_y = other.shape.x + other.shape.width / 2, other.shape.y + other.shape.height / 2
        self.shape.x, self.shape.y = center_x - self.shape.width / 2, center_y - self.shape.height / 2


class Robot(RectangularObject):
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple, direction: Direction, batch: Batch):
        super().__init__(x, y, width, height, color, batch)
        self.__direction = direction
        self.arrow = pyglet.shapes.Triangle()

    @property
    def direction(self) -> Direction:
        return self.__direction

    @direction.setter
    def direction(self, direction: Direction):
        self.__direction = direction
        pass



class Application(pyglet.window.Window):
    def __init__(self):
        super(Application, self).__init__()
        # initialize window and application
        display = pyglet.canvas.Display().get_default_screen()
        x_mult, y_mult = display.width / 16, display.height / 9
        mult = min(x_mult, y_mult) * 0.75
        self.set_size(16 * mult, 9 * mult)
        self.set_location(0, 0)

        # initialize field variables
        self.tileSize = 0.6096
        self.pixel_per_meter = self.height / (self.tileSize * 6)
        self.backgroundBatch = pyglet.graphics.Batch()
        self.foregroundBatch = pyglet.graphics.Batch()

        # initialize objects
        size = self.tileSize * self.pixel_per_meter
        self.tiles = []
        for number in range(36):
            x, y = (number // 6 + 0.5) * size, (number % 6 + 0.5) * size
            self.tiles.append(RectangularObject(x, y, size, size, (25, 25, 25), self.backgroundBatch))
        size = 0.4572 * self.pixel_per_meter
        self.robot = RectangularObject(0, 0, size, size, (255, 200, 200), self.foregroundBatch)
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
        shape = self.robot.shape
        min_x, max_x = shape.x - shape.width/2, shape.x + shape.width/2
        min_y, max_y = shape.y - shape.height/2, shape.y + shape.height/2
        if max_x >= x >= min_x and max_y >= y >= min_y:
            distance = 0
            direction = None
            if abs(dy) > abs(dx):
                shape.y += dy
            else:
                shape.x += dx
            self.movements.append((direction, distance))


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
