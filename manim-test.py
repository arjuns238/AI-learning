from manim import *

class CantorDiagonalArgument(Scene):
    def construct(self):
        # Set background color to a deep blue
        self.camera.background_color = "#0C1226"

        # Title
        title = Text("Cantor's Infinity Paradox", color=YELLOW).scale(1.2)
        subtitle = Text("Breaking Down Infinite Sets", color="#66FF66").scale(0.8)
        subtitle.next_to(title, DOWN)

        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Question about infinity
        question = Text("Have you ever tried counting to infinity?", color=WHITE)
        self.play(Write(question))
        self.wait(1)

        # Brief visualization of counting
        numbers = VGroup()
        for i in range(1, 6):
            num = Text(str(i), color=WHITE)
            num.move_to([-4 + i*1.5, 0, 0])
            numbers.add(num)

        dots = Text("...", color=WHITE)
        dots.next_to(numbers, RIGHT)
        infinity = Text("∞", color=YELLOW)
        infinity.next_to(dots, RIGHT)

        self.play(FadeOut(question))
        self.play(Write(numbers), Write(dots), Write(infinity))
        self.wait(1)

        # Statement about different sizes of infinity
        statement = Text("Some infinities are larger than others", color=GREEN)
        statement.to_edge(UP)
        self.play(Write(statement))
        self.wait(1)

        # Clear the screen for the next part
        self.play(FadeOut(numbers), FadeOut(dots), FadeOut(infinity), FadeOut(statement))

        # Show mapping natural numbers to real numbers
        mapping_title = Text("Mapping Natural Numbers to Real Numbers", color=YELLOW)
        mapping_title.to_edge(UP)
        self.play(Write(mapping_title))

        # Formula for generating real numbers
        formula = Text("a_n = n/10^n", color=WHITE)
        formula.move_to([0, 2, 0])
        self.play(Write(formula))
        self.wait(1)

        # Create a simple table showing the mapping
        table_entries = [
            ["n", "Real Number"],
            ["1", "0.1"],
            ["2", "0.02"],
            ["3", "0.003"],
            ["4", "0.0004"]
        ]

        table = VGroup()
        for i, row in enumerate(table_entries):
            for j, item in enumerate(row):
                cell_text = Text(item, color=WHITE if i > 0 else YELLOW).scale(0.7)
                cell_text.move_to([j*3 - 2, -i + 1, 0])
                table.add(cell_text)

        self.play(FadeOut(formula))
        self.play(Write(table))
        self.wait(1)

        # Highlight the diagonal elements
        diagonal_digits = ["1", "2", "3", "4"]  # The digits we'll extract from the diagonal
        arrows = VGroup()

        for i in range(1, 5):
            arrow = Arrow(
                start=[-2, -i + 1.3, 0],
                end=[0, -i + 1, 0],
                color=RED,
                buff=0.1
            ).scale(0.7)
            arrows.add(arrow)

        self.play(Create(arrows))

        # Show the diagonal digits
        diagonal_text = Text(f"Diagonal digits: {', '.join(diagonal_digits)}", color=RED).scale(0.7)
        diagonal_text.to_edge(DOWN, buff=1.5)
        self.play(Write(diagonal_text))
        self.wait(1)

        # Create a new number by modifying diagonal digits
        new_formula = Text("b_i = a_i + 1", color=GREEN)
        new_formula.next_to(diagonal_text, DOWN)
        self.play(Write(new_formula))

        # Calculate new digits by adding 1 to each diagonal digit
        new_digits = []
        for digit in diagonal_digits:
            new_digit = str((int(digit) + 1) % 10)
            new_digits.append(new_digit)

        new_number = Text(f"New number: 0.{''.join(new_digits)}...", color=GREEN).scale(0.7)
        new_number.next_to(new_formula, DOWN)
        self.play(Write(new_number))
        self.wait(1)

        # Key insight
        insight = Text("This new number differs from EVERY number in our list!", color=YELLOW).scale(0.7)
        insight.to_edge(DOWN, buff=0.2)
        self.play(Write(insight))
        self.wait(1)

        # Clear for conclusion
        self.play(
            FadeOut(table), FadeOut(arrows), FadeOut(diagonal_text),
            FadeOut(new_formula), FadeOut(new_number), FadeOut(insight), FadeOut(mapping_title)
        )

        # Final conclusion
        conclusion1 = Text("The set of real numbers between 0 and 1", color=WHITE).scale(0.8)
        conclusion2 = Text("CANNOT be put in one-to-one correspondence", color=YELLOW).scale(0.8)
        conclusion3 = Text("with the natural numbers", color=WHITE).scale(0.8)

        conclusion_group = VGroup(conclusion1, conclusion2, conclusion3).arrange(DOWN)
        self.play(Write(conclusion_group))
        self.wait(1)

        final = Text("Not all infinities are equal!", color=GREEN).scale(1.2)
        final.to_edge(DOWN, buff=1)
        self.play(Write(final))
        self.wait(2)
