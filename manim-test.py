from manim import *
'''	
Display a set of coordinate axes with a cosine curve plotted. A yellow square is positioned exactly at the point on the curve where \( x = \pi \), visually marking that location on the graph.
'''


class LoopSpacesScene(Scene):
    def construct(self):
        # Set custom colors for vibrant visuals
        blue_hue = "#3a86ff"
        purple_hue = "#8338ec"
        green_hue = "#38e889"
        highlight_color = "#ff006e"

        # Introduction - Title of the animation
        title = Text("Unraveling the Intricacies of Loop Spaces", font_size=36, color=blue_hue)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))

        # Key Concept 1: S^1 and its fundamental group
        # Show a circle representing S^1
        circle = Circle(radius=2, color=blue_hue)
        label_s1 = Text("S¹ (Circle)", font_size=30, color=blue_hue).next_to(circle, DOWN)
        self.play(Create(circle), Write(label_s1))

        # Show a loop on the circle
        loop = Circle(radius=2, color=highlight_color, stroke_width=4)
        self.play(Create(loop))

        # Show the fundamental group equation
        eq1 = Text("π₁(S¹)", font_size=36, color=purple_hue).to_edge(DOWN)
        self.play(Write(eq1))
        self.wait(1)
        self.play(FadeOut(circle), FadeOut(label_s1), FadeOut(loop), FadeOut(eq1))

        # Key Concept 2: Loop space of S^1
        # Visualize the loop space as a torus-like structure with two circles
        outer_circle = Circle(radius=2, color=blue_hue)
        inner_circle = Circle(radius=0.7, color=green_hue).move_to([1, 0, 0])
        label_ls1 = Text("L(S¹) (Loop Space)", font_size=30, color=blue_hue).next_to(outer_circle, DOWN)
        self.play(Create(outer_circle), Write(label_ls1))
        self.play(Create(inner_circle))

        # Show the equation for the fundamental group of the loop space
        eq2 = Text("π₁(L(S¹))", font_size=36, color=purple_hue).to_edge(DOWN)
        self.play(Write(eq2))
        self.wait(1)
        self.play(FadeOut(outer_circle), FadeOut(inner_circle), FadeOut(label_ls1), FadeOut(eq2))

        # Key Concept 3: Loop space of S^2
        # Represent S^2 (sphere) and its loops
        circle_s2 = Circle(radius=2, color=purple_hue)
        label_s2 = Text("S² (Sphere)", font_size=30, color=purple_hue).next_to(circle_s2, DOWN)
        self.play(Create(circle_s2), Write(label_s2))

        # Show loops on S^2
        loop1 = Arc(radius=1.5, start_angle=0, angle=PI, color=highlight_color).shift(UP*0.5)
        loop2 = Arc(radius=1.5, start_angle=PI, angle=PI, color=highlight_color).shift(DOWN*0.5)
        self.play(Create(loop1), Create(loop2))

        # Show the equation for the loop space of S^2
        eq3 = Text("L(S²)", font_size=36, color=purple_hue).to_edge(DOWN)
        self.play(Write(eq3))
        self.wait(1)
        self.play(FadeOut(circle_s2), FadeOut(loop1), FadeOut(loop2), FadeOut(label_s2), FadeOut(eq3))

        # Key Insight: Visualize the complexity of loop spaces
        insight_text = Text("Loop spaces form complex geometric structures", font_size=30, color=purple_hue)
        self.play(Write(insight_text))
        self.wait(1)
        self.play(FadeOut(insight_text))

        # Show a visual representation of a complex loop structure
        main_circle = Circle(radius=2, color=blue_hue)
        loop1 = Circle(radius=0.5, color=highlight_color).move_to([1, 0, 0])
        loop2 = Circle(radius=0.5, color=green_hue).move_to([-1, 0, 0])
        loop3 = Circle(radius=0.5, color=purple_hue).move_to([0, 1, 0])

        # Create the loops sequentially to illustrate complexity
        self.play(Create(main_circle))
        self.play(Create(loop1))
        self.play(Create(loop2))
        self.play(Create(loop3))

        # Add a label for the complex structure
        complex_label = Text("Visualizing L(S²)", font_size=30, color=blue_hue).next_to(main_circle, DOWN)
        self.play(Write(complex_label))
        self.wait(1)

        # Fade out everything
        self.play(
        FadeOut(main_circle),
        FadeOut(loop1),
        FadeOut(loop2),
        FadeOut(loop3),
        FadeOut(complex_label)
        )

        # Conclusion
        conclusion = Text("The beauty of loop spaces lies in their recursive nature", font_size=30, color=blue_hue)
        self.play(Write(conclusion))
        self.wait(2)
        self.play(FadeOut(conclusion))