"""
Manim API Reference for Layer 4 Code Generation

Provides contextual API documentation to prevent hallucination and guide
correct usage of ManimCE v0.18+ APIs.
"""

from typing import List


MANIM_API_REFERENCE = {
    "axes": """
## Axes and Graphing APIs
**Axes**: Create 2D coordinate system
  - `Axes(x_range=[min, max, step], y_range=[min, max, step], x_length, y_length, axis_config)`
  - `.plot(function, x_range=[min, max], color)` → Graph object
  - `.get_x_axis_label(label, edge, direction)` → Text
  - `.get_y_axis_label(label, edge, direction)` → Text
  - `.c2p(x, y)` → Convert coordinates to point (coordinates-to-point)
  - `.p2c(point)` → Convert point to coordinates (point-to-coordinates)

**Graph**: Function plots
  - Created via `axes.plot(lambda x: x**2, ...)`
  - Inherits from VMobject (can be colored, animated, etc.)
""",

    "mobjects": """
## Basic Mobject APIs
**Dot**: Point marker
  - `Dot(point, radius, color)` - Create dot at point
  - `.get_center()` → Get position
  - `.move_to(point)` → Move to absolute position
  - `.shift(vector)` → Move by relative amount

**Circle, Square, Rectangle**: Basic shapes
  - `Circle(radius, color, fill_opacity)`
  - `Square(side_length, color, fill_opacity)`
  - `Rectangle(width, height, color)`

**Arrow**: Directional arrow
  - `Arrow(start, end, color, buff, stroke_width, max_tip_length_to_length_ratio)`
  - `.get_start()` → Start point
  - `.get_end()` → End point
  - `.put_start_and_end_on(start, end)` → Reposition arrow
""",

    "text": """
## Text and Math APIs
**Text**: Regular text
  - `Text(text, font_size, color, font)`
  - `.next_to(mobject, direction, buff)` → Position relative to object
  - `.to_edge(edge, buff)` → Position at screen edge (UP, DOWN, LEFT, RIGHT)
  - `.to_corner(corner)` → Position at corner (UL, UR, DL, DR)

**MathTex**: LaTeX mathematical expressions
  - `MathTex(r"x^2 + y^2 = z^2", font_size, color)`
  - Use raw strings (r"...") for LaTeX
  - Supports standard LaTeX math syntax

**DecimalNumber**: Dynamic number display
  - `DecimalNumber(value, num_decimal_places, font_size)`
  - `.set_value(new_value)` → Update the number
""",

    "animations": """
## Animation APIs
**Creation/Drawing**:
  - `Create(mobject, run_time)` - Draw object into existence
  - `Write(text, run_time)` - Write text letter by letter
  - `DrawBorderThenFill(mobject, run_time)` - Draw outline then fill
  - `Uncreate(mobject)` - Reverse of Create

**Fading**:
  - `FadeIn(mobject, shift, run_time)` - Fade in object
  - `FadeOut(mobject, shift, run_time)` - Fade out object

**Transforms**:
  - `Transform(mobject1, mobject2, run_time)` - Morph mobject1 into mobject2
  - `ReplacementTransform(mobject1, mobject2)` - Replace mob1 with mob2
  - `FadeTransform(mobject1, mobject2)` - Fade-based transform
""",

    "movement": """
## Movement and Animation APIs
**Direct movement**:
  - `mobject.animate.move_to(point)` - Smooth movement to position
  - `mobject.animate.shift(vector)` - Smooth relative movement
  - `mobject.animate.scale(factor)` - Smooth scaling
  - `mobject.animate.rotate(angle)` - Smooth rotation

**Path-based movement**:
  - `MoveAlongPath(mobject, path, rate_func, run_time)` - Follow a path
  - `Rotate(mobject, angle, about_point, run_time)` - Rotate around point

**Dynamic updates**:
  - `always_redraw(lambda: ...)` - Mobject that redraws every frame
  - Useful for labels that follow moving objects
  - Must return a Mobject
""",

    "vectorfield": """
## Vector Field APIs
**ArrowVectorField**: Field of arrows
  - `ArrowVectorField(func, x_range, y_range, color)`
  - `func` should be: `lambda pos: np.array([x_component, y_component, 0])`

**StreamLines**: Flow lines
  - `StreamLines(func, x_range, y_range, color, stroke_width)`
  - Shows direction of flow in a vector field
""",

    "constants": """
## Useful Constants
**Directions**: UP, DOWN, LEFT, RIGHT, UR, UL, DR, DL, ORIGIN
**Colors**: RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, WHITE, BLACK, GRAY
**Rate Functions**: linear, smooth, rush_into, rush_from, there_and_back
"""
}


def get_relevant_manim_apis(user_prompt: str) -> str:
    """
    Extract relevant Manim API documentation based on the scene specification.

    Args:
        user_prompt: The user prompt containing scene specification

    Returns:
        String containing relevant API documentation
    """
    prompt_lower = user_prompt.lower()
    api_sections = []

    # Check for axes/graphing
    if any(keyword in prompt_lower for keyword in ['axes', 'graph', 'plot', 'curve', 'function']):
        api_sections.append(MANIM_API_REFERENCE['axes'])

    # Check for basic shapes and mobjects
    if any(keyword in prompt_lower for keyword in ['dot', 'circle', 'square', 'rectangle', 'arrow', 'point']):
        api_sections.append(MANIM_API_REFERENCE['mobjects'])

    # Check for text
    if any(keyword in prompt_lower for keyword in ['text', 'label', 'title', 'mathtex', 'decimal', 'number']):
        api_sections.append(MANIM_API_REFERENCE['text'])

    # Check for animations
    if any(keyword in prompt_lower for keyword in ['create', 'write', 'fade', 'transform', 'animate']):
        api_sections.append(MANIM_API_REFERENCE['animations'])

    # Check for movement
    if any(keyword in prompt_lower for keyword in ['move', 'shift', 'path', 'iterate', 'gradient_descent', 'always_redraw']):
        api_sections.append(MANIM_API_REFERENCE['movement'])

    # Check for vector fields
    if any(keyword in prompt_lower for keyword in ['vector', 'field', 'streamlines', 'flow']):
        api_sections.append(MANIM_API_REFERENCE['vectorfield'])

    # Always include constants as they're commonly used
    api_sections.append(MANIM_API_REFERENCE['constants'])

    if not api_sections:
        return ""

    # Build the API reference section
    api_reference = "\n## Manim API Reference\n\n"
    api_reference += "The following APIs are available for this visualization:\n\n"
    api_reference += "\n".join(api_sections)
    api_reference += "\n---\n\n"

    return api_reference
