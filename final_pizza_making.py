from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import sys

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
pizza_box_open = True     # Open box is visible from start
pizza_box_closed = False

# Cooking timer variables
cooking_start_time = 0
cooking_in_progress = False
cooking_duration = 2  # 2 seconds

# Positions
dough_position = (-300, 0)
pizza_position = (-300, 40)
pizza_in_box_position = (500, -150)

topping_positions = {
    "sauce": (-500, 200),
    "cheese": (-400, 200),
    "sausage": (-300, 200),
    "pepperoni": (-200, 200),
    "onion": (-100, 200),
    "black_olive": (0, 200),
    "oregano": (100, 200)
}

dough_position_display = (-440, -150)
oven_position = (300, 0)
box_position = (500, -150)

# Applied toppings on pizza
pizza_toppings = []

instructions = [
    "Press 'R' to restart for a new customer",
    "Click on open box to close it after placing pizza",
    "Click on cooked pizza to place it in the open box",
    "Click on oven to cook pizza (2 seconds)",
    "Click once pizza to apply selected toppings",
    "Click once toppings to select them",
    "Click on dough to place it on the table"
]

# Convert window coordinates to OpenGL coordinates
def convert_coordinate(x, y):
    a = x - (W_Width / 2)
    b = (W_Height / 2) - y
    return a, b

# Modify this function:
def keyboardListener(key, x, y):
    global pizza_box_open, pizza_box_closed, pizza_in_box
    global bread_before_oven, bread_after_oven, pizza_toppings, toppings

    if key == b'R' or key == b'r':  # Restart
        pizza_box_open = True
        pizza_box_closed = False
        pizza_in_box = False
        bread_before_oven = False
        bread_after_oven = False
        pizza_toppings = []
        for topping in toppings:
            toppings[topping] = False

    glutPostRedisplay()

# Mouse logic remains mostly the same with the open/close box fix
def mouseListener(button, state, x, y):
    global bread_before_oven, bread_after_oven, pizza_box_open, pizza_box_closed
    global pizza_in_box, cooking_in_progress, cooking_start_time, pizza_toppings

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        c_X, c_y = convert_coordinate(x, y)

        if abs(c_X - dough_position_display[0]) < 40 and abs(c_y - dough_position_display[1]) < 40:
            if not bread_before_oven and not bread_after_oven and not pizza_in_box:
                bread_before_oven = True
                pizza_toppings = []

        for topping, position in topping_positions.items():
            if abs(c_X - position[0]) < 25 and abs(c_y - position[1]) < 25:
                toppings[topping] = not toppings[topping]

        if bread_before_oven and not cooking_in_progress:
            if abs(c_X - pizza_position[0]) < 50 and abs(c_y - pizza_position[1]) < 50:
                for topping, selected in toppings.items():
                    if selected and topping not in pizza_toppings:
                        pizza_toppings.append(topping)
                        toppings[topping] = False

        if bread_before_oven and not cooking_in_progress and not bread_after_oven:
            if abs(c_X - oven_position[0]) < 75 and abs(c_y - oven_position[1]) < 75:
                cooking_in_progress = True
                cooking_start_time = time.time()

        if bread_after_oven and not pizza_in_box:
            if abs(c_X - pizza_position[0]) < 50 and abs(c_y - pizza_position[1]) < 50:
                bread_after_oven = False
                pizza_in_box = True
                pizza_box_open = True
                pizza_box_closed = False

        if pizza_in_box and pizza_box_open:
            if abs(c_X - box_position[0]) < 70 and abs(c_y - box_position[1]) < 60:
                pizza_in_box = False
                pizza_box_open = False
                pizza_box_closed = True

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

# Draw game elements
def draw_dough():
    draw_rect(dough_position_display[0] - 70, dough_position_display[1] - 70, 140, 140, (0.5, 0.4, 0.5))
    draw_circle(dough_position_display[0], dough_position_display[1], 60, (0.9, 0.8, 0.7))
    draw_text(dough_position_display[0] - 20, dough_position_display[1] - 80, "Dough")
    draw_rect(pizza_position[0] - 60, pizza_position[1] - 60, 120, 120, (0.4, 0.3, 0.2) ) # pizza board
    draw_text(pizza_position[0] - 50, pizza_position[1] - 80, "Pizza Board")

