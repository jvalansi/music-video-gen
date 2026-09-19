"""Shuffle clip retimed to the track: steady footwork at the 172 BPM subdivision
of Ono-meno-me (86.2 BPM downbeat). Seedance has no BPM control, so the tempo is
specified physically -- steps per second -- and verified after with dance_tempo.py.
"""
from generate import generate_image, generate_video

IMAGE_PROMPT = (
    "Stylized illustrated girl mid-shuffle-dance in a wide empty warehouse at night, "
    "face in shadow, baggy pants and crop top, chunky sneakers, one heel kicked out in a "
    "running-man step, low wide camera angle framing her full body and the floor, "
    "haze lit by teal and magenta stage light, volumetric beams, reflective concrete, "
    "painterly cinematic animation style, dreamy neon palette, film grain, 4K"
)

VIDEO_PROMPT = (
    "She shuffle dances with a strict metronomic rhythm: roughly three footfalls every "
    "second, each step the same length as the last, never speeding up or slowing down. "
    "Running-man footwork, heels sliding back and kicking out, occasional T-step spin, "
    "weight snapping side to side on every step, baggy pants rippling on each impact. "
    "Locked static low wide camera, no camera movement, no cuts, haze drifting in the beams."
)

if __name__ == "__main__":
    img = generate_image(IMAGE_PROMPT, "shuffle86.png")
    generate_video(img, VIDEO_PROMPT, "shuffle86.mp4", loop=False)
