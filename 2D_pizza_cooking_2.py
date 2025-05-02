from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

W_Width, W_Height = 1200, 600

# Toppings and dough setup
toppings = {
    "sauce": False,
    "cheese": False,
    "sausage": False,
    "pepperoni": False,
    "onion": False,
    "black_olive": False,
    "oregano": False
}

selected_topping = None
dough_has_topping = {}  # Track which toppings are on the dough

bread_before_oven = False
bread_after_oven = False
pizza_box_open = True  # Start with open box
pizza_box_closed = False

# Dough position and toppings position
dough_position = (-300, 0)
dough_radius = 100

topping_positions = {
    "sauce": (-500, 250),
    "cheese": (-400, 250),
    "sausage": (-300, 250),
    "pepperoni": (-200, 250),
    "onion": (-100, 250),
    "black_olive": (0, 250),
    "oregano": (100, 250)
}

# Initialize dough toppings
for topping in toppings:
    dough_has_topping[topping] = False

oven_position = (300, 0)
pizza_box_position = (450, -150)

# Coordinate conversion for mouse clicks
def convert_coordinate(x, y):
    global W_Width, W_Height
    a = x - (W_Width / 2)
    b = (W_Height / 2) - y
    return a, b

def draw_circle(x, y, radius, color):
    glBegin(GL_POLYGON)
    glColor3f(*color)
    for i in range(360):
        angle = math.radians(i)
        glVertex2f(x + math.cos(angle) * radius, y + math.sin(angle) * radius)
    glEnd()

def draw_rect(x, y, width, height, color):
    glBegin(GL_QUADS)
    glColor3f(*color)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def draw_bread():
    if bread_before_oven:
        # Draw base bread
        draw_circle(dough_position[0], dough_position[1], dough_radius, (0.9, 0.8, 0.6))  # Light brown dough
        
        # Draw toppings on the bread
        if dough_has_topping["sauce"]:
            draw_circle(dough_position[0], dough_position[1], dough_radius-5, (0.8, 0.2, 0.2))  # Red sauce
        
        if dough_has_topping["cheese"]:
            # Draw cheese with slight offset to show layering
            draw_circle(dough_position[0], dough_position[1], dough_radius-10, (1.0, 0.9, 0.4))  # Yellow cheese
        
        if dough_has_topping["pepperoni"]:
            # Draw pepperoni slices
            for i in range(8):
                angle = math.radians(i * 45)
                offset_x = math.cos(angle) * (dough_radius/2)
                offset_y = math.sin(angle) * (dough_radius/2)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 15, (0.8, 0.1, 0.1))
        
        if dough_has_topping["sausage"]:
            # Draw sausage pieces
            for i in range(6):
                angle = math.radians(i * 60)
                offset_x = math.cos(angle) * (dough_radius/1.7)
                offset_y = math.sin(angle) * (dough_radius/1.7)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 12, (0.6, 0.3, 0))
        
        if dough_has_topping["onion"]:
            # Draw onion pieces
            for i in range(10):
                angle = math.radians(i * 36)
                offset_x = math.cos(angle) * (dough_radius/1.5)
                offset_y = math.sin(angle) * (dough_radius/1.5)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 8, (1, 1, 1))
        
        if dough_has_topping["black_olive"]:
            # Draw black olives
            for i in range(7):
                angle = math.radians(i * 51.4)
                offset_x = math.cos(angle) * (dough_radius/1.8)
                offset_y = math.sin(angle) * (dough_radius/1.8)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 10, (0.1, 0.1, 0.1))
        
        if dough_has_topping["oregano"]:
            # Visual effect for oregano (small green specks)
            glPointSize(2.0)
            glBegin(GL_POINTS)
            glColor3f(0.0, 0.5, 0.0)
            for i in range(100):
                angle = math.radians(i * 3.6)
                r = random.uniform(0, dough_radius-15)
                x = dough_position[0] + math.cos(angle) * r
                y = dough_position[1] + math.sin(angle) * r
                glVertex2f(x, y)
            glEnd()

    elif bread_after_oven:
        # Draw cooked bread with darker color
        draw_circle(dough_position[0], dough_position[1], dough_radius, (0.7, 0.5, 0.3))  # Darker cooked bread
        
        # Draw toppings on the bread (with slightly darker colors to show cooking)
        if dough_has_topping["sauce"]:
            draw_circle(dough_position[0], dough_position[1], dough_radius-5, (0.7, 0.1, 0.1))  # Darker red sauce
        
        if dough_has_topping["cheese"]:
            # Draw cheese with slight browning
            draw_circle(dough_position[0], dough_position[1], dough_radius-10, (0.9, 0.8, 0.3))  # Slightly browned cheese
        
        # Similarly darken other toppings for cooked appearance
        if dough_has_topping["pepperoni"]:
            for i in range(8):
                angle = math.radians(i * 45)
                offset_x = math.cos(angle) * (dough_radius/2)
                offset_y = math.sin(angle) * (dough_radius/2)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 15, (0.7, 0.1, 0.1))
        
        if dough_has_topping["sausage"]:
            for i in range(6):
                angle = math.radians(i * 60)
                offset_x = math.cos(angle) * (dough_radius/1.7)
                offset_y = math.sin(angle) * (dough_radius/1.7)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 12, (0.5, 0.25, 0))
        
        if dough_has_topping["onion"]:
            for i in range(10):
                angle = math.radians(i * 36)
                offset_x = math.cos(angle) * (dough_radius/1.5)
                offset_y = math.sin(angle) * (dough_radius/1.5)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 8, (0.9, 0.9, 0.8))
        
        if dough_has_topping["black_olive"]:
            for i in range(7):
                angle = math.radians(i * 51.4)
                offset_x = math.cos(angle) * (dough_radius/1.8)
                offset_y = math.sin(angle) * (dough_radius/1.8)
                draw_circle(dough_position[0] + offset_x, dough_position[1] + offset_y, 10, (0.1, 0.1, 0.1))