def draw_toppings_bar():
    # Background for toppings
    draw_rect(-600, 350, 800, -750, (0.7, 0.4, 0.6))
    
    # Draw individual toppings
    for topping, position in topping_positions.items():
        # Draw square box for the topping
        draw_rect(position[0] - 45, position[1] - 45, 90, 90, (0.5, 0.4, 0.5))
        if topping == "sauce":
            draw_circle(position[0], position[1], 40, (1, 0, 0))
            draw_text(position[0] - 20, position[1] - 60, "Sauce")
        elif topping == "cheese":
            draw_circle(position[0], position[1], 40, (1, 1, 0))
            draw_text(position[0] - 26, position[1] - 60, "Cheese")
        elif topping == "sausage":
            draw_circle(position[0], position[1], 40, (0.6, 0.3, 0))
            draw_text(position[0] - 29, position[1] - 60, "Sausage")
        elif topping == "pepperoni":
            draw_circle(position[0], position[1], 40, (1.0, 0.5, 0.0))
            draw_text(position[0] - 37, position[1] - 60, "Pepperoni")
        elif topping == "onion":
            draw_circle(position[0], position[1], 40, (1, 1, 1))
            draw_text(position[0] - 22, position[1] - 60, "Onion")
        elif topping == "black_olive":
            draw_circle(position[0], position[1], 40, (0, 0, 0))
            draw_text(position[0] - 27, position[1] - 60, "Olives")
        elif topping == "oregano":
            draw_circle(position[0], position[1], 40, (0, 0.5, 0))
            draw_text(position[0] - 30, position[1] - 60, "Oregano")
        
        # Highlight selected toppings
        if toppings[topping]:
            glLineWidth(3.0)
            glColor3f(1, 0.5, 0)
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = i * math.pi / 180
                glVertex2f(position[0] + 28 * math.cos(angle), position[1] + 28 * math.sin(angle))
            glEnd()

def draw_pizza():
    if bread_before_oven and not cooking_in_progress:
        # Draw base pizza dough
        draw_circle(pizza_position[0], pizza_position[1], 53, (0.9, 0.8, 0.7))
        
        # Draw applied toppings
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle(pizza_position[0], pizza_position[1], 48, (0.8, 0.2, 0.1))
            elif topping == "cheese":
                draw_circle(pizza_position[0], pizza_position[1], 45, (1.0, 0.9, 0.4))
            elif topping == "sausage":
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 25
                    y = pizza_position[1] + math.sin(angle) * 25
                    draw_circle(x, y, 8, (0.6, 0.3, 0))
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 30
                    y = pizza_position[1] + math.sin(angle) * 30
                    draw_circle(x, y, 7, (1.0, 0.5, 0.0))
            elif topping == "onion":
                for i in range(10):
                    angle = i * 36 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 35
                    y = pizza_position[1] + math.sin(angle) * 35
                    draw_circle(x, y, 5, (1, 0.9, 0.9))
            elif topping == "black_olive":
                for i in range(7):
                    angle = i * 51.4 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 32
                    y = pizza_position[1] + math.sin(angle) * 32
                    draw_circle(x, y, 6, (0.2, 0.2, 0.2))
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.5, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_position[0] + math.cos(angle) * distance
                    y = pizza_position[1] + math.sin(angle) * distance
                    glVertex2f(x, y)
                glEnd()
    
    # Draw cooked pizza
    if bread_after_oven and not pizza_in_box:
        # Draw cooked base
        draw_circle(pizza_position[0], pizza_position[1], 53, (0.8, 0.6, 0.3))
        
        # Draw applied toppings with cooked appearance
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle(pizza_position[0], pizza_position[1], 48, (0.7, 0.15, 0.05))
            elif topping == "cheese":
                draw_circle(pizza_position[0], pizza_position[1], 45, (0.9, 0.8, 0.4))
            elif topping == "sausage":
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 25
                    y = pizza_position[1] + math.sin(angle) * 25
                    draw_circle(x, y, 8, (0.5, 0.25, 0))
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 30
                    y = pizza_position[1] + math.sin(angle) * 30
                    draw_circle(x, y, 7, (0.7, 0.5, 0.0))
            elif topping == "onion":
                for i in range(10):
                    angle = i * 36 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 35
                    y = pizza_position[1] + math.sin(angle) * 35
                    draw_circle(x, y, 5, (0.9, 0.8, 0.7))
            elif topping == "black_olive":
                for i in range(7):
                    angle = i * 51.4 * math.pi / 180
                    x = pizza_position[0] + math.cos(angle) * 32
                    y = pizza_position[1] + math.sin(angle) * 32
                    draw_circle(x, y, 6, (0.1, 0.1, 0.1))
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.4, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_position[0] + math.cos(angle) * distance
                    y = pizza_position[1] + math.sin(angle) * distance
                    glVertex2f(x, y)
                glEnd()

def draw_pizza_in_box():
    if pizza_in_box and (pizza_box_open or pizza_box_closed):
        # Draw pizza in box only if the box is visible
        draw_circle(pizza_in_box_position[0], pizza_in_box_position[1]-15, 53, (0.8, 0.6, 0.3))
        
        # Draw toppings in the box
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle(pizza_in_box_position[0], pizza_in_box_position[1]-15, 48, (0.7, 0.15, 0.05))
            elif topping == "cheese":
                draw_circle(pizza_in_box_position[0], pizza_in_box_position[1]-15, 45, (0.9, 0.8, 0.4))
            elif topping == "sausage":
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 25
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 25
                    draw_circle(x, y, 8, (0.5, 0.25, 0))
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 30
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 30
                    draw_circle(x, y, 7, (0.7, 0.5, 0.0))
            elif topping == "onion":
                for i in range(10):
                    angle = i * 36 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 35
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 35
                    draw_circle(x, y, 5, (0.9, 0.8, 0.7))
            elif topping == "black_olive":
                for i in range(7):
                    angle = i * 51.4 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 32
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * 32
                    draw_circle(x, y, 6, (0.1, 0.1, 0.1))
            elif topping == "oregano":
                glPointSize(2.0)
                glBegin(GL_POINTS)
                glColor3f(0, 0.4, 0)
                for i in range(100):
                    angle = i * 3.6 * math.pi / 180
                    distance = 20 + 25 * (i % 5) / 5.0
                    x = pizza_in_box_position[0] + math.cos(angle) * distance
                    y = pizza_in_box_position[1]-15 + math.sin(angle) * distance
                    glVertex2f(x, y)
                glEnd()

def draw_oven():
    # Oven body
    draw_rect(oven_position[0] - 75, oven_position[1] - 75, 150, 150, (0.6, 0.6, 0.6))
    
    # Oven door
    draw_rect(oven_position[0] - 60, oven_position[1] - 60, 120, 120, (0.3, 0.3, 0.3))
    
    # Oven window
    draw_rect(oven_position[0] - 40, oven_position[1] - 40, 80, 80, (0.1, 0.1, 0.1))
    
    # Temperature indicator
    if cooking_in_progress:
        draw_circle(oven_position[0], oven_position[1] + 65, 5, (1, 0, 0))
    else:
        draw_circle(oven_position[0], oven_position[1] + 65, 5, (0, 1, 0))
    
    draw_text(oven_position[0] - 20, oven_position[1] + 85, "OVEN")

def draw_pizza_box():
    if pizza_box_open:
        # Open box with solid color
        draw_rect(box_position[0] - 80, box_position[1] - 80, 160, 120, (0.4, 0.3, 0.2))
        
        # Lid with solid color, darker and shorter on the y-axis
        draw_rect(box_position[0] - 80, box_position[1] + 61, 160, 80, (0.6, 0.4, 0.3))
        # Open box 
        draw_rect(box_position[0] - 80, box_position[1] - 80, 160, 10, (0.8, 0.6, 0.4))
        draw_rect(box_position[0] - 80, box_position[1] - 80, 10, 120, (0.8, 0.6, 0.4))
        draw_rect(box_position[0] + 70, box_position[1] - 80, 10, 120, (0.8, 0.6, 0.4))
        draw_rect(box_position[0] - 80, box_position[1] + 40, 160, 10, (0.8, 0.6, 0.4))
        
        # Box lid (open)
        draw_rect(box_position[0] - 80, box_position[1] + 50, 160, 5, (0.7, 0.5, 0.3))
        draw_rect(box_position[0] - 80, box_position[1] + 50, 5, 100, (0.7, 0.5, 0.3))
        draw_rect(box_position[0] + 75, box_position[1] + 50, 5, 100, (0.7, 0.5, 0.3))
        draw_rect(box_position[0] - 80, box_position[1] + 150, 160, 5, (0.7, 0.5, 0.3))
        
        draw_text(box_position[0] - 30, box_position[1] + 110, "OPEN BOX")
    
    elif pizza_box_closed:
        # Closed box (increased size)
        draw_rect(box_position[0] - 80, box_position[1] - 80, 160, 100, (0.7, 0.5, 0.3))
        draw_text(box_position[0] - 40, box_position[1], "CLOSED BOX")

def draw_instructions():
        y_pos = -250  # Bottom middle part of the window
        for line in instructions:
            draw_text(-300, y_pos, line)  # Centered horizontally
            y_pos += 20

def display():
    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Reset the coordinate system
    glLoadIdentity()
    
    # Draw background
    draw_rect(-600, -300, 1200, 600, (0.4, 0.7, 1))
    
    
    # Draw game elements
    
    
    draw_toppings_bar()
    draw_dough()
    draw_instructions()
    draw_oven()
    draw_pizza_box()
    draw_pizza()
    draw_pizza_in_box()
    
    # Swap buffers
    glutSwapBuffers()

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

# Initialization
def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-600, 600, -300, 300)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# Start OpenGL
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
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
