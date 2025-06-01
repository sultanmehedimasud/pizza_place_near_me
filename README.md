# pizza_place_near_me

---

## Features

- **3D kitchen environment** with detailed elements like ovens, counters, shelves, and a waiting area.
- **Player movement and interaction** with WASD keys and mouse clicks to navigate and perform actions.
- **Multiple camera modes**: toggle between third-person and first-person views.
- **Pizza making mechanics**: pick up ingredients, add toppings, bake pizzas, and pack them into boxes.
- **Customer orders and management**: receive random orders, serve customers, and earn money.
- **Time and score tracking** with multiple levels and game-over conditions.
- **Visual HUD** displaying instructions, score, money, level, time, and mistakes.
- **Realistic 3D models** of kitchen items, pizza, customers, and ingredients using OpenGL primitives.

---

## Controls

| Key/Button      | Action                                         |
|-----------------|------------------------------------------------|
| `W`             | Move forward                                   |
| `S`             | Move backward                                  |
| `A`             | Move left                                      |
| `D`             | Move right                                     |
| `Q`             | Turn left                                     |
| `E`             | Turn right                                    |
| `F`             | Interact (e.g., receive orders, deliver pizza)|
| `C`             | Toggle camera mode (third-person / first-person)|
| `P`             | Start pizza making (only when near pizza table and order received) |
| `R`             | Restart game / Reset pizza making (in pizza mode) |
| Mouse Click     | Select toppings, interact with pizza/oven/box  |

---

## Installation

1. **Prerequisites:**

   - Python 3.6 or higher
   - OpenGL bindings for Python

2. **Install dependencies:**

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

3. **Run**

```bash
python pizza_ready.py
```