def draw_topping_containers():
    for topping, position in topping_positions.items():
        container_color = (0.8, 0.8, 0.8)
        draw_rect(position[0] - 30, position[1] - 30, 60, 60, container_color)
        
        # Draw the topping sample in the container
        if topping == "sauce":
            draw_circle(position[0], position[1], 20, (0.8, 0.2, 0.2))  # Red sauce
        elif topping == "cheese":
            draw_circle(position[0], position[1], 20, (1.0, 0.9, 0.4))  # Yellow cheese
        elif topping == "sausage":
            draw_circle(position[0], position[1], 20, (0.6, 0.3, 0))  # Brown sausage
        elif topping == "pepperoni":
            draw_circle(position[0], position[1], 20, (0.8, 0.1, 0.1))  # Pepperoni red
        elif topping == "onion":
            draw_circle(position[0], position[1], 20, (1, 1, 1))  # White onion
        elif topping == "black_olive":
            draw_circle(position[0], position[1], 20, (0.1, 0.1, 0.1))  # Black olives
        elif topping == "oregano":
            draw_circle(position[0], position[1], 20, (0, 0.5, 0))  # Oregano green

def draw_dough_station():
    # Draw dough preparation area
    draw_rect(-350, -50, 100, 100, (0.8, 0.7, 0.6))  # Dough station
    draw_circle(-300, 0, 30, (0.9, 0.8, 0.6))  # Raw dough ball

def draw_pizza_box():
    if pizza_box_open:
        # Draw open box
        draw_rect(pizza_box_position[0], pizza_box_position[1], 200, 30, (0.8, 0.6, 0.3))  # Box bottom
        draw_rect(pizza_box_position[0], pizza_box_position[1] + 30, 200, 150, (0.9, 0.7, 0.4))  # Box inside
        draw_rect(pizza_box_position[0], pizza_box_position[1] + 180, 200, 30, (0.8, 0.6, 0.3))  # Box top (open)
    
    if pizza_box_closed:
        # Draw closed box
        draw_rect(pizza_box_position[0], pizza_box_position[1], 200, 30, (0.8, 0.6, 0.3))  # Box
        
        # Add some details to the closed box
        draw_rect(pizza_box_position[0] + 20, pizza_box_position[1] + 30, 160, 5, (0.7, 0.5, 0.2))  # Box details
        draw_rect(pizza_box_position[0] + 20, pizza_box_position[1] + 15, 160, 5, (0.7, 0.5, 0.2))  # Box details

def draw_oven():
    # Main oven body
    draw_rect(oven_position[0] - 75, oven_position[1] - 75, 150, 150, (0.3, 0.3, 0.3))
    
    # Oven door
    draw_rect(oven_position[0] - 65, oven_position[1] - 65, 130, 130, (0.5, 0.5, 0.5))
    
    # Oven controls
    draw_rect(oven_position[0] - 50, oven_position[1] + 60, 100, 15, (0.2, 0.2, 0.2))
    
    # Control knobs
    draw_circle(oven_position[0] - 30, oven_position[1] + 67, 5, (0.8, 0.1, 0.1))
    draw_circle(oven_position[0], oven_position[1] + 67, 5, (0.8, 0.1, 0.1))
    draw_circle(oven_position[0] + 30, oven_position[1] + 67, 5, (0.8, 0.1, 0.1))
    
    # Oven window
    draw_rect(oven_position[0] - 40, oven_position[1] - 40, 80, 80, (0.1, 0.1, 0.1))

