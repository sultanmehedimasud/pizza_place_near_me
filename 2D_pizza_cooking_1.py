from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

# Window dimensions
W_Width, W_Height = 1200, 600

# Game state variables
game_state = "start"  # start, preparing, baking, packaging, complete
current_topping = None
pizza_toppings = []
baking_start_time = 0
baking_duration = 3  # seconds

# Coordinates and dimensions
topping_area_x = 10
topping_area_y = 500
topping_size = 60
topping_spacing = 10

preparation_area_x = 400
preparation_area_y = 300
pizza_radius = 120

oven_x = 800
oven_y = 300
oven_width = 200
oven_height = 150

box_x = 950
box_y = 100
box_width = 200
box_height = 150

# Topping definitions with positions
toppings = {
    "dough": {"x": topping_area_x, "y": topping_area_y, "color": (0.95, 0.9, 0.7), "applied": False},
    "sauce": {"x": topping_area_x + topping_size + topping_spacing, "y": topping_area_y, "color": (0.8, 0.2, 0.1), "applied": False},
    "cheese": {"x": topping_area_x + (topping_size + topping_spacing) * 2, "y": topping_area_y, "color": (0.95, 0.95, 0.6), "applied": False},
    "pepperoni": {"x": topping_area_x + (topping_size + topping_spacing) * 3, "y": topping_area_y, "color": (0.7, 0.1, 0.1), "applied": False},
    "sausage": {"x": topping_area_x + (topping_size + topping_spacing) * 4, "y": topping_area_y, "color": (0.6, 0.3, 0.2), "applied": False},
    "onion": {"x": topping_area_x, "y": topping_area_y - topping_size - topping_spacing, "color": (0.9, 0.4, 0.9), "applied": False},
    "black_olive": {"x": topping_area_x + topping_size + topping_spacing, "y": topping_area_y - topping_size - topping_spacing, "color": (0.2, 0.2, 0.2), "applied": False},
    "oregano": {"x": topping_area_x + (topping_size + topping_spacing) * 2, "y": topping_area_y - topping_size - topping_spacing, "color": (0.2, 0.6, 0.2), "applied": False}
}

# Pizza states
raw_pizza = {"exists": False, "x": preparation_area_x, "y": preparation_area_y, "color": (0.95, 0.9, 0.7)}
cooked_pizza = {"exists": False, "x": oven_x + oven_width + 50, "y": oven_y, "color": (0.8, 0.7, 0.5)}

# Box states
open_box = {"exists": False, "x": box_x, "y": box_y}
closed_box = {"exists": False, "x": box_x, "y": box_y}

# Helper functions
def draw_circle(x, y, radius, segments=30):
    glBegin(GL_POLYGON)
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        dx = radius * math.cos(theta)
        dy = radius * math.sin(theta)
        glVertex2f(x + dx, y + dy)
    glEnd()

def draw_rectangle(x, y, width, height):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def is_point_in_circle(px, py, cx, cy, radius):
    return math.sqrt((px - cx)**2 + (py - cy)**2) <= radius

def is_point_in_rect(px, py, rx, ry, rw, rh):
    return px >= rx and px <= rx + rw and py >= ry and py <= ry + rh

# Drawing functions
def draw_topping_area():
    # Background for topping area
    glColor3f(0.9, 0.9, 0.8)
    draw_rectangle(0, W_Height - 200, 350, 200)
    
    # Draw topping containers
    for name, topping in toppings.items():
        glColor3f(*topping["color"])
        draw_rectangle(topping["x"], topping["y"], topping_size, topping_size)
        
        # Draw border
        glColor3f(0.3, 0.3, 0.3)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(topping["x"], topping["y"])
        glVertex2f(topping["x"] + topping_size, topping["y"])
        glVertex2f(topping["x"] + topping_size, topping["y"] + topping_size)
        glVertex2f(topping["x"], topping["y"] + topping_size)
        glEnd()
        glLineWidth(1)

