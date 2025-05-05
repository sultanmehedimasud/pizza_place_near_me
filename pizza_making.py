from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import sys

# --- Camera class for 3D view ---
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

camera = Camera()

# Window dimensions
W_Width, W_Height = 1200, 600

# Game state variables
toppings = {
    "sauce": False,
    "cheese": False,
    "sausage": False,
    "pepperoni": False,
    "onion": False,
    "black_olive": False,
    "oregano": False
}

# Pizza state
bread_before_oven = False
bread_after_oven = False
pizza_in_box = False
pizza_box_open = True
pizza_box_closed = False

# Add game_over flag
game_over = False

# Cooking timer variables
cooking_start_time = 0
cooking_in_progress = False
cooking_duration = 2  # 2 seconds

# --- All positions now have z=0 ---
dough_position = (-300, 0, 0)
pizza_position = (-300, 40, 0)
pizza_in_box_position = (500, -150, 0)

# Increase spacing between toppings
topping_positions = {
    "sauce": (-600, 200, 0),
    "cheese": (-470, 200, 0),
    "sausage": (-340, 200, 0),
    "pepperoni": (-210, 200, 0),
    "onion": (-80, 200, 0),
    "black_olive": (50, 200, 0),
    "oregano": (180, 200, 0)
}

dough_position_display = (-440, -150, 0)
oven_position = (300, 0, 0)
box_position = (500, -150, 0)

pizza_toppings = []

instructions = [
    "Press 'R' to restart",
    "Click on open box to close it after placing pizza",
    "Click on cooked pizza to place it in the open box",
    "Click on oven to cook pizza (2 seconds)",
    "Click once pizza to apply selected toppings",
    "Click once toppings to select them",
    "Click on dough to place it on the table"
]

# --- 3D Drawing helpers ---
def draw_circle3d(x, y, z, radius, color):
    glColor3f(*color)
    glBegin(GL_POLYGON)
    for i in range(360):
        angle = i * math.pi / 180
        glVertex3f(x + radius * math.cos(angle), y + radius * math.sin(angle), z)
    glEnd()

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

def draw_text3d(x, y, z, text):
    glColor3f(0, 0, 0)
    glRasterPos3f(x, y, z)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

# --- 3D versions of all draw functions ---
def draw_dough():
    # Draw pizza board below the pizza (z=5)
    draw_rect3d(pizza_position[0] - 60, pizza_position[1] - 60, 5, 120, 120, 10, (0.5, 0.35, 0.18))
    draw_text3d(pizza_position[0] - 50, pizza_position[1] - 80, 20, "Pizza Board")
    # Draw dough on the left (z=10)
    draw_rect3d(dough_position_display[0] - 70, dough_position_display[1] - 70, 0, 140, 140, 10, (0.5, 0.4, 0.5))
    draw_circle3d(dough_position_display[0], dough_position_display[1], 10, 60, (0.9, 0.8, 0.7))
    draw_text3d(dough_position_display[0] - 20, dough_position_display[1] - 80, 20, "Dough")

