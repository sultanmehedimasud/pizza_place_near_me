import math
import random
import time
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

class Camera_Pizza:
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
            # Camera is positioned at the top of player's head and looks in the direction the player is facing
            cam_height = 110
            look_x = player.position[0] + 100 * math.cos(math.radians(player.angle))
            look_y = player.position[1] + 100 * math.sin(math.radians(player.angle)) + 70
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
        self.holding_delivery_box = False # Track if holding delivery box

        # Adjust torso to touch hands
        self.body_parts = {
            'head': {'radius': 18, 'color': (237/255, 192/255, 178/255), 'position': (0, 0, 80)},
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
        self._check_collision("forward")

    def move_backward(self):
        angle_rad = math.radians(self.angle)
        new_x = self.position[0] - self.speed * math.cos(angle_rad)
        new_y = self.position[1] - self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision("backward")

    def move_left(self):
        angle_rad = math.radians(self.angle + 90)
        new_x = self.position[0] + self.speed * math.cos(angle_rad)
        new_y = self.position[1] + self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y) and not self._collides_with_objects(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision("left")

    def move_right(self):
        angle_rad = math.radians(self.angle - 90)
        new_x = self.position[0] + self.speed * math.cos(angle_rad)
        new_y = self.position[1] + self.speed * math.sin(angle_rad)
        if self._within_bounds(new_x, new_y) and not self._collides_with_objects(new_x, new_y):
            self.position[0] = new_x
            self.position[1] = new_y
        self._check_collision("right")

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

        # Draw the pizza box if the player is holding it
        if self.holding_delivery_box:
            self._draw_pizza_box_in_hand()

        glPopMatrix()

    def _draw_pizza_box_in_hand(self):
        """Draw the pizza box in the player's hand."""
        glPushMatrix()
        # Position the box near the player's hand
        glTranslatef(20 * math.cos(math.radians(self.angle)), 20 * math.sin(math.radians(self.angle)), 40)
        glColor3f(0.8, 0.6, 0.4)  # Pizza box color
        glScalef(30, 30, 5)  # Scale to make it look like a pizza box
        glutSolidCube(1)  # Draw the box
        glPopMatrix()

    def _check_collision(self, direction):
        """
        Check for collisions with objects and walls, and adjust the player's position accordingly.
        :param direction: The direction of movement ('forward', 'backward', 'left', 'right').
        """
        collision_distance = 100  # Collision threshold

        # Check collision with objects (including waiting area)
        for obj in (
            game.pizza_manager.ingredient_stations +
            [game.pizza_manager.oven, game.pizza_manager.delivery_station, game.pizza_manager.pizza_station] +
            game.pizza_manager.customer_manager.customers +
            [game.pizza_manager.shelf, game.pizza_manager.customer_manager.waiting_area]  # Add waiting area here
        ):
            if self.distance_to(obj) < collision_distance:
                angle_rad = math.radians(self.angle)
                if direction == "forward":
                    self.position[0] -= self.speed * math.cos(angle_rad)
                    self.position[1] -= self.speed * math.sin(angle_rad)
                elif direction == "backward":
                    self.position[0] += self.speed * math.cos(angle_rad)
                    self.position[1] += self.speed * math.sin(angle_rad)
                elif direction == "left":
                    self.position[0] -= self.speed * math.cos(angle_rad + math.pi / 2)
                    self.position[1] -= self.speed * math.sin(angle_rad + math.pi / 2)
                elif direction == "right":
                    self.position[0] -= self.speed * math.cos(angle_rad - math.pi / 2)
                    self.position[1] -= self.speed * math.sin(angle_rad - math.pi / 2)
                return  # Stop further checks if a collision is detected

        # Check collision with walls
        boundary = game.settings.grid_size - 50
        if not (-boundary <= self.position[0] <= boundary and -boundary <= self.position[1] <= boundary):
            angle_rad = math.radians(self.angle)
            if direction == "forward":
                self.position[0] -= self.speed * math.cos(angle_rad)
                self.position[1] -= self.speed * math.sin(angle_rad)
            elif direction == "backward":
                self.position[0] += self.speed * math.cos(angle_rad)
                self.position[1] += self.speed * math.sin(angle_rad)
            elif direction == "left":
                self.position[0] -= self.speed * math.cos(angle_rad + math.pi / 2)
                self.position[1] -= self.speed * math.sin(angle_rad + math.pi / 2)
            elif direction == "right":
                self.position[0] -= self.speed * math.cos(angle_rad - math.pi / 2)
                self.position[1] -= self.speed * math.sin(angle_rad - math.pi / 2)

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
        # Check collision with all objects in the game, including waiting area
        collision_distance = 75
        objects = (
            game.pizza_manager.ingredient_stations +
            [game.pizza_manager.oven, game.pizza_manager.delivery_station, game.pizza_manager.pizza_station] +
            game.pizza_manager.customer_manager.customers +
            [game.pizza_manager.shelf, game.pizza_manager.customer_manager.waiting_area]  # Add waiting area here
        )
        for obj in objects:
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
        elif self.ingredient_type == "pepperoni":
            return Ingredient("pepperoni", *self.position, (0.8, 0.2, 0.2))
        elif self.ingredient_type == "onion":
            return Ingredient("onion", *self.position, (0.9, 0.9, 0.6))
        elif self.ingredient_type == "black_olive":
            return Ingredient("black_olive", *self.position, (0.1, 0.4, 0.1))
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
        glPopMatrix()

        glPopMatrix()

class PizzaStation(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 300
        self.height = 10
        self.depth = 100
        self.pizza = None

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
    def __init__(self):
        self.required_ingredients = ["sauce", "cheese"]
        self.completed = False
        self.expired = False
        # No level, time_limit, or time_remaining

class Customer(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.order = Order()
        self.served = False
        # Removed happiness, patience, waiting_time

        self.colors = {
            'body': (
                random.randint(30, 220)/255,
                random.randint(30, 220)/255,
                random.randint(30, 220)/255
            ),
            'head': (
                245/255,
                194/255,
                166/255
            ),
            'eyes': (1.0, 1.0, 1.0),
            'mouth': (0.0, 0.0, 0.0)
        }

        self.body_parts = {
            'head': {'radius': 15, 'position': (0, 0, 70)},
            'torso': {'top_radius': 15, 'bottom_radius': 15, 'height': 60},
            'arms': {'top_radius': 5, 'bottom_radius': 3, 'height': 40},
            'legs': {'top_radius': 7, 'bottom_radius': 5, 'height': 40}
        }

    # Removed update method (not used)

    def receive_pizza(self, pizza_game):
        if not self.served:
            self.served = True
            required_ingredients = set(self.order.required_ingredients)
            added_toppings = set(pizza_game.added_topping)
            if required_ingredients.issubset(added_toppings):
                self.order.completed = True
                print("Pizza matches the customer's order!")
                return True
            else:
                print("Pizza does not match the customer's order!")
                return False
        return False

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        # Set body color based on served state
        if self.served:
            if self.order.completed:
                body_color = (0.1, 0.7, 0.3)
            else:
                body_color = (0.8, 0.1, 0.1)
        else:
            body_color = self.colors['body']

        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(),
                    self.body_parts['torso']['top_radius'],
                    self.body_parts['torso']['bottom_radius'],
                    self.body_parts['torso']['height'], 10, 10)

        glTranslatef(0, 0, self.body_parts['torso']['height'] + 10)
        glColor3f(*self.colors['head'])
        glutSolidSphere(self.body_parts['head']['radius'], 10, 10)

        glColor3f(*self.colors['eyes'])
        glPushMatrix()
        glTranslatef(5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()

        glColor3f(*self.colors['mouth'])
        glPushMatrix()
        glTranslatef(0, 5, 0)
        if self.served and self.order.completed:
            gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
        else:
            glRotatef(180, 0, 0, 1)
            gluPartialDisk(gluNewQuadric(), 5, 8, 10, 1, 0, 180)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-self.body_parts['torso']['top_radius'] - 2, 0, -self.body_parts['torso']['height'])
        glRotatef(30, 0, 1, 0)
        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(),
                    self.body_parts['arms']['top_radius'],
                    self.body_parts['arms']['bottom_radius'],
                    self.body_parts['arms']['height'], 8, 2)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(self.body_parts['torso']['top_radius'] + 2, 0, -self.body_parts['torso']['height'])
        glRotatef(-30, 0, 1, 0)
        glColor3f(*body_color)
        gluCylinder(gluNewQuadric(),
                    self.body_parts['arms']['top_radius'],
                    self.body_parts['arms']['bottom_radius'],
                    self.body_parts['arms']['height'], 8, 2)
        glPopMatrix()
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
        if self.display_message != None:
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
        self.pizza_station = PizzaStation(-100, -450, 80)
        self.ingredient_stations = [
            IngredientStation("dough", -250, 150, 30, color=(0.9, 0.8, 0.6)),
            IngredientStation("sauce", -150, 150, 30, color=(0.8, 0.1, 0.1)),
            IngredientStation("cheese", -50, 150, 30, color=(1.0, 0.8, 0.0)),
            IngredientStation("sausage", 50, 150, 30, color=(0.7, 0.4, 0.3)),
            IngredientStation("pepperoni", 150, 150, 30, color=(0.8, 0.2, 0.2)),
            IngredientStation("onion", 250, 150, 30, color=(0.9, 0.9, 0.6)),
            IngredientStation("black_olive", 350, 150, 30, color=(0.1, 0.4, 0.1)),
            IngredientStation("oregano", 450, 150, 30, color=(0.6, 0.8, 0.4))
        ]
        # Move oven beside the pizza-making table
        self.oven = Oven(150, -325, 30)
        self.delivery_station = DeliveryStation(100, 150, 80)
        self.customer_manager = CustomerManager()
        self.shelf = Shelf(-450, -500, 0)

    def update(self, delta_time, player):
        self.customer_manager.update(delta_time)

        # Check interactions
        for station in self.ingredient_stations:
            if player.distance_to(station) < 50 and not player.holding_ingredient:
                player.pick_up_ingredient(station.get_ingredient())
                break

        if player.distance_to(self.pizza_station) < 150:
            if player.holding_ingredient:
                player.place_ingredient(self.pizza_station.pizza)
            elif not player.holding_pizza and self.pizza_station.pizza and self.pizza_station.pizza.is_complete():
                player.pick_up_pizza(self.pizza_station.pizza)
                self.pizza_station.pizza = None

        if player.distance_to(self.oven) < 150:
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

        if player.distance_to(self.delivery_station) < 170 and player.holding_pizza:
            player.place_pizza(self.delivery_station)

        for customer in self.customer_manager.customers:
            if player.distance_to(customer) < 150 and player.holding_pizza:
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
            new_order = Order()
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
        self.spawn_interval = 7  # Reduced time between customer spawns (was 20)
        self.waiting_area = CustomerWaitingArea(-450, 400, 0)  # Position in corner opposite to oven
        self.order_area = OrderArea(-300, 150, 0)  # Near delivery station
        self.delivery_station_position = [100, 150, 30]  # Position of the delivery station
        self.received_order = False
        self.display_message = None  # Custom message to display

    def update(self, delta_time):
        self.spawn_timer += delta_time

        # Spawn new customers if we have space in the waiting area
        if self.spawn_timer >= self.spawn_interval and len(self.waiting_customers) < self.max_waiting:
            new_customer = Customer(0, 0, 0)
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

    def receive_order(self, player):
        """Receive an order from the customer."""
        for customer in self.customers:
            distance = player.distance_to(self.order_area)
            if distance < 150 and self.received_order == False:  # Interaction range
                # Mark the order as received
                self.received_order = True
                self.current_order = customer.order
                self.order_area.current_order = None
                self.order_area.display_message = "Order is received"

                print(f"Order received! Required ingredients: {customer.order.required_ingredients}")

                # Move the customer to the delivery station
                self.move_customer_to_delivery_station(customer)
                return True
        return False

    def move_customer_to_delivery_station(self, customer):
        """Move the customer to the delivery station."""
        customer.position = [self.delivery_station_position[0], self.delivery_station_position[1] + 50, self.delivery_station_position[2]]
        print("Customer moved to the delivery station.")

    def remove_customer(self, customer):
        if customer in self.customers:
            self.customers.remove(customer)
            self.order_area.current_order = None  # Clear the menu board when the customer leaves
            self.received_order = False  # Reset when customer leaves
            print("Customer removed from the counter.")

        # Bring the next customer from the waiting area to the counter
        if len(self.waiting_customers) > 0:
            next_customer = self.waiting_customers.pop(0)
            next_customer.position = [
                self.order_area.position[0],
                self.order_area.position[1] + 50,  # Move behind the table
                self.order_area.position[2]
            ]
            self.customers.append(next_customer)
            self.order_area.display_message = None  # Reset the display message
            self.order_area.current_order = next_customer.order  # Set the current order for the menu board
            print("Next customer moved to the counter. Order updated on the menu board.")

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

        # Draw instructions
        self.draw_text(10, 30, "WASD: Move, F: Interact, C: Camera, R: Restart P: Make Pizza")

        # Draw game information
        if not self.game_settings.started:
            self.draw_text(250, 400, "Pizza Ready!")
            self.draw_text(250, 380, "Press any key to start")
        elif self.game_settings.game_over:
            self.draw_text(300, 400, "Game Over!")
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

        # Draw payment message if available
        if game.payment_message:
            self.draw_text(self.game_settings.window_width - 300, self.game_settings.window_height - 100, game.payment_message)


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
        global game
        self.bread_before_oven = False
        self.bread_after_oven = False
        self.pizza_in_box = False
        self.pizza_box_open = True
        self.pizza_box_closed = False
        self.cooking_start_time = 0
        self.cooking_in_progress = False
        self.cooking_duration = 2
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
        self.update_cooking()
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
            DrawingHelper.draw_rect3d(pos[0] - 48, pos[1] - 40, 5, 95, 95, 5, (0.7, 0.7, 0.7))
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
                DrawingHelper.draw_text3d(pos[0] - 27, pos[1] - 70, 20, "black_olive")
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
                glColor3f(0, 0, 1)
                glBegin(GL_LINE_LOOP)
                for i in range(360):
                    angle = i * math.pi / 180
                    glVertex3f(pos[0] + 28 * math.cos(angle), pos[1] + 28 * math.sin(angle), 15)
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
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 48, (0.8, 0.2, 0.1))
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 43, (1.0, 0.9, 0.4))
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
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 48, (0.7, 0.15, 0.05))
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza"][0], self.positions["pizza"][1], z, 43, (0.9, 0.8, 0.4))
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
            DrawingHelper.draw_circle3d(self.positions["pizza_in_box"][0], self.positions["pizza_in_box"][1], self.positions["pizza_in_box"][2], 53, (0.8, 0.6, 0.3))

            # Draw toppings in the box
            z = self.positions["pizza_in_box"][2] + 1  # Start toppings just above pizza base
            for topping in self.pizza_toppings:
                if topping == "sauce":
                    DrawingHelper.draw_circle3d(self.positions["pizza_in_box"][0], self.positions["pizza_in_box"][1], z, 48, (0.7, 0.15, 0.05))
                    z += 1
                elif topping == "cheese":
                    DrawingHelper.draw_circle3d(self.positions["pizza_in_box"][0], self.positions["pizza_in_box"][1], z, 43, (0.9, 0.8, 0.4))
                    z += 1
                elif topping == "sausage":
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 25, self.positions["pizza_in_box"][1] + 20, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 35, self.positions["pizza_in_box"][1] + 3, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 15, self.positions["pizza_in_box"][1] - 12, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    DrawingHelper.draw_rect3d(self.positions["pizza_in_box"][0] - 25, self.positions["pizza_in_box"][1] - 25, z, 50, 5, 3, (0.5, 0.2, 0.1))
                    z += 1
                elif topping == "pepperoni":
                    for i in range(8):
                        angle = i * 45 * math.pi / 180
                        x = self.positions["pizza_in_box"][0] + math.cos(angle) * 30
                        y = self.positions["pizza_in_box"][1]+3 + math.sin(angle) * 30
                        DrawingHelper.draw_circle3d(x, y, z, 7, (0.7, 0.35, 0.2))
                    z += 1
                elif topping == "onion":
                    glColor3f(.3, .1, .5)
                    for i in range(7):
                        angle = i * 51.4 * math.pi / 180
                        cx = self.positions["pizza_in_box"][0] + math.cos(angle) * 25
                        cy = self.positions["pizza_in_box"][1]+3 + math.sin(angle) * 25
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
                        y = self.positions["pizza_in_box"][1]+3 + math.sin(angle) * 32
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
                        y = self.positions["pizza_in_box"][1]+3 + math.sin(angle) * distance
                        glVertex3f(x, y, z)
                    glEnd()
                    z += 1
            glEnable(GL_DEPTH_TEST)

    def draw_oven(self):
        # Oven base: dark brown
        DrawingHelper.draw_rect3d(300 - 75, 0 - 75, 0, 150, 150, 60, (0.25, 0.13, 0.05))
        # Oven front: black
        DrawingHelper.draw_rect3d(300 - 60, 0 - 60, 60, 120, 120, 10, (0.3, 0.3, 0.3))
        # Oven door: black
        DrawingHelper.draw_rect3d(300 - 40, 0 - 40, 70, 80, 80, 5, (0.1, 0.1, 0.1))
        # Oven indicator: red if cooking, green if not
        if game.state.cooking_in_progress:
            DrawingHelper.draw_circle3d(300, 0 + 65, 80, 5, (1, 0, 0))
        else:
            DrawingHelper.draw_circle3d(300, 0 + 65, 80, 5, (0, 1, 0))
        DrawingHelper.draw_text3d(300 - 20, 0 + 85, 90, "OVEN")

    def draw_pizza_box(self):
        # Improved 3D pizza box with a real lid and sides
        base_z = -5
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
            DrawingHelper.draw_rect3d(box_x - box_w//2, box_y - box_d//2, base_z, box_w, box_d, base_height, (0.4, 0.3, 0.2))
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
            elapsed_time = current_time - game.state.cooking_start_time

            if elapsed_time >= game.state.cooking_duration:
                # Pizza is done cooking after 2 seconds
                game.state.cooking_in_progress = False
                game.state.bread_before_oven = False
                game.state.bread_after_oven = True  # Pizza is now cooked

                # Reset cooking timer
                game.state.cooking_start_time = 0

    def handle_click(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            c_X, c_y, c_z = self.convert_coordinate(x, y)

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
                if math.hypot(dx, dy) < 40 and topping not in self.pizza_toppings:
                    game.state.toppings[topping] = not game.state.toppings[topping]

            # Pizza (circle)
            dx = c_X - self.positions["pizza"][0]
            dy = c_y - self.positions["pizza"][1]
            if game.state.bread_before_oven and not game.state.cooking_in_progress:
                if math.hypot(dx, dy) < 53:
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
            if game.state.pizza_in_box and game.state.pizza_box_open:  # Check for open box
                if (bx - box_w//2 <= c_X <= bx + box_w//2 and
                    by - box_h//2 <= c_y <= by + box_h//2):
                    game.state.pizza_box_open = False
                    game.state.pizza_box_closed = True
                    print("Pizza box closed.")
                    return  # Stop further processing for this click

            # End pizza-making process when clicking the closed box
            if game.state.pizza_box_closed:  # Check for closed box
                if (bx - box_w//2 <= c_X <= bx + box_w//2 and
                    by - box_h//2 <= c_y <= by + box_h//2):
                    game.finish_pizza_making()  # End pizza-making process
                    print("Pizza-making process completed.")

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

class PizzaGame:
    def __init__(self):
        ...
        self.payment_message = None  # Add this to store the payment message
        self.payment_message_timer = 0  # Timer to control how long the message is displayed
        self.pizza_making_active = False  # Track if pizza making is active
        self.settings = GameSettings()
        self.camera = Camera()
        self.camera_pizza = Camera_Pizza()
        self.player = Player()
        self.kitchen = Kitchen(self.settings.grid_size)
        self.pizza_manager = PizzaManager()
        self.hud = HUD(self.settings)
        self.input_manager = InputManager()  # Add this line
        self.counters = [
            KitchenCounter(-100, -450, 0, width=300, depth=80),  # Ingredient counter
            KitchenCounter(100, 150, 0, width=200, depth=80)     # delivery counter
        ]
        self.order_generator = OrderGenerator()
        self.last_time = 0
        self.pizza_cost = 0  # Track the cost of the current pizza
        self.current_customer = None  # Track the customer being served
        self.added_topping = []  # Track added toppings
        self.total_money = 20  # Initialize total money


        #Pizza Section
        self.camera_pizza = Camera_Pizza()
        self.state = GameState()
        self.pizza_maker = PizzaMaker()
        self.drawing_helper = DrawingHelper()


    def reset_game(self):
        self.settings = GameSettings()  # Reset game settings
        self.player = Player()  # Reset the player
        self.pizza_manager = PizzaManager()  # Reset the pizza manager
        self.order_generator = OrderGenerator()  # Reset the order generator
        self.total_money = 20  # Reset total money
        self.pizza_cost = 0  # Reset pizza cost
        self.added_topping = []  # Clear added toppings
        self.payment_message = None  # Clear payment message
        self.payment_message_timer = 0  # Reset payment message timer
        self.pizza_making_active = False  # Reset pizza-making state
        self.settings.game_over = False  # Reset game over flag
        self.settings.started = False  # Reset game started flag
        self.hud = HUD(self.settings) # Reset HUD
        print("Game has been reset!")


    def start_game(self):
        self.settings.started = True
        self.last_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0

    def start_pizza_making(self):
        if self.pizza_manager.customer_manager.received_order:
            self.pizza_making_active = True
            print("Pizza making process started")
        else:
            print("Cannot start making pizza without an order")

    def finish_pizza_making(self):
        """Finish the pizza-making process and return to the 3D game."""
        self.pizza_making_active = False
        self.player.holding_delivery_box = True  # Give the player the delivery box
        self.pizza_cost = len(self.added_topping)  # $1 per topping
        print(f"Pizza making process finished. Total cost: ${self.pizza_cost}")

    def update(self):
        if not self.settings.started or self.settings.game_over:
            return

        # Calculate delta time
        current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
        delta_time = current_time - self.last_time
        self.last_time = current_time

        # Update time remaining
        self.settings.time_remaining -= delta_time

        if self.pizza_making_active:
            # Update the pizza-making process
            self.update_pizza_making()
        else:
            # Update the 3D game logic
            self.pizza_manager.update(delta_time, self.player)
            # Update orders
            failures = self.order_generator.update(delta_time, self.settings)

        # Check for game over conditions
        if self.total_money < 0:
            self.settings.game_over = True

        # Check for level completion
        if self.settings.score >= self.settings.current_level * 500:
            self.settings.current_level += 1
            self.settings.time_remaining = 180  # Reset timer for next level

        # Reduce the payment message timer
        if self.payment_message_timer > 0:
            self.payment_message_timer -= delta_time
            if self.payment_message_timer <= 0:
                self.payment_message = None  # Clear the message after the timer expires

    def update_pizza_making(self):
        """Handle the pizza-making process."""
        for topping, selected in game.state.toppings.items():
            if selected and topping not in self.added_topping:
                self.added_topping.append(topping)
                self.total_money -= 1  # Deduct $1 for each topping added
                print(f"Topping added: {topping}. Total money: {self.total_money}$")

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glViewport(0, 0, self.settings.window_width, self.settings.window_height)

        if self.pizza_making_active:
            # Render the pizza-making window
            self.camera_pizza.setup()
            self.camera_pizza.position_camera()
            self.render_pizza_making()
        else:
            # Render the 3D game
            self.camera.setup()
            self.camera.position_camera(self.player)
            self.kitchen.draw()
            # Draw counters
            for counter in self.counters:
                counter.draw()
            # Draw all pizza-related elements
            self.pizza_manager.draw()
            # Draw player
            self.player.draw()
            # Draw HUD elements
            self.hud.draw()

        # Display total money at the top right of the screen
        self.hud.draw_text(self.settings.window_width - 150, self.settings.window_height - 30, f"Money: {self.total_money}$")

        glutSwapBuffers()

    def render_pizza_making(self):
        self.drawing_helper.draw_platform()
        self.drawing_helper.draw_background()
        self.pizza_maker.draw_all()
        pass


# Update keyboard callback function
def keyboard_callback(key, x, y):
    if not game.settings.started:
        game.start_game()
        return

    if game.pizza_making_active:
        # Handle pizza making controls
        if key == b'R' or key == b'r':
            game.state.reset()
            game.added_topping = []  # Reset added toppings
    else:
        # Handle starting the pizza-making process
        if key == b'P' or key == b'p':  # Check for 'P' key press
            if game.player.near_pizza_table:
                if game.pizza_manager.customer_manager.received_order:
                    game.start_pizza_making()
                    print("Starting pizza making process...")
                else:
                    print("Cannot start making pizza without an order!")

        # Handle delivery process
        if key == b'f':  # Interact key
            print("F key pressed")  # Debug message
            if game.player.holding_delivery_box:
                for customer in game.pizza_manager.customer_manager.customers:
                    if game.player.distance_to(game.pizza_manager.delivery_station) < 150:  # Interaction range
                        # Check if the pizza matches the customer's preference
                        if customer.receive_pizza(game):
                            payment = game.pizza_cost * 2.5  # Full payment
                            game.payment_message = f"Customer paid: ${payment:.2f}"  # Set payment message
                        else:
                            payment = game.pizza_cost * 0.7  # Partial payment
                            game.payment_message = f"Customer paid: ${payment:.2f}"  # Set payment message
                        game.total_money += payment  # Add payment to total money
                        game.payment_message_timer = 7  # Display the message for 7 seconds
                        game.player.holding_delivery_box = False  # Remove the delivery box
                        game.pizza_manager.customer_manager.remove_customer(customer)  # Remove the customer
                        print(f"Customer left. Total money: ${game.total_money}")
                        break
            else:
                if game.pizza_manager.customer_manager.receive_order(game.player):
                    game.pizza_manager.customer_manager.received_order = True

        #Toggle camera
        if key == b'c' or key == b'C':
            game.camera.toggle_mode()
            if game.camera.mode == 1:
                print("Camera switched to first-person mode.")
            else:
                print("Camera switched to third-person mode.")

        if key == b'R' or key == b'r':  # Restart game
            game.reset_game()

        # Existing movement and interaction logic...
        if not game.settings.game_over:
            if key == b'w':  # Move forward
                game.player.move_forward()
            elif key == b's':  # Move backward
                game.player.move_backward()
            elif key == b'a':  # Move left
                game.player.move_left()
            elif key == b'd':  # Move right
                game.player.move_right()
            elif key == b'q':  # Turn left
                game.player.turn_left()
            elif key == b'e':  # Turn right
                game.player.turn_right()

def keyboard_up_callback(key, x, y):
    if not game.pizza_making_active:
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
    game.pizza_maker.handle_click(button, state, x, y)
    glutPostRedisplay()


# Add this before the main() function
def initialize_game():
    """Initialize the game state and create global game instance"""
    global game
    game = PizzaGame()

    # Initialize OpenGL settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.0, 0.0, 0.0, 0.0)  # Black background

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

    glutMainLoop()



if __name__ == '__main__':
    main()