def draw_preparation_area():
    # Draw table
    glColor3f(0.8, 0.7, 0.6)
    draw_rectangle(350, 100, 300, 300)
    
    # Draw cutting board
    glColor3f(0.9, 0.8, 0.7)
    draw_rectangle(375, 150, 250, 250)
    
    # Draw raw pizza if it exists
    if raw_pizza["exists"]:
        # Base
        glColor3f(*raw_pizza["color"])
        draw_circle(raw_pizza["x"], raw_pizza["y"], pizza_radius)
        
        # Draw applied toppings
        for topping in pizza_toppings:
            if topping == "sauce":
                glColor3f(*toppings["sauce"]["color"])
                draw_circle(raw_pizza["x"], raw_pizza["y"], pizza_radius * 0.95)
            elif topping == "cheese":
                glColor3f(*toppings["cheese"]["color"])
                draw_circle(raw_pizza["x"], raw_pizza["y"], pizza_radius * 0.9)
            elif topping == "pepperoni":
                glColor3f(*toppings["pepperoni"]["color"])
                for i in range(12):
                    angle = 2 * math.pi * i / 12
                    px = raw_pizza["x"] + math.cos(angle) * (pizza_radius * 0.6)
                    py = raw_pizza["y"] + math.sin(angle) * (pizza_radius * 0.6)
                    draw_circle(px, py, pizza_radius * 0.15)
            elif topping == "sausage":
                glColor3f(*toppings["sausage"]["color"])
                for i in range(8):
                    angle = 2 * math.pi * i / 8 + 0.3
                    px = raw_pizza["x"] + math.cos(angle) * (pizza_radius * 0.5)
                    py = raw_pizza["y"] + math.sin(angle) * (pizza_radius * 0.5)
                    draw_circle(px, py, pizza_radius * 0.1)
            elif topping == "onion":
                glColor3f(*toppings["onion"]["color"])
                for i in range(15):
                    angle = 2 * math.pi * i / 15 + 0.2
                    px = raw_pizza["x"] + math.cos(angle) * (pizza_radius * 0.7) * (1 + 0.3 * (i % 3))
                    py = raw_pizza["y"] + math.sin(angle) * (pizza_radius * 0.7) * (1 + 0.3 * (i % 3))
                    draw_circle(px, py, pizza_radius * 0.05)
            elif topping == "black_olive":
                glColor3f(*toppings["black_olive"]["color"])
                for i in range(10):
                    angle = 2 * math.pi * i / 10 + 0.5
                    px = raw_pizza["x"] + math.cos(angle) * (pizza_radius * 0.65)
                    py = raw_pizza["y"] + math.sin(angle) * (pizza_radius * 0.65)
                    draw_circle(px, py, pizza_radius * 0.08)
            elif topping == "oregano":
                glColor3f(*toppings["oregano"]["color"])
                glPointSize(2)
                glBegin(GL_POINTS)
                for i in range(100):
                    angle = 2 * math.pi * i / 100
                    r = pizza_radius * 0.8 * math.sqrt(i / 100.0)
                    px = raw_pizza["x"] + math.cos(angle) * r
                    py = raw_pizza["y"] + math.sin(angle) * r
                    glVertex2f(px, py)
                glEnd()

def draw_oven():
    # Oven background
    glColor3f(0.5, 0.5, 0.5)
    draw_rectangle(oven_x, oven_y, oven_width, oven_height)
    
    # Oven door
    glColor3f(0.3, 0.3, 0.3)
    draw_rectangle(oven_x + 10, oven_y + 10, oven_width - 20, oven_height - 20)
    
    # Oven controls
    glColor3f(0.2, 0.2, 0.2)
    draw_rectangle(oven_x + 20, oven_y + oven_height + 10, oven_width - 40, 30)
    
    # Indicator light
    if game_state == "baking":
        glColor3f(1.0, 0.0, 0.0)  # Red when baking
    else:
        glColor3f(0.0, 1.0, 0.0)  # Green when ready
    draw_circle(oven_x + oven_width - 30, oven_y + oven_height + 25, 10)

