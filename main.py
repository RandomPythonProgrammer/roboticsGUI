import pyglet
from pyglet.graphics import Batch
import time


class RectangularObject:
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple,  batch: Batch = None):
        self.batch = batch
        self.shape = pyglet.shapes.Rectangle(x, y, width, height, color, self.batch)
        self.shape.anchor_x, self.shape.anchor_y = width / 2, height / 2

    def center(self, other):
        center_x, center_y = other.shape.x + other.shape.width / 2, other.shape.y + other.shape.height / 2
        self.shape.x, self.shape.y = center_x - self.shape.width / 2, center_y - self.shape.height / 2


class Application(pyglet.window.Window):
    def __init__(self):
        super(Application, self).__init__()
        # initialize window and application
        display = pyglet.canvas.Display().get_default_screen()
        x_mult, y_mult = display.width / 16, display.height / 9
        mult = min(x_mult, y_mult) * 0.75
        self.set_size(16 * mult, 9 * mult)
        self.set_location(0, 0)
        self.lastTime = self.startTime = time.time()

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

    def on_update(self, dt: float):
        pass

    def on_draw(self):
        self.on_update(time.time() - self.lastTime)
        self.lastTime = time.time()
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        for tile in self.tiles:
            shape = tile.shape
            min_x, max_x = shape.x - shape.width/2, shape.x + shape.width/2
            min_y, max_y = shape.y - shape.height/2, shape.y + shape.height/2
            if max_x >= x >= min_x and max_y >= y >= min_y:
                if shape.color != (0, 0, 0):
                    tile.shape.color = (255, 0, 0)
                    break;


if __name__ == '__main__':
    app = Application()
    pyglet.app.run()