def draw_toppings_bar():
    # Make the bar wider to fit the new spacing
    draw_rect3d(-700, 350, 0, 1100, -750, 10, (0.7, 0.5, 0.3))
    for topping, pos in topping_positions.items():
        draw_rect3d(pos[0] - 45, pos[1] - 45, 0, 90, 90, 10, (0.7, 0.5, 0.3))
        if topping == "sauce":
            draw_circle3d(pos[0], pos[1], 10, 40, (1, 0, 0))
            draw_text3d(pos[0] - 30, pos[1] - 70, 20, "Sauce")
        elif topping == "cheese":
            draw_circle3d(pos[0], pos[1], 10, 40, (1, 1, 0))
            draw_text3d(pos[0] - 36, pos[1] - 70, 20, "Cheese")
        elif topping == "sausage":
            draw_circle3d(pos[0], pos[1], 10, 40, (0.6, 0.3, 0))
            draw_rect3d(pos[0] - 25, pos[1] + 20, 12, 50, 5, 3, (0.5, 0.2, 0.1))
            draw_rect3d(pos[0] - 35, pos[1] + 5, 12, 50, 5, 3, (0.5, 0.2, 0.1))
            draw_rect3d(pos[0] - 15, pos[1] - 10, 12, 50, 5, 3, (0.5, 0.2, 0.1))
            draw_rect3d(pos[0] - 25, pos[1] - 25, 12, 50, 5, 3, (0.5, 0.2, 0.1))
            draw_text3d(pos[0] - 39, pos[1] - 70, 20, "Sausage")
        elif topping == "pepperoni":
            draw_circle3d(pos[0], pos[1], 10, 40, (1.0, 0.5, 0.0))
            offsets = [(-15, 10), (10, 15), (-10, -15), (15, -10)]
            for dx, dy in offsets:
                draw_circle3d(pos[0] + dx, pos[1] + dy, 12, 9, (0.9, 0.2, 0.2))
            draw_text3d(pos[0] - 47, pos[1] - 70, 20, "Pepperoni")
        elif topping == "onion":
            draw_circle3d(pos[0], pos[1], 10, 40, (1, 0, 1))
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
            draw_text3d(pos[0] - 18, pos[1] - 70, 20, "Onion")
        elif topping == "black_olive":
            draw_circle3d(pos[0], pos[1], 10, 40, (0, 0, 0))
            draw_circle3d(pos[0]-10, pos[1]+15, 12, 5, (.2, .2, .2))
            draw_circle3d(pos[0]+10, pos[1]+27, 12, 8, (.2, .2, .2))
            draw_circle3d(pos[0]-18, pos[1]-18, 12, 4, (.2, 0.2, 0.2))
            draw_circle3d(pos[0]+20, pos[1]-20, 12, 6, (0.2, 0.2, 0.2))
            draw_text3d(pos[0] - 27, pos[1] - 70, 20, "Olives")
        elif topping == "oregano":
            draw_circle3d(pos[0], pos[1], 10, 40, (1, 1, 1))
            draw_circle3d(pos[0] + 10, pos[1] + 15, 12, 5, (0, 0.7, 0))
            draw_circle3d(pos[0] - 12, pos[1] + 25, 12, 8, (0, 0.7, 0))
            draw_circle3d(pos[0] + 18, pos[1] + 20, 12, 6, (0, 0.7, 0))
            draw_circle3d(pos[0] - 20, pos[1] - 15, 12, 4, (0, 0.7, 0))
            draw_circle3d(pos[0] + 25, pos[1] - 10, 12, 7, (0, 0.7, 0))
            draw_circle3d(pos[0] - 15, pos[1] - 20, 12, 6, (0, 0.7, 0))
            draw_circle3d(pos[0] + 5, pos[1] + 30, 12, 5, (0, 0.7, 0))
            draw_text3d(pos[0] - 30, pos[1] - 70, 20, "Oregano")
        if toppings[topping] and topping not in pizza_toppings:
            glLineWidth(3.0)
            glColor3f(1, 0.5, 0)
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = i * math.pi / 180
                glVertex3f(pos[0] + 28 * math.cos(angle), pos[1] + 28 * math.sin(angle), 20)
            glEnd()

