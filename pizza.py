import math
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class GameSettings:
    def __init__(self):
        self.grid_size = 600
        self.window_width = 800
        self.window_height = 800
        self.started = False
        self.game_over = False
        self.score = 0
        self.mistakes_limit = 5
        self.mistakes = 0
        self.current_level = 1
        self.time_remaining = 180  # 3 minutes per level
        self.last_time_update = 0

class Camera:
    def __init__(self):
        self.position = [0, 500, 500]  # Default camera position
        self.fov = 120
        self.mode = 0  # 0 = third-person, 1 = first-person
        
    def setup(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, 1.0, 0.1, 1500)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
    def position_camera(self, player):
        if self.mode == 0:  # Third-person view
            gluLookAt(*self.position, 0, 0, 0, 0, 0, 1)
        else:  # First-person view
            # Camera follows player's position and direction
            cam_height = 100
            look_x = player.position[0] + 100 * math.cos(math.radians(player.angle))
            look_y = player.position[1] + 100 * math.sin(math.radians(player.angle))
            
            gluLookAt(player.position[0], player.position[1], player.position[2] + cam_height,
                      look_x, look_y, player.position[2] + cam_height,
                      0, 0, 1)
    
    def move(self, direction):
        if direction == "up":
            self.position[2] += 10
        elif direction == "down":
            self.position[2] -= 10
        elif direction == "left":
            self.position[0] -= 10
        elif direction == "right":
            self.position[0] += 10
            
    def toggle_mode(self):
        self.mode = 1 - self.mode

class Entity:
    def __init__(self, x=0, y=0, z=0):
        self.position = [x, y, z]
        
    def distance_to(self, other_entity):
        return math.sqrt(
            (self.position[0] - other_entity.position[0])**2 + 
            (self.position[1] - other_entity.position[1])**2 + 
            (self.position[2] - other_entity.position[2])**2
        )

class Player(Entity):
    def __init__(self):
        super().__init__(0, 0, 30)
        self.angle = 0
        self.cheat_mode = False
        self.holding_ingredient = None
        self.holding_pizza = None
        self.inventory = []
        
    def move_forward(self):
        self.position[0] += 10 * math.cos(math.radians(self.angle))
        self.position[1] += 10 * math.sin(math.radians(self.angle))
        
    def move_backward(self):
        self.position[0] -= 10 * math.cos(math.radians(self.angle))
        self.position[1] -= 10 * math.sin(math.radians(self.angle))
        
    def move_left(self):
        self.position[0] += 10 * math.cos(math.radians(self.angle - 90))
        self.position[1] += 10 * math.sin(math.radians(self.angle - 90))
        
    def move_right(self):
        self.position[0] += 10 * math.cos(math.radians(self.angle + 90))
        self.position[1] += 10 * math.sin(math.radians(self.angle + 90))
        
    def turn_left(self):
        self.angle += 5
        
    def turn_right(self):
        self.angle -= 5
        
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
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.angle, 0, 0, 1)
        
        # Draw player body
        glColor3f(0.2, 0.6, 0.8)
        gluCylinder(gluNewQuadric(), 15, 15, 40, 10, 10)
        
        # Draw player head
        glTranslatef(0, 0, 45)
        glColor3f(0.8, 0.6, 0.4)
        glutSolidSphere(10, 10, 10)
        
        # Draw player arms
        glTranslatef(0, 0, -15)
        
        # Left arm
        glPushMatrix()
        glTranslatef(15, 0, 0)
        glRotatef(90, 0, 1, 0)
        glColor3f(0.8, 0.6, 0.4)
        gluCylinder(gluNewQuadric(), 5, 5, 20, 10, 10)
        glPopMatrix()
        
        # Right arm
        glPushMatrix()
        glTranslatef(-15, 0, 0)
        glRotatef(-90, 0, 1, 0)
        glColor3f(0.8, 0.6, 0.4)
        gluCylinder(gluNewQuadric(), 5, 5, 20, 10, 10)
        glPopMatrix()
        
        # Draw held items
        if self.holding_ingredient:
            glPushMatrix()
            glTranslatef(0, 20, 0)
            self.holding_ingredient.draw()
            glPopMatrix()
            
        if self.holding_pizza:
            glPushMatrix()
            glTranslatef(0, 20, 0)
            self.holding_pizza.draw()
            glPopMatrix()
        
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
        elif self.ingredient_type == "vegetable1":
            return Ingredient("vegetable1", *self.position, (0.1, 0.8, 0.1))
        elif self.ingredient_type == "vegetable2":
            return Ingredient("vegetable2", *self.position, (0.8, 0.1, 0.8))
        elif self.ingredient_type == "meat1":
            return Ingredient("meat1", *self.position, (0.7, 0.3, 0.3))
        elif self.ingredient_type == "meat2":
            return Ingredient("meat2", *self.position, (0.5, 0.2, 0.2))
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        
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
        
        glPopMatrix()

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
        elif (("vegetable" in ingredient.name or "meat" in ingredient.name) 
              and self.cheese_added):
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
        
        glPopMatrix()