def draw_cooked_pizza():
    if cooked_pizza["exists"]:
        # Cooked base
        glColor3f(*cooked_pizza["color"])
        draw_circle(cooked_pizza["x"], cooked_pizza["y"], pizza_radius)
        
        # Draw applied toppings (slightly darker to show cooking)
        for topping in pizza_toppings:
            if topping == "sauce":
                r, g, b = toppings["sauce"]["color"]
                glColor3f(r * 0.8, g * 0.8, b * 0.8)
                draw_circle(cooked_pizza["x"], cooked_pizza["y"], pizza_radius * 0.95)
            elif topping == "cheese":
                r, g, b = toppings["cheese"]["color"]
                glColor3f(r * 0.8, g * 0.8, b * 0.8)
                draw_circle(cooked_pizza["x"], cooked_pizza["y"], pizza_radius * 0.9)
            elif topping == "pepperoni":
                r, g, b = toppings["pepperoni"]["color"]
                glColor3f(r * 0.7, g * 0.7, b * 0.7)
                for i in range(12):
                    angle = 2 * math.pi * i / 12
                    px = cooked_pizza["x"] + math.cos(angle) * (pizza_radius * 0.6)
                    py = cooked_pizza["y"] + math.sin(angle) * (pizza_radius * 0.6)
                    draw_circle(px, py, pizza_radius * 0.15)
            elif topping == "sausage":
                r, g, b = toppings["sausage"]["color"]
                glColor3f(r * 0.7, g * 0.7, b * 0.7)
                for i in range(8):
                    angle = 2 * math.pi * i / 8 + 0.3
                    px = cooked_pizza["x"] + math.cos(angle) * (pizza_radius * 0.5)
                    py = cooked_pizza["y"] + math.sin(angle) * (pizza_radius * 0.5)
                    draw_circle(px, py, pizza_radius * 0.1)
            elif topping == "onion":
                r, g, b = toppings["onion"]["color"]
                glColor3f(r * 0.7, g * 0.7, b * 0.7)
                for i in range(15):
                    angle = 2 * math.pi * i / 15 + 0.2
                    px = cooked_pizza["x"] + math.cos(angle) * (pizza_radius * 0.7) * (1 + 0.3 * (i % 3))
                    py = cooked_pizza["y"] + math.sin(angle) * (pizza_radius * 0.7) * (1 + 0.3 * (i % 3))
                    draw_circle(px, py, pizza_radius * 0.05)
            elif topping == "black_olive":
                r, g, b = toppings["black_olive"]["color"]
                glColor3f(r * 0.7, g * 0.7, b * 0.7)
                for i in range(10):
                    angle = 2 * math.pi * i / 10 + 0.5
                    px = cooked_pizza["x"] + math.cos(angle) * (pizza_radius * 0.65)
                    py = cooked_pizza["y"] + math.sin(angle) * (pizza_radius * 0.65)
                    draw_circle(px, py, pizza_radius * 0.08)
            elif topping == "oregano":
                r, g, b = toppings["oregano"]["color"]
                glColor3f(r * 0.7, g * 0.7, b * 0.7)
                glPointSize(2)
                glBegin(GL_POINTS)
                for i in range(100):
                    angle = 2 * math.pi * i / 100
                    r = pizza_radius * 0.8 * math.sqrt(i / 100.0)
                    px = cooked_pizza["x"] + math.cos(angle) * r
                    py = cooked_pizza["y"] + math.sin(angle) * r
                    glVertex2f(px, py)
                glEnd()

def draw_pizza_box():
    if open_box["exists"]:
        # Bottom of box
        glColor3f(0.8, 0.6, 0.4)
        draw_rectangle(open_box["x"], open_box["y"], box_width, box_height * 0.2)
        
        # Sides of box
        glColor3f(0.7, 0.5, 0.3)
        draw_rectangle(open_box["x"], open_box["y"] + box_height * 0.2, box_width, box_height * 0.1)
        draw_rectangle(open_box["x"], open_box["y"], box_width * 0.1, box_height * 0.2)
        draw_rectangle(open_box["x"] + box_width - box_width * 0.1, open_box["y"], box_width * 0.1, box_height * 0.2)
        draw_rectangle(open_box["x"] + box_width * 0.1, open_box["y"], box_width * 0.8, box_width * 0.05)
        
    if closed_box["exists"]:
        # Closed box
        glColor3f(0.8, 0.6, 0.4)
        draw_rectangle(closed_box["x"], closed_box["y"], box_width, box_height * 0.3)
        
        # Box top
        glColor3f(0.7, 0.5, 0.3)
        draw_rectangle(closed_box["x"], closed_box["y"] + box_height * 0.3, box_width, box_height * 0.05)
        
        # Box logo
        glColor3f(0.9, 0.2, 0.2)
        draw_circle(closed_box["x"] + box_width / 2, closed_box["y"] + box_height * 0.15, box_width * 0.2)
        
        glColor3f(0.8, 0.6, 0.4)
        draw_circle(closed_box["x"] + box_width / 2, closed_box["y"] + box_height * 0.15, box_width * 0.15)

def draw_instructions():
    instructions = [
        "Pizza Making Instructions:",
        "1. Click on dough to start",
        "2. Click on toppings, then pizza to apply",
        "3. Click on the oven to bake",
        "4. Click on cooked pizza to place in box",
        "5. Click on open box to close it",
        "Press 'r' to reset the game"
    ]
    
    glColor3f(0.0, 0.0, 0.0)
    y_pos = 50
    for line in instructions:
        glRasterPos2f(50, y_pos)
        for char in line:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        y_pos += 20

