import pyglet
from pyglet.graphics import Batch
from enum import Enum
import os


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
        self.background = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.backgroundBatch)
        field_size = round(self.tileSize * self.pixel_per_meter * 6)
        self.background.scale_x = field_size / self.background.width
        self.background.scale_y = field_size / self.background.height

        # initialize objects
        size = 0.4572 * self.pixel_per_meter
        path = os.path.join(os.getcwd(), "robot.png")
        self.robot = pyglet.sprite.Sprite(pyglet.image.load(path), 0, 0, batch=self.foregroundBatch)
        self.robot.scale_x = size / self.robot.width
        self.robot.scale_y = size / self.robot.height

        # storage variables
        self.movements = []

    def on_update(self, dt: float):
        pass

    def on_render(self, dt: float):
        self.clear()
        self.backgroundBatch.draw()
        self.foregroundBatch.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        for tile in self.tiles:
            if (abs(x - tile.x) ** 2 + abs(y - tile.y) ** 2) ** 0.5 < tile.radius:
                tile.shape.color = (255, 0, 0)
                break

    def on_mouse_release(self, x, y, button, modifiers):
        pass


if __name__ == '__main__':
    app = Application()
    # start the event loop and render loop
    pyglet.clock.schedule(app.on_render)
    pyglet.clock.schedule(app.on_update)
    pyglet.app.run()