def keyboardListener(key, x, y):
    global pizza_box_open, pizza_box_closed, bread_after_oven
    
    if key == b'o':  # Open the pizza box
        pizza_box_open = True
        pizza_box_closed = False
    
    if key == b'c':  # Close the pizza box
        if bread_after_oven:
            pizza_box_open = False
            pizza_box_closed = True
            bread_after_oven = False  # Pizza is now in the box
    
    if key == b'r':  # Reset game
        reset_game()
    
    glutPostRedisplay()

def reset_game():
    global bread_before_oven, bread_after_oven, pizza_box_open, pizza_box_closed, selected_topping
    global toppings, dough_has_topping
    
    bread_before_oven = False
    bread_after_oven = False
    pizza_box_open = True
    pizza_box_closed = False
    selected_topping = None
    
    for topping in toppings:
        toppings[topping] = False
        dough_has_topping[topping] = False

def mouseListener(button, state, x, y):
    global bread_before_oven, bread_after_oven, selected_topping, dough_has_topping
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        c_X, c_y = convert_coordinate(x, y)
        print(f"Click at ({c_X}, {c_y})")
        
        # Check if clicked on dough station
        if -350 <= c_X <= -250 and -50 <= c_y <= 50:
            if not bread_before_oven and not bread_after_oven:
                bread_before_oven = True
                print("Dough prepared")
        
        # Check if clicked on a topping
        for topping, position in topping_positions.items():
            if abs(c_X - position[0]) < 30 and abs(c_y - position[1]) < 30:
                selected_topping = topping
                print(f"Selected topping: {selected_topping}")
                break
        
        # If a topping is selected and clicked on bread, apply topping
        if selected_topping and bread_before_oven:
            distance = math.sqrt((c_X - dough_position[0])**2 + (c_y - dough_position[1])**2)
            if distance < dough_radius:
                dough_has_topping[selected_topping] = True
                selected_topping = None
                print("Applied topping to dough")
        
        # If clicked on oven
        if abs(c_X - oven_position[0]) < 75 and abs(c_y - oven_position[1]) < 75:
            if bread_before_oven:
                bread_before_oven = False
                bread_after_oven = True
                print("Pizza cooked in oven")
        
        # If clicked on pizza box and have cooked pizza
        if pizza_box_position[0] <= c_X <= pizza_box_position[0] + 200 and \
           pizza_box_position[1] <= c_y <= pizza_box_position[1] + 180:
            if bread_after_oven and pizza_box_open:
                print("Pizza placed in box")
                # The transition to closed box is handled by keyboard 'c'
        
        glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.95, 0.95, 0.9, 1.0)  # Slight cream background
    glLoadIdentity()
    
    # Set up the ortho view
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-W_Width/2, W_Width/2, -W_Height/2, W_Height/2)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Draw countertop background
    draw_rect(-W_Width/2, -W_Height/2, W_Width, W_Height, (0.9, 0.85, 0.8))
    
    # Draw all components
    draw_dough_station()
    draw_topping_containers()
    draw_oven()
    draw_pizza_box()
    draw_bread()
    
    # Draw instructions
    
    glutSwapBuffers()

def init():
    glClearColor(0.95, 0.95, 0.9, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-W_Width/2, W_Width/2, -W_Height/2, W_Height/2)
    glMatrixMode(GL_MODELVIEW)

# Need to import random for oregano effect
import random

glutInit()
glutInitWindowSize(W_Width, W_Height)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)
wind = glutCreateWindow(b"Pizza Making Game")

init()
glutDisplayFunc(display)
glutKeyboardFunc(keyboardListener)
glutMouseFunc(mouseListener)

print("Pizza Making Game Instructions:")
print("1. Click on the dough area to prepare the dough")
print("2. Click on a topping and then on the dough to add that topping")
print("3. Click on the oven to cook the pizza")
print("4. Click on the pizza box to place the pizza")
print("5. Press 'c' to close the box")
print("6. Press 'o' to open the box")
print("7. Press 'r' to reset the game")

glutMainLoop()
#Problem- box close korar pore abar open korbo for new pizza
#but topping add korle i think ager pizza er ta chole ashe,yes ashe,dbl checked
#and age dough click kore pizza banabo,then topping add korbo
#so dough e click na kore jodi topping e click kori,tahole kono kisu howa uchit na
#but eikhane hocche,eikhane topping diye jodi dough er upor click kori
#taile oi topping shoho dough ashe, this needs to be handled
#pizza box e place korar poreo pizza left e exist kore,handle