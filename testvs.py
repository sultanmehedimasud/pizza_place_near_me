import math
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class Entity:
    def __init__(self, x, y, z):
        self.position = [x, y, z]

    def distance_to(self, other):
        # Calculate the Euclidean distance to another entity
        return math.sqrt(
            (self.position[0] - other.position[0]) ** 2 +
            (self.position[1] - other.position[1]) ** 2 +
            (self.position[2] - other.position[2]) ** 2
        )

class GameSettings:
    def __init__(self):
        self.grid_size = 600
        self.window_width = 1200  # Changed from 800 to 1200
        self.window_height = 600  # Changed from 800 to 600
        self.started = False
        self.game_over = False
        self.score = 0
        self.mistakes_limit = 5
        self.mistakes = 0
        self.current_level = 1
        self.time_remaining = 180  # 3 minutes per level
        self.last_time_update = 0

# Add this after the GameSettings class
class InputManager:
    def __init__(self):
        self.pressed_keys = set()
    
    def key_down(self, key):
        self.pressed_keys.add(key)
    
    def key_up(self, key):
        self.pressed_keys.discard(key)
    
    def is_key_pressed(self, key):
        return key in self.pressed_keys

class Camera:
    def __init__(self):
        # Adjusted to allign with the hand and start behind the player
        self.offset = [0, 0, 150]
        self.fov = 120
        self.mode = 0  # 0 = third-person, 1 = first-person
        self.rotation_angle = 180  # Start behind the player
        self.zoom_level = 150

    def move(self, direction):
        if direction == "up":
            self.zoom_level = max(50, self.zoom_level - 10)  # Zoom in
        elif direction == "down":
            self.zoom_level = min(300, self.zoom_level + 10)  # Zoom out
        elif direction == "left":
            self.rotation_angle += 5  # Rotate left
        elif direction == "right":
            self.rotation_angle -= 5  # Rotate right

    def setup(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, 1.0, 0.1, 1500)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def position_camera(self, player):
        if self.mode == 0:  # Third-person view
            angle_rad = math.radians(player.angle + self.rotation_angle)
            cam_x = player.position[0] + self.zoom_level * math.cos(angle_rad)
            cam_y = player.position[1] + self.zoom_level * math.sin(angle_rad)
            cam_z = min(player.position[2] + self.offset[2], 300)  # Keep camera within building height
            gluLookAt(cam_x, cam_y, cam_z, player.position[0], player.position[1], player.position[2], 0, 0, 1)
        else:  # First-person view
            # Camera is positioned at the player's head and looks in the direction the player is facing
            cam_height = 120
            look_x = player.position[0] + 100 * math.cos(math.radians(player.angle))
            look_y = player.position[1] + 100 * math.sin(math.radians(player.angle))
            gluLookAt(player.position[0], player.position[1], player.position[2] + cam_height,
                      look_x, look_y, player.position[2] + cam_height, 0, 0, 1)

    def toggle_mode(self):
        # Toggle between third-person and first-person modes
        self.mode = 1 - self.mode

    def _within_bounds(self, x, y):
        # Ensure the camera stays within the room boundaries
        boundary = game.settings.grid_size - 50  # Adjusted for camera offset
        return -boundary <= x <= boundary and -boundary <= y <= boundary