def draw_status():
    status_text = f"Game State: {game_state}"
    if game_state == "baking":
        elapsed = time.time() - baking_start_time
        remaining = max(0, baking_duration - elapsed)
        status_text += f" - Baking Time: {remaining:.1f}s"
    
    glColor3f(0.0, 0.0, 0.0)
    glRasterPos2f(W_Width - 300, 30)
    for char in status_text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))

def keyboardListener(key, x, y):
    global game_state
    
    if key == b'r':  # Reset the game
        reset_game()
        
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global game_state, current_topping, raw_pizza, cooked_pizza, open_box, closed_box, pizza_toppings
    global baking_start_time
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Convert screen coordinates to OpenGL coordinates
        y = W_Height - y  # Invert y-coordinate
        
        # Check if we clicked on a topping
        for name, topping in toppings.items():
            if is_point_in_rect(x, y, topping["x"], topping["y"], topping_size, topping_size):
                print(f"Selected topping: {name}")
                
                if name == "dough" and not raw_pizza["exists"] and game_state == "start":
                    raw_pizza["exists"] = True
                    pizza_toppings = []
                    game_state = "preparing"
                    print("Dough placed on preparation area")
                else:
                    current_topping = name
                
                glutPostRedisplay()
                return
        
        # Check if we clicked on the raw pizza to apply topping
        if raw_pizza["exists"] and current_topping and current_topping != "dough" and game_state == "preparing":
            if is_point_in_circle(x, y, raw_pizza["x"], raw_pizza["y"], pizza_radius):
                if current_topping not in pizza_toppings:
                    pizza_toppings.append(current_topping)
                    toppings[current_topping]["applied"] = True
                    print(f"Applied {current_topping} to pizza")
                    current_topping = None
                    glutPostRedisplay()
                    return
        
        # Check if we clicked on the oven
        if raw_pizza["exists"] and is_point_in_rect(x, y, oven_x, oven_y, oven_width, oven_height) and game_state == "preparing":
            if len(pizza_toppings) > 0:  # Must have at least one topping
                game_state = "baking"
                baking_start_time = time.time()
                raw_pizza["exists"] = False
                print("Pizza is baking")
                glutPostRedisplay()
                return
        
        # Check if we clicked on the cooked pizza to move it to the box
        if cooked_pizza["exists"] and is_point_in_circle(x, y, cooked_pizza["x"], cooked_pizza["y"], pizza_radius) and game_state == "packaging":
            open_box["exists"] = True
            cooked_pizza["exists"] = False
            print("Pizza placed in box")
            glutPostRedisplay()
            return
        
        # Check if we clicked on the open box to close it
        if open_box["exists"] and is_point_in_rect(x, y, open_box["x"], open_box["y"], box_width, box_height) and game_state == "packaging":
            closed_box["exists"] = True
            open_box["exists"] = False
            print("Box closed. Pizza is ready for delivery!")
            game_state = "complete"
            glutPostRedisplay()
            return
    
    glutPostRedisplay()

def reset_game():
    global game_state, current_topping, raw_pizza, cooked_pizza, open_box, closed_box, pizza_toppings
    
    game_state = "start"
    current_topping = None
    raw_pizza["exists"] = False
    cooked_pizza["exists"] = False
    open_box["exists"] = False
    closed_box["exists"] = False
    pizza_toppings = []
    
    for name in toppings:
        toppings[name]["applied"] = False
    
    print("Game reset")

def animate():
    global game_state, baking_start_time, cooked_pizza
    
    if game_state == "baking":
        elapsed = time.time() - baking_start_time
        if elapsed >= baking_duration:
            game_state = "packaging"
            cooked_pizza["exists"] = True
            print("Pizza is ready!")
    
    glutPostRedisplay()

def display():
    # Clear the display
    glClearColor(0.9, 0.9, 0.9, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Draw the game elements
    draw_topping_area()
    draw_preparation_area()
    draw_oven()
    draw_cooked_pizza()
    draw_pizza_box()
    draw_instructions()
    draw_status()
    
    # Debug rectangle to test rendering
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex2f(0, 0)
    glVertex2f(100, 100)
    glEnd()
    
    glutSwapBuffers()

def init():
    # Set clear color
    glClearColor(0.9, 0.9, 0.9, 1.0)
    
    # Set up 2D projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, W_Width, 0, W_Height)
    
    # Switch back to modelview
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# Initialize GLUT
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(W_Width, W_Height)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Pizza Making Game")

# Initialize OpenGL
init()

# Register callbacks
glutDisplayFunc(display)
glutIdleFunc(animate)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)

# Start the main loop
print("Pizza Making Game Started!")
print("Click on the dough to begin!")
glutMainLoop()

#eita te ami kono logic error pai nai,its just not visually good