from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import sys

class PizzaGame:
    def __init__(self):
        self.camera = Camera()
        self.window = Window(1200, 600)
        self.state = GameState()
        self.pizza_maker = PizzaMaker()
        self.drawing_helper = DrawingHelper()

    def initialize(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        self.camera.setup()

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.camera.position_camera()
        self.drawing_helper.draw_platform()
        self.drawing_helper.draw_background()
        self.pizza_maker.draw_all()
        glutSwapBuffers()

    def run(self):
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(self.window.width, self.window.height)
        glutInitWindowPosition(100, 100)
        glutCreateWindow(b"Pizza Making Game")
        
        self.initialize()
        glutDisplayFunc(self.display)
        glutKeyboardFunc(self.keyboard_callback)
        glutMouseFunc(self.mouse_callback)
        glutTimerFunc(100, self.check_timers, 0)
        
        glutMainLoop()

    def check_timers(self, value):
        self.pizza_maker.update_cooking()
        glutPostRedisplay()
        glutTimerFunc(100, self.check_timers, 0)
    
    def keyboard_callback(self, key, x, y):
        self.state.handle_keyboard(key)
        glutPostRedisplay()
    
    def mouse_callback(self, button, state, x, y):
        if not self.state.game_over:
            self.pizza_maker.handle_click(button, state, x, y)
            glutPostRedisplay()

class Window:
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Camera:
    def __init__(self):
        self.fov = 120

    def setup(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, 2.0, 0.1, 2000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def position_camera(self):
        # Fixed camera at (0, -900, 400), looking at (0, 0, 0), z is up
        gluLookAt(0, -100, 300, 0, 0, 0, 0, 0, 1)

class GameState:
    def __init__(self):
        self.toppings = {
            "sauce": False,
            "cheese": False,
            "sausage": False,
            "pepperoni": False,
            "onion": False,
            "black_olive": False,
            "oregano": False
        }
        self.reset()

    def reset(self):
        self.bread_before_oven = False
        self.bread_after_oven = False
        self.pizza_in_box = False
        self.pizza_box_open = True
        self.pizza_box_closed = False
        self.game_over = False
        self.cooking_start_time = 0
        self.cooking_in_progress = False
        self.cooking_duration = 2
        
    def handle_keyboard(self, key):
        if key in [b'R', b'r']:
            self.reset()
            for topping in self.toppings:
                self.toppings[topping] = False

class PizzaMaker:
    def __init__(self):
        self.pizza_toppings = []
        self.positions = self.initialize_positions()
        
    def initialize_positions(self):
        return {
            "dough": (-400, -200, 0),
            "pizza": (-300, 40, 0),
            "pizza_in_box": (500, -100, 15),  # Adjusted Z from 0 to 15 to place pizza above box base
            "toppings": {
                "sauce": (-600, 200, 0),
                "cheese": (-470, 200, 0),
                "sausage": (-340, 200, 0),
                "pepperoni": (-210, 200, 0),
                "onion": (-80, 200, 0),
                "black_olive": (50, 200, 0),
                "oregano": (180, 200, 0)
            }
        }
    
    def draw_all(self):
        self.draw_toppings_bar()
        self.draw_dough()
        self.draw_pizza()
        self.draw_pizza_in_box()
        self.draw_oven()
        self.draw_pizza_box()
        self.draw_instructions()

    def draw_toppings_bar(self):
        # Make the bar wider to fit the new spacing
        DrawingHelper.draw_rect3d(-700, 350, 0, 1100, -750, 10, (0.7, 0.5, 0.3))
        for topping, pos in self.positions["toppings"].items():
            DrawingHelper.draw_rect3d(pos[0] - 45, pos[1] - 45, 0, 90, 90, 10, (0.7, 0.5, 0.3))
            if topping == "sauce":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (1, 0, 0))
                DrawingHelper.draw_text3d(pos[0] - 30, pos[1] - 70, 20, "Sauce")
            elif topping == "cheese":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (1, 1, 0))
                DrawingHelper.draw_text3d(pos[0] - 36, pos[1] - 70, 20, "Cheese")
            elif topping == "sausage":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (0.6, 0.3, 0))
                DrawingHelper.draw_rect3d(pos[0] - 25, pos[1] + 20, 12, 50, 5, 3, (0.5, 0.2, 0.1))
                DrawingHelper.draw_rect3d(pos[0] - 35, pos[1] + 5, 12, 50, 5, 3, (0.5, 0.2, 0.1))
                DrawingHelper.draw_rect3d(pos[0] - 15, pos[1] - 10, 12, 50, 5, 3, (0.5, 0.2, 0.1))
                DrawingHelper.draw_rect3d(pos[0] - 25, pos[1] - 25, 12, 50, 5, 3, (0.5, 0.2, 0.1))
                DrawingHelper.draw_text3d(pos[0] - 39, pos[1] - 70, 20, "Sausage")
            elif topping == "pepperoni":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (1.0, 0.5, 0.0))
                offsets = [(-15, 10), (10, 15), (-10, -15), (15, -10)]
                for dx, dy in offsets:
                    DrawingHelper.draw_circle3d(pos[0] + dx, pos[1] + dy, 12, 9, (0.9, 0.2, 0.2))
                DrawingHelper.draw_text3d(pos[0] - 47, pos[1] - 70, 20, "Pepperoni")
            elif topping == "onion":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (1, 0, 1))
                glColor3f(0.9, 0.8, 1.0)
                glBegin(GL_TRIANGLES)
                glVertex3f(pos[0], pos[1] + 5, 12)
                glVertex3f(pos[0] - 5, pos[1] - 5, 12)
                glVertex3f(pos[0] + 5, pos[1] - 5, 12)
                glEnd()
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    cx = pos[0] + 20 * math.cos(angle)
                    cy = pos[1] + 20 * math.sin(angle)
                    size = 10
                    glBegin(GL_TRIANGLES)
                    glVertex3f(cx, cy, 12)
                    glVertex3f(cx + size * math.cos(angle + 0.3), cy + size * math.sin(angle + 0.3), 12)
                    glVertex3f(cx + size * math.cos(angle - 0.3), cy + size * math.sin(angle - 0.3), 12)
                    glEnd()
                DrawingHelper.draw_text3d(pos[0] - 18, pos[1] - 70, 20, "Onion")
            elif topping == "black_olive":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (0, 0, 0))
                DrawingHelper.draw_circle3d(pos[0]-10, pos[1]+15, 12, 5, (.2, .2, .2))
                DrawingHelper.draw_circle3d(pos[0]+10, pos[1]+27, 12, 8, (.2, .2, .2))
                DrawingHelper.draw_circle3d(pos[0]-18, pos[1]-18, 12, 4, (.2, 0.2, 0.2))
                DrawingHelper.draw_circle3d(pos[0]+20, pos[1]-20, 12, 6, (0.2, 0.2, 0.2))
                DrawingHelper.draw_text3d(pos[0] - 27, pos[1] - 70, 20, "Olives")
            elif topping == "oregano":
                DrawingHelper.draw_circle3d(pos[0], pos[1], 10, 40, (1, 1, 1))
                DrawingHelper.draw_circle3d(pos[0] + 10, pos[1] + 15, 12, 5, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] - 12, pos[1] + 25, 12, 8, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] + 18, pos[1] + 20, 12, 6, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] - 20, pos[1] - 15, 12, 4, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] + 25, pos[1] - 10, 12, 7, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] - 15, pos[1] - 20, 12, 6, (0, 0.7, 0))
                DrawingHelper.draw_circle3d(pos[0] + 5, pos[1] + 30, 12, 5, (0, 0.7, 0))
                DrawingHelper.draw_text3d(pos[0] - 30, pos[1] - 70, 20, "Oregano")
            if game.state.toppings[topping] and topping not in self.pizza_toppings:
                glLineWidth(3.0)
                glColor3f(1, 0.5, 0)
                glBegin(GL_LINE_LOOP)
                for i in range(360):
                    angle = i * math.pi / 180
                    glVertex3f(pos[0] + 28 * math.cos(angle), pos[1] + 28 * math.sin(angle), 20)
                glEnd()

    def draw_dough(self):
        # Draw pizza board below the pizza (z=5)
        DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 60, self.positions["pizza"][1] - 60, 5, 120, 120, 10, (0.5, 0.35, 0.18))
        DrawingHelper.draw_text3d(self.positions["pizza"][0] - 50, self.positions["pizza"][1] - 80, 20, "Pizza Board")
        # Draw dough on the left (z=10)
        DrawingHelper.draw_rect3d(self.positions["dough"][0] - 70, self.positions["dough"][1] - 70, 0, 140, 140, 10, (0.5, 0.4, 0.5))
        DrawingHelper.draw_circle3d(self.positions["dough"][0], self.positions["dough"][1], 10, 60, (0.9, 0.8, 0.7))
        DrawingHelper.draw_text3d(self.positions["dough"][0] - 20, self.positions["dough"][1] - 80, 20, "Dough")

    def draw_pizza(self):
        if game.state.bread_before_oven and not game.state.cooking_in_progress:
            # Draw base pizza dough
            DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], 10, 53, (0.9, 0.8, 0.7))
            # Draw toppings in the order they were added (bottom to top)
            z = 11
            for topping in self.pizza_toppings:
                if topping == "sauce":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 49, (0.8, 0.2, 0.1))
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 47, (1.0, 0.9, 0.4))
                    z += 1
                elif topping == "sausage":
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 25, self.positions["pizza"][1] + 20, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 35, self.positions["pizza"][1] + 5, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 15, self.positions["pizza"][1] - 10, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 25, self.positions["pizza"][1] - 25, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    z += 1
                elif topping == "pepperoni":
                    for i in range(8):
                        angle = i * 45 * math.pi / 180
                        x = self.positions["pizza"][0] + math.cos(angle) * 30
                        y = self.positions["pizza"][1] + math.sin(angle) * 30
                        DrawingHelper.draw_circle3d(x, y, z, 7, (1.0, 0.5, 0.0))
                    z += 1
                elif topping == "onion":
                    for i in range(6):
                        angle = i * 60 * math.pi / 180
                        cx = self.positions["pizza"][0] + 20 * math.cos(angle)
                        cy = self.positions["pizza"][1] + 20 * math.sin(angle)
                        size = 18
                        glColor3f(0.8, 0.6, 1.0)
                        glBegin(GL_TRIANGLES)
                        glVertex3f(cx, cy, z)
                        glVertex3f(cx + size * math.cos(angle + 0.3), cy + size * math.sin(angle + 0.3), z)
                        glVertex3f(cx + size * math.cos(angle - 0.3), cy + size * math.sin(angle - 0.3), z)
                        glEnd()
                    z += 1
                elif topping == "black_olive":
                    for i in range(7):
                        angle = i * 51.4 * math.pi / 180
                        x = self.positions["pizza"][0] + math.cos(angle) * 32
                        y = self.positions["pizza"][1] + math.sin(angle) * 32
                        DrawingHelper.draw_circle3d(x, y, z, 6, (0.2, 0.2, 0.2))
                    z += 1
                elif topping == "oregano":
                    glPointSize(2.0)
                    glBegin(GL_POINTS)
                    glColor3f(0, 0.5, 0)
                    for i in range(100):
                        angle = i * 3.6 * math.pi / 180
                        distance = 20 + 25 * (i % 5) / 5.0
                        x = self.positions["pizza"][0] + math.cos(angle) * distance
                        y = self.positions["pizza"][1] + math.sin(angle) * distance
                        glVertex3f(x, y, z)
                    glEnd()
                    z += 1
        # Draw cooked pizza
        if game.state.bread_after_oven and not game.state.pizza_in_box:
            DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], 10, 53, (0.8, 0.6, 0.3))
            z = 11
            for topping in self.pizza_toppings:
                if topping == "sauce":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 49, (0.7, 0.15, 0.05))
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 47, (0.9, 0.8, 0.4))
                    z += 1
                elif topping == "sausage":
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 25, self.positions["pizza"][1] + 20, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 35, self.positions["pizza"][1] + 5, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 15, self.positions["pizza"][1] - 10, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza"][0] - 25, self.positions["pizza"][1] - 25, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    z += 1
                elif topping == "pepperoni":
                    for i in range(8):
                        angle = i * 45 * math.pi / 180
                        x = self.positions["pizza"][0] + math.cos(angle) * 30
                        y = self.positions["pizza"][1] + math.sin(angle) * 30
                        DrawingHelper.draw_circle3d(x, y, z, 7, (0.7, 0.35, 0.2))
                    z += 1
                elif topping == "onion":
                    for i in range(6):
                        angle = i * 60 * math.pi / 180
                        cx = self.positions["pizza"][0] + 20 * math.cos(angle)
                        cy = self.positions["pizza"][1] + 20 * math.sin(angle)
                        size = 18
                        glColor3f(0.3, .1, .5)
                        glBegin(GL_TRIANGLES)
                        glVertex3f(cx, cy, z)
                        glVertex3f(cx + size * math.cos(angle + 0.3), cy + size * math.sin(angle + 0.3), z)
                        glVertex3f(cx + size * math.cos(angle - 0.3), cy + size * math.sin(angle - 0.3), z)
                        glEnd()
                    z += 1
                elif topping == "black_olive":
                    for i in range(7):
                        angle = i * 51.4 * math.pi / 180
                        x = self.positions["pizza"][0] + math.cos(angle) * 32
                        y = self.positions["pizza"][1] + math.sin(angle) * 32
                        DrawingHelper.draw_circle3d(x, y, z, 6, (0.1, 0.1, 0.1))
                    z += 1
                elif topping == "oregano":
                    glPointSize(2.0)
                    glBegin(GL_POINTS)
                    glColor3f(0, 0.4, 0)
                    for i in range(100):
                        angle = i * 3.6 * math.pi / 180
                        distance = 20 + 25 * (i % 5) / 5.0
                        x = self.positions["pizza"][0] + math.cos(angle) * distance
                        y = self.positions["pizza"][1] + math.sin(angle) * distance
                        glVertex3f(x, y, z)
                    glEnd()
                    z += 1

    def draw_pizza_in_box(self):
        if game.state.pizza_in_box and (game.state.pizza_box_open or game.state.pizza_box_closed):
            # Draw pizza in box right above the box base
            DrawingHelper.draw_circle3d(
                self.positions["pizza_in_box"][0], 
                self.positions["pizza_in_box"][1], 
                self.positions["pizza_in_box"][2], 
                53, 
                (0.8, 0.6, 0.3)
            )
            
            # Draw toppings in the box
            z = self.positions["pizza_in_box"][2] + 1  # Start toppings just above pizza base
            for topping in self.pizza_toppings:
                if topping == "sauce":
                    DrawingHelper.draw_circle3d(
                        self.positions["pizza_in_box"][0], 
                        self.positions["pizza_in_box"][1], 
                        z, 
                        49, 
                        (0.7, 0.15, 0.05)
                    )
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza_in_box"][0], self.positions["pizza_in_box"][1], z, 47, (0.9, 0.8, 0.4))
                    z += 1
                elif topping == "sausage":
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 25, self.positions["pizza_in_box"][1] + 12, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 35, self.positions["pizza_in_box"][1] - 8, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 15, self.positions["pizza_in_box"][1] - 28, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 25, self.positions["pizza_in_box"][1] - 48, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    z += 1
                elif topping == "pepperoni":
                    for i in range(8):
                        angle = i * 45 * math.pi / 180
                        x = self.positions["pizza_in_box"][0] + math.cos(angle) * 30
                        y = self.positions["pizza_in_box"][1]-15 + math.sin(angle) * 30
                        DrawingHelper.draw_circle3d(x, y, z, 7, (0.7, 0.35, 0.2))
                    z += 1
                elif topping == "onion":
                    glColor3f(.3, .1, .5)
                    for i in range(7):
                        angle = i * 51.4 * math.pi / 180
                        cx = self.positions["pizza_in_box"][0] + math.cos(angle) * 25
                        cy = self.positions["pizza_in_box"][1]-15 + math.sin(angle) * 25
                        size = 18
                        glBegin(GL_TRIANGLES)
                        glVertex3f(cx, cy, z)
                        glVertex3f(cx + size * math.cos(angle + 0.3), cy + size * math.sin(angle + 0.3), z)
                        glVertex3f(cx + size * math.cos(angle - 0.3), cy + size * math.sin(angle - 0.3), z)
                        glEnd()
                    z += 1
                elif topping == "black_olive":
                    for i in range(7):
                        angle = i * 51.4 * math.pi / 180
                        x = self.positions["pizza_in_box"][0] + math.cos(angle) * 32
                        y = self.positions["pizza_in_box"][1]-15 + math.sin(angle) * 32
                        DrawingHelper.draw_circle3d(x, y, z, 6, (0.1, 0.1, 0.1))
                    z += 1
                elif topping == "oregano":
                    glPointSize(2.0)
                    glBegin(GL_POINTS)
                    glColor3f(0, 0.4, 0)
                    for i in range(100):
                        angle = i * 3.6 * math.pi / 180
                        distance = 20 + 25 * (i % 5) / 5.0
                        x = self.positions["pizza_in_box"][0] + math.cos(angle) * distance
                        y = self.positions["pizza_in_box"][1]-15 + math.sin(angle) * distance
                        glVertex3f(x, y, z)
                    glEnd()
                    z += 1
            glEnable(GL_DEPTH_TEST)

    def draw_oven(self):
        # Oven base: dark brown
        DrawingHelper.draw_rect3d(300 - 75, 0 - 75, 0, 150, 150, 60, (0.25, 0.13, 0.05))
        # Oven front: black
        DrawingHelper.draw_rect3d(300 - 60, 0 - 60, 60, 120, 120, 10, (0.0, 0.0, 0.0))
        # Oven door: black
        DrawingHelper.draw_rect3d(300 - 40, 0 - 40, 70, 80, 80, 5, (0.0, 0.0, 0.0))
        # Oven indicator: red if cooking, green if not
        if game.state.cooking_in_progress:
            DrawingHelper.draw_circle3d(300, 0 + 65, 80, 5, (1, 0, 0))
        else:
            DrawingHelper.draw_circle3d(300, 0 + 65, 80, 5, (0, 1, 0))
        DrawingHelper.draw_text3d(300 - 20, 0 + 85, 90, "OVEN")

    def draw_pizza_box(self):
        # Improved 3D pizza box with a real lid and sides
        base_z = 0
        base_height = 10
        side_thickness = 5
        side_height = 25
        lid_thickness = 3
        lid_length = 120
        box_w = 160
        box_d = 120

        box_x = 500  # Keep X position
        box_y = -100  # Adjusted from -150 to -100 to match new pizza_in_box position

        if game.state.pizza_box_open:
            # Draw base (bottom) - adjusted Y position
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z, box_w, box_d, base_height, (0.8, 0.6, 0.4))
            # Draw sides (left, right, front, back)
            # Left
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z + base_height, side_thickness, box_d, side_height, (0.7, 0.5, 0.3))
            # Right
            DrawingHelper.draw_rect3d(box_x + box_w//2 - side_thickness, box_y - box_d//2, base_z + base_height, side_thickness, box_d, side_height, (0.7, 0.5, 0.3))
            # Front
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z + base_height, box_w, side_thickness, side_height, (0.7, 0.5, 0.3))
            # Back
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y + box_d//2 - side_thickness, base_z + base_height, box_w, side_thickness, side_height, (0.7, 0.5, 0.3))
            # Draw lid (open, hinged at back, rotated up)
            glPushMatrix()
            glTranslatef(box_x, box_y + box_d//2, base_z + base_height + side_height)
            glRotatef(-80, 1, 0, 0)  # Open upwards, adjust angle as needed
            DrawingHelper.draw_rect3d(-box_w/2, -lid_thickness/2, 0, box_w, lid_thickness, lid_length, (0.9, 0.7, 0.5))
            glPopMatrix()
            # Draw a handle on the lid
            glPushMatrix()
            glTranslatef(box_x, box_y + box_d//2 + 2, base_z + base_height + side_height + lid_length - 10)
            glRotatef(-80, 1, 0, 0)
            DrawingHelper.draw_circle3d(0, 0, 2, 10, (0.6, 0.4, 0.2))
            glPopMatrix()
            # Label
            DrawingHelper.draw_text3d(box_x - 30, box_y + 110, base_z + base_height + side_height + 10, "OPEN BOX")
        elif game.state.pizza_box_closed:
            # Closed box: a thick box with a slightly raised lid
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z, box_w, box_d, base_height + side_height, (0.8, 0.6, 0.4))
            # Slightly raised lid
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z + base_height + side_height, box_w, box_d, lid_thickness, (0.9, 0.7, 0.5))
            DrawingHelper.draw_text3d(box_x - 40, box_y, base_z + base_height + side_height + lid_thickness + 10, "CLOSED BOX")

    def draw_instructions(self):
        instructions = [
            "Press 'R' to restart",
            "Click on open box to close it after placing pizza",
            "Click on cooked pizza to place it in the open box",
            "Click on oven to cook pizza (2 seconds)",
            "Click once pizza to apply selected toppings",
            "Click once toppings to select them",
            "Click on dough to place it on the table"
        ]
        y_pos = -250
        for line in instructions:
            DrawingHelper.draw_text3d(-150, y_pos, 100, line)
            y_pos += 20

    def update_cooking(self):
        if game.state.cooking_in_progress:
            current_time = time.time()
            if current_time - game.state.cooking_start_time >= game.state.cooking_duration:
                game.state.cooking_in_progress = False
                game.state.bread_before_oven = False
                game.state.bread_after_oven = True
    
    def handle_click(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            c_X, c_y, c_z = self.convert_coordinate(x, y)
            # Improved click accuracy: use true object bounds (circle/rect)
            # Dough (circle)
            dx = c_X - self.positions["dough"][0]
            dy = c_y - self.positions["dough"][1]
            if math.hypot(dx, dy) < 60:
                if not game.state.bread_before_oven and not game.state.bread_after_oven and not game.state.pizza_in_box:
                    game.state.bread_before_oven = True
                    self.pizza_toppings = []

            # Toppings (circle)
            for topping, position in self.positions["toppings"].items():
                dx = c_X - position[0]
                dy = c_y - position[1]
                # Only allow selection if not already used
                if math.hypot(dx, dy) < 40 and topping not in self.pizza_toppings:
                    game.state.toppings[topping] = not game.state.toppings[topping]

            # Pizza (circle)
            dx = c_X - self.positions["pizza"][0]
            dy = c_y - self.positions["pizza"][1]
            if game.state.bread_before_oven and not game.state.cooking_in_progress:
                if math.hypot(dx, dy) < 53:
                    # Add toppings in the order clicked (append to end)
                    for topping, selected in game.state.toppings.items():
                        if selected and topping not in self.pizza_toppings:
                            self.pizza_toppings.append(topping)
                            game.state.toppings[topping] = False

            # Oven (rectangle, top face)
            oven_cx, oven_cy = 300, 0
            oven_w, oven_h = 150, 150
            if game.state.bread_before_oven and not game.state.cooking_in_progress and not game.state.bread_after_oven:
                if (oven_cx - oven_w//2 <= c_X <= oven_cx + oven_w//2 and
                    oven_cy - oven_h//2 <= c_y <= oven_cy + oven_h//2):
                    game.state.cooking_in_progress = True
                    game.state.cooking_start_time = time.time()

            # Move pizza to box (circle)
            dx = c_X - self.positions["pizza"][0]
            dy = c_y - self.positions["pizza"][1]
            if game.state.bread_after_oven and not game.state.pizza_in_box:
                if math.hypot(dx, dy) < 53:
                    game.state.bread_after_oven = False
                    game.state.pizza_in_box = True
                    game.state.pizza_box_open = True
                    game.state.pizza_box_closed = False

            # Close box (rectangle)
            bx, by = 500, -150
            box_w, box_h = 160, 120
            if game.state.pizza_in_box and game.state.pizza_box_open:
                if (bx - box_w//2 <= c_X <= bx + box_w//2 and
                    by - box_h//2 <= c_y <= by + box_h//2):
                    game.state.pizza_in_box = False
                    game.state.pizza_box_open = False
                    game.state.pizza_box_closed = True
                    game.state.game_over = True  # Prevent further pizza making

    def convert_coordinate(self, x, y):
        # Convert screen (window) x, y to world x, y at z=0 plane using gluUnProject
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        winX = float(x)
        winY = float(viewport[3] - y)
        # Read depth at mouse position (optional, but we want z=0 plane)
        # winZ = glReadPixels(x, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        # Use winZ = 0 for near plane, but we want intersection with z=0 plane
        # So, unproject at winZ=0 (near) and winZ=1 (far), then interpolate
        near = gluUnProject(winX, winY, 0.0, modelview, projection, viewport)
        far = gluUnProject(winX, winY, 1.0, modelview, projection, viewport)
        # Ray: near + t*(far-near), solve for t where z=0
        dz = far[2] - near[2]
        if abs(dz) < 1e-6:
            t = 0
        else:
            t = -near[2] / dz
        wx = near[0] + t * (far[0] - near[0])
        wy = near[1] + t * (far[1] - near[1])
        return wx, wy, 0

class DrawingHelper:
    @staticmethod
    def draw_circle3d(x, y, z, radius, color):
        glColor3f(*color)
        glBegin(GL_POLYGON)
        for i in range(360):
            angle = i * math.pi / 180
            glVertex3f(x + radius * math.cos(angle), y + radius * math.sin(angle), z)
        glEnd()

    @staticmethod
    def draw_rect3d(x, y, z, width, height, depth, color):
        glColor3f(*color)
        # Draw a flat rectangle at z
        glBegin(GL_QUADS)
        glVertex3f(x, y, z)
        glVertex3f(x + width, y, z)
        glVertex3f(x + width, y + height, z)
        glVertex3f(x, y + height, z)
        glEnd()
        # Optionally extrude for depth
        if depth > 0:
            # Draw sides (simple box)
            glBegin(GL_QUADS)
            # Front
            glVertex3f(x, y, z)
            glVertex3f(x + width, y, z)
            glVertex3f(x + width, y, z + depth)
            glVertex3f(x, y, z + depth)
            # Back
            glVertex3f(x, y + height, z)
            glVertex3f(x + width, y + height, z)
            glVertex3f(x + width, y + height, z + depth)
            glVertex3f(x, y + height, z + depth)
            # Left
            glVertex3f(x, y, z)
            glVertex3f(x, y + height, z)
            glVertex3f(x, y + height, z + depth)
            glVertex3f(x, y, z + depth)
            # Right
            glVertex3f(x + width, y, z)
            glVertex3f(x + width, y + height, z)
            glVertex3f(x + width, y + height, z + depth)
            glVertex3f(x + width, y, z + depth)
            glEnd()

    @staticmethod
    def draw_text3d(x, y, z, text):
        glColor3f(0, 0, 0)
        glRasterPos3f(x, y, z)
        for c in text:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    @staticmethod
    def draw_platform():
        DrawingHelper.draw_rect3d(-900, -350, -60, 1800, 700, 40, (0.5, 0.5, 0.5))

    @staticmethod
    def draw_background():
        DrawingHelper.draw_rect3d(-900, -350, -100, 1800, 700, 0, (0.4, 0.7, 1))

def main():
    global game
    game = PizzaGame()
    game.run()

if __name__ == '__main__':
    main()