def draw_pizza():
    if bread_before_oven and not cooking_in_progress:
        # Draw base pizza dough
        draw_circle3d(pizza_position[0], pizza_position[1], 10, 53, (0.9, 0.8, 0.7))
        # Draw toppings in the order they were added (bottom to top)
        z = 11
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle3d(pizza_position[0], pizza_position[1], z, 49, (0.8, 0.2, 0.1))
                z += 1
            elif topping == "cheese":
                draw_circle3d(pizza_position[0], pizza_position[1], z, 47, (1.0, 0.9, 0.4))
                z += 1
            elif topping == "sausage":
                draw_rect3d(pizza_position[0] - 25, pizza_position[1] + 20, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 35, pizza_position[1] + 5, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 15, pizza_position[1] - 10, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 25, pizza_position[1] - 25, z, 50, 5, 3, (0.5, 0.2, 0.1))
                z += 1
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 30
                    y = pizza_position[1] + math.sin(angle) * 30
                    draw_circle3d(x, y, z, 7, (1.0, 0.5, 0.0))
                z += 1
            elif topping == "onion":
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    cx = pizza_position[0] + 20 * math.cos(angle)
                    cy = pizza_position[1] + 20 * math.sin(angle)
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
                    x = pizza_position[0] + math.cos(angle) * 32
                    y = pizza_position[1] + math.sin(angle) * 32
                    draw_circle3d(x, y, z, 6, (0.2, 0.2, 0.2))
                z += 1
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.5, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_position[0] + math.cos(angle) * distance
                    y = pizza_position[1] + math.sin(angle) * distance
                    glVertex3f(x, y, z)
                glEnd()
                z += 1
    # Draw cooked pizza
    if bread_after_oven and not pizza_in_box:
        draw_circle3d(pizza_position[0], pizza_position[1], 10, 53, (0.8, 0.6, 0.3))
        z = 11
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle3d(pizza_position[0], pizza_position[1], z, 49, (0.7, 0.15, 0.05))
                z += 1
            elif topping == "cheese":
                draw_circle3d(pizza_position[0], pizza_position[1], z, 47, (0.9, 0.8, 0.4))
                z += 1
            elif topping == "sausage":
                draw_rect3d(pizza_position[0] - 25, pizza_position[1] + 20, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 35, pizza_position[1] + 5, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 15, pizza_position[1] - 10, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_position[0] - 25, pizza_position[1] - 25, z, 50, 5, 3, (0.5, 0.2, 0.1))
                z += 1
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 30
                    y = pizza_position[1] + math.sin(angle) * 30
                    draw_circle3d(x, y, z, 7, (0.7, 0.35, 0.2))
                z += 1
            elif topping == "onion":
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    cx = pizza_position[0] + 20 * math.cos(angle)
                    cy = pizza_position[1] + 20 * math.sin(angle)
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
                    x = pizza_position[0] + math.cos(angle) * 32
                    y = pizza_position[1] + math.sin(angle) * 32
                    draw_circle3d(x, y, z, 6, (0.1, 0.1, 0.1))
                z += 1
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.4, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_position[0] + math.cos(angle) * distance
                    y = pizza_position[1] + math.sin(angle) * distance
                    glVertex3f(x, y, z)
                glEnd()
                z += 1

def draw_pizza_in_box():
    if pizza_in_box and (pizza_box_open or pizza_box_closed):
        # Disable depth test so pizza is always drawn on top of the box base
        glDisable(GL_DEPTH_TEST)
        # Draw pizza in box only if the box is visible
        draw_circle3d(pizza_in_box_position[0], pizza_in_box_position[1]-15, 30, 53, (0.8, 0.6, 0.3))
        # Draw toppings in the box, using same z as pizza so they are not faded
        z = 31
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle3d(pizza_in_box_position[0], pizza_in_box_position[1]-15, z, 49, (0.7, 0.15, 0.05))
                z += 1
            elif topping == "cheese":
                draw_circle3d(pizza_in_box_position[0], pizza_in_box_position[1]-15, z, 47, (0.9, 0.8, 0.4))
                z += 1
            elif topping == "sausage":
                draw_rect3d(pizza_in_box_position[0] - 25, pizza_in_box_position[1] + 12, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_in_box_position[0] - 35, pizza_in_box_position[1] - 8, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_in_box_position[0] - 15, pizza_in_box_position[1] - 28, z, 50, 5, 3, (0.5, 0.2, 0.1))
                draw_rect3d(pizza_in_box_position[0] - 25, pizza_in_box_position[1] - 48, z, 50, 5, 3, (0.5, 0.2, 0.1))
                z += 1
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 30
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 30
                    draw_circle3d(x, y, z, 7, (0.7, 0.35, 0.2))
                z += 1
            elif topping == "onion":
                glColor3f(.3, .1, .5)
                for i in range(7):
                    angle = i * 51.4 * math.pi / 180
                    cx = pizza_in_box_position[0] + math.cos(angle) * 25
                    cy = pizza_in_box_position[1]-15 + math.sin(angle) * 25
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
                    x = pizza_in_box_position[0] + math.cos(angle) * 32
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 32
                    draw_circle3d(x, y, z, 6, (0.1, 0.1, 0.1))
                z += 1
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.4, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_in_box_position[0] + math.cos(angle) * distance
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * distance
                    glVertex3f(x, y, z)
                glEnd()
                z += 1
        glEnable(GL_DEPTH_TEST)

