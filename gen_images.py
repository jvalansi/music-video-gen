"""Generate a set of dreamy/ethereal stills for the 'what I want' track."""
import os
from generate import generate_image

PROMPTS = {
    "dream_1_figure": (
        "A lone figure standing in a vast dreamlike expanse at dusk, soft pastel aurora "
        "sky in lilac and teal, drifting clouds, gentle volumetric light, ethereal and "
        "longing atmosphere, cinematic wide shot, film grain, 4K"
    ),
    "dream_2_clouds": (
        "Endless sea of glowing pink and violet clouds under a starry gradient sky, "
        "soft god rays, floating luminous particles, serene ethereal dreamscape, "
        "cinematic, photorealistic, 4K"
    ),
    "dream_3_water": (
        "Mirror-still water reflecting a pastel neon sky at twilight, faint silhouette on "
        "the horizon, ripples of light, dreamy melancholic mood, minimalist cinematic "
        "composition, soft focus, 4K"
    ),
    "dream_4_neon": (
        "Abstract dreamscape of flowing aurora light ribbons in teal, magenta and gold "
        "over a dark reflective surface, bokeh particles, ethereal and hypnotic, "
        "cinematic, high detail, 4K"
    ),
}

if __name__ == "__main__":
    for name, prompt in PROMPTS.items():
        out = f"{name}.png"
        try:
            generate_image(prompt, out)
        except Exception as e:
            print(f"FAILED {name}: {e}")
