"""Shuffle-dance clip — stylized so Seedance's real-person filter doesn't reject it."""
from generate import generate_image, generate_video

IMAGE_PROMPT = (
    "Stylized illustrated girl doing the Melbourne shuffle dance in a wide empty warehouse "
    "at night, face in shadow, baggy pants and crop top, sneakers, arms out for balance, "
    "low wide camera angle emphasising the feet, haze lit by teal and magenta stage light, "
    "volumetric beams, reflective concrete floor, painterly cinematic animation style, "
    "dreamy neon palette, film grain, 4K"
)

VIDEO_PROMPT = (
    "She performs the shuffle dance: fast running-man footwork, heels sliding and kicking "
    "out, T-step spins, weight shifting side to side, baggy pants rippling with each step, "
    "arms swinging loosely for balance, feet skimming the floor, energetic and continuous, "
    "static low wide camera, haze drifting through the light beams"
)

if __name__ == "__main__":
    img = generate_image(IMAGE_PROMPT, "shuffle.png")
    generate_video(img, VIDEO_PROMPT, "shuffle.mp4", loop=False)
