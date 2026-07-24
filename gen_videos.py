"""Generate Seedance motion clips from the dreamy stills."""
from generate import generate_video

CLIPS = {
    "dream_1_figure.png": (
        "Subtle cinematic motion: aurora ribbons slowly drifting and shimmering across the "
        "sky, faint clouds drifting, soft ripples moving across the mirror water reflection, "
        "the lone figure standing perfectly still, gentle atmospheric drift, seamless loop"
    ),
    "dream_2_clouds.png": (
        "Slow billowing pink and violet clouds glowing and drifting, luminous particles "
        "floating gently upward, soft god rays shifting, dreamy hypnotic parallax, seamless loop"
    ),
    "dream_3_water.png": (
        "Gentle ripples spreading across mirror-still water, soft shimmering pastel reflections "
        "rippling, slow drifting light on the horizon, calm meditative motion, seamless loop"
    ),
    "dream_4_neon.png": (
        "Flowing aurora light ribbons undulating and morphing in teal, magenta and gold, "
        "bokeh particles drifting, hypnotic liquid light motion, seamless loop"
    ),
}

if __name__ == "__main__":
    for img, prompt in CLIPS.items():
        out = img.replace(".png", "_clip.mp4")
        print(f"\n=== {img} -> {out} ===", flush=True)
        try:
            generate_video(img, prompt, out, loop=True)
        except Exception as e:
            print(f"FAILED {img}: {e}", flush=True)
