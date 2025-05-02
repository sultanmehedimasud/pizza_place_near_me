from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

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
pizza_box_open = False
pizza_box_closed = False

# Cooking timer variables
cooking_start_time = 0
cooking_in_progress = False
cooking_duration = 2  # 2 seconds

# Box cycle timer variables
box_close_time = 0
box_cycle_duration = 5  # 5 seconds before box reopens

# Positions
dough_position = (-300, 0)
pizza_position = (-300, 0)
pizza_in_box_position = (500, -150)
right_box_position = (450, 0)  # Position for the open box on the right side of the oven

topping_positions = {
    "sauce": (-500, 250),
    "cheese": (-400, 250),
    "sausage": (-300, 250),
    "pepperoni": (-200, 250),
    "onion": (-100, 250),
    "black_olive": (0, 250),
    "oregano": (100, 250)
}

dough_position_display = (-500, -150)
oven_position = (300, 0)
box_position = (500, -150)

# Applied toppings on pizza
pizza_toppings = []

# Game instructions
instructions = [
    "Click on dough to place it on the table",
    "Click on toppings to select them",
    "Click on pizza to apply selected toppings",
    "Click on oven to cook pizza (2 seconds)",
    "Click on cooked pizza to place it in the box",
    "Click on open box to close it",
    "Box will reopen after 5 seconds to start again"
]

# Convert window coordinates to OpenGL coordinates
def convert_coordinate(x, y):
    a = x - (W_Width / 2)
    b = (W_Height / 2) - y
    return a, b

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

# Draw game instructions
def draw_instructions():
    y_pos = -250  # Bottom middle part of the window
    for line in instructions:
        draw_text(-300, y_pos, line)  # Centered horizontally
        y_pos += 20

# Draw oven
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

# Draw pizza
def draw_pizza():
    if bread_before_oven and not cooking_in_progress:
        # Draw base pizza dough
        draw_circle(pizza_position[0], pizza_position[1], 50, (0.9, 0.8, 0.7))
        
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
                    draw_circle(x, y, 7, (1.0, 0.5, 0.0))  # Orange color for pepperoni
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

# Draw pizza in the box
def draw_pizza_in_box():
    if pizza_in_box and (pizza_box_open or pizza_box_closed):
        # Draw pizza in box only if the box is visible
        draw_circle(pizza_in_box_position[0], pizza_in_box_position[1], 50, (0.8, 0.6, 0.3))
        
        # Draw toppings in the box
        for topping in pizza_toppings:
            if topping == "sauce":
                draw_circle(pizza_in_box_position[0], pizza_in_box_position[1], 48, (0.7, 0.15, 0.05))
            elif topping == "cheese":
                draw_circle(pizza_in_box_position[0], pizza_in_box_position[1], 45, (0.9, 0.8, 0.4))
            elif topping == "pepperoni":
                for i in range(8):
                    angle = i * 45 * math.pi / 180
                    x = pizza_in_box_position[0] + math.cos(angle) * 30
                    y = pizza_in_box_position[1] + math.sin(angle) * 30
                    draw_circle(x, y, 7, (1.0, 0.5, 0.0))  # Orange color for pepperoni

def draw_dough():
    draw_circle(dough_position_display[0], dough_position_display[1], 40, (0.9, 0.8, 0.7))
    draw_text(dough_position_display[0] - 20, dough_position_display[1] - 60, "Dough")

# Keyboard listener
def keyboardListener(key, x, y):
    global pizza_box_open, pizza_box_closed
    
    if key == b'o':  # Open box
        pizza_box_open = True
        pizza_box_closed = False
    elif key == b'c':  # Close box
        if pizza_box_open:
            pizza_box_open = False
            pizza_box_closed = True
            global box_close_time
            box_close_time = time.time()
    elif key == b'q':  # Quit
        sys.exit(0)
        
    glutPostRedisplay()

def display():
    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Reset the coordinate system
    glLoadIdentity()
    
    # Draw background
    draw_rect(-600, -300, 1200, 600, (0.9, 0.85, 0.8))
    
    # Draw game elements
    draw_instructions()
    draw_dough()
    #draw_toppings_bar()
    draw_oven()
    #draw_pizza_box()
    draw_pizza()
    draw_pizza_in_box()
    
    # Swap buffers
    glutSwapBuffers()

def mouseListener(button, state, x, y):
    global bread_before_oven, bread_after_oven, pizza_box_open, pizza_box_closed
    global pizza_in_box, cooking_in_progress, cooking_start_time, pizza_toppings
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Convert screen coordinates to OpenGL coordinates
        c_X, c_y = convert_coordinate(x, y)
        
        
        # Click on dough
        if abs(c_X - dough_position_display[0]) < 40 and abs(c_y - dough_position_display[1]) < 40:
            if not bread_before_oven and not bread_after_oven and not pizza_in_box:
                bread_before_oven = True
                pizza_toppings = []
        
        # Click on toppings
        for topping, position in topping_positions.items():
            if abs(c_X - position[0]) < 25 and abs(c_y - position[1]) < 25:
                toppings[topping] = not toppings[topping]
        
        # Click on pizza to add toppings
        if bread_before_oven and not cooking_in_progress:
            if abs(c_X - pizza_position[0]) < 50 and abs(c_y - pizza_position[1]) < 50:
                for topping, selected in toppings.items():
                    if selected and topping not in pizza_toppings:
                        pizza_toppings.append(topping)
                        toppings[topping] = False
        
        # Click on oven
        if bread_before_oven and not cooking_in_progress and not bread_after_oven:
            if abs(c_X - oven_position[0]) < 75 and abs(c_y - oven_position[1]) < 75:
                cooking_in_progress = True
                cooking_start_time = time.time()
        
        # Click on cooked pizza
        if bread_after_oven and not pizza_in_box:
            if abs(c_X - pizza_position[0]) < 50 and abs(c_y - pizza_position[1]) < 50:
                bread_after_oven = False
                pizza_in_box = True
                pizza_box_open = True
                pizza_box_closed = False
        
        # Click on open box
        if pizza_in_box and pizza_box_open:
            if abs(c_X - box_position[0]) < 70 and abs(c_y - box_position[1]) < 60:
                pizza_box_open = False
                pizza_box_closed = True
                box_close_time = time.time()
        
        glutPostRedisplay()

def keyboardListener(key, x, y):
    global pizza_box_open, pizza_box_closed
    
    if key == b'o':  # Open box
        pizza_box_open = True
        pizza_box_closed = False
    elif key == b'c':  # Close box
        if pizza_box_open:
            pizza_box_open = False
            pizza_box_closed = True
            global box_close_time
            box_close_time = time.time()
    elif key == b'q':  # Quit
        sys.exit(0)
        
    glutPostRedisplay()


def check_timers(value):
    # Check cooking timer
    global pizza_toppings
    global cooking_in_progress, bread_before_oven, bread_after_oven
    global pizza_box_closed, pizza_box_open, pizza_in_box
    if cooking_in_progress:
        current_time = time.time()
        if current_time - cooking_start_time >= cooking_duration:
            cooking_in_progress = False
            bread_before_oven = False
            bread_after_oven = True
    
    # Check box cycle timer
    if pizza_box_closed:
        current_time = time.time()
        if current_time - box_close_time >= box_cycle_duration:
            pizza_box_closed = False
            pizza_box_open = False
            pizza_in_box = False
            bread_before_oven = False
            bread_after_oven = False
            pizza_toppings = []
    
    glutPostRedisplay()
    glutTimerFunc(100, check_timers, 0)

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-600, 600, -300, 300)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