def draw_oven():
    # Oven base: dark brown
    draw_rect3d(oven_position[0] - 75, oven_position[1] - 75, 0, 150, 150, 60, (0.25, 0.13, 0.05))
    # Oven front: black
    draw_rect3d(oven_position[0] - 60, oven_position[1] - 60, 60, 120, 120, 10, (0.0, 0.0, 0.0))
    # Oven door: black
    draw_rect3d(oven_position[0] - 40, oven_position[1] - 40, 70, 80, 80, 5, (0.0, 0.0, 0.0))
    # Oven indicator: red if cooking, green if not
    if cooking_in_progress:
        draw_circle3d(oven_position[0], oven_position[1] + 65, 80, 5, (1, 0, 0))
    else:
        draw_circle3d(oven_position[0], oven_position[1] + 65, 80, 5, (0, 1, 0))
    draw_text3d(oven_position[0] - 20, oven_position[1] + 85, 90, "OVEN")

def draw_pizza_box():
    # Improved 3D pizza box with a real lid and sides
    base_z = 0
    base_height = 10
    side_thickness = 5
    side_height = 25
    lid_thickness = 3
    lid_length = 120
    box_w = 160
    box_d = 120

    if pizza_box_open:
        # Draw base (bottom)
        draw_rect3d(box_position[0] - box_w//2, box_position[1] - box_d//2, base_z, box_w, box_d, base_height, (0.8, 0.6, 0.4))
        # Draw sides (left, right, front, back)
        # Left
        draw_rect3d(box_position[0] - box_w//2, box_position[1] - box_d//2, base_z + base_height, side_thickness, box_d, side_height, (0.7, 0.5, 0.3))
        # Right
        draw_rect3d(box_position[0] + box_w//2 - side_thickness, box_position[1] - box_d//2, base_z + base_height, side_thickness, box_d, side_height, (0.7, 0.5, 0.3))
        # Front
        draw_rect3d(box_position[0] - box_w//2, box_position[1] - box_d//2, base_z + base_height, box_w, side_thickness, side_height, (0.7, 0.5, 0.3))
        # Back
        draw_rect3d(box_position[0] - box_w//2, box_position[1] + box_d//2 - side_thickness, base_z + base_height, box_w, side_thickness, side_height, (0.7, 0.5, 0.3))
        # Draw lid (open, hinged at back, rotated up)
        glPushMatrix()
        glTranslatef(box_position[0], box_position[1] + box_d//2, base_z + base_height + side_height)
        glRotatef(-80, 1, 0, 0)  # Open upwards, adjust angle as needed
        draw_rect3d(-box_w/2, -lid_thickness/2, 0, box_w, lid_thickness, lid_length, (0.9, 0.7, 0.5))
        glPopMatrix()
        # Draw a handle on the lid
        glPushMatrix()
        glTranslatef(box_position[0], box_position[1] + box_d//2 + 2, base_z + base_height + side_height + lid_length - 10)
        glRotatef(-80, 1, 0, 0)
        draw_circle3d(0, 0, 2, 10, (0.6, 0.4, 0.2))
        glPopMatrix()
        # Label
        draw_text3d(box_position[0] - 30, box_position[1] + 110, base_z + base_height + side_height + 10, "OPEN BOX")
    elif pizza_box_closed:
        # Closed box: a thick box with a slightly raised lid
        draw_rect3d(box_position[0] - box_w//2, box_position[1] - box_d//2, base_z, box_w, box_d, base_height + side_height, (0.8, 0.6, 0.4))
        # Slightly raised lid
        draw_rect3d(box_position[0] - box_w//2, box_position[1] - box_d//2, base_z + base_height + side_height, box_w, box_d, lid_thickness, (0.9, 0.7, 0.5))
        draw_text3d(box_position[0] - 40, box_position[1], base_z + base_height + side_height + lid_thickness + 10, "CLOSED BOX")

def draw_instructions():
    y_pos = -250
    for line in instructions:
        draw_text3d(-150, y_pos, 100, line)
        y_pos += 20

# --- 3D Mouse coordinate conversion (improved for perspective) ---
def convert_coordinate(x, y):
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

# Modify this function:
def keyboardListener(key, x, y):
    global pizza_box_open, pizza_box_closed, pizza_in_box
    global bread_before_oven, bread_after_oven, pizza_toppings, toppings
    global game_over

    if key == b'R' or key == b'r':  # Restart
        pizza_box_open = True
        pizza_box_closed = False
        pizza_in_box = False
        bread_before_oven = False
        bread_after_oven = False
        pizza_toppings = []
        for topping in toppings:
            toppings[topping] = False
        game_over = False

    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global bread_before_oven, bread_after_oven, pizza_box_open, pizza_box_closed
    global pizza_in_box, cooking_in_progress, cooking_start_time, pizza_toppings
    global game_over

    if game_over:
        return

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        glutSetWindow(glutGetWindow())
        c_X, c_y, c_z = convert_coordinate(x, y)

        # Improved click accuracy: use true object bounds (circle/rect)
        # Dough (circle)
        dx = c_X - dough_position_display[0]
        dy = c_y - dough_position_display[1]
        if math.hypot(dx, dy) < 60:
            if not bread_before_oven and not bread_after_oven and not pizza_in_box:
                bread_before_oven = True
                pizza_toppings = []

        # Toppings (circle)
        for topping, position in topping_positions.items():
            dx = c_X - position[0]
            dy = c_y - position[1]
            # Only allow selection if not already used
            if math.hypot(dx, dy) < 40 and topping not in pizza_toppings:
                toppings[topping] = not toppings[topping]

        # Pizza (circle)
        dx = c_X - pizza_position[0]
        dy = c_y - pizza_position[1]
        if bread_before_oven and not cooking_in_progress:
            if math.hypot(dx, dy) < 53:
                # Add toppings in the order clicked (append to end)
                for topping, selected in toppings.items():
                    if selected and topping not in pizza_toppings:
                        pizza_toppings.append(topping)
                        toppings[topping] = False

        # Oven (rectangle, top face)
        oven_cx, oven_cy = oven_position[0], oven_position[1]
        oven_w, oven_h = 150, 150
        if bread_before_oven and not cooking_in_progress and not bread_after_oven:
            if (oven_cx - oven_w//2 <= c_X <= oven_cx + oven_w//2 and
                oven_cy - oven_h//2 <= c_y <= oven_cy + oven_h//2):
                cooking_in_progress = True
                cooking_start_time = time.time()

        # Move pizza to box (circle)
        dx = c_X - pizza_position[0]
        dy = c_y - pizza_position[1]
        if bread_after_oven and not pizza_in_box:
            if math.hypot(dx, dy) < 53:
                bread_after_oven = False
                pizza_in_box = True
                pizza_box_open = True
                pizza_box_closed = False

        # Close box (rectangle)
        bx, by = box_position[0], box_position[1]
        box_w, box_h = 160, 120
        if pizza_in_box and pizza_box_open:
            if (bx - box_w//2 <= c_X <= bx + box_w//2 and
                by - box_h//2 <= c_y <= by + box_h//2):
                pizza_in_box = False
                pizza_box_open = False
                pizza_box_closed = True
                game_over = True  # Prevent further pizza making

        glutPostRedisplay()

# Basic drawing functions
def draw_circle(x, y, radius, color):
    glColor3f(*color)
    glBegin(GL_POLYGON)
    for i in range(360):
        angle = i * math.pi / 180
        glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
    glEnd()

def draw_rect(x, y, width, height, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def draw_text(x, y, text):
    glColor3f(0, 0, 0)
    glRasterPos2f(x, y)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

# Remove automatic box reopen
def check_timers(value):
    global cooking_in_progress, bread_before_oven, bread_after_oven

    if cooking_in_progress:
        current_time = time.time()
        if current_time - cooking_start_time >= cooking_duration:
            cooking_in_progress = False
            bread_before_oven = False
            bread_after_oven = True

    glutPostRedisplay()
    glutTimerFunc(100, check_timers, 0)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    camera.position_camera()
    # Platform: bigger, thicker, and a distinct color (e.g., grayish)
    draw_rect3d(-900, -350, -60, 1800, 700, 40, (0.5, 0.5, 0.5))
    # Background behind the platform
    draw_rect3d(-900, -350, -100, 1800, 700, 0, (0.4, 0.7, 1))
    draw_toppings_bar()
    draw_dough()
    draw_instructions()
    draw_oven()
    draw_pizza_box()
    draw_pizza()
    draw_pizza_in_box()
    glutSwapBuffers()

# Initialization
def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    camera.setup()

# Start OpenGL
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(W_Width, W_Height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Pizza Making Game")

# Register
init()
glutDisplayFunc(display)
glutKeyboardFunc(keyboardListener)
glutMouseFunc(mouseListener)
glutTimerFunc(100, check_timers, 0)

# Run main loop
glutMainLoop()