class Player(Entity):
    def __init__(self):
        super().__init__(0, 0, 30)
        self.angle = 0
        self.speed = 10  # Movement speed
        self.cheat_mode = False
        self.holding_ingredient = None
        self.holding_pizza = None
        self.inventory = []
        self.near_pizza_table = False  # Track if near pizza table
        
        # Adjust torso to touch hands
        self.body_parts = {
            'head': {'radius': 18, 'color': (0.8, 0.6, 0.4), 'position': (0, 0, 80)},
            'torso': {'size': (25, 15, 40), 'color': (0.2, 0.6, 0.3), 'position': (0, 0, 50)},  # Adjusted position
            'arm_left': {'top_radius': 10, 'bottom_radius': 2, 'length': 40, 
                         'color': (1.0, 0.9, 0.7), 'position': (20, 0, 50)},
            'arm_right': {'top_radius': 9, 'bottom_radius': 2, 'length': 40, 
                          'color': (1.0, 0.9, 0.7), 'position': (-20, 0, 50)},
            'leg_left': {'top_radius': 10, 'bottom_radius': 2, 'length': 50, 
                         'color': (0, 0, 1), 'position': (10, 0, 30)},
            'leg_right': {'top_radius': 10, 'bottom_radius': 2, 'length': 50, 
                          'color': (0, 0, 1), 'position': (-10, 0, 30)},
        }

    def move_forward(self):
        angle_rad = math.radians(self.angle)
        new_x = self.position[0] + self.speed * math.cos(angle_rad)
        new_y = self.position[1] + self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y) and not self._collides_with_pizza_table(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision()
    
    def move_backward(self):
        angle_rad = math.radians(self.angle)
        new_x = self.position[0] - self.speed * math.cos(angle_rad)
        new_y = self.position[1] - self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision()
    
    def move_left(self):
        angle_rad = math.radians(self.angle + 90)
        new_x = self.position[0] + self.speed * math.cos(angle_rad)
        new_y = self.position[1] + self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y) and not self._collides_with_objects(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision()
    
    def move_right(self):
        angle_rad = math.radians(self.angle - 90)
        new_x = self.position[0] + self.speed * math.cos(angle_rad)
        new_y = self.position[1] + self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y) and not self._collides_with_objects(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision()

    def turn_left(self):
        self.angle += 5
        self.angle %= 360  # Keep angle within 0-359 degrees

    def turn_right(self):
        self.angle -= 5
        self.angle %= 360  # Keep angle within 0-359 degrees
        
    def toggle_cheat_mode(self):
        self.cheat_mode = not self.cheat_mode
        
    def pick_up_ingredient(self, ingredient):
        self.holding_ingredient = ingredient
        
    def place_ingredient(self, pizza):
        if self.holding_ingredient:
            pizza.add_ingredient(self.holding_ingredient)
            self.holding_ingredient = None
            return True
        return False
    
    def pick_up_pizza(self, pizza):
        self.holding_pizza = pizza
        
    def place_pizza(self, target):
        result = False
        if self.holding_pizza:
            if isinstance(target, Oven):
                target.insert_pizza(self.holding_pizza)
                result = True
            elif isinstance(target, DeliveryStation):
                target.add_pizza(self.holding_pizza)
                result = True
            elif isinstance(target, Customer):
                result = target.receive_pizza(self.holding_pizza)
            
            if result:
                self.holding_pizza = None
        return result
    
    def _draw_sphere(self, part_name):
        part = self.body_parts[part_name]
        glColor3f(*part['color'])
        glPushMatrix()
        glTranslatef(*part['position'])
        glutSolidSphere(part['radius'], 20, 20)
        glPopMatrix()
    
    def _draw_cube(self, part_name):
        part = self.body_parts[part_name]
        glColor3f(*part['color'])
        glPushMatrix()
        glTranslatef(*part['position'])
        glScalef(*part['size'])  # Scale the cube to the desired dimensions
        glutSolidCube(1)  # Use a unit cube and scale it
        glPopMatrix()
    
    def _draw_cylinder(self, part_name, rotation=None):
        part = self.body_parts[part_name]
        glColor3f(*part['color'])
        glPushMatrix()
        glTranslatef(*part['position'])
        
        if rotation:
            for rot in rotation:
                x, y, z, angle = rot
                glRotatef(angle, x, y, z)
        
        gluCylinder(gluNewQuadric(), 
                    part['top_radius'], 
                    part['bottom_radius'], 
                    part['length'], 10, 10)
        glPopMatrix()
    
    def draw(self, game_over=False, camera_mode=0):
        glPushMatrix()
        glTranslatef(*self.position)
        
        if camera_mode == 1 and not game_over:
            glPopMatrix()
            return
        
        if game_over:
            glRotatef(90, 1, 0, 0)
        else:
            glRotatef(self.angle - 90, 0, 0, 1)
        
        self._draw_sphere('head')
        self._draw_cube('torso')
        self._draw_cylinder('arm_left', [(1, 0, 0, -90), (0, 0, 1, self.angle)])  # Adjusted for camera angle
        self._draw_cylinder('arm_right', [(1, 0, 0, -90), (0, 0, 1, self.angle)])  # Adjusted for camera angle
        self._draw_cylinder('leg_left', [(1, 0, 0, -180)])
        self._draw_cylinder('leg_right', [(1, 0, 0, -180)])
        
        # Draw held items
        if self.holding_ingredient:
            glPushMatrix()
            glTranslatef(20 * math.cos(math.radians(self.angle)), 20 * math.sin(math.radians(self.angle)), 40)
            self.holding_ingredient.draw()
            glPopMatrix()
            
        if self.holding_pizza:
            glPushMatrix()
            glTranslatef(20 * math.cos(math.radians(self.angle)), 20 * math.sin(math.radians(self.angle)), 40)
            self.holding_pizza.draw()
            glPopMatrix()
        
        # Update the popup message based on order status
        if self.near_pizza_table:
            if game.pizza_manager.customer_manager.received_order:
                game.hud.draw_text(300, 300, "Press P to start making pizza")
            else:
                game.hud.draw_text(300, 300, "No pizza order is received")
        
        glPopMatrix()

    def _check_collision(self):
        # Updated to check collision with all objects
        for obj in (
            game.pizza_manager.ingredient_stations +
            [game.pizza_manager.oven, game.pizza_manager.delivery_station, game.pizza_manager.pizza_station] +
            game.pizza_manager.customer_manager.customers +
            [game.pizza_manager.shelf]
        ):
            if self.distance_to(obj) < 75:  # Collision threshold
                angle_rad = math.radians(self.angle)
                self.position[0] -= self.speed * math.cos(angle_rad)
                self.position[1] -= self.speed * math.sin(angle_rad)
                return
        
        # Check collision with walls
        boundary = game.settings.grid_size - 50
        if not (-boundary <= self.position[0] <= boundary and -boundary <= self.position[1] <= boundary):
            angle_rad = math.radians(self.angle)
            self.position[0] -= self.speed * math.cos(angle_rad)
            self.position[1] -= self.speed * math.sin(angle_rad)

    def _within_bounds(self, x, y):
        # Ensure the player stays within the room boundaries
        boundary = game.settings.grid_size - 50  # Adjusted for player size
        return -boundary <= x <= boundary and -boundary <= y <= boundary

    def _collides_with_pizza_table(self, x, y):
        # Check collision with the pizza table
        pizza_table = game.pizza_manager.pizza_station
        collision_distance = 150
        if math.sqrt((x - pizza_table.position[0]) ** 2 + (y - pizza_table.position[1]) ** 2) < collision_distance:
            self.near_pizza_table = True
            return True
        self.near_pizza_table = False
        return False

    def _collides_with_objects(self, x, y):
        # Check collision with all objects in the game
        collision_distance = 150
        for obj in (
            game.pizza_manager.ingredient_stations +
            [game.pizza_manager.oven, game.pizza_manager.delivery_station, game.pizza_manager.pizza_station] +
            game.pizza_manager.customer_manager.customers +
            [game.pizza_manager.shelf]
        ):
            dx = abs(x - obj.position[0])
            dy = abs(y - obj.position[1])
            if dx < collision_distance and dy < collision_distance:
                return True
        return False

class CustomerWaitingArea(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 200
        self.depth = 100
        self.height = 10
        
        # Seating positions for waiting customers
        self.seating_positions = [
            [x - 60, y + 30, z],
            [x, y + 30, z],
            [x + 60, y + 30, z],
            [x - 60, y - 30, z],
            [x, y - 30, z],
            [x + 60, y - 30, z]
        ]
        
        # Queue line markers
        self.queue_markers = []
        for i in range(5):
            self.queue_markers.append([x + self.width/2 + 30, y - 40 + i*20, z])
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        try:
            # Draw waiting area floor (elevated platform)
            glColor3f(0.7, 0.7, 0.8)  # Light blue-gray
            glutSolidCube(1)
            
            # Draw seats
            self._draw_seats()
            
            # Draw queue markers
            self._draw_queue_markers()
            
            # Draw "Waiting Area" sign
            self._draw_sign()
        finally:
            glPopMatrix()  # Ensure glPopMatrix is always called
    
    def _draw_seats(self):
        # Draw 6 seats in the waiting area
        seat_color = (0.6, 0.3, 0.3)  # Brown seats
        seat_size = 20
        seat_height = 20
        
        for pos in self.seating_positions:
            rel_x = pos[0] - self.position[0]
            rel_y = pos[1] - self.position[1]
            
            # Seat base
            glPushMatrix()
            glTranslatef(rel_x, rel_y, self.height + seat_height/2)
            glColor3f(*seat_color)
            glScalef(seat_size, seat_size, seat_height)
            glutSolidCube(1)
            glPopMatrix()
            
            # Seat back
            glPushMatrix()
            glTranslatef(rel_x, rel_y - seat_size/2, self.height + seat_height + 20)
            glColor3f(*seat_color)
            glScalef(seat_size, 5, 40)
            glutSolidCube(1)
            glPopMatrix()
            
            # Seat arms
            glPushMatrix()
            glTranslatef(rel_x + seat_size/2, rel_y, self.height + seat_height + 10)
            glColor3f(*seat_color)
            glScalef(3, seat_size, 20)
            glutSolidCube(1)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(rel_x - seat_size/2, rel_y, self.height + seat_height + 10)
            glColor3f(*seat_color)
            glScalef(3, seat_size, 20)
            glutSolidCube(1)
            glPopMatrix()
    
    def _draw_queue_markers(self):
        # Draw queue line markers
        for i, pos in enumerate(self.queue_markers):
            rel_x = pos[0] - self.position[0]
            rel_y = pos[1] - self.position[1]
            
            glPushMatrix()
            glTranslatef(rel_x, rel_y, self.height)
            
            # Pole
            glColor3f(0.7, 0.1, 0.1)  # Dark red
            gluCylinder(gluNewQuadric(), 3, 3, 80, 8, 1)
            
            # Base
            glColor3f(0.4, 0.4, 0.4)  # Dark gray
            glTranslatef(0, 0, 0)
            gluDisk(gluNewQuadric(), 0, 10, 8, 1)
            
            # Rope to next marker (except for last one)
            if i < len(self.queue_markers) - 1:
                next_pos = self.queue_markers[i + 1]
                next_rel_x = next_pos[0] - self.position[0]
                next_rel_y = next_pos[1] - self.position[1]
                
                # Draw rope
                glColor3f(0.8, 0.1, 0.1)  # Red
                glTranslatef(0, 0, 40)  # Middle height of rope
                
                glBegin(GL_LINES)
                glVertex3f(0, 0, 0)
                glVertex3f(next_rel_x - rel_x, next_rel_y - rel_y, 0)
                glEnd()
            
            glPopMatrix()
    
    def _draw_sign(self):
        # Draw "Waiting Area" sign above the area
        glPushMatrix()
        glTranslatef(0, 0, 100)
        
        # Sign board
        glColor3f(0.9, 0.9, 0.9)  # Light gray
        glPushMatrix()
        glScalef(120, 5, 40)
        glutSolidCube(1)
        glPopMatrix()
        
        # Text will be rendered by the HUD system
        
        glPopMatrix()

class Ingredient(Entity):
    def __init__(self, name, x, y, z, color=(1, 1, 1)):
        super().__init__(x, y, z)
        self.name = name
        self.color = color
        self.size = 10
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glColor3f(*self.color)
        
        if self.name == "dough":
            self.draw_dough()
        elif self.name == "sauce":
            self.draw_sauce()
        elif self.name == "cheese":
            self.draw_cheese()
        elif "vegetable" in self.name:
            self.draw_vegetable()
        elif "meat" in self.name:
            self.draw_meat()
        
        glPopMatrix()
    
    def draw_dough(self):
        # Flat circle for dough
        glColor3f(0.9, 0.8, 0.6)
        gluDisk(gluNewQuadric(), 0, 20, 20, 1)
    
    def draw_sauce(self):
        # Red sphere for sauce
        glColor3f(0.8, 0.1, 0.1)
        glutSolidSphere(self.size / 2, 10, 10)
    
    def draw_cheese(self):
        # Yellow cube for cheese
        glColor3f(1.0, 0.8, 0.0)
        glutSolidCube(self.size)
    
    def draw_vegetable(self):
        # Green cube for vegetables
        glColor3f(0.1, 0.8, 0.1)
        glutSolidCube(self.size)
    
    def draw_meat(self):
        # Red cylinder for meat
        glColor3f(0.7, 0.3, 0.3)
        gluCylinder(gluNewQuadric(), self.size/2, self.size/2, self.size/4, 10, 10)

class IngredientStation(Entity):
    def __init__(self, ingredient_type, x, y, z, color=(1, 1, 1)):
        super().__init__(x, y, z)
        self.ingredient_type = ingredient_type
        self.color = color
        self.width = 80
        self.height = 20
        self.depth = 40
    
    def get_ingredient(self):
        if self.ingredient_type == "dough":
            return Ingredient("dough", *self.position, (0.9, 0.8, 0.6))
        elif self.ingredient_type == "sauce":
            return Ingredient("sauce", *self.position, (0.8, 0.1, 0.1))
        elif self.ingredient_type == "cheese":
            return Ingredient("cheese", *self.position, (1.0, 0.8, 0.0))
        elif self.ingredient_type == "sausage":
            return Ingredient("sausage", *self.position, (0.7, 0.4, 0.3))
        elif self.ingredient_type == "peperonni":
            return Ingredient("peperonni", *self.position, (0.8, 0.2, 0.2))
        elif self.ingredient_type == "onion":
            return Ingredient("onion", *self.position, (0.9, 0.9, 0.6))
        elif self.ingredient_type == "olives":
            return Ingredient("olives", *self.position, (0.1, 0.4, 0.1))
        elif self.ingredient_type == "oregano":
            return Ingredient("oregano", *self.position, (0.6, 0.8, 0.4))
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        try:
            # Draw the ingredient shelf/station
            glColor3f(*self.color)
            glPushMatrix()
            glScalef(self.width, self.depth, self.height)
            glutSolidCube(1)
            glPopMatrix()
            
            # Draw sample of the ingredient on top
            glTranslatef(0, 0, self.height + 5)
            sample = self.get_ingredient()
            sample.draw()
        finally:
            glPopMatrix()  # Ensure glPopMatrix is always called

class Pizza(Entity):
    def __init__(self, x=0, y=0, z=0):
        super().__init__(x, y, z)
        self.ingredients = []
        self.base_added = False
        self.sauce_added = False
        self.cheese_added = False
        self.cooking_level = 0  # 0 = raw, 100 = perfectly cooked, >100 = burnt
        self.cooking_time = 0
        self.ready = False
        self.in_box = False  # Track if the pizza is in a box
    
    def add_ingredient(self, ingredient):
        if ingredient.name == "dough" and not self.base_added:
            self.base_added = True
            self.ingredients.append(ingredient)
            return True
        elif ingredient.name == "sauce" and self.base_added and not self.sauce_added:
            self.sauce_added = True
            self.ingredients.append(ingredient)
            return True
        elif ingredient.name == "cheese" and self.sauce_added and not self.cheese_added:
            self.cheese_added = True
            self.ingredients.append(ingredient)
            return True
        elif ingredient.name in ["sausage", "peperonni", "onion", "olives", "oregano"] and self.cheese_added:
            self.ingredients.append(ingredient)
            return True
        return False
    
    def is_complete(self):
        return self.base_added and self.sauce_added and self.cheese_added
    
    def is_cooked(self):
        return 80 <= self.cooking_level <= 120
    
    def is_burnt(self):
        return self.cooking_level > 120
    
    def cook(self, amount):
        if self.cooking_level < 150:  # Cap at 150
            self.cooking_level += amount
            self.cooking_time += 1
    
    def matches_order(self, order):
        # Check if pizza matches the order requirements
        if not self.is_complete() or not self.is_cooked():
            return False
            
        # Check ingredients
        required_ingredients = {}
        pizza_ingredients = {}
        
        for ingredient in order.required_ingredients:
            if ingredient not in required_ingredients:
                required_ingredients[ingredient] = 0
            required_ingredients[ingredient] += 1
            
        for ingredient in self.ingredients:
            if ingredient.name not in pizza_ingredients:
                pizza_ingredients[ingredient.name] = 0
            pizza_ingredients[ingredient.name] += 1
        
        # Check that all required ingredients are in the pizza
        for ingredient, count in required_ingredients.items():
            if ingredient not in pizza_ingredients or pizza_ingredients[ingredient] < count:
                return False
                
        return True
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        try:
            if self.in_box:
                # Draw a pizza box
                glColor3f(0.8, 0.6, 0.4)  # Brown box color
                glPushMatrix()
                glScalef(80, 80, 15)  # Box size
                glutSolidCube(1)
                glPopMatrix()
                
                # Draw box lid lines
                glLineWidth(2.0)
                glColor3f(0.5, 0.3, 0.2)  # Darker brown
                glBegin(GL_LINES)
                # X lines
                glVertex3f(-40, -40, 7.5)
                glVertex3f(40, -40, 7.5)
                glVertex3f(-40, 40, 7.5)
                glVertex3f(40, 40, 7.5)
                # Y lines
                glVertex3f(-40, -40, 7.5)
                glVertex3f(-40, 40, 7.5)
                glVertex3f(40, -40, 7.5)
                glVertex3f(40, 40, 7.5)
                glEnd()
                
                # Draw pizza logo on the box
                glColor3f(1.0, 0.0, 0.0)  # Red logo
                glPushMatrix()
                glTranslatef(0, 0, 7.6)  # Slightly above the box
                glutSolidTorus(3, 12, 20, 20)  # Pizza logo
                glPopMatrix()
            else:
                # Draw the regular pizza
                # Draw base - adapt color based on cooking level
                cooking_color = min(self.cooking_level / 100, 1.0)
                base_color = (0.9 - cooking_color * 0.5, 0.8 - cooking_color * 0.6, 0.6 - cooking_color * 0.5)
                
                # Draw the pizza base
                glColor3f(*base_color)
                gluDisk(gluNewQuadric(), 0, 30, 20, 1)
                
                height = 2  # Starting height for stacking ingredients
                
                # Draw ingredients
                for ingredient in self.ingredients:
                    if ingredient.name == "dough":
                        continue  # Base already drawn
                        
                    if ingredient.name == "sauce":
                        glColor3f(0.8, 0.1, 0.1)
                        glTranslatef(0, 0, height)
                        gluDisk(gluNewQuadric(), 0, 28, 20, 1)
                        height += 1
                    elif ingredient.name == "cheese":
                        glColor3f(1.0, 0.8, 0.0)
                        glTranslatef(0, 0, height)
                        gluDisk(gluNewQuadric(), 0, 27, 20, 1)
                        height += 1
                        height += 1
                    elif "vegetable" in ingredient.name:
                        # Randomly place vegetables on the pizza
                        for i in range(5):
                            angle = random.uniform(0, 360)
                            dist = random.uniform(0, 20)
                            x = dist * math.cos(math.radians(angle))
                            y = dist * math.sin(math.radians(angle))
                            
                            glPushMatrix()
                            glTranslatef(x, y, height)
                            glColor3f(0.1, 0.8, 0.1)
                            glutSolidCube(5)
                            glPopMatrix()
                        height += 2
                    elif "meat" in ingredient.name:
                        # Randomly place meat on the pizza
                        for i in range(5):
                            angle = random.uniform(0, 360)
                            dist = random.uniform(0, 20)
                            x = dist * math.cos(math.radians(angle))
                            y = dist * math.sin(math.radians(angle))
                            
                            glPushMatrix()
                            glTranslatef(x, y, height)
                            glRotatef(90, 1, 0, 0)
                            glColor3f(0.7, 0.3, 0.3)
                            gluCylinder(gluNewQuadric(), 2.5, 2.5, 2, 10, 10)
                            glPopMatrix()
                        height += 2
        finally:
            glPopMatrix()  # Ensure glPopMatrix is always called

class Oven(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        # Make oven 1.5 times larger
        self.width = 120  # Was 80
        self.height = 90  # Was 60
        self.depth = 90   # Was 60
        self.pizza = None
        self.cooking_time = 0
        self.cooking_speed = 1
        self.door_open = False
        
    def insert_pizza(self, pizza):
        if not self.pizza and self.door_open:
            pizza.position = self.position.copy()
            pizza.position[2] += 15  # Place pizza inside the oven (adjusted for larger size)
            self.pizza = pizza
            return True
        return False
    
    def remove_pizza(self):
        if self.pizza and self.door_open:
            pizza = self.pizza
            self.pizza = None
            return pizza
        return None
    
    def toggle_door(self):
        self.door_open = not self.door_open
    
    def update(self):
        if self.pizza and not self.door_open:
            self.cooking_time += 1
            self.pizza.cook(self.cooking_speed)
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        # Rotate 90 degrees clockwise (around Z axis)
        glRotatef(-90, 0, 0, 1)
        
        # Draw oven base with orange color
        glColor3f(0.9, 0.5, 0.1)  # Orange color
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Door should now be on the right side due to rotation
        glPushMatrix()
        door_angle = 90 if self.door_open else 0
        glTranslatef(0, -self.depth/2, 0)  # Door position adjusted for rotation
        glRotatef(door_angle, 1, 0, 0)  # Door now rotates around X axis
        glTranslatef(0, self.depth/2, 0)
        glColor3f(0.7, 0.4, 0.1)  # Darker orange for the door
        glTranslatef(0, -self.depth/2, 0)
        glScalef(self.width * 0.8, 5, self.height * 0.8)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw progress bar for cooking
        if self.pizza:
            cooking_percentage = min(self.pizza.cooking_level / 100, 1.5)
            
            glPushMatrix()
            glTranslatef(self.width/2 + 10, 0, self.height/2)  # Adjusted for rotation
            glRotatef(90, 0, 1, 0)  # Rotate progress bar to match oven orientation
            
            # Background bar
            glColor3f(0.2, 0.2, 0.2)
            glPushMatrix()
            glScalef(self.width * 0.8, 5, 10)
            glutSolidCube(1)
            glPopMatrix()
            
            # Progress bar
            if cooking_percentage <= 1.0:
                glColor3f(cooking_percentage, 1.0 - cooking_percentage, 0)
            else:
                # Burnt - show red
                glColor3f(1.0, 0, 0)
                
            glPushMatrix()
            glTranslatef(-(self.width * 0.8)/2 + (self.width * 0.8 * cooking_percentage)/2, 0, 0)
            glScalef(self.width * 0.8 * cooking_percentage, 5, 10)
            glutSolidCube(1)
            glPopMatrix()
            
            glPopMatrix()
            
            # Draw pizza in oven if door closed
            if not self.door_open:
                glPushMatrix()
                glTranslatef(0, 0, 15)  # Adjusted for larger oven
                self.pizza.draw()
                glPopMatrix()
        
        # Draw chimney on the oven
        glPushMatrix()
        glTranslatef(self.width/4, 0, self.height/2)  # Position on top of the oven

        # Main chimney cylinder
        glColor3f(0.4, 0.2, 0.1)  # Dark brown color for chimney
        gluCylinder(gluNewQuadric(), 12, 12, 45, 10, 10)  # Scaled up by 1.5

        # Chimney top rim
        glTranslatef(0, 0, 45)
        glColor3f(0.3, 0.15, 0.05)  # Darker brown for the rim
        glutSolidTorus(4.5, 13.5, 12, 12)  # Scaled up by 1.5

        # Smoke effect (if oven has pizza cooking)
        if self.pizza and not self.door_open:
            glTranslatef(0, 0, 4.5)  # Scaled up
            cooking_progress = min(self.pizza.cooking_level / 50, 1.0)
            
            # Smoke particles - more smoke as pizza cooks
            for i in range(int(5 * cooking_progress)):
                offset_x = random.uniform(-7.5, 7.5)  # Scaled up
                offset_y = random.uniform(-7.5, 7.5)  # Scaled up
                size = random.uniform(4.5, 9) * cooking_progress  # Scaled up
                
                glPushMatrix()
                glTranslatef(offset_x, offset_y, i * 4.5)  # Scaled up
                glColor4f(0.8, 0.8, 0.8, 0.7 - (i * 0.1))  # Semi-transparent gray
                glutSolidSphere(size, 8, 8)
                glPopMatrix()
        glPopMatrix()
        
        glPopMatrix()

class PizzaStation(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 300
        self.height = 10
        self.depth = 100
        self.pizza = None
    
    def create_pizza(self):
        if not self.pizza:
            pizza_pos = self.position.copy()
            pizza_pos[2] += self.height
            self.pizza = Pizza(*pizza_pos)
            return True
        return False
    
    def get_pizza(self):
        pizza = self.pizza
        self.pizza = None
        return pizza
    
    def add_ingredient(self, ingredient):
        if self.pizza:
            return self.pizza.add_ingredient(ingredient)
        return False
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Draw the station surface
        glColor3f(0.6, 0.4, 0.2)  # Wooden color
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw pizza if present
        if self.pizza:
            glTranslatef(0, 0, self.height)
            self.pizza.draw()
        
        glPopMatrix()

class DeliveryStation(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 200
        self.height = 10
        self.depth = 80
        self.pizzas = []
        self.max_pizzas = 3
    
    def add_pizza(self, pizza):
        if len(self.pizzas) < self.max_pizzas:
            pizza_pos = self.position.copy()
            pizza_pos[2] += self.height + 5 * len(self.pizzas)
            pizza.position = pizza_pos
            self.pizzas.append(pizza)
            return True
        return False
    
    def get_pizza(self):
        if self.pizzas:
            return self.pizzas.pop(0)
        return None
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Draw delivery counter
        glColor3f(0.6, 0.4, 0.2)
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw pizzas on counter
        for i, pizza in enumerate(self.pizzas):
            glPushMatrix()
            glTranslatef(0, 0, self.height + 5 * i)
            pizza.draw()
            glPopMatrix()
        
        glPopMatrix()

class Order:
    def __init__(self, level):
        self.level = level
        self.required_ingredients = ["sauce", "cheese"]  # Base ingredients (excluding dough)
        self.time_limit = 60 + 30 * level  # Seconds to complete
        self.time_remaining = self.time_limit
        self.completed = False
        self.expired = False

        # Add random toppings based on level difficulty
        num_toppings = random.randint(0, min(level, 4))
        toppings = ["sausage", "peperonni", "onion", "olives", "oregano"]
        random.shuffle(toppings)
        for i in range(num_toppings):
            self.required_ingredients.append(toppings[i])

    def update(self, delta_time):
        if not self.completed and not self.expired:
            self.time_remaining -= delta_time
            if self.time_remaining <= 0:
                self.expired = True
                return True  # Order failed
        return False

class Customer(Entity):
    def __init__(self, x, y, z, order_level):
        super().__init__(x, y, z)
        self.order = Order(order_level)
        self.happiness = 100  # 0-100 scale
        self.waiting_time = 0
        self.served = False
        self.patience = random.randint(30, 60)  # Seconds before happiness starts dropping
        
        # Assign random colors for varietyt
        self.colors = {
            'body': (
                random.randint(30, 220)/255,  # Random R
                random.randint(30, 220)/255,  # Random G
                random.randint(30, 220)/255   # Random B
            ),
            'head': (
                245/255,  #  R (skin tone)
                194/255,  #  G (skin tone)
                166/255   #  B (skin tone)
            ),
            'eyes': (1.0, 1.0, 1.0),  # White eyes
            'mouth': (0.0, 0.0, 0.0)  # Black mouth
        }
        
        # Customer body parts with properties
        self.body_parts = {
            'head': {'radius': 15, 'position': (0, 0, 70)},
            'torso': {'top_radius': 15, 'bottom_radius': 15, 'height': 60},
            'arms': {'top_radius': 5, 'bottom_radius': 3, 'height': 40},
            'legs': {'top_radius': 7, 'bottom_radius': 5, 'height': 40}
        }
    
    def update(self, delta_time):
        if not self.served:
            self.waiting_time += delta_time
            
            # Reduce happiness if waiting too long
            if self.waiting_time > self.patience:
                self.happiness -= delta_time * 5  # Lose 5 happiness per second after patience expired
                
            # Update order timer
            return self.order.update(delta_time)
        return False
    
    def receive_pizza(self, pizza):
        if not self.served:
            self.served = True
            if pizza.matches_order(self.order):
                self.order.completed = True
                return True
            else:
                # Wrong pizza
                self.happiness = 0
                return False
        return False
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Set body color based on emotional state
        if self.served:
            if self.order.completed:
                body_color = (0.1, 0.7, 0.3)  # Happy green
            else:
                body_color = (0.8, 0.1, 0.1)  # Angry red
        else:
            # Get base color but modify based on happiness
            happiness_percent = max(0, min(self.happiness / 100, 1))
            r = self.colors['body'][0] * (1.5 - happiness_percent)  # More red when unhappy
            g = self.colors['body'][1] * happiness_percent          # More green when happy
            b = self.colors['body'][2] * 0.5                        # Reduce blue component
            body_color = (min(r, 1.0), min(g, 1.0), min(b, 1.0))
        
        # Draw customer body (cylinder)
        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(), 
                    self.body_parts['torso']['top_radius'], 
                    self.body_parts['torso']['bottom_radius'], 
                    self.body_parts['torso']['height'], 10, 10)
        
        # Draw customer head (sphere)
        glTranslatef(0, 0, self.body_parts['torso']['height'] + 10)
        glColor3f(*self.colors['head'])
        glutSolidSphere(self.body_parts['head']['radius'], 10, 10)
        
        # Draw customer face
        # Eyes
        glColor3f(*self.colors['eyes'])
        glPushMatrix()
        glTranslatef(5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
        # Mouth - smile or frown based on happiness
        glColor3f(*self.colors['mouth'])
        glPushMatrix()
        glTranslatef(0, 5, 0)
        if self.served:
            if self.order.completed:
                # Happy smile
                gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
            else:
                # Sad frown
                glRotatef(180, 0, 0, 1)
                gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
        else:
            happiness_percent = max(0, min(self.happiness / 100, 1))
            if happiness_percent > 0.5:
                # Neutral to happy
                gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
            else:
                # Neutral to sad
                glRotatef(180, 0, 0, 1)
                gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
        glPopMatrix()
        
        # Draw arms
        glPushMatrix()
        glTranslatef(-self.body_parts['torso']['top_radius'] - 2, 
                     0, 
                     -self.body_parts['torso']['height'])
        glRotatef(30, 0, 1, 0)  # Angle the arm outward
        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(), 
                    self.body_parts['arms']['top_radius'], 
                    self.body_parts['arms']['bottom_radius'], 
                    self.body_parts['arms']['height'], 8, 2)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.body_parts['torso']['top_radius'] + 2, 
                     0, 
                     -self.body_parts['torso']['height'])
        glRotatef(-30, 0, 1, 0)  # Angle the arm outward
        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(), 
                    self.body_parts['arms']['top_radius'], 
                    self.body_parts['arms']['bottom_radius'], 
                    self.body_parts['arms']['height'], 8, 2)
        glPopMatrix()
        
        # Remove the order bubble
        # if not self.served:
        #     self._draw_order_bubble()
        
        glPopMatrix()

            
# Kitchen related classes and functionality
class Kitchen:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.floor_color1 = (0.9, 0.9, 0.9)  # Light gray
        self.floor_color2 = (0.8, 0.8, 0.8)  # Slightly darker gray
        self.wall_color = (0.7, 0.7, 0.8)    # Wall color
        self.door_color = (0.6, 0.4, 0.2)    # Wooden door color
        self.door_handle_color = (0.8, 0.8, 0.1)  # Brass handle color
        
    def draw(self):
        # Draw kitchen floor with checkered pattern
        tile_size = 40
        for i in range(-self.grid_size, self.grid_size, tile_size):
            for j in range(-self.grid_size, self.grid_size, tile_size):
                if (i + j) // tile_size % 2 == 0:
                    glColor3f(*self.floor_color1)
                else:
                    glColor3f(*self.floor_color2)
                    
                glBegin(GL_QUADS)
                glVertex3f(i, j, 0)
                glVertex3f(i + tile_size, j, 0)
                glVertex3f(i + tile_size, j + tile_size, 0)
                glVertex3f(i, j + tile_size, 0)
                glEnd()
        
        # Draw kitchen walls
        wall_height = 100  # Reduced from 200
        
        # Back wall (negative Y)
        glColor3f(*self.wall_color)
        glBegin(GL_QUADS)
        glVertex3f(-self.grid_size, -self.grid_size, 0)
        glVertex3f(self.grid_size, -self.grid_size, 0)
        glVertex3f(self.grid_size, -self.grid_size, wall_height)
        glVertex3f(-self.grid_size, -self.grid_size, wall_height)
        glEnd()
        
        # Front wall (positive Y)
        glBegin(GL_QUADS)
        glVertex3f(-self.grid_size, self.grid_size, 0)
        glVertex3f(self.grid_size, self.grid_size, 0)
        glVertex3f(self.grid_size, self.grid_size, wall_height)
        glVertex3f(-self.grid_size, self.grid_size, wall_height)
        glEnd()
        
        # Left wall (negative X)
        glBegin(GL_QUADS)
        glVertex3f(-self.grid_size, -self.grid_size, 0)
        glVertex3f(-self.grid_size, self.grid_size, 0)
        glVertex3f(-self.grid_size, self.grid_size, wall_height)
        glVertex3f(-self.grid_size, -self.grid_size, wall_height)
        glEnd()
        
        # Right wall (positive X) with door cutout
        glBegin(GL_QUADS)
        # Bottom section (below door)
        glVertex3f(self.grid_size, -self.grid_size, 0)
        glVertex3f(self.grid_size, self.grid_size - 100, 0)
        glVertex3f(self.grid_size, self.grid_size - 100, wall_height)
        glVertex3f(self.grid_size, -self.grid_size, wall_height)
        
        # Top section (above door)
        glVertex3f(self.grid_size, self.grid_size - 100, 180)
        glVertex3f(self.grid_size, self.grid_size, 180)
        glVertex3f(self.grid_size, self.grid_size, wall_height)
        glVertex3f(self.grid_size, self.grid_size - 100, wall_height)
        
        # Side section (beside door)
        glVertex3f(self.grid_size, self.grid_size - 40, 0)
        glVertex3f(self.grid_size, self.grid_size, 0)
        glVertex3f(self.grid_size, self.grid_size, 180)
        glVertex3f(self.grid_size, self.grid_size - 40, 180)
        glEnd()
        
        # Draw door in corner (positive X, positive Y)
        glPushMatrix()
        glColor3f(*self.door_color)
        
        # Door frame
        glBegin(GL_QUADS)
        glVertex3f(self.grid_size - 5, self.grid_size - 100, 0)
        glVertex3f(self.grid_size - 5, self.grid_size - 40, 0)
        glVertex3f(self.grid_size - 5, self.grid_size - 40, 180)
        glVertex3f(self.grid_size - 5, self.grid_size - 100, 180)
        glEnd()
        
        # Door handle
        glPushMatrix()
        glColor3f(*self.door_handle_color)
        glTranslatef(self.grid_size - 8, self.grid_size - 60, 90)
        glutSolidSphere(5, 10, 10)
        glPopMatrix()
        
        # Door hinges
        glColor3f(0.4, 0.4, 0.4)  # Dark gray for hinges
        glPushMatrix()
        glTranslatef(self.grid_size - 5, self.grid_size - 95, 30)
        glutSolidCube(8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.grid_size - 5, self.grid_size - 95, 150)
        glutSolidCube(8)
        glPopMatrix()
        
        glPopMatrix()
        
        # Remove the roof by skipping the ceiling drawing code
        # glBegin(GL_QUADS)
        # glVertex3f(-self.grid_size, -self.grid_size, 300)  # Ceiling code removed
        # glVertex3f(self.grid_size, -self.grid_size, 300)
        # glVertex3f(self.grid_size, self.grid_size, 300)
        # glVertex3f(-self.grid_size, self.grid_size, 300)
        # glEnd()

class Shelf(Entity):
    def __init__(self, x, y, z, width=200, depth=50, height=150):
        super().__init__(x, y, z)
        self.width = width
        self.depth = depth
        self.height = height
        self.num_shelves = 3  # Number of horizontal shelves
        self.shelf_thickness = 5
        self.shelf_color = (0.6, 0.4, 0.2)  # Wooden color
        self.support_color = (0.5, 0.3, 0.15)  # Darker wood for supports
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Draw the back panel
        glColor3f(0.5, 0.3, 0.3)  # Darker brown for the back panel
        glPushMatrix()
        glTranslatef(0, -self.depth/2, self.height/2)
        glScalef(self.width, 2, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw the shelves (horizontal boards)
        shelf_spacing = self.height / (self.num_shelves + 1)
        for i in range(self.num_shelves + 1):  # +1 for bottom and top shelves
            y_pos = 0
            z_pos = i * shelf_spacing
            
            glColor3f(*self.shelf_color)
            glPushMatrix()
            glTranslatef(0, y_pos, z_pos)
            glScalef(self.width, self.depth, self.shelf_thickness)
            glutSolidCube(1)
            glPopMatrix()
        
        # Draw the side supports
        glColor3f(*self.support_color)
        
        # Left support
        glPushMatrix()
        glTranslatef(-self.width/2 + 2, 0, self.height/2)
        glScalef(4, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Right support
        glPushMatrix()
        glTranslatef(self.width/2 - 2, 0, self.height/2)
        glScalef(4, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw some items on the shelves
        self._draw_shelf_items()
        
        glPopMatrix()
    
    def _draw_shelf_items(self):
        # This method adds some decorative items to the shelves
        shelf_spacing = self.height / (self.num_shelves + 1)
        
        # Draw items on first shelf
        glPushMatrix()
        glTranslatef(-self.width/3, 0, shelf_spacing + self.shelf_thickness)
        
        # Draw a cookbook
        glColor3f(0.8, 0.2, 0.2)  # Red book
        glPushMatrix()
        glScalef(30, 20, 40)
        glutSolidCube(1)
        glPopMatrix()
        glPopMatrix()
        
        # Draw items on second shelf
        glPushMatrix()
        glTranslatef(self.width/4, 0, 2 * shelf_spacing + self.shelf_thickness)
        
        # Draw a jar
        glColor3f(0.7, 0.7, 0.9)  # Light blue jar
        gluCylinder(gluNewQuadric(), 15, 15, 30, 12, 2)
        
        # Jar lid
        glTranslatef(0, 0, 30)
        glColor3f(0.4, 0.4, 0.4)
        gluDisk(gluNewQuadric(), 0, 15, 12, 1)
        glPopMatrix()
        
        # Draw items on third shelf
        glPushMatrix()
        glTranslatef(-self.width/5, 0, 3 * shelf_spacing + self.shelf_thickness)
        
        # Draw a mixing bowl
        glColor3f(0.9, 0.9, 0.9)  # White bowl
        glPushMatrix()
        glRotatef(180, 1, 0, 0)
        glutSolidCone(25, 15, 12, 1)
        glPopMatrix()
        glPopMatrix()

class OrderArea(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 200
        self.depth = 40
        self.height = 100
        self.current_order = None  # Track the current order to display
        self.display_message = None  # Custom message to display

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Draw order counter
        glColor3f(0.3, 0.3, 0.5)  # Dark blue-gray
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw counter top
        glColor3f(0.9, 0.9, 0.9)  # Light gray
        glPushMatrix()
        glTranslatef(0, 0, self.height/2 + 5)
        glScalef(self.width + 10, self.depth + 10, 10)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw menu board above counter
        self._draw_menu_board()
        
        glPopMatrix()
    
    def _draw_menu_board(self):
        # Draw menu board
        glPushMatrix()
        glTranslatef(0, 0, self.height + 50)  # Position the board above the counter

        # Board background
        glColor3f(0.2, 0.2, 0.2)  # Dark gray
        glPushMatrix()
        glScalef(180, 5, 70)  # Adjust the size of the board
        glutSolidCube(1)
        glPopMatrix()

        # Display the current order or a custom message
        glColor3f(1, 1, 1)  # White text
        if self.display_message:
            glRasterPos3f(-70, -20, 0)  # Center the message
            for ch in self.display_message:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        elif self.current_order:
            # Render each ingredient on a new line
            for i, ingredient in enumerate(self.current_order.required_ingredients):
                glRasterPos3f(-70, -20, 30 - i * 10)  # Adjust position for better alignment
                for ch in ingredient:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

        glPopMatrix()

class KitchenCounter(Entity):
    def __init__(self, x, y, z, width=100, depth=60, height=80):
        super().__init__(x, y, z)
        self.width = width
        self.depth = depth
        self.height = height
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
        # Draw counter top
        glColor3f(0.8, 0.8, 0.8)  # Light gray counter top
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw counter edges with darker color
        glColor3f(0.6, 0.6, 0.6)
        edge_thickness = 5
        
        # Top edge
        glPushMatrix()
        glTranslatef(0, self.depth/2 + edge_thickness/2, self.height/2)
        glScalef(self.width + edge_thickness*2, edge_thickness, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Bottom edge
        glPushMatrix()
        glTranslatef(0, -self.depth/2 + edge_thickness/2, self.height/2)
        glScalef(self.width + edge_thickness*2, edge_thickness, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Left edge
        glPushMatrix()
        glTranslatef(-self.width/2 + edge_thickness/2, 0, self.height/2)
        glScalef(edge_thickness, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Right edge
        glPushMatrix()
        glTranslatef(self.width/2 + edge_thickness/2, 0, self.height/2)
        glScalef(edge_thickness, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        glPopMatrix()

class PizzaManager:
    def __init__(self):
        self.pizza_station = PizzaStation(-150, -450, 80)
        self.ingredient_stations = [
            IngredientStation("dough", -250, 150, 30, color=(0.9, 0.8, 0.6)),
            IngredientStation("sauce", -150, 150, 30, color=(0.8, 0.1, 0.1)),
            IngredientStation("cheese", -50, 150, 30, color=(1.0, 0.8, 0.0)),
            IngredientStation("sausage", 50, 150, 30, color=(0.7, 0.4, 0.3)),
            IngredientStation("peperonni", 150, 150, 30, color=(0.8, 0.2, 0.2)),
            IngredientStation("onion", 250, 150, 30, color=(0.9, 0.9, 0.6)),
            IngredientStation("olives", 350, 150, 30, color=(0.1, 0.4, 0.1)),
            IngredientStation("oregano", 450, 150, 30, color=(0.6, 0.8, 0.4))
        ]
        # Move oven beside the pizza-making table
        self.oven = Oven(-150, -300, 30)
        self.delivery_station = DeliveryStation(100, 150, 80)
        self.customer_manager = CustomerManager()
        self.shelf = Shelf(-450, -500, 0)
        
    def update(self, delta_time, player):
        self.oven.update()
        self.customer_manager.update(delta_time)
        
        # Check interactions
        for station in self.ingredient_stations:
            if player.distance_to(station) < 50 and not player.holding_ingredient:
                player.pick_up_ingredient(station.get_ingredient())
                break
        
        if player.distance_to(self.pizza_station) < 50:
            if player.holding_ingredient:
                player.place_ingredient(self.pizza_station.pizza)
            elif not player.holding_pizza and self.pizza_station.pizza and self.pizza_station.pizza.is_complete():
                player.pick_up_pizza(self.pizza_station.pizza)
                self.pizza_station.pizza = None
            elif not self.pizza_station.pizza and player.near_pizza_table:
                # Start pizza-making process
                self.pizza_station.create_pizza()
        
        if player.distance_to(self.oven) < 50:
            if player.holding_pizza:
                self.oven.toggle_door()
                if player.place_pizza(self.oven):
                    self.oven.toggle_door()
            elif self.oven.pizza and self.oven.pizza.is_cooked():
                self.oven.toggle_door()
                pizza = self.oven.remove_pizza()
                if pizza:
                    player.pick_up_pizza(pizza)
                    self.oven.toggle_door()
        
        if player.distance_to(self.delivery_station) < 50 and player.holding_pizza:
            player.place_pizza(self.delivery_station)
        
        for customer in self.customer_manager.customers:
            if player.distance_to(customer) < 50 and player.holding_pizza:
                if player.place_pizza(customer):
                    self.customer_manager.remove_customer(customer)
                    break
    
    def draw(self):
        # Draw all kitchen elements
        for station in self.ingredient_stations:
            station.draw()
        self.pizza_station.draw()
        self.oven.draw()
        self.delivery_station.draw()
        self.customer_manager.draw()
        self.shelf.draw()

class OrderGenerator:
    def __init__(self):
        self.current_order = None
        self.order_timer = 0
        self.order_interval = 60  # Seconds between orders
        self.max_concurrent_orders = 3
        self.active_orders = []
        
    def update(self, delta_time, game_settings):
        self.order_timer += delta_time
        
        # Generate new orders based on level
        if self.order_timer >= self.order_interval and len(self.active_orders) < self.max_concurrent_orders:
            new_order = Order(game_settings.current_level)
            self.active_orders.append(new_order)
            self.order_timer = 0
            
        # Update existing orders
        completed_orders = []
        failed_orders = []
            
        for order in self.active_orders:
            if order.expired:
                failed_orders.append(order)
            elif order.completed:
                completed_orders.append(order)
                game_settings.score += 100 * game_settings.current_level
            else:
                if order.update(delta_time):
                    game_settings.mistakes += 1
                    
        # Remove completed and failed orders
        for order in completed_orders:
            self.active_orders.remove(order)
                    
        for order in failed_orders:
            self.active_orders.remove(order)
            
        return len(failed_orders)

class CustomerManager:
    def __init__(self):
        self.customers = []  # Customers at the counter
        self.waiting_customers = []  # Customers in the waiting area
        self.max_customers = 1  # Only 1 customer at the counter
        self.max_waiting = 4  # Maximum 4 customers in the waiting area
        self.spawn_timer = 0
        self.spawn_interval = 20  # Seconds between customer spawns
        self.waiting_area = CustomerWaitingArea(-450, 400, 0)  # Position in corner opposite to oven
        self.order_area = OrderArea(-300, 150, 0)  # Near delivery station
        self.received_order = False  # Change from None to False
        self.display_message = None  # Custom message to display
        
    def update(self, delta_time):
        self.spawn_timer += delta_time
        
        # Spawn new customers if we have space in the waiting area
        if self.spawn_timer >= self.spawn_interval and len(self.waiting_customers) < self.max_waiting:
            new_customer = Customer(0, 0, 0, random.randint(1, 3))
            # Position at a free seat in the waiting area
            if len(self.waiting_customers) < len(self.waiting_area.seating_positions):
                pos = self.waiting_area.seating_positions[len(self.waiting_customers)]
                new_customer.position = [pos[0], pos[1], pos[2] + 30]  # Adjust height to sit on seat
                self.waiting_customers.append(new_customer)
                self.spawn_timer = 0
        
        # Move customers from waiting area to the counter if space is available
        if len(self.customers) < self.max_customers and len(self.waiting_customers) > 0:
            next_customer = self.waiting_customers.pop(0)
            # Position the customer slightly behind the counter
            next_customer.position = [
                self.order_area.position[0],
                self.order_area.position[1] + 50,  # Move behind the table
                self.order_area.position[2]
            ]
            self.customers.append(next_customer)
            self.order_area.current_order = next_customer.order  # Set the current order for the menu board
        
        # Update existing customers
        for customer in self.customers:
            customer.update(delta_time)

        for customer in self.waiting_customers:
            customer.waiting_time += delta_time  # Waiting customers don't have active orders yet
            customer.update(delta_time)
    
    def receive_order(self, player):
        """Receive an order from the customer."""
        for customer in self.customers:
            distance = player.distance_to(self.order_area) 
            if distance < 100:  # Interaction range
                # Mark the order as received
                self.received_order = True  # Change to boolean
                self.current_order = customer.order
                self.order_area.current_order = None
                self.order_area.display_message = "Order is received"
                
                print(f"Order received! Required ingredients: {customer.order.required_ingredients}")
                return True
        return False
    
    def remove_customer(self, customer):
        if customer in self.customers:
            self.customers.remove(customer)
            self.order_area.current_order = None  # Clear the menu board when the customer leaves
            self.received_order = False  # Reset when customer leaves
    
    def draw(self):
        # Draw the physical waiting area
        self.waiting_area.draw()
        self.order_area.draw()
        
        # Draw customers at the counter
        for customer in self.customers:
            customer.draw()

        # Draw waiting customers
        for customer in self.waiting_customers:
            customer.draw()

class HUD:
    def __init__(self, game_settings):
        self.game_settings = game_settings
        self.font = GLUT_BITMAP_HELVETICA_18
        
    def draw_text(self, x, y, text, font=None):
        if not font:
            font = self.font
            
        glColor3f(1, 1, 1)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.game_settings.window_width, 0, self.game_settings.window_height)  # Use new window size
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glRasterPos2f(x, y)
        for ch in text:
            glutBitmapCharacter(font, ord(ch))
            
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def draw(self):
        # Draw game information
        if not self.game_settings.started:
            self.draw_text(250, 400, "Pizza Ready!")
            self.draw_text(250, 380, "Press any key to start")
        elif self.game_settings.game_over:
            self.draw_text(300, 400, "Game Over!")
            self.draw_text(300, 380, f"Final Score: {self.game_settings.score}")
            self.draw_text(300, 360, "Press R to restart")
        else:
            # Game stats during gameplay
            self.draw_text(10, 780, f"Level: {self.game_settings.current_level}")
            self.draw_text(150, 780, f"Score: {self.game_settings.score}")
            self.draw_text(300, 780, f"Mistakes: {self.game_settings.mistakes}/{self.game_settings.mistakes_limit}")
            
            # Time remaining
            minutes = int(self.game_settings.time_remaining / 60)
            seconds = int(self.game_settings.time_remaining % 60)
            self.draw_text(500, 780, f"Time: {minutes:02d}:{seconds:02d}")
            
            # Draw instructions
            self.draw_text(10, 30, "WASD: Move, F: Interact, C: Camera, R: Restart")

class PizzaGame:
    def __init__(self):
        self.settings = GameSettings()
        self.camera = Camera()
        self.player = Player()
        self.kitchen = Kitchen(self.settings.grid_size)
        self.pizza_manager = PizzaManager()
        self.hud = HUD(self.settings)
        self.input_manager = InputManager()  # Add this line
        self.counters = [
            KitchenCounter(-150, -450, 0, width=300, depth=80),  # Ingredient counter
            KitchenCounter(100, 150, 0, width=200, depth=80)     # delivery counter
        ]
        self.order_generator = OrderGenerator()
        self.last_time = 0
        self.pizza_cost = 0  # Track the cost of the current pizza
        self.pizza_making_active = False  # Flag for 2D pizza-making window
        self.current_customer = None  # Track the customer being served
        
    def reset_game(self):
        self.settings = GameSettings()
        self.player = Player()
        self.pizza_manager = PizzaManager()
        self.order_generator = OrderGenerator()
        self.settings = GameSettings()
        
    def start_game(self):
        self.settings.started = True
        self.last_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0

    def start_pizza_making(self):
        """Switch to pizza making mode"""
        global toppings, bread_before_oven, bread_after_oven, pizza_in_box
        global pizza_box_open, pizza_box_closed, pizza_toppings, cooking_in_progress
        
        # Reset all pizza making state variables
        toppings = {
            "sauce": False,
            "cheese": False,
            "sausage": False,
            "pepperoni": False,
            "onion": False,
            "black_olive": False,
            "oregano": False
        }
        bread_before_oven = False
        bread_after_oven = False
        pizza_in_box = False
        pizza_box_open = True
        pizza_box_closed = False
        pizza_toppings = []
        cooking_in_progress = False
        
        if self.pizza_manager.customer_manager.received_order:
            self.pizza_making_active = True
            print("Starting pizza making view...")
        else:
            print("Cannot start making pizza without an order!")

    def finish_pizza_making(self):
        """Finish the pizza-making process and return to the 3D game."""
        self.pizza_making_active = False
        self.player.pick_up_pizza(self.pizza_manager.pizza_station.get_pizza())
        
        # Reset OpenGL state for 3D mode
        self.camera.setup()
        self.camera.position_camera(self.player)
    
    def finish_pizza_making_with_box(self):
        """Finish pizza-making and package the pizza into a box"""
        try:
            if self.pizza_manager.pizza_station.pizza and self.pizza_manager.pizza_station.pizza.is_complete():
                pizza = self.pizza_manager.pizza_station.get_pizza()
                pizza.in_box = True  # Mark the pizza as being in a box
                self.player.holding_pizza = pizza
                
                # IMPORTANT: Set mode flag to false AFTER getting the pizza
                self.pizza_making_active = False
                print("Pizza packaged in a box and ready for delivery!")
            else:
                print("Cannot box an incomplete pizza! Need dough, sauce, and cheese at minimum.")
        except Exception as e:
            print(f"Error in finish_pizza_making_with_box: {e}")
        
    def handle_customer_interaction(self):
        """Handle interaction with the customer at the counter."""
        if self.pizza_manager.customer_manager.receive_order(self.player):
            self.pizza_manager.customer_manager.order_area.display_message = "Order received!"
            self.pizza_manager.customer_manager.received_order = True
            print("Order received from customer!")
        else:
            print("No customer to interact with or already have an order!")
    
    def update(self):
        if not self.settings.started or self.settings.game_over:
            return
            
        # Calculate delta time
        current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Update time remaining
        self.settings.time_remaining -= delta_time
        
        # Update based on current mode
        if self.pizza_making_active:
            # Handle pizza making updates
            self.update_pizza_making(delta_time)
        else:
            # Handle regular game updates
            self.pizza_manager.update(delta_time, self.player)
            self.order_generator.update(delta_time, self.settings)
        
        # Check game state
        if self.settings.time_remaining <= 0 or self.settings.mistakes >= self.settings.mistakes_limit:
            self.settings.game_over = True
            
        # Check for level completion
        if self.settings.score >= self.settings.current_level * 500:
            self.settings.current_level += 1
            self.settings.time_remaining = 180  # Reset timer for next level
    
    
    def update_pizza_making(self, delta_time):
        """Handle the 2D pizza-making process."""
        if not self.pizza_manager.pizza_station.pizza:
            return
        
        # Initialize selected_toppings attribute if it doesn't exist
        if not hasattr(self, 'selected_toppings'):
            self.selected_toppings = []
        
        # Example logic for adding ingredients
        if self.input_manager.is_key_pressed(b'd'):  # Add dough
            if not self.pizza_manager.pizza_station.pizza.base_added:
                self.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("dough", 0, 0, 0)
                )
                self.pizza_cost += 5  # Example cost for dough
        if self.input_manager.is_key_pressed(b's'):  # Add sauce
            if not self.pizza_manager.pizza_station.pizza.sauce_added:
                self.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("sauce", 0, 0, 0)
                )
                self.pizza_cost += 2  # Example cost for sauce
                self.selected_toppings = []  # Clear selection after adding
        if self.input_manager.is_key_pressed(b'c'):  # Add cheese
            if not self.pizza_manager.pizza_station.pizza.sauce_added:
                print("You need to add sauce first!")
            elif not self.pizza_manager.pizza_station.pizza.cheese_added:
                self.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("cheese", 0, 0, 0)
                )
                self.pizza_cost += 3  # Example cost for cheese
                self.selected_toppings = []  # Clear selection after adding
        if self.input_manager.is_key_pressed(b'v'):  # Add vegetable
            if not self.pizza_manager.pizza_station.pizza.cheese_added:
                print("You need to add cheese first!")
            else:
                # Add a random vegetable
                veg_type = random.choice(["vegetable1", "vegetable2", "onion", "olives"])
                self.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient(veg_type, 0, 0, 0)
                )
                self.pizza_cost += 1  # Example cost for vegetable
                self.selected_toppings = []  # Clear selection after adding
        if self.input_manager.is_key_pressed(b'm'):  # Add meat
            if not self.pizza_manager.pizza_station.pizza.cheese_added:
                print("You need to add cheese first!")
            else:
                # Add a random meat
                meat_type = random.choice(["meat1", "meat2", "sausage", "peperonni"])
                self.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient(meat_type, 0, 0, 0)
                )
                self.pizza_cost += 4  # Example cost for meat
                self.selected_toppings = []  # Clear selection after adding
        
        # Finish pizza-making process
        if self.input_manager.is_key_pressed(b'f'):  # Finish pizza
            if self.pizza_manager.pizza_station.pizza.is_complete():
                self.finish_pizza_making()
            else:
                print("Pizza is not complete! You need dough, sauce, and cheese at minimum.")
    
    def render(self):
        """Unified render function that handles both 3D and pizza making views"""
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.pizza_making_active:
            self.render_pizza_making()
        else:
            # 3D KITCHEN VIEW (unchanged)
            self.camera.setup()
            self.camera.position_camera(self.player)
            
            # Draw 3D game elements
            self.kitchen.draw()
            for counter in self.counters:
                counter.draw()
            self.pizza_manager.draw()
            self.player.draw(game_over=self.settings.game_over, camera_mode=self.camera.mode)
            self.hud.draw()
        
        # Swap buffers only once
        glutSwapBuffers()

    def render_pizza_making(self):
        """Direct port of the display function from pizza_making.py"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(-900, 900, -350, 450)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Platform and background
        self._pm_draw_rect(-900, -350, 1800, 700, (0.4, 0.7, 1))
        self._pm_draw_rect(-900, -350, 1800, 250, (0.5, 0.5, 0.5))
        
        self._pm_draw_toppings_bar()
        self._pm_draw_dough()
        self._pm_draw_instructions()
        self._pm_draw_oven()
        self._pm_draw_pizza_box()
        self._pm_draw_pizza()
        self._pm_draw_pizza_in_box()
        
        # Restore matrices
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

# Update keyboard callback function
def keyboard_callback(key, x, y):
    if not game.settings.started:
        game.start_game()
        return

    # Always track key presses
    game.input_manager.key_down(key)
    
    if game.pizza_making_active:
        # Handle pizza making mode keys
        if key == b'b' or key == b'B':  # Box and finish pizza
            game.finish_pizza_making_with_box()
        elif key == b'd' or key == b'D':  # Add dough
            if game.pizza_manager.pizza_station.pizza and not game.pizza_manager.pizza_station.pizza.base_added:
                game.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("dough", 0, 0, 0, color=(0.9, 0.8, 0.6))
                )
        elif key == b's' or key == b'S':  # Add sauce
            if game.pizza_manager.pizza_station.pizza and game.pizza_manager.pizza_station.pizza.base_added:
                game.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("sauce", 0, 0, 0, color=(0.8, 0.1, 0.1))
                )
        elif key == b'c' or key == b'C':  # Add cheese
            if game.pizza_manager.pizza_station.pizza and game.pizza_manager.pizza_station.pizza.sauce_added:
                game.pizza_manager.pizza_station.pizza.add_ingredient(
                    Ingredient("cheese", 0, 0, 0, color=(1.0, 0.8, 0.0))
                )
        # Other pizza-making keys...
    else:
        # Regular game mode keys
        if key == b'p' or key == b'P':  # Start pizza making
            if game.player.near_pizza_table:
                if game.pizza_manager.customer_manager.received_order:
                    game.start_pizza_making()
                else:
                    print("Cannot start making pizza without an order!")
        elif key == b'f' or key == b'F':  # Interact with customers
            game.handle_customer_interaction()
        elif key == b'w' or key == b'W':  # Move forward
            game.player.move_forward()
        elif key == b's' or key == b'S':  # Move backward
            game.player.move_backward()
        elif key == b'a' or key == b'A':  # Move left
            game.player.move_left()
        elif key == b'd' or key == b'D':  # Move right
            game.player.move_right()
        elif key == b'q' or key == b'Q':  # Turn left
            game.player.turn_left()
        elif key == b'e' or key == b'E':  # Turn right
            game.player.turn_right()
        elif key == b'c' or key == b'C':  # Toggle camera
            game.camera.toggle_mode()
        elif key == b'r' or key == b'R':  # Restart
            game.reset_game()

def keyboard_up_callback(key, x, y):
    game.input_manager.key_up(key)

def special_key_callback(key, x, y):
    if key == GLUT_KEY_UP:
        game.camera.move("up")  # Zoom in
    elif key == GLUT_KEY_DOWN:
        game.camera.move("down")  # Zoom out
    elif key == GLUT_KEY_LEFT:
        game.camera.move("left")  # Rotate camera left
    elif key == GLUT_KEY_RIGHT:
        game.camera.move("right")  # Rotate camera right

def mouse_callback(button, state, x, y):
    pass  # We'll use mouse events for pizza making 

# Add this before the main() function
def initialize_game():
    """Initialize the game state and create global game instance"""
    global game
    game = PizzaGame()
    
    # Initialize OpenGL settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.0, 0.0, 0.0, 0.0)  # Black background

def check_cooking_timer(value):
    global cooking_in_progress, bread_before_oven, bread_after_oven, cooking_start_time
    
    if cooking_in_progress:
        current_time = time.time()
        if current_time - cooking_start_time >= cooking_duration:
            cooking_in_progress = False
            bread_before_oven = False
            bread_after_oven = True
            
    glutTimerFunc(100, check_cooking_timer, 0)
# Add this if not already present
def display_callback():
    """GLUT display callback"""
    game.render()

def idle_callback():
    """GLUT idle callback"""
    game.update()
    glutPostRedisplay()

def main():
    # Initialize GLUT first
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    # Create window before any OpenGL calls
    glutInitWindowSize(1200, 600)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Pizza Ready")
    
    # Now initialize OpenGL settings after window creation
    glEnable(GL_DEPTH_TEST)
    
    # Initialize game after OpenGL context is created
    initialize_game()
    
    # Register callbacks
    glutDisplayFunc(display_callback)
    glutKeyboardFunc(keyboard_callback) 
    glutKeyboardUpFunc(keyboard_up_callback)
    glutSpecialFunc(special_key_callback)
    glutMouseFunc(mouse_callback)
    glutIdleFunc(idle_callback)
    glutTimerFunc(100, check_cooking_timer, 0)
    
    glutMainLoop()



if __name__ == '__main__':
    main()