class Oven(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 80
        self.height = 60
        self.depth = 60
        self.pizza = None
        self.cooking_time = 0
        self.cooking_speed = 1
        self.door_open = False
        
    def insert_pizza(self, pizza):
        if not self.pizza and self.door_open:
            pizza.position = self.position.copy()
            pizza.position[2] += 10  # Place pizza inside the oven
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
        
        # Draw oven base
        glColor3f(0.5, 0.5, 0.5)
        glPushMatrix()
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw oven door
        glPushMatrix()
        door_angle = 90 if self.door_open else 0
        glTranslatef(-self.width/2, 0, 0)
        glRotatef(door_angle, 0, 0, 1)
        glTranslatef(self.width/2, 0, 0)
        glColor3f(0.2, 0.2, 0.2)
        glTranslatef(-self.width/2, 0, 0)
        glScalef(5, self.depth * 0.8, self.height * 0.8)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw progress bar for cooking
        if self.pizza:
            cooking_percentage = min(self.pizza.cooking_level / 100, 1.5)
            
            glPushMatrix()
            glTranslatef(0, self.depth/2 + 10, self.height/2)
            
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
                glTranslatef(0, 0, 10)
                self.pizza.draw()
                glPopMatrix()
        
        glPopMatrix()

class PizzaStation(Entity):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.width = 100
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
        glColor3f(0.8, 0.8, 0.8)
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
        self.width = 100
        self.height = 10
        self.depth = 60
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
        self.required_ingredients = ["dough", "sauce", "cheese"]
        self.time_limit = 60 + 30 * level  # Seconds to complete
        self.time_remaining = self.time_limit
        self.completed = False
        self.expired = False
        
        # Add random toppings based on level difficulty
        num_toppings = random.randint(0, min(level, 4))
        toppings = ["vegetable1", "vegetable2", "meat1", "meat2"]
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
        
        # Draw customer body
        if self.served:
            if self.order.completed:
                glColor3f(0.1, 0.7, 0.3)  # Happy green
            else:
                glColor3f(0.8, 0.1, 0.1)  # Angry red
        else:
            # Color based on happiness
            happiness_percent = max(0, min(self.happiness / 100, 1))
            glColor3f(1 - happiness_percent, happiness_percent, 0.1)
            
        gluCylinder(gluNewQuadric(), 15, 15, 60, 10, 10)
        
        # Draw customer head
        glTranslatef(0, 0, 70)
        glutSolidSphere(15, 10, 10)
        
        # Draw customer face
        # Eyes
        glColor3f(1, 1, 1)
        glPushMatrix()
        glTranslatef(5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-5, 10, 0)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
        # Mouth - smile or frown based on happiness
        glColor3f(0, 0, 0)
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
        
        # Draw order bubble
        if not self.served:
            glPushMatrix()
            glTranslatef(30, 30, 0)
            
            # Order bubble background
            glColor3f(1, 1, 1)
            glutSolidSphere(20, 10, 10)
            
            # Draw ingredients in bubble
            for i, ingredient in enumerate(self.order.required_ingredients):
                if ingredient == "dough":
                    continue  # Skip drawing dough in bubble
                
                angle = i * 45
                dist = 10
                x = dist * math.cos(math.radians(angle))
                y = dist * math.sin(math.radians(angle))
                
                glPushMatrix()
                glTranslatef(x, y, 0)
                glScalef(0.5, 0.5, 0.5)
                
                if ingredient == "sauce":
                    glColor3f(0.8, 0.1, 0.1)
                    glutSolidSphere(5, 10, 10)
                elif ingredient == "cheese":
                    glColor3f(1.0, 0.8, 0.0)
                    glutSolidCube(10)
                elif "vegetable" in ingredient:
                    glColor3f(0.1, 0.8, 0.1)
                    glutSolidCube(10)
                elif "meat" in ingredient:
                    glColor3f(0.7, 0.3, 0.3)
                    gluCylinder(gluNewQuadric(), 5, 5, 2, 10, 10)
                
                glPopMatrix()
            
            glPopMatrix()
            
            # Draw timer bar
            timer_percentage = max(0, min(self.order.time_remaining / self.order.time_limit, 1))
            
            glPushMatrix()
            glTranslatef(0, 0, 30)
            
            # Background timer bar
            glColor3f(0.2, 0.2, 0.2)
            glPushMatrix()
            glScalef(40, 5, 5)
            glutSolidCube(1)
            glPopMatrix()
            
            # Progress timer bar
            if timer_percentage > 0.6:
                glColor3f(0.1, 0.8, 0.1)  # Green
            elif timer_percentage > 0.3:
                glColor3f(1.0, 0.8, 0.0)  # Yellow
            else:
                glColor3f(0.8, 0.1, 0.1)  # Red
                
            glPushMatrix()
            glTranslatef(-(40)/2 + (40 * timer_percentage)/2, 0, 0)
            glScalef(40 * timer_percentage, 5, 5)
            glutSolidCube(1)
            glPopMatrix()
            
            glPopMatrix()
        
        glPopMatrix()
            
# Kitchen related classes and functionality
class Kitchen:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.floor_color1 = (0.9, 0.9, 0.9)  # Light gray
        self.floor_color2 = (0.8, 0.8, 0.8)  # Slightly darker gray
        
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
        wall_height = 200
        glColor3f(0.7, 0.7, 0.8)  # Wall color
        
        # Back wall
        glBegin(GL_QUADS)
        glVertex3f(-self.grid_size, -self.grid_size, 0)
        glVertex3f(self.grid_size, -self.grid_size, 0)
        glVertex3f(self.grid_size, -self.grid_size, wall_height)
        glVertex3f(-self.grid_size, -self.grid_size, wall_height)
        glEnd()
        
        # Side wall
        glBegin(GL_QUADS)
        glVertex3f(-self.grid_size, -self.grid_size, 0)
        glVertex3f(-self.grid_size, self.grid_size, 0)
        glVertex3f(-self.grid_size, self.grid_size, wall_height)
        glVertex3f(-self.grid_size, -self.grid_size, wall_height)
        glEnd()

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
        glTranslatef(0, -self.depth/2 - edge_thickness/2, self.height/2)
        glScalef(self.width + edge_thickness*2, edge_thickness, self.height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Left edge
        glPushMatrix()
        glTranslatef(-self.width/2 - edge_thickness/2, 0, self.height/2)
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
        self.pizza_station = PizzaStation(0, 0, 30)
        self.ingredient_stations = [
            IngredientStation("dough", -250, 150, 30, color=(0.9, 0.8, 0.6)),
            IngredientStation("sauce", -150, 150, 30, color=(0.8, 0.1, 0.1)),
            IngredientStation("cheese", -50, 150, 30, color=(1.0, 0.8, 0.0)),
            IngredientStation("vegetable1", 50, 150, 30, color=(0.1, 0.8, 0.1)),
            IngredientStation("vegetable2", 150, 150, 30, color=(0.1, 0.6, 0.1)),
            IngredientStation("meat1", 250, 150, 30, color=(0.7, 0.3, 0.3)),
            IngredientStation("meat2", 350, 150, 30, color=(0.6, 0.2, 0.2))
        ]
        self.oven = Oven(-200, -150, 30)
        self.delivery_station = DeliveryStation(200, -150, 30)
        self.customer_manager = CustomerManager()
        
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
            elif not self.pizza_station.pizza:
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
        self.customers = []
        self.max_customers = 3
        self.spawn_timer = 0
        self.spawn_interval = 20  # Seconds between customer spawns
        
    def update(self, delta_time):
        self.spawn_timer += delta_time
        
        # Spawn new customers if we have space
        if self.spawn_timer >= self.spawn_interval and len(self.customers) < self.max_customers:
            # Create a new customer at the waiting area
            x = 300 + len(self.customers) * 100
            new_customer = Customer(x, -250, 0, random.randint(1, 3))
            self.customers.append(new_customer)
            self.spawn_timer = 0
            
        # Update existing customers
        for customer in self.customers:
            customer.update(delta_time)
            
    def remove_customer(self, customer):
        if customer in self.customers:
            self.customers.remove(customer)
            
    def draw(self):
        for customer in self.customers:
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
        gluOrtho2D(0, 800, 0, 800)
        
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
            self.draw_text(10, 30, "WASD: Move, E: Interact, C: Camera, R: Restart")

class PizzaGame:
    def __init__(self):
        self.settings = GameSettings()
        self.camera = Camera()
        self.player = Player()
        self.kitchen = Kitchen(self.settings.grid_size)
        self.pizza_manager = PizzaManager()
        self.hud = HUD(self.settings)
        self.counters = [
            KitchenCounter(-150, 150, 0, width=400, depth=80),  # Ingredient counter
            KitchenCounter(0, -150, 0, width=400, depth=80)     # Oven/delivery counter
        ]
        self.order_generator = OrderGenerator()
        self.last_time = 0
        
    def reset_game(self):
        self.settings = GameSettings()
        self.player = Player()
        self.pizza_manager = PizzaManager()
        self.order_generator = OrderGenerator()
        
    def start_game(self):
        self.settings.started = True
        self.last_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
        
    def update(self):
        if not self.settings.started or self.settings.game_over:
            return
            
        # Calculate delta time
        current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Update time remaining
        self.settings.time_remaining -= delta_time
        
        # Update pizza manager
        self.pizza_manager.update(delta_time, self.player)
        
        # Update orders
        failures = self.order_generator.update(delta_time, self.settings)
        
        # Check for game over conditions
        if self.settings.time_remaining <= 0 or self.settings.mistakes >= self.settings.mistakes_limit:
            self.settings.game_over = True
            
        # Check for level completion
        if self.settings.score >= self.settings.current_level * 500:
            self.settings.current_level += 1
            self.settings.time_remaining = 180  # Reset timer for next level
            
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glViewport(0, 0, self.settings.window_width, self.settings.window_height)
        
        self.camera.setup()
        self.camera.position_camera(self.player)
        
        # Draw kitchen environment
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
        
        glutSwapBuffers()

# Global game instance
game = None

def initialize_game():
    global game
    game = PizzaGame()

def idle_callback():
    game.update()
    glutPostRedisplay()

def display_callback():
    game.render()

def keyboard_callback(key, x, y):
    if not game.settings.started:
        game.start_game()
        return
        
    if key == b'w':
        game.player.move_forward()
    elif key == b's':
        game.player.move_backward()
    elif key == b'a':
        game.player.move_left()
    elif key == b'd':
        game.player.move_right()
    elif key == b'q':
        game.player.turn_left()
    elif key == b'e':
        game.player.turn_right()
    elif key == b'c':
        game.camera.toggle_mode()
    elif key == b'r' and game.settings.game_over:
        game.reset_game()
    elif key == b' ':
        # Interact with nearest object
        pass

def special_key_callback(key, x, y):
    if key == GLUT_KEY_UP:
        game.camera.move("up")
    elif key == GLUT_KEY_DOWN:
        game.camera.move("down")
    elif key == GLUT_KEY_LEFT:
        game.camera.move("left")
    elif key == GLUT_KEY_RIGHT:
        game.camera.move("right")

def mouse_callback(button, state, x, y):
    pass  # We'll handle interactions with keyboard in this game

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    initialize_game()
    
    glutInitWindowSize(game.settings.window_width, game.settings.window_height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Pizza Ready")
    
    glEnable(GL_DEPTH_TEST)
    
    glutDisplayFunc(display_callback)
    glutKeyboardFunc(keyboard_callback)
    glutSpecialFunc(special_key_callback)
    glutMouseFunc(mouse_callback)
    glutIdleFunc(idle_callback)
    
    glutMainLoop()

if __name__ == '__main__':
    main()