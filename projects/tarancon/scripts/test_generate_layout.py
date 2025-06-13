from layout_generators.biomimetic_spiral_layout_generator import generate_biomimetic_spiral_layout
from pathlib import Path

if __name__ == "__main__":
    output_file = Path("projects/tarancon/layouts/layout_test.csv")
    
    # Biomimetic spiral parameters (example values)
    a0 = 15.0
    b = 1.8
    delta = 0.0  # radians
    tower_height = 35.0
    num_heliostats = 223
    bubble_radius = 4.5  # meters

    generate_biomimetic_spiral_layout(
        output_file=output_file,
        num_heliostats=num_heliostats,
        tower_height=tower_height,
        a0=a0,
        b=b,
        delta=delta,
        bubble_radius=bubble_radius
    )

    print(f"✅ Layout generated at {output_file